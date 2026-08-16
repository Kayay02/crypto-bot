"""Guards for bucket aggregation and, above all, for the holdout seal.

Resampling is a NEW CODE PATH ONTO SEALED DATA. The 1m layer is partitioned by
year and year=2025 / year=2026 exist on disk, so the seal is not maintained by
the data's absence -- it is maintained by an explicit filter, and a filter that
nothing tests is a filter that will be widened by someone in a hurry. The
planted mutation at the bottom widens it and is required to be caught.

Synthetic expectations here are computed by hand, never from module output.
"""

import ast
import datetime as dt
import os

import numpy as np
import pandas as pd
import pytest

from src.folds import schedule as sch
from src.timeframe import resample as rs

MIN = 60_000


def _bars(ts_list, highs, lows, closes, vols=None):
    return pd.DataFrame({
        "ts": ts_list,
        "high": highs,
        "low": lows,
        "close": closes,
        "volume": vols if vols is not None else [1.0] * len(ts_list),
    })


# ---------------------------------------------------------------------------
# 1. Aggregation exactness.
# ---------------------------------------------------------------------------

def test_aggregation_is_exact_on_a_known_series():
    """Two full 5m buckets from ten 1m bars, every field checked by hand."""
    ts = [i * MIN for i in range(10)]
    highs = [10, 12, 11, 15, 13, 20, 18, 22, 19, 21]
    lows = [5, 6, 3, 7, 8, 14, 11, 16, 15, 17]
    closes = [8, 9, 7, 14, 12, 18, 15, 20, 17, 19]
    vols = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
    bars, stats = rs.resample(_bars(ts, highs, lows, closes, vols), 5 * MIN, 5)

    assert len(bars) == 2
    assert stats["buckets_dropped"] == 0
    # Bucket 0 covers bars 0-4, bucket 1 covers bars 5-9.
    assert list(bars["ts"]) == [0, 5 * MIN]
    assert list(bars["high"]) == [15, 22]          # max of highs, exactly
    assert list(bars["low"]) == [3, 11]            # min of lows, exactly
    assert list(bars["close"]) == [12, 19]         # LAST close, not max/min
    assert list(bars["volume"]) == [15, 40]        # sum


def test_close_is_the_chronologically_last_not_the_largest():
    """A falling bucket: last close is the smallest value in it."""
    ts = [i * MIN for i in range(5)]
    bars, _ = rs.resample(_bars(ts, [10] * 5, [1] * 5, [9, 8, 7, 6, 5]),
                          5 * MIN, 5)
    assert list(bars["close"]) == [5]


def test_close_survives_shuffled_input():
    """Input order must not decide `close`; the sort inside resample must."""
    ts = [4 * MIN, 0, 3 * MIN, 1 * MIN, 2 * MIN]
    closes = [50, 10, 40, 20, 30]
    bars, _ = rs.resample(_bars(ts, [99] * 5, [1] * 5, closes), 5 * MIN, 5)
    assert list(bars["close"]) == [50]
    assert list(bars["ts"]) == [0]


# ---------------------------------------------------------------------------
# 2. Incomplete-bucket rejection.
# ---------------------------------------------------------------------------

def test_incomplete_bucket_is_dropped_not_emitted():
    """A gap leaves a short bucket whose range is understated. It must vanish.

    Ten minutes of data with minutes 5 and 6 missing: bucket 1 has 3 bars, not
    5, and its high (20) misses the true high (25) that the missing bars would
    have carried. Emitting it would bias ATR DOWN -- the direction that makes a
    timeframe look admissible when it is not.
    """
    ts = [0, 1 * MIN, 2 * MIN, 3 * MIN, 4 * MIN, 7 * MIN, 8 * MIN, 9 * MIN]
    highs = [10, 10, 10, 10, 10, 20, 20, 20]
    lows = [1] * 8
    closes = [5] * 8
    bars, stats = rs.resample(_bars(ts, highs, lows, closes), 5 * MIN, 5)

    assert stats["buckets_formed"] == 2
    assert stats["buckets_dropped"] == 1
    assert stats["buckets_kept"] == 1
    assert stats["dropped_pct"] == pytest.approx(50.0)
    assert list(bars["ts"]) == [0], "the short bucket was emitted"
    assert 20 not in list(bars["high"])


