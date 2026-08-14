# THE STANDING PROJECT BRIEF — TRANSCRIBED

## 1. WHAT THIS DOCUMENT IS

**This is a verbatim transcription of the standing project premises as given by
the project owner in conversation.** It is the source those premises are cited
from. It is not a derivation, and it is not a summary of any derivation.

**IT SUPERSEDES AND AMENDS NOTHING.** It is non-normative with respect to every
frozen document in this repository, all of which were written against the
premises recorded here and all of which already assume them.

**THE AUTHORITY FOR EACH PREMISE IS THE CONVERSATION IT CAME FROM.** This file
does not confer authority on them and cannot; what it does is make that
conversation **checkable** by a reader who has only the repository.

**WHY IT EXISTS.** `docs/handoff/31_point_5_closing.md` §12.1 records that the
project's foundational premises appeared in no committed file, that they existed
only in conversation, and that at least one frozen document derives a central
figure from one of them — and therefore rested on a premise no reader of this
repository could check. **This file is the transcription that defect called
for.** Writing it down changes none of the premises and settles none of the
questions they leave open.

**THE WORDING IS PRESERVED AS IT STANDS**, including where it is hedged,
approximate, range-valued or unresolved. **Where the source wording is loose,
the looseness is the content**, because every frozen document was written
against the loose version and not against a tightened one.

---

## 2. THE PREMISES, TRANSCRIBED

**Capital:** approximately $2,000.

**Risk per trade:** never more than 1% (that is, $20), enforced after fees and
estimated slippage.

**Assets:** crypto only — BTC, ETH, SOL.

**Exchange:** Bitget by default. A switch is to be proposed only if there is a
strong reason (data quality, API reliability, fees, historical data), and the
case is to be made if so.

**Style:** intraday. The timeframe is to be chosen jointly; 5m, 15m and 1h are
named as candidates, with tradeoffs to be weighed.

**Drawdown tolerance:** a 30–50% peak-to-trough drawdown is acceptable if the
long-run edge is real, but risk controls are still to be designed, and a
drawdown that looks like a broken strategy rather than variance is to be flagged
as such.

**Indicators:** 3 to 4, proposed with justification — ideally a trend or
momentum indicator, an oscillator, and at least one volume indicator. The
project owner's stated position is that volume analysis is underrated and that
it should be central rather than decorative, and that the indicators must
combine into one coherent thesis rather than a stack.

**Fee honesty:** before any strategy is treated as promising, Bitget's fee
mathematics is to be modelled — maker and taker, both sides of a round trip —
and the win rate and reward-to-risk needed merely to break even after costs
stated. If the style is very hard at this account size, that is to be said
plainly, together with what would improve the odds.

**Regime-aware validation:** characterise the current market regime in
measurable terms; test across multiple historical windows resembling it; test
across different regimes to find where the strategy breaks; use walk-forward
analysis and a strict out-of-sample holdout; run parameter-sensitivity checks. A
strategy that works only at one exact parameter setting is curve-fit and is to
be flagged.

**A backtest is a hypothesis, never proof.** "Profitable in backtest" is
unproven until it survives paper trading. Overfitting, look-ahead bias and
survivorship are to be watched for.

**Not financial advice.** Neither party predicts markets. The goal is a
disciplined, testable process, not a promise of profit.

---

## 3. WHAT THIS DOCUMENT DELIBERATELY EXCLUDES, AND WHY

**DERIVED QUANTITIES ARE EXCLUDED.** This file records premises. It does not
record anything reasoned from them.

**THE EXCLUSION, NAMED EXPLICITLY.** The project's book-level open risk limit is
derived in `docs/design/05_aggregate_risk_budget.md` §2, from the drawdown
tolerance recorded in §2 above. **It is not restated here.** The premise and its
consequence each have exactly one home, and a figure with two homes is a figure
that can drift between them.

**THE WORKING-METHOD RULES ARE EXCLUDED.** One point at a time, decisions before
code, no code in chat, and the artifact read-back protocol are committed at
`docs/handoff/31_point_5_closing.md` §13. They are not premises about the
strategy or the account, and restating them here would create the same two-homes
problem in a second place.

---

## 4. CHANGE DISCIPLINE

**A CHANGE TO ANY PREMISE RECORDED HERE IS A NEW DOCUMENT WITH ITS OWN COMMIT
AND AN EXPLICIT STATEMENT OF WHAT CHANGED AND WHY — NEVER A SILENT EDIT TO THIS
FILE.**

This is the procedure `docs/design/05_aggregate_risk_budget.md` §11 sets for
itself, applied here on the same terms. **A silent edit is a contamination
event**, and it is a worse one in this file than in most: the frozen documents
downstream were written against the wording above, so an edit here retroactively
changes what they were written against, without leaving a trace in either.
