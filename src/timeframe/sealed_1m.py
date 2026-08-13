"""THE SEALED 1m LOADER. Three layers, and the third one is not redundant.

WHY THIS EXISTS. Report 27 measured the per-trade upper bound on trades whose
exit levels could both sit inside a single 1h bar at 10.21%, against a 2.0%
criterion, and document 06 section 2 froze the verdict that exits are resolved
on 1m. Step 5.3.4 cannot resolve an exit until 1m bars can be read SAFELY.

WHY THIS IS NOT LIKE THE 1h LAYER'S SEAL. Every other error in this project is
recoverable: a miscounted skip rate can be recounted, a wrong denominator can be
fixed and the measurement re-run. A HOLDOUT BAR THAT HAS BEEN READ CANNOT BE
UNREAD. The window 2025-01-01 through 2026-07-26 has never been opened and its
entire value depends on that remaining true.

THE SPECIFIC HAZARD, AND IT IS NOT THE ONE THE 15m LAYER FACES. The 1m layer is
hive-partitioned by symbol and year, and BOTH SEALED YEARS EXIST ON DISK. A
query engine handed a directory PRUNES PARTITIONS BEFORE IT READS ROWS. If a
date predicate is applied after the load rather than pushed into the scan, the
sealed partition is OPENED AND READ and then filtered out of the result:

    THE OUTPUT IS CORRECT AND THE SEAL HAS BEEN BROKEN, AND NOTHING IN THE
    RETURNED DATA SHOWS IT HAPPENED.

Filtering rows is therefore not sufficient. The seal has to operate on WHICH
FILES ARE OPENED, which is what the three layers below do.

    LAYER 1 -- EXPLICIT ENUMERATION, NO DISCOVERY. This module builds its own
    list of files and hands that list to the reader, one path at a time. It
    never hands a directory, a glob, a dataset root or a partition root to the
    reader and lets it discover partitions. A sealed year is never named, and a
    file that is never named cannot be pruned, pushed down or footer-read.

    LAYER 2 -- POST-READ ASSERTION ON WHAT WAS OPENED. Every path this module
    passes to the reader is checked against the allowed years. A violation
    RAISES. It does not warn, log, or filter the answer clean.

    LAYER 3 -- THE INDEPENDENT ON-DISK CHECK. Layers 1 and 2 are NOT
    independent of each other: both reason over this module's own notion of
    which files it means to open, so a wrong enumeration is asserted over by the
    same wrong set and passes twice. Layer 3 walks the partition tree ON DISK,
    subtracts the allowed set, and requires every remaining file to be sealed or
    a sidecar. It catches a partition whose existence the enumeration did not
    anticipate, which is exactly what layers 1 and 2 cannot catch.

THE BOUNDARY IS NOT DECLARED HERE. `WINDOW_START`, `WINDOW_END` and
`ALLOWED_YEARS` are read from `src.timeframe.resample`, which derives them from
`src.folds.schedule.HOLDOUT_TEST_START`. Two independently declared boundaries
are two things that can drift apart, so this module declares none of its own --
asserted by test, and the mutation battery in report 29 widens the ONE
definition and watches this module's tests fail.

NO SIDECAR IS EVER OPENED. A dataset-level `_metadata` or `_common_metadata`
file describes ALL partitions, sealed ones included: row counts and per-column
min/max statistics. Min/max on a price column for a sealed partition IS holdout
information, and it is the subtlest way in, so every file whose name begins with
an underscore is excluded from the enumeration by construction and asserted
absent from the opened set.

WHAT THIS MODULE DOES NOT DO. It loads bars. It computes no indicator, compares
no level, pairs no bar with any position, and knows nothing about the exit rules
document 06 froze. 5.3.4 implements those; a test asserts the vocabulary of exit
resolution appears nowhere here.
"""

import os

import pandas as pd

from src.folds import schedule as sch
from src.timeframe import resample as rs

ROOT = rs.ROOT
DERIVED = rs.DERIVED

