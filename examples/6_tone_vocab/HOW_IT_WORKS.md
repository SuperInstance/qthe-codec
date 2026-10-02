# HOW IT WORKS — 6_tone_vocab

**The idea:** examples 1–5 asked what the tone can *mean*. This one asks how
many meanings the tone channel can carry *reliably*. A tone is a momentum
trajectory — n steps over a 4-symbol alphabet {down, flat, up, hold}. One
flipped timbre byte silently rewrites one step, and a corrupted trajectory
can re-read as a different feeling. Feelings don't have checksums — unless
you design the vocabulary so they do.

## The construction

Treat each meaning as a codeword: an 8-token momentum sequence in the space
4^8 = 65,536. Build a vocabulary with minimum pairwise Hamming distance ≥ 3
by **greedy sphere-packing**: sweep all trajectories lexicographically, keep
a trajectory iff no kept trajectory lies within distance 2 (covering radius-2
balls; a candidate inside one is skippable, so kept codewords are ≥ 3 apart).

Distance ≥ 3 in Hamming space = any single momentum step can be corrupted
and the damaged trajectory is still strictly closer to the true codeword
than to any other — so nearest-neighbor decode corrects it exactly.

## The numbers (measured, this repo, 2026-09-28)

- **P1** — greedy single-error-correcting vocabulary: **1,024 meanings**,
  which is **39.1%** of the sphere-packing bound 65,536 / (1 + 8·3) = 2,621.
  Greedy leaves real room on the table (expected; perfect codes over Z4^8
  don't exist at these parameters).
- **P2** — a 12-meaning hand-carryable vocabulary (tenderness, sarcasm, awe,
  grief, playful, urgent, warmth, doubt, resolve, wonder, consolation,
  sparks) drawn from that code has minimum pairwise distance **4** (≥ 3
  required). A 12-feeling vocabulary fits on a stream as short as 8 tokens.
- **P3** — every single-tone corruption of every word (12 words × 8
  positions × 3 wrong momentum values = **288 trials**) decodes back to the
  original meaning: **288/288**. The text plane is untouched by design —
  "I love you" roundtrips exactly through the corrupted lane.

## Interpretation

The tone channel is dense: only 1.6% of raw trajectory space is spent to buy
single-error correction across 1,024 robust meanings. The cost is real but
modest, and the naive-reader property is untouched — the Latin square still
hides the whole vocabulary inside the top 2 bits.

## Run it

    python3 examples/6_tone_vocab/demo.py

Zero dependencies; imports `qthe_codec.py` from the repo root.
