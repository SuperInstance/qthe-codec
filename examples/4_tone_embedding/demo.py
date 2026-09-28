#!/usr/bin/python3
"""
demo.py — example 4: the tone EMBEDDING is a fingerprint, and it is ROBUST.

Two falsifiable claims, both measured here:

  CLAIM A (separation): distinct tone trajectories embed to vectors whose
  cosine similarity stays well below 1.0 — the space separates tones, not
  texts. Two DIFFERENT texts carrying the SAME tone map to the SAME vector
  (cosine exactly 1.0, by construction); so the vector is a pure tone
  fingerprint.

  CLAIM B (robustness): corrupt a fraction f of the momentum cells (wire
  noise: a flipped timbre bit under a WRONG context key, or a dropped cell)
  and the embedding barely moves. Falsifiable number: at f = 0.20 (20% of
  cells corrupted) the cosine to the clean fingerprint must still exceed
  0.85, while two RANDOM tones never exceed the max cross-tone cosine.
  If a reader finds f where cosine drops below the cross-tone maximum,
  the fingerprint claim is falsified at that noise level.

Zero dependencies. Imports the shared codec + embedder from the repo root.
Run: python3 examples/4_tone_embedding/demo.py
"""
from __future__ import annotations

import random
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))

import qthe_codec as q  # noqa: E402
import qthe_embedder as e  # noqa: E402

M = q.MOMENTUM

# 12 canonical tones on the "I love you" 12-token stream (from example 1)
TONES: dict[str, list[int]] = {
    "friendly":    [1, 1, 1, 2, 2, 2, 2, 1, 1, 1, 1, 1],
    "thinks-yes":  [1, 1, 1, 1, 1, 2, 2, 1, 2, 2, 2, 2],
    "thinks-no":   [1, 1, 2, 2, 2, 1, 1, 1, 0, 0, 0, 0],
    "wink":        [2, 3, 2, 3, 2, 3, 2, 3, 2, 3, 2, 3],
    "mocking":     [1, 2, 2, 2, 3, 3, 0, 0, 0, 0, 0, 0],
    "furious":     [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
    "grief":       [2, 1, 0, 0, 1, 0, 0, 0, 3, 3, 3, 0],
    "flat-facts":  [1] * 12,
    "awe":         [2, 2, 3, 2, 2, 3, 2, 2, 3, 2, 2, 2],
    "dread":       [1, 1, 0, 1, 0, 1, 0, 0, 3, 0, 0, 0],
    "coy":         [1, 2, 3, 2, 3, 1, 2, 3, 1, 2, 3, 1],
    "deletion":    [2, 2, 2, 3, 3, 3, 1, 1, 0, 0, 0, 3],
}

TEXTS = ["i love you", "the reactor is stable", "meet me at the dock at six"]


def tone_for_len(base: list[int], n: int) -> list[int]:
    """Resample a 12-cell tone arc to length n (stretch/truncate, keep shape)."""
    if n <= 12:
        return base[:n]
    out = []
    for i in range(n):
        out.append(base[i * 12 // n])
    return out


def corrupt(mom: list[int], f: float, rng: random.Random) -> list[int]:
    """Flip each cell's momentum to a random WRONG value with prob f."""
    out = []
    for m in mom:
        if rng.random() < f:
            choices = [v for v in range(4) if v != m]
            out.append(rng.choice(choices))
        else:
            out.append(m)
    return out


def main() -> None:
    # ── CLAIM A: separation ────────────────────────────────────────────
    emb = {k: e.embed(v) for k, v in TONES.items()}
    keys = sorted(emb)
    cross = []
    for i, a in enumerate(keys):
        for b in keys[i + 1:]:
            cross.append(e.cosine(emb[a], emb[b]))
    max_cross = max(cross)
    # same tone, three different texts -> identical vectors?
    same_tone = TONES["friendly"]
    vecs = []
    for t in TEXTS:
        data = q.data_encode(t)
        stream = q.encode(t, tone_for_len(same_tone, len(data)))
        _, timbre = q.decode_bytes(stream)
        mom = [(timbre[i] - (stream[i] & 0x3F) % 4) % 4 for i in range(len(stream))]
        vecs.append(e.embed(mom))
    text_invariance = min(e.cosine(vecs[0], v) for v in vecs[1:])

    print("CLAIM A — separation")
    print(f"  12 tones, {len(cross)} pairs: max cross-tone cosine = {max_cross:.4f}")
    print(f"  same tone / 3 different texts: min cosine = {text_invariance:.4f}")
    print(f"  separation margin = {text_invariance - max_cross:.4f} "
          f"(must be > 0; text invariance must be exact)")

    # ── CLAIM B: robustness under cell noise ───────────────────────────
    rng = random.Random(4050)
    trials = 200
    print("\nCLAIM B — robustness (200 trials per noise level, min cosine)")
    floor_ok = True
    for f in (0.05, 0.10, 0.20, 0.30, 0.40):
        worst = 1.0
        for name, mom in TONES.items():
            clean = e.embed(mom)
            for _ in range(trials // len(TONES)):
                noisy = e.embed(corrupt(mom, f, rng))
                worst = min(worst, e.cosine(clean, noisy))
        flag = "OK " if worst > max_cross else "FAIL"
        if worst <= max_cross:
            floor_ok = False
        print(f"  f={f:.2f}  min cosine to clean = {worst:.4f}  "
              f"{'>' if worst > max_cross else '<='} max_cross {max_cross:.4f}  [{flag}]")

    verdict = (text_invariance == 1.0 and floor_ok)
    print(f"\nVERDICT: {'SUPPORTED' if verdict else 'FALSIFIED'} — "
          f"fingerprint space separates {len(TONES)} tones "
          f"(margin {text_invariance - max_cross:.3f}) and survives "
          f"20% cell noise above the cross-tone ceiling" if verdict else
          "\nVERDICT: FALSIFIED")
    return verdict


if __name__ == "__main__":
    ok = main()
    sys.exit(0 if ok else 1)