#: The hive layout this layer was written in by `src/data/build_derived.py`:
#: `ohlcv_1m/symbol=<SYM>/year=<YYYY>/<name>.parquet`.
LAYER_DIR = "ohlcv_1m"
SYMBOL_PREFIX = "symbol="
YEAR_PREFIX = "year="
PARQUET_SUFFIX = ".parquet"

#: Parquet's own convention for dataset-level sidecars -- `_metadata`,
#: `_common_metadata`, `_SUCCESS`. Excluded from every enumeration.
SIDECAR_PREFIX = "_"

BAR_MS = rs.BAR_1M_MS
SYMBOLS = rs.SYMBOLS

#: WHAT THE LOADER RETURNS, AND NOTHING ELSE.
#:
#: `open_synth` is dropped at the boundary, exactly as `schedule.load_bars` and
#: `resample._drop_open` drop it -- report 27 section 8 records that the column
#: is carried forward from the previous close and is not an observed price, so
#: no bar's first observed price exists at any resolution.
#:
#: VOLUME IS NOT CARRIED EITHER. Point 3R's standing rule is "No 1m volume. No
#: 1m open", which `src/engine/simulate.py` implements the same way and
#: `tests/test_holdout_seal.py` asserts: the cheapest way to guarantee a column
#: is never read is to not carry it at all. This is narrower than the derived
#: layer's own column set, deliberately, and report 29 records the choice.
COLUMNS = ("ts", "high", "low", "close")


class SealBreach(rs.HoldoutBreach):
    """A sealed partition was named, opened, or requested.

    Subclasses the 1h layer's own breach type so a caller that already refuses
    `HoldoutBreach` cannot accidentally let this one through, while the message
    names which seal fired.

    NEVER CAUGHT INSIDE THIS PACKAGE. Degrading a breach into a partial answer
    would convert the one unrecoverable error in this project into a silently
    wrong number.
    """


# ---------------------------------------------------------------------------
# The boundary. READ from the single definition, never restated.
# ---------------------------------------------------------------------------

def allowed_years():
    """The year partitions that may be opened, from `resample.ALLOWED_YEARS`."""
    return tuple(rs.ALLOWED_YEARS)


def sealed_boundary_ms():
    """First epoch ms of the sealed window, from `schedule.HOLDOUT_TEST_START`."""
    return rs.holdout_start_ms()


def readable_bounds_ms():
    """[lo, hi) in epoch ms of the window this loader may serve."""
    return rs.window_bounds_ms()


# ---------------------------------------------------------------------------
# LAYER 1 -- explicit enumeration. Path arithmetic; nothing is opened here.
# ---------------------------------------------------------------------------

def year_in_path(path):
    """The hive year component of `path`, or None if it carries none.

    Parsed from the path COMPONENT rather than by substring, so a directory that
    merely contains the text `year=` somewhere in its name cannot be mistaken
    for a partition key.
    """
    for part in os.path.normpath(str(path)).split(os.sep):
        if part.startswith(YEAR_PREFIX):
            token = part[len(YEAR_PREFIX):]
            if token.isdigit():
                return int(token)
    return None


def is_sealed_path(path):
    """THE SINGLE CLASSIFIER. Is this a partition the seal forbids opening?

    True only for a hive-partitioned path whose year is not allowed. A path with
    no year component -- the 15m layer's files, the flags, the folds -- is not a
    partition of this layer and is not classified as sealed by this predicate.

    ONE PREDICATE, USED EVERYWHERE. `src/analysis/structural_pass.py` and
    `tests/test_manifest_integrity.py` both classify manifest entries with this
    function rather than with a second copy of the year arithmetic, so there is
    one answer to "is this sealed" in the repository and not three.
    """
    year = year_in_path(path)
    if year is None:
        return False
    return year not in allowed_years()


