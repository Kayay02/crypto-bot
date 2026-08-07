"""Fold generation from the fixed calendar rule (§4.2).

Rolling 6-month train / 3-month test / 3-month step across 2022-04-01 ->
2024-12-31, giving exactly nine folds. Adjacent training windows overlap by
50%: the nine folds are a STABILITY PROBE, NOT NINE INDEPENDENT TRIALS, and if
they are ever counted as trials the arithmetic is wrong.

Rolling rather than anchored so that constant training length makes
fold-to-fold parameter variation attributable to the market rather than to
estimation noise shrinking as the window grows.

The rule is a pure function of the constants below. No data file is read to
build a schedule, so `build_schedule()` is deterministic and reproducible
without the dataset present.

BOUNDARIES. Start dates are inclusive at 00:00:00Z; end dates are inclusive at
23:45:00Z, the last 15m bar of that day. Train and test are contiguous:
test_start is the day after train_end.
"""

import datetime as dt
import json
import os
import subprocess

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DERIVED = os.path.join(ROOT, "data", "derived")
FOLDS_DIR = os.path.join(DERIVED, "folds")
FOLDS_PATH = os.path.join(FOLDS_DIR, "folds.json")

BAR_15M_MS = 900_000
DAY_MS = 86_400_000
# Last 15m bar of a day opens at 23:45.
LAST_BAR_OFFSET_MS = DAY_MS - BAR_15M_MS

# ---- the calendar rule. Decided in advance; never fitted. -----------------
IS_START = dt.date(2022, 4, 1)      # Q1 2022 is warm-up and is never traded
IS_END = dt.date(2024, 12, 31)      # the contamination ledger's own seam
TRAIN_MONTHS = 6
TEST_MONTHS = 3
STEP_MONTHS = 3
WARMUP_DAYS = 45
EXPECTED_FOLDS = 9

# ---- holdout: DEFINED here, never LOADED ---------------------------------
HOLDOUT_TEST_START = dt.date(2025, 1, 1)
HOLDOUT_TEST_END = dt.date(2026, 7, 26)

# First bar present in the derived layer. Used only to assert fold 1's buffer
# is fully available -- never to move a boundary.
DATA_START = dt.date(2022, 1, 1)


def log(msg):
    print(msg, flush=True)


def git_revision():
    """Commit hash of the code that produced this artifact.

    Suffixed '-dirty' when the working tree has uncommitted changes, so an
    artifact can never claim provenance it cannot reproduce.
    """
    try:
        rev = subprocess.run(["git", "-C", ROOT, "rev-parse", "HEAD"],
                             capture_output=True, text=True, timeout=10)
        if rev.returncode != 0:
            return "unknown"
        head = rev.stdout.strip()
        st = subprocess.run(["git", "-C", ROOT, "status", "--porcelain"],
                            capture_output=True, text=True, timeout=10)
        if st.returncode != 0:
            return f"{head}-dirty"
        return f"{head}-dirty" if st.stdout.strip() else head
    except (OSError, subprocess.SubprocessError):
        return "unknown"


# ---------------------------------------------------------------------------
# calendar helpers
# ---------------------------------------------------------------------------

def add_months(d, n):
    """Add `n` calendar months to date `d`, clamping the day if it overflows.

    Every boundary the rule produces lands on the first of a month, so the
    clamp never fires in production; it exists so the helper is total rather
    than raising on a date it was not expected to see.
    """
    total = (d.year * 12 + (d.month - 1)) + n
    y, m = divmod(total, 12)
    m += 1
    day = min(d.day, _days_in_month(y, m))
    return dt.date(y, m, day)


def _days_in_month(y, m):
    if m == 12:
        return 31
    return (dt.date(y, m + 1, 1) - dt.date(y, m, 1)).days


def day_start_ms(d):
    """Epoch ms at 00:00:00Z on date `d` -- the first 15m bar of the day."""
    return int(dt.datetime(d.year, d.month, d.day,
                           tzinfo=dt.timezone.utc).timestamp() * 1000)


def day_last_bar_ms(d):
    """Epoch ms at 23:45:00Z on date `d` -- the last 15m bar of the day."""
    return day_start_ms(d) + LAST_BAR_OFFSET_MS


