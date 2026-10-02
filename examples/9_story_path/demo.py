#!/usr/bin/env python3
"""
9_story_path — TRANSFORMER lane: is project() a narrative FINGERPRINT?

The transformer's project() maps a momentum stream to a 1-D story path
(running sum on a 3-cell grid). The claim under test: the path is a
NARRATIVE FINGERPRINT — it separates distinct emotional archetypes more
than it varies across texts carrying the same archetype, at multiple
lengths, WITHOUT any normalization (raw clamped path, L1 distance).

Four falsifiable predictions, all with real numbers:

  P1 (separation): 8 narrative archetypes (rise, fall, arc, valley,
     plunge-recover, hold-then-rise, oscillate, flat-drift) sampled at
     3 lengths (24/36/48) yield min cross-archetype path L1 distance
     STRICTLY GREATER than max within-archetype distance. If within >=
     across, the path is not a fingerprint.
  P2 (text invariance): same archetype on 4 different texts (encoded
     through the REAL codec, decode -> momentum -> project) at n=36
     deviates at most delta_max; report delta_max and whether it is
     below the P1 cross-archetype minimum.
  P3 (compression): story paths are stepwise; run-length encoding of
     the path beats RLE of the momentum stream on smooth arcs, and the
     3-cell path is decodable as <= log2(3) bits/step of narrative.
  P4 (decisiveness): each archetype's path visits a DISTINCT final cell
     distribution; a nearest-centroid classifier on the raw path
     (leave-one-length-out) classifies all 8x3 = 24 streams exactly.
     Any misclassification falsifies "path is discriminative as-is".

Zero deps. Imports qthe_codec (real encode/decode path) and
qthe_transformer.project.
"""
from __future__ import annotations
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
import qthe_codec as q
from qthe_transformer import project, NAME

M = q.MOMENTUM

# ── 8 narrative archetypes as momentum patterns (unit cell, resampled) ────
ARCHETYPES = {
    "rise":           [M["up"]] * 8,
    "fall":           [M["down"]] * 8,
    "arc":            [M["up"]] * 4 + [M["down"]] * 4,
    "valley":         [M["down"]] * 4 + [M["up"]] * 4,
    "plunge-recover": [M["down"]] * 2 + [M["up"]] * 5 + [M["down"]] * 1,
    "hold-then-rise": [M["hold"]] * 4 + [M["up"]] * 4,
    "oscillate":      [M["up"], M["down"]] * 4,
    "flat-drift":     [M["flat"]] * 6 + [M["up"], M["down"]],
}

TEXTS = [
    "i love you",
    "the sea does not know about you yet",
    "hello world this is a longer message for testing",
    "we are the ship and the ship is us",
]
LENGTHS = [24, 36, 48]


def resample(pattern: list[int], n: int) -> list[int]:
    """Nearest-index stretch of an archetype cell to length n."""
    return [pattern[min(len(pattern) - 1, int(i * len(pattern) / n))] for i in range(n)]


def path_of(momentum: list[int], grid: int = 3) -> list[int]:
    return project(momentum, grid=grid)


def l1(a: list[int], b: list[int]) -> int:
    n = min(len(a), len(b))
    return sum(abs(a[i] - b[i]) for i in range(n))


