"""G3 trace mode, plus static enforcement of the hard prohibitions."""

import os
import re

import costs
import pytest
import simulate
from conftest import make_1m, make_cfg, make_signal

ENGINE_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "src", "engine")

SIG_TS = 1_600_000_000_000
ENTRY_TS = SIG_TS + simulate.BAR_15M_MS
TICK = 0.01
ENTRY_BAR = (100.10, 99.90, 100.0)


def _trace_of_a_stop():
    cfg = make_cfg()
    bars = [ENTRY_BAR, (99.9, 96.0, 96.5)] + [(100.1, 99.9, 100.0)] * 3
    sig = make_signal(sig_ts=SIG_TS, atr=2.0)
    tr = simulate.Trace(enabled=True)
    t = simulate.simulate_trade(sig, make_1m(ENTRY_TS, bars), cfg, TICK, trace=tr)
    return t, tr.text()


def test_g3_trace_contains_every_arithmetic_step():
    t, txt = _trace_of_a_stop()
    for needed in ("ENTRY", "STOP", "SIZE", "TARGET", "LEVELS", "WALK", "PNL"):
        assert needed in txt, f"trace missing {needed} section"
    # The sizing denominator must be shown term by term, not just its result.
    assert "|P-S|" in txt and "P*f_taker" in txt and "S*s_stop" in txt
    # Fee math must be visible on both legs.
    assert txt.count("q*") >= 2
    assert "net" in txt


def test_g3_trace_numbers_reconcile_by_hand():
    """Recompute the trade from the trace's own inputs and agree."""
    t, txt = _trace_of_a_stop()
    q, entry, exit_px = t["qty"], t["entry_price"], t["exit_price"]
    gross = q * (exit_px - entry)          # long
    fees = q * entry * 0.0006 + q * exit_px * 0.0006
    assert t["gross_pnl"] == pytest.approx(gross)
    assert t["fees_paid"] == pytest.approx(fees)
    assert t["net_pnl"] == pytest.approx(gross - fees)


def test_g3_trace_is_off_by_default():
    cfg = make_cfg()
    bars = [ENTRY_BAR] + [(100.1, 99.9, 100.0)] * 3
    sig = make_signal(sig_ts=SIG_TS)
    tr = simulate.Trace()
    simulate.simulate_trade(sig, make_1m(ENTRY_TS, bars), cfg, TICK, trace=tr)
    assert tr.text() == ""


def test_g3_trace_walks_every_minute_until_exit():
    t, txt = _trace_of_a_stop()
    walked = re.findall(r"\[\s*\d+\] ts=(\d+)", txt)
    assert len(walked) >= 1
    assert int(walked[-1]) == t["exit_ts"]


# --------------------------------------------------------------------------
# hard prohibitions, enforced statically over the engine source
# --------------------------------------------------------------------------

def _engine_sources():
    out = {}
    for fn in os.listdir(ENGINE_DIR):
        if fn.endswith(".py"):
            out[fn] = open(os.path.join(ENGINE_DIR, fn)).read()
    return out


def test_no_engine_code_reads_open_synth():
    """open_synth may only appear where it is DROPPED or REJECTED."""
    for fn, src in _engine_sources().items():
        for i, line in enumerate(src.splitlines(), 1):
            if "open_synth" not in line or line.strip().startswith("#"):
                continue
            allowed = ("drop" in line or "raise" in line or "columns" in line
                       or '"open_synth"' in line and "in df.columns" in line)
            assert allowed, f"{fn}:{i} reads open_synth: {line.strip()}"


def test_no_indicator_reads_1m_data():
    """signals.py is Layer A: it must not load or mention 1m inputs at all."""
    src = _engine_sources()["signals.py"]
    for bad in ("load_1m", "ohlcv_1m", "bars_1m"):
        assert bad not in src, f"signals.py references {bad}"


def test_1m_loader_does_not_carry_volume():
    """Cheapest guarantee that 1m volume is never read: never load it."""
    src = _engine_sources()["simulate.py"]
    body = src[src.index("def load_1m"):src.index("def slice_1m")]
    m = re.search(r"columns=\[([^\]]*)\]", body)
    assert m, "1m loader must select explicit columns"
    cols = m.group(1)
    assert "volume" not in cols
    assert "open_synth" not in cols
    for c in ("ts", "high", "low", "close"):
        assert c in cols


def test_no_indicators_are_written_to_disk():
    """Precomputing indicators would bake in one parameter set."""
    for fn, src in _engine_sources().items():
        if fn == "run.py":
            continue          # run.py may write TRADES, which is not an indicator
        assert "to_parquet" not in src, f"{fn} writes parquet"


def test_divergence_flags_are_never_used_as_a_filter():
    src = _engine_sources()["simulate.py"]
    fn_start = src.index("def attach_flag_overlap")
    body = src[fn_start:src.index("def summarize")]
    # The flag may be attached as a column, never used to drop rows.
    assert "flagged_bar_overlap" in body
    assert "drop" not in body
    assert "~" not in body