def day_end_exclusive_ms(d):
    """Epoch ms at 00:00:00Z on the day AFTER `d`.

    Provided because the repo's existing range helpers (regime concordance) are
    end-EXCLUSIVE, and mixing the two conventions silently drops or double-counts
    the final bar of a period.
    """
    return day_start_ms(d) + DAY_MS


def iso(d):
    return d.isoformat()


# ---------------------------------------------------------------------------
# schedule
# ---------------------------------------------------------------------------

def build_schedule(is_start=IS_START, is_end=IS_END, train_months=TRAIN_MONTHS,
                   test_months=TEST_MONTHS, step_months=STEP_MONTHS,
                   warmup_days=WARMUP_DAYS, expected=EXPECTED_FOLDS,
                   data_start=DATA_START):
    """The nine in-sample folds. Pure function of the calendar constants.

    Raises rather than adjusting anything if the rule does not produce
    `expected` folds ending exactly on `is_end`. A schedule quietly reshaped to
    make a count come out right is not the pre-registered schedule.
    """
    folds, k = [], 0
    while True:
        train_start = add_months(is_start, step_months * k)
        test_start = add_months(train_start, train_months)
        train_end = test_start - dt.timedelta(days=1)
        next_start = add_months(test_start, test_months)
        test_end = next_start - dt.timedelta(days=1)
        if test_end > is_end:
            break
        folds.append({
            "fold_id": k + 1,
            "warmup_start": train_start - dt.timedelta(days=warmup_days),
            "train_start": train_start,
            "train_end": train_end,
            "test_start": test_start,
            "test_end": test_end,
        })
        k += 1
        if k > 1000:                       # runaway guard, never reached
            raise RuntimeError("fold generation did not terminate")

    if len(folds) != expected:
        raise ValueError(
            f"calendar rule produced {len(folds)} folds, expected {expected}. "
            f"The rule is pre-registered -- report the discrepancy, do not "
            f"adjust the rule to fit.")
    if folds[-1]["test_end"] != is_end:
        raise ValueError(
            f"final fold test_end is {folds[-1]['test_end']}, expected "
            f"{is_end}. Report the discrepancy, do not adjust the rule.")
    if folds[0]["warmup_start"] < data_start:
        raise ValueError(
            f"fold 1 warmup_start {folds[0]['warmup_start']} precedes the "
            f"first available bar {data_start}; the buffer would be truncated "
            f"and §4.2 grants no truncated-first-fold exception.")
    return folds


def holdout_definition(warmup_days=WARMUP_DAYS):
    """The holdout, DEFINED. Nothing here loads a bar of it.

    No train period: the holdout is evaluated once, whole-window, against a
    candidate selected entirely elsewhere by the 4.3/4.4 procedure.
    """
    return {
        "fold_id": "holdout",
        "warmup_start": HOLDOUT_TEST_START - dt.timedelta(days=warmup_days),
        "train_start": None,
        "train_end": None,
        "test_start": HOLDOUT_TEST_START,
        "test_end": HOLDOUT_TEST_END,
    }


def fold_periods(fold):
    """(name, start_date, end_date) for each period a fold defines.

    `warmup` spans warmup_start -> the day before train_start: indicators are
    computed continuously from warmup_start, but the traded population begins
    at train_start. Because train and test are contiguous, this one buffer
    covers both; there is deliberately no separate buffer before test_start.
    """
    out = [("warmup", fold["warmup_start"],
            fold["train_start"] - dt.timedelta(days=1))]
    if fold["train_start"] is not None:
        out.append(("train", fold["train_start"], fold["train_end"]))
    out.append(("test", fold["test_start"], fold["test_end"]))
    return out


def _serialise(fold):
    o = {"fold_id": fold["fold_id"]}
    for k in ("warmup_start", "train_start", "train_end", "test_start",
              "test_end"):
        d = fold[k]
        o[k] = iso(d) if d is not None else None
        o[f"{k}_ms"] = (None if d is None else
                        (day_start_ms(d) if k.endswith("_start")
                         else day_last_bar_ms(d)))
    return o


