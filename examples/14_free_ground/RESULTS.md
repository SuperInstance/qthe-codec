# 14_free_ground — RESULTS

Ran: `python3 demo.py` (exit 0). Zero-dep; imports `qthe_codec`, `qthe_compiler`.

## Direction advanced
**7TH-BIT lane** — ex 7's booked hint ("an escape-aware tone encoder must AVOID
timbre 3 on base cells") taken literally: what if a COMMON symbol doesn't need
tone at all and can burn its whole cell to ABSTAIN? The symbol then rides in the
cell itself, costing 0 data bits. This example prices that trade.

## Numbers

| claim | result |
|---|---|
| P1 table size costs nothing | SURVIVES — cells flat at 87 for tables 1–4; table 1 (space) drops 88 → 87 cells |
| P2 data-plane index-sum drop | SURVIVES — 35.6% / 46.5% / 43.3% / 34.4% (min 34.4%, threshold 25%) |
| P3 free cells mask tone | SURVIVES — 60.0% / 63.2% / 67.0% of cells masked; all-free text masks 100% |
| P4 retention = 1 − density | apparent 0.0000 leakage, but **an accounting identity**, and it breaks at high density (35% density → retention 0.0% vs predicted 65.0%). FALSIFIED |
| P5 exact roundtrip on the wire | FALSIFIED — mem layer exact on 4/6 texts; escape-aware wire receiver 0/6 |
| P6 phantom escapes | MEASURED — 1/10, 11/87, 11/106, 4/27 base cells wear timbre 3 |

## The two real findings

**1. The 2-bit abstain marker is a real bit budget, not free.**
`(3 << 6) = 0b11000000` — timbre 3 forces bits 4 and 5 of the byte to 1. So an
abstain cell's honest payload is only the bits BELOW a variable-width marker:
slot 0 carries 0 bits (the cell IS the symbol → exactly ONE truly zero-cost
symbol), slots 1–2 carry 1 bit, 3–6 carry 2, 7–14 carry 3. Slot k costs
`k << w`. The "free table" is therefore not free per entry; only the first
symbol is.

**2. The phantom-escape collision is unavoidable and structural.**
Wire timbre is `latin_timbre(momentum, data % 4)`, so for EVERY momentum state
there is exactly one data residue that sums to 3 — a base cell wearing the
escape marker. Measured on real streams: 1/10, 11/87, 11/106, 4/27 base cells.
A plaintext-only receiver misreads every one as RARE data.
`hold` is the only 3-safe momentum (its phantom residue is r=1, and
`latin_timbre(3, 3) = 2`), which is exactly why ex 7's "3-safe-choices" hint is
the *only* escape grammar that works.

## Verdict
The **free-symbol table is real but much smaller than it looked**: exactly one
symbol (space) is genuinely zero-cost, and the rest of the table must pay
`slot << w` payload bits inside the escape cell — it is a *repacking* of the
escape channel, not new capacity. And any symbol-based escape must ride on
`hold` or it collides with the Latin square. Honest next step: price the
`slot << w` table against plain base-plane indices (the data-plane index-sum
drop in P2 is the upside, the tone masking in P3 is the cost) and pick the
crossover.

Left uncommitted for review. No commits made.