def test_every_bucket_short_means_nothing_survives():
    ts = [0, 20 * MIN, 40 * MIN]
    bars, stats = rs.resample(_bars(ts, [1, 1, 1], [0, 0, 0], [1, 1, 1]),
                              5 * MIN, 5)
    assert len(bars) == 0
    assert stats["buckets_dropped"] == 3
    assert stats["dropped_pct"] == pytest.approx(100.0)


def test_overfull_bucket_is_an_error_not_a_drop():
    """More sub-bars than the period holds means duplicate timestamps."""
    ts = [0, 0, 1 * MIN, 2 * MIN, 3 * MIN, 4 * MIN]
    with pytest.raises(ValueError, match="MORE than the expected"):
        rs.resample(_bars(ts, [1] * 6, [0] * 6, [1] * 6), 5 * MIN, 5)


def test_no_forward_fill_or_padding_occurs():
    """The kept bucket count must equal the number of FULL buckets, exactly."""
    ts = [i * MIN for i in range(5)] + [i * MIN for i in range(10, 15)]
    bars, stats = rs.resample(
        _bars(ts, [1] * 10, [0] * 10, [1] * 10), 5 * MIN, 5)
    # Buckets at 0 and 10min are full; the 5min bucket does not exist at all.
    assert list(bars["ts"]) == [0, 10 * MIN]
    assert stats["buckets_formed"] == 2


# ---------------------------------------------------------------------------
# 4. 15m identity.
# ---------------------------------------------------------------------------

def test_15m_at_factor_one_is_the_identity_on_hlc():
    rng = np.random.default_rng(7)
    n = 200
    ts = [i * 15 * MIN for i in range(n)]
    highs = rng.uniform(100, 110, n)
    lows = rng.uniform(80, 95, n)
    closes = rng.uniform(90, 105, n)
    src = _bars(ts, highs, lows, closes)
    bars, stats = rs.resample(src, 15 * MIN, 1)

    assert stats["buckets_dropped"] == 0
    assert list(bars["ts"]) == list(src["ts"])
    for col in ("high", "low", "close"):
        # Exact, bit-for-bit: a factor-1 aggregation must not perturb a float.
        assert bars[col].to_numpy().tolist() == src[col].to_numpy().tolist()


def test_15m_timeframe_spec_is_a_passthrough():
    assert rs.TIMEFRAMES["15m"] == (15 * MIN, "15m", 1)


def test_bucket_alignment_is_epoch_floored_to_natural_boundaries():
    """1d buckets land on UTC midnight; 4h on 00/04/08/12/16/20 UTC."""
    day0 = sch.day_start_ms(dt.date(2023, 6, 15))
    ts = [day0 + i * 15 * MIN for i in range(96 * 2)]
    bars, _ = rs.resample(_bars(ts, [1] * 192, [0] * 192, [1] * 192),
                          1440 * MIN, 96)
    for t in bars["ts"]:
        d = dt.datetime.fromtimestamp(t / 1000, dt.timezone.utc)
        assert (d.hour, d.minute, d.second) == (0, 0, 0)

    bars4, _ = rs.resample(_bars(ts, [1] * 192, [0] * 192, [1] * 192),
                           240 * MIN, 16)
    for t in bars4["ts"]:
        d = dt.datetime.fromtimestamp(t / 1000, dt.timezone.utc)
        assert d.hour % 4 == 0 and d.minute == 0


def test_every_candidate_period_divides_a_day_exactly():
    """Why epoch flooring is sufficient: no period straddles UTC midnight."""
    for tf, (period_ms, _, _) in rs.TIMEFRAMES.items():
        assert 86_400_000 % period_ms == 0, tf


def test_timeframe_order_is_finest_first():
    """The rule selects the FINEST admissible timeframe, so order matters."""
    periods = [rs.TIMEFRAMES[tf][0] for tf in rs.TIMEFRAME_ORDER]
    assert periods == sorted(periods)
    assert rs.TIMEFRAME_ORDER == ("5m", "15m", "1h", "4h", "1d")