def partition_dir(symbol, year, derived_dir=DERIVED):
    """The directory of one partition. The year is NAMED, never discovered."""
    return os.path.join(derived_dir, LAYER_DIR,
                        SYMBOL_PREFIX + str(symbol),
                        YEAR_PREFIX + str(int(year)))


def allowed_paths(symbol, years=None, derived_dir=DERIVED):
    """Every file this loader is permitted to open for `symbol`, enumerated.

    LAYER 1, AND IT IS THE LOAD-BEARING ONE. The years come from
    `allowed_years()` and are written into the path; the filesystem is consulted
    only for the file names INSIDE an already-named allowed year directory, and
    never for which years exist. A sealed year directory is therefore not
    listed, not named, and not handed to anything.

    `years`, when given, may only NARROW the allowed set. Naming a sealed year
    raises rather than being quietly dropped, because a caller that asked for
    2025 has a defect that silence would hide.

    SIDECARS ARE EXCLUDED HERE, at the only place a file name enters the list.
    """
    permitted = allowed_years()
    if years is None:
        wanted = permitted
    else:
        asked = sorted({int(y) for y in years})
        forbidden = [y for y in asked if y not in permitted]
        if forbidden:
            raise SealBreach(
                "year(s) %s lie at or past the sealed boundary %s; the "
                "readable years are %s. The seal is not maintained by the "
                "absence of the data -- every sealed partition exists on disk "
                "-- so a request naming one is refused here rather than "
                "silently narrowed." % (forbidden, sch.HOLDOUT_TEST_START,
                                        list(permitted)))
        wanted = tuple(y for y in permitted if y in set(asked))

    paths = []
    for year in wanted:
        directory = partition_dir(symbol, year, derived_dir=derived_dir)
        if not os.path.isdir(directory):
            continue
        for name in sorted(os.listdir(directory)):
            if name.startswith(SIDECAR_PREFIX):
                continue
            if not name.endswith(PARQUET_SUFFIX):
                continue
            paths.append(os.path.join(directory, name))

    # LAYER 2 IS APPLIED WHERE THE LIST IS PRODUCED, NOT ONLY WHERE IT IS
    # CONSUMED. `resample.load_1m` takes this list and reads it directly, with
    # no assertion of its own between the enumeration and the read, so an
    # assertion that lived only inside `load` would leave that caller
    # unprotected. Asserting here means no consumer can be handed a sealed path
    # at all, whatever it intends to do with it.
    return assert_opened(paths, "allowed_paths(%s)" % symbol)


def years_overlapping(start_ms, end_ms):
    """Allowed years whose calendar span intersects [start_ms, end_ms).

    Narrows the enumeration to the partitions a request actually needs, so a
    one-day range opens one file rather than three.
    """
    out = []
    for year in allowed_years():
        lo = sch.day_start_ms(_first_day(year))
        hi = sch.day_start_ms(_first_day(year + 1))
        if start_ms < hi and end_ms > lo:
            out.append(year)
    return tuple(out)


def _first_day(year):
    import datetime as _dt
    return _dt.date(int(year), 1, 1)


def paths_for(symbol, start_ms, end_ms, derived_dir=DERIVED):
    """Exactly the files `load` would open for this request, without opening
    any of them. Tests assert on this list directly."""
    years = years_overlapping(int(start_ms), int(end_ms))
    return allowed_paths(symbol, years=years, derived_dir=derived_dir)


# ---------------------------------------------------------------------------
# LAYER 2 -- the assertion on what was actually handed to the reader.
# ---------------------------------------------------------------------------