def main() -> None:
    # synthetic streams: archetype x length
    synth = {}
    for name, pat in ARCHETYPES.items():
        for n in LENGTHS:
            synth[(name, n)] = path_of(resample(pat, n))

    # P1: separation
    cross_min, cross_pair = 10**9, None
    within_max, within_pair = 0, None
    names = list(ARCHETYPES)
    for i, a in enumerate(names):
        for b in names[i + 1:]:
            for n in LENGTHS:
                d = l1(synth[(a, n)], synth[(b, n)])
                if d < cross_min:
                    cross_min, cross_pair = d, (a, b, n)
    for a in names:
        for n1 in LENGTHS:
            for n2 in LENGTHS:
                if n1 != n2:
                    d = l1(synth[(a, n1)], synth[(a, n2)])
                    if d > within_max:
                        within_max, within_pair = d, (a, n1, n2)
    p1 = cross_min > within_max
    print(f"P1 separation: cross-archetype min L1 = {cross_min} {cross_pair}; "
          f"within-archetype max = {within_max} {within_pair} -> "
          f"{'SURVIVES' if p1 else 'FALSIFIED'}")

    # P2: text invariance through the REAL codec
    devs = {}
    for name, pat in ARCHETYPES.items():
        paths = []
        for text in TEXTS:
            n = len(q.data_encode(text))
            tone = resample(pat, n)
            stream = q.encode(text, tone)
            _, mom = q.decode_bytes(stream)
            paths.append(path_of(mom))
        dev = max(l1(paths[i], paths[j])
                  for i in range(len(paths)) for j in range(i + 1, len(paths)))
        devs[name] = dev
    dev_max, dev_name = max(zip(devs.values(), devs.keys()))
    p2 = dev_max < cross_min
    print(f"P2 text invariance: worst within-archetype deviation over real codec = "
          f"{dev_max} ({dev_name}); vs cross-archetype min {cross_min} -> "
          f"{'SURVIVES' if p2 else 'FALSIFIED'}")
    print("   per-archetype:", {k: v for k, v in devs.items()})

    # P1b: is the failure the 3-cell grid saturating? sweep grid size.
    # also normalize lengths: resample every path to a common 24 steps so
    # length mismatch no longer inflates L1.
    def resample_path(p: list[int], n: int = 24) -> list[int]:
        return [p[min(len(p) - 1, int(i * len(p) / n))] for i in range(n)]
    print("P1b grid sweep (normalized paths, n=24):")
    for grid in (3, 6, 12, 24, 48):
        syn = {(a, n): resample_path(path_of(resample(ARCHETYPES[a], n), grid))
               for a in names for n in LENGTHS}
        cmin = min(l1(syn[(a, n)], syn[(b, n)])
                   for i, a in enumerate(names) for b in names[i + 1:] for n in LENGTHS)
        wmax = max(l1(syn[(a, n1)], syn[(a, n2)])
                   for a in names for n1 in LENGTHS for n2 in LENGTHS if n1 != n2)
        print(f"   grid={grid:2d}: cross_min={cmin:4d} within_max={wmax:4d} "
              f"{'SEPARABLE' if cmin > wmax else 'collapsed'}")

    # P3: compression — RLE of path vs RLE of momentum on smooth arcs
    wins = 0
    total = 0
    ratio_samples = []
    for name, pat in ARCHETYPES.items():
        n = 36
        mom = resample(pat, n)
        pth = path_of(mom)
        def rle(xs):
            out = 0
            i = 0
            while i < len(xs):
                j = i
                while j < len(xs) and xs[j] == xs[i]:
                    j += 1
                out += 1
                i = j
            return out
        r_mom, r_path = rle(mom), rle(pth)
        total += 1
        wins += r_path <= r_mom
        ratio_samples.append((name, r_mom, r_path))
    p3 = wins == total
    print(f"P3 compression: path-RLE <= momentum-RLE on {wins}/{total} streams "
          f"-> {'SURVIVES' if p3 else 'FALSIFIED'}")
    print("   ", ratio_samples)

    # P4: leave-one-length-out nearest-centroid classification
    correct = 0
    total4 = 0
    misses = []
    for a in names:
        for n in LENGTHS:
            # centroid of the other two lengths, truncated to min len
            others = [synth[(a, m)] for m in LENGTHS if m != n]
            L = min(len(o) for o in others)
            cent = [round(sum(o[i] for o in others) / 2) for i in range(L)]
            # classify against each archetype's centroid
            best, best_d = None, 10**9
            for c in names:
                cs = [synth[(c, m)] for m in LENGTHS if m != n]
                Lc = min(len(o) for o in cs)
                cc = [round(sum(o[i] for o in cs) / 2) for i in range(Lc)]
                d = l1(synth[(a, n)][:min(L, Lc)], cc[:min(L, Lc)])
                if d < best_d:
                    best, best_d = c, d
            total4 += 1
            if best == a:
                correct += 1
            else:
                misses.append((a, n, best))
    p4 = correct == total4
    print(f"P4 classification: {correct}/{total4} leave-one-length-out exact -> "
          f"{'SURVIVES' if p4 else 'FALSIFIED'}")
    if misses:
        print("   misses:", misses)

    print(f"\nVERDICT: P1 {'PASS' if p1 else 'FAIL'} P2 {'PASS' if p2 else 'FAIL'} "
          f"P3 {'PASS' if p3 else 'FAIL'} P4 {'PASS' if p4 else 'FAIL'}")


if __name__ == "__main__":
    main()