# ---------------------------------------------------------------------------
# 5. HOLDOUT SEAL. The planted mutation this file exists for.
# ---------------------------------------------------------------------------

def test_window_end_is_strictly_before_the_holdout_boundary():
    """PLANTED MUTATION GUARD: the window widened to reach the holdout.

    THE MUTATION. In `src/timeframe/resample.py`, widen the date filter --
    either `WINDOW_END` past 2024-12-31 or `ALLOWED_YEARS` to include 2025 --
    so the loaders admit sealed bars.

    WHY IT WOULD OTHERWISE PASS UNNOTICED. The 1m layer physically contains
    year=2025 and year=2026 directories. Nothing about a widened filter fails
    at import, at load, or in any ATR figure -- the numbers simply get quietly
    better-sampled and the holdout is spent without anyone deciding to spend
    it. Both halves of the filter are therefore asserted directly, and the
    loaded data is checked independently below.

    Confirmed to fail under the mutation before being committed.
    """
    assert rs.WINDOW_END < sch.HOLDOUT_TEST_START
    assert rs.WINDOW_END == dt.date(2024, 12, 31)
    assert rs.WINDOW_START == dt.date(2022, 1, 1)
    # Adjacent, so no day is silently skipped either.
    assert rs.WINDOW_END + dt.timedelta(days=1) == sch.HOLDOUT_TEST_START
    # And the year filter cannot reach the holdout.
    assert rs.ALLOWED_YEARS == (2022, 2023, 2024)
    assert max(rs.ALLOWED_YEARS) < sch.HOLDOUT_TEST_START.year
    lo, hi = rs.window_bounds_ms()
    assert hi <= rs.holdout_start_ms()


def test_assert_sealed_refuses_a_holdout_bar():
    """The guard must be able to REFUSE, or it proves nothing."""
    sealed = rs.holdout_start_ms()
    ok = pd.DataFrame({"ts": [sealed - 1]})
    assert rs.assert_sealed(ok, "test") is ok
    for bad_ts in (sealed, sealed + 1, sealed + 86_400_000):
        with pytest.raises(rs.HoldoutBreach, match="sealed holdout boundary"):
            rs.assert_sealed(pd.DataFrame({"ts": [bad_ts]}), "test")
    # An empty frame is vacuously sealed, not an error.
    rs.assert_sealed(pd.DataFrame({"ts": []}), "test")


def test_one_minute_partition_paths_exclude_the_holdout_years():
    """The 2025/2026 partitions exist on disk and must not be opened."""
    for sym in rs.SYMBOLS:
        paths = rs._one_minute_paths(sym)
        assert paths, "no 1m partitions found for %s" % sym
        for p in paths:
            assert "year=2025" not in p and "year=2026" not in p, p
        years = {int(p.split("year=")[1].split(os.sep)[0]) for p in paths}
        assert years <= set(rs.ALLOWED_YEARS), years
    # The seal is a filter, not an accident: prove the sealed years are there.
    on_disk = os.path.join(rs.DERIVED, "ohlcv_1m", "symbol=BTCUSDT", "year=2025")
    assert os.path.isdir(on_disk), (
        "expected year=2025 to exist on disk -- if it does not, this test is "
        "not proving the filter does any work")


@pytest.mark.parametrize("timeframe", list(rs.TIMEFRAME_ORDER))
def test_no_loaded_or_resampled_bar_reaches_the_holdout(timeframe):
    """End to end, on the real data, at every candidate timeframe."""
    sealed = rs.holdout_start_ms()
    for sym in rs.SYMBOLS:
        bars, _ = rs.build(sym, timeframe)
        assert len(bars)
        assert int(bars["ts"].max()) < sealed
        assert int((bars["ts"] >= sealed).sum()) == 0
        last = dt.datetime.fromtimestamp(int(bars["ts"].max()) / 1000,
                                         dt.timezone.utc)
        assert last.year == 2024


