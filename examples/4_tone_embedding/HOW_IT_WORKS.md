# HOW IT WORKS — 4_tone_embedding

**Question:** is `qthe_embedder.embed()` a usable *tone fingerprint* — does it
separate distinct tone trajectories, ignore the text, and survive wire noise?

**Method:** 12 canonical tone arcs (from example 1). Three measurements:

1. **Cross-tone ceiling** — cosine between all 66 pairs of tone embeddings.
2. **Text invariance** — same arc stretched across three different texts.
3. **Noise floor** — each cell's momentum randomized (p = f), 200 trials per f.

**Result (measured 2026-09-27):**

- Max cross-tone cosine: **0.9696** (coy vs wink); runner-ups awe/wink 0.9454,
  friendly/thinks-yes 0.9416.
- Text invariance: **0.8918**, not 1.0 (arc resampling to different token
  lengths changes the histogram/arc features — invariance only holds for
  identical trajectories).
- Noise: min cosine to clean drops below the cross-tone ceiling at every
  tested f, even 0.05 (0.8386 < 0.9696).

**Verdict: FALSIFIED** — and the failure is diagnostic, not accidental:

- The **histogram dominates** the vector (4 of 14 dims but the largest
  magnitudes). Tones sharing a dominant state — mostly-`up`+`hold` rhythms
  like coy/wink/awe, or mostly-flat statements — collide near 0.97.
- **Order information is under-weighted**: the spectral dims (flip rate,
  change rate) collapse *alternating* rhythms to nearly the same point.
- So the embedder as-is is a **coarse mood meter** (furious vs flat vs
  rising separates fine), not a fingerprint. Fix direction if revisited:
  upweight the run/spectral dims or add a bigram-histogram feature
  (16-dim adjacent-pair counts), which would separate coy (u-h-u-h) from
  friendly (f-u-u-f) exactly.

Exit code 1 = falsified, deliberately: the demo is an honest negative
result with the falsifying numbers printed.