def assert_opened(paths, where):
    """Refuse if anything in `paths` is a partition the seal forbids.

    LAYER 2. Applied to the list the reader was given, not to the frame that
    came back: a row filter cannot tell you which files were opened, and it is
    the opening that is irreversible.

    Also refuses a sidecar and refuses a path with no year at all -- an
    unclassifiable path is not evidence of safety.
    """
    permitted = allowed_years()
    bad = []
    for path in paths:
        name = os.path.basename(str(path))
        year = year_in_path(path)
        if name.startswith(SIDECAR_PREFIX):
            bad.append((path, "dataset sidecar; describes ALL partitions"))
        elif year is None:
            bad.append((path, "no year component; unclassifiable"))
        elif year not in permitted:
            bad.append((path, "year %d is sealed" % year))
    if bad:
        raise SealBreach(
            "%s would open %d path(s) the seal forbids: %s. The readable years "
            "are %s and the sealed window begins %s. This is the one error in "
            "this project that cannot be undone by re-running anything."
            % (where, len(bad), bad, list(permitted), sch.HOLDOUT_TEST_START))
    return list(paths)


# ---------------------------------------------------------------------------
# LAYER 3 -- the independent on-disk check. Reads no parquet content.
# ---------------------------------------------------------------------------

def on_disk_inventory(derived_dir=DERIVED):
    """Walk the partition tree ON DISK. Pure path arithmetic, no parquet read.

    Returns {(symbol, year): [paths]} for every partition that EXISTS, sealed
    ones included. Listing a directory name is not reading a bar; the point of
    this function is to know what the seal has to guard against, which cannot be
    established from the loader's own allowed set.
    """
    inventory = {}
    root = os.path.join(derived_dir, LAYER_DIR)
    if not os.path.isdir(root):
        return inventory
    for sym_dir in sorted(os.listdir(root)):
        if not sym_dir.startswith(SYMBOL_PREFIX):
            continue
        symbol = sym_dir[len(SYMBOL_PREFIX):]
        sym_path = os.path.join(root, sym_dir)
        if not os.path.isdir(sym_path):
            continue
        for year_dir in sorted(os.listdir(sym_path)):
            if not year_dir.startswith(YEAR_PREFIX):
                continue
            token = year_dir[len(YEAR_PREFIX):]
            if not token.isdigit():
                continue
            year_path = os.path.join(sym_path, year_dir)
            if not os.path.isdir(year_path):
                continue
            inventory[(symbol, int(token))] = [
                os.path.join(year_path, f)
                for f in sorted(os.listdir(year_path))]
    return inventory


def audit(derived_dir=DERIVED):
    """LAYER 3. On-disk minus allowed; every remainder must be explained.

    THE ONLY CHECK HERE THAT IS INDEPENDENT OF THE LOADER'S OWN BOOKKEEPING.
    Layers 1 and 2 both reason over the set this module believes it should open.
    If that belief is wrong -- a partition nobody anticipated, a year directory
    added after this code was written -- both layers agree with each other and
    are both wrong. This walks the disk instead and requires that every file NOT
    in the allowed set is either sealed or a sidecar.

    Returns the inventory, the allowed set, the complement and its
    classification. `unexplained` must be empty and `sealed_in_allowed` must be
    empty; `assert_seal_holds` turns that into a raise.
    """
    inventory = on_disk_inventory(derived_dir=derived_dir)
    on_disk = {p for paths in inventory.values() for p in paths}

    allowed = set()
    for symbol in sorted({s for s, _ in inventory}):
        allowed.update(allowed_paths(symbol, derived_dir=derived_dir))

    complement = on_disk - allowed
    sealed = sorted(p for p in complement if is_sealed_path(p))
    sidecars = sorted(p for p in complement
                      if os.path.basename(p).startswith(SIDECAR_PREFIX)
                      and not is_sealed_path(p))
    unexplained = sorted(complement - set(sealed) - set(sidecars))
    sealed_in_allowed = sorted(p for p in allowed if is_sealed_path(p))

    return {
        "inventory": inventory,
        "partitions": len(inventory),
        "files_on_disk": len(on_disk),
        "allowed": sorted(allowed),
        "complement": sorted(complement),
        "sealed": sealed,
        "sidecars": sidecars,
        "unexplained": unexplained,
        "sealed_in_allowed": sealed_in_allowed,
        "sealed_years_present": sorted({y for _, y in inventory
                                        if y not in allowed_years()}),
        "ok": not unexplained and not sealed_in_allowed,
    }