def test_source_loaders_stop_at_the_window_edge():
    for sym in rs.SYMBOLS:
        for loader in (rs.load_15m, rs.load_1m):
            df = loader(sym)
            lo, hi = rs.window_bounds_ms()
            assert int(df["ts"].min()) >= lo
            assert int(df["ts"].max()) < hi


# ---------------------------------------------------------------------------
# 6 and 7. Open-price and firewall guards over the whole package.
# ---------------------------------------------------------------------------

def _package_sources():
    import src.timeframe as pkg
    d = os.path.dirname(pkg.__file__)
    return [os.path.join(d, f) for f in sorted(os.listdir(d))
            if f.endswith(".py")]


def test_open_synth_appears_nowhere_in_the_package():
    """ATR needs only H/L/C. A synthesised open has no business here.

    `resample.py` legitimately DROPS the column, so the name appears once as a
    string literal in a drop list. Anything beyond that -- a read, an
    assignment, an aggregation -- is the defect this guards.
    """
    for path in _package_sources():
        src = open(path).read()
        tree = ast.parse(src)
        for node in ast.walk(tree):
            # Reading it as an attribute or a subscript key is the failure.
            if isinstance(node, ast.Attribute) and node.attr == "open_synth":
                pytest.fail("%s reads .open_synth" % path)
            if isinstance(node, ast.Name) and node.id == "open_synth":
                pytest.fail("%s binds open_synth" % path)
        # The only permitted occurrences are inside the drop tuple and prose.
        assert src.count('"open_synth"') <= 1, path


from src.firewall import PERFORMANCE_NAMES  # noqa: E402
"""The canonical twelve-name list, defined once at `src/firewall.py`.

Previously written out in full here. Eighteen copies had drifted into two
different lists; this module now imports the one definition."""


def test_no_performance_quantity_appears_in_the_package():
    """FIREWALL GUARD, over identifiers and string literals, not prose.

    The docstrings NAME the prohibited quantities in order to state the
    prohibition, so a raw grep would fire on the statement of the rule rather
    than a violation of it. Docstrings are excluded; everything else is not.
    """
    for path in _package_sources():
        tree = ast.parse(open(path).read())
        docstrings = set()
        for node in ast.walk(tree):
            if isinstance(node, (ast.Module, ast.FunctionDef, ast.ClassDef)):
                d = ast.get_docstring(node, clean=False)
                if d is not None:
                    docstrings.add(d)
        names = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Name):
                names.add(node.id)
            elif isinstance(node, ast.Attribute):
                names.add(node.attr)
            elif isinstance(node, ast.arg):
                names.add(node.arg)
            elif isinstance(node, (ast.FunctionDef, ast.ClassDef)):
                names.add(node.name)
            elif isinstance(node, ast.Constant) and isinstance(node.value, str):
                if node.value not in docstrings:
                    names.add(node.value)
        blob = " ".join(names).lower()
        for banned in PERFORMANCE_NAMES:
            assert banned not in blob, "%r used as a name in %s" % (banned, path)


BANNED_IMPORTS = ("simulate", "signals", "costs", "src.engine", "src.sweep",
                  "src.analysis", "src.regime")


def test_package_imports_no_engine_strategy_or_analysis_module():
    """Checked over the IMPORT GRAPH, not the source text.

    The docstrings say "no trade is simulated" in order to state the
    prohibition, so a text grep fires on the statement of the rule rather than
    on a violation. What actually matters is what the modules import.
    """
    for path in _package_sources():
        tree = ast.parse(open(path).read())
        imported = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for a in node.names:
                    imported.add(a.name)
            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    imported.add(node.module)
                    for a in node.names:
                        imported.add("%s.%s" % (node.module, a.name))
        for mod in imported:
            for banned in BANNED_IMPORTS:
                assert not (mod == banned or mod.startswith(banned + ".")), (
                    "%s imports %r" % (path, mod))
        # The only project dependency permitted is the fold schedule, which is
        # where the holdout boundary is defined.
        project = {m for m in imported if m.startswith("src.")}
        assert project <= {"src.folds", "src.folds.schedule", "src.timeframe",
                           "src.timeframe.resample",
                           "src.timeframe.sealed_1m"}, (path, project)