def schedule_payload(folds=None, holdout=None):
    """The folds.json payload: definitions plus the rule that produced them."""
    folds = folds if folds is not None else build_schedule()
    holdout = holdout if holdout is not None else holdout_definition()
    return {
        "script": "src/folds/schedule.py",
        "git_commit": git_revision(),
        "calendar_rule": {
            "in_sample_start": iso(IS_START),
            "in_sample_end": iso(IS_END),
            "train_months": TRAIN_MONTHS,
            "test_months": TEST_MONTHS,
            "step_months": STEP_MONTHS,
            "warmup_days": WARMUP_DAYS,
            "expected_folds": EXPECTED_FOLDS,
            "boundary_convention": (
                "start dates inclusive at 00:00:00Z; end dates inclusive at "
                "23:45:00Z (last 15m bar of the day); test_start is the day "
                "after train_end"),
            "provenance": (
                "fixed calendar rule decided in advance; never derived from "
                "data and never from regime labels (§4.1)"),
        },
        "holdout_seal": (
            "DEFINED, NEVER LOADED. Loaders require authorised=True and "
            "refuse on the default path."),
        "folds": [_serialise(f) for f in folds],
        "holdout": _serialise(holdout),
    }


def write_schedule(path=FOLDS_PATH, payload=None):
    payload = payload or schedule_payload()
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w") as fh:
        json.dump(payload, fh, indent=2, sort_keys=True)
        fh.write("\n")
    return path


def load_schedule(path=FOLDS_PATH):
    if not os.path.exists(path):
        raise FileNotFoundError(
            f"fold schedule missing at {path}; generate it with "
            f"`python -m src.folds.schedule`")
    return json.load(open(path))


# ---------------------------------------------------------------------------
# data access -- holdout sealed
# ---------------------------------------------------------------------------

def is_holdout_range(start_date, end_date):
    """Does [start_date, end_date] touch 2025-01-01 or later?"""
    return end_date >= HOLDOUT_TEST_START


def load_bars(symbol, start_date, end_date, derived_dir=DERIVED,
              authorised=False):
    """15m bars over an inclusive date range. REFUSES the holdout by default.

    `authorised` defaults to False and must be passed explicitly to read
    anything at or after 2025-01-01. The holdout is evaluated ONCE, at step 9
    of the 4.4 sequence; every other read of it is a leak.

    `open_synth` is dropped at the boundary -- no downstream code may read a
    synthesized open, and there is no real `open` column to read.
    """
    import pyarrow.parquet as pq

    if is_holdout_range(start_date, end_date) and not authorised:
        raise PermissionError(
            f"range {start_date} -> {end_date} reaches the holdout "
            f"({HOLDOUT_TEST_START} onward), which is SEALED. Pass "
            f"authorised=True only for the single pre-registered holdout "
            f"evaluation at step 9 of the 4.4 sequence.")

    path = os.path.join(derived_dir, "ohlcv_15m", f"{symbol}.parquet")
    df = pq.read_table(path).to_pandas()
    if "open" in df.columns:
        raise ValueError(f"{path} exposes a real `open` column; Point 2 "
                         f"forbids it")
    df = df.drop(columns=["open_synth"])
    lo, hi = day_start_ms(start_date), day_end_exclusive_ms(end_date)
    df = df[(df["ts"] >= lo) & (df["ts"] < hi)]
    return df.sort_values("ts", kind="mergesort").reset_index(drop=True)


def bar_counts(symbols=("BTCUSDT", "ETHUSDT", "SOLUSDT"), folds=None,
               derived_dir=DERIVED):
    """Bars per period per symbol, for every in-sample fold.

    Never touches the holdout: only `build_schedule()` folds are counted.
    """
    folds = folds if folds is not None else build_schedule()
    out = {}
    for f in folds:
        per = {}
        for name, a, b in fold_periods(f):
            per[name] = {s: int(len(load_bars(s, a, b, derived_dir)))
                         for s in symbols}
        out[f["fold_id"]] = per
    return out


if __name__ == "__main__":
    folds = build_schedule()
    payload = schedule_payload(folds)
    path = write_schedule(payload=payload)
    log(f"[folds] {len(folds)} folds  commit {payload['git_commit']}")
    for f in folds:
        log(f"  fold {f['fold_id']}: warmup {f['warmup_start']}  "
            f"train {f['train_start']}..{f['train_end']}  "
            f"test {f['test_start']}..{f['test_end']}")
    h = holdout_definition()
    log(f"  holdout (DEFINED, NOT LOADED): warmup {h['warmup_start']}  "
        f"test {h['test_start']}..{h['test_end']}")
    log(f"[artifact] {path}")