def assert_seal_holds(derived_dir=DERIVED):
    """Run the layer-3 audit and RAISE on either failure mode."""
    result = audit(derived_dir=derived_dir)
    if result["sealed_in_allowed"]:
        raise SealBreach(
            "the allowed set contains %d SEALED path(s): %s. Layer 1's "
            "enumeration is wrong, which is the failure layers 1 and 2 cannot "
            "detect between themselves."
            % (len(result["sealed_in_allowed"]), result["sealed_in_allowed"]))
    if result["unexplained"]:
        raise SealBreach(
            "%d file(s) on disk are neither allowed, nor sealed, nor a "
            "sidecar: %s. A file the enumeration did not anticipate is exactly "
            "what this layer exists to find."
            % (len(result["unexplained"]), result["unexplained"]))
    return result


# ---------------------------------------------------------------------------
# The loader.
# ---------------------------------------------------------------------------

def _read_one(path):
    """One partition file, columns named explicitly.

    `open_synth` is not dropped after the fact -- it is NEVER MATERIALISED,
    because only `COLUMNS` are requested. That is the same thing
    `src/engine/simulate.py` does and it is strictly stronger than dropping:
    a column that was not read cannot be read.
    """
    import pyarrow.parquet as pq

    frame = pq.read_table(path, columns=list(COLUMNS)).to_pandas()
    frame = rs._drop_open(frame, path)
    for forbidden in ("open", "open_synth", "volume", "quote_volume"):
        if forbidden in frame.columns:
            raise ValueError("%s carries %r, which this loader must not return"
                             % (path, forbidden))
    return frame


def load(symbol, start_ms, end_ms, derived_dir=DERIVED):
    """1m bars for `symbol` over [start_ms, end_ms), in epoch milliseconds.

    A REQUEST THAT MEETS THE SEALED WINDOW RAISES. It is not truncated to the
    readable part, because silent truncation lets a caller believe it received
    the full range it asked for and then reason about a hole it does not know
    about. The exception names the seal.

    The end is EXCLUSIVE, so a request ending exactly at the boundary instant is
    the largest readable request and is permitted.
    """
    start_ms, end_ms = int(start_ms), int(end_ms)
    lo, hi = readable_bounds_ms()

    if end_ms <= start_ms:
        raise ValueError("empty or reversed range: [%d, %d)"
                         % (start_ms, end_ms))
    if start_ms < lo:
        raise ValueError(
            "start %d precedes the readable window, which begins %d (%s)"
            % (start_ms, lo, rs.WINDOW_START))
    if end_ms > hi:
        raise SealBreach(
            "%s: the requested range [%d, %d) intersects the SEALED window, "
            "which begins at %d (%s) and runs to the end of the data. The "
            "readable window ends at %d (%s inclusive). The request is REFUSED "
            "rather than narrowed: a truncated answer would look like a "
            "complete one." % (symbol, start_ms, end_ms, sealed_boundary_ms(),
                               sch.HOLDOUT_TEST_START, hi, rs.WINDOW_END))

    paths = paths_for(symbol, start_ms, end_ms, derived_dir=derived_dir)
    if not paths:
        raise FileNotFoundError(
            "%s: no readable 1m partition covers [%d, %d) under %s"
            % (symbol, start_ms, end_ms, derived_dir))

    opened = assert_opened(paths, "load(%s)" % symbol)
    frame = pd.concat([_read_one(p) for p in opened], ignore_index=True)
    assert_opened(opened, "load(%s) [post-read]" % symbol)

    frame = frame[(frame["ts"] >= start_ms) & (frame["ts"] < end_ms)]
    frame = frame.sort_values("ts", kind="mergesort").reset_index(drop=True)
    frame = frame[list(COLUMNS)]
    return rs.assert_sealed(frame, "sealed_1m.load(%s)" % symbol)
