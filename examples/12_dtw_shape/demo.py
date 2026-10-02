#!/usr/bin/env python3
"""
Example 12 — DTW / fixed-K shape fingerprints (the booked transformer round 3).

Round 2 (example 10) proved the running-sum story path is dead as a
fingerprint under both clamped and unbounded registers: length-coupled
resampling + clamp saturation means the raw per-step path encodes
length-phase, not archetype shape. Booked fix: compare SHAPES after length
normalization — (a) fixed-K binning (resample each path to K steps) and
(b) DTW (dynamic time warping) — instead of raw per-step paths.

FALSIFIABLE PREDICTIONS (over the same 8 archetypes x 3 lengths as ex 9/10):

  P1 (shape separation): fixed-K binned hold-aware paths (hold as its own
     symbol, per the ex-10 fix) separate archetypes: min cross-archetype
     distance > 0 for K in {8, 16, 24}. Falsified if any two archetypes
     collide exactly at some K (the ex-9 valley/hold-then-rise failure mode).

  P2 (length invariance -> classification): leave-one-length-out centroid
     classification over binned paths beats ex-10's 0/24. Falsified if
     accuracy <= 11/24 (ex-9's raw-path baseline).

  P3 (DTW beat): full DTW over the raw per-step paths (warping time instead
     of binning it) achieves cross > within separation. Falsified if
     DTW min-cross < DTW max-within.

  P4 (codec robustness): same archetype via the real codec across 4 texts
     (11/22/27 cells, encoded+decoded) classifies to the right archetype by
     nearest binned-centroid. Falsified if accuracy < 8/12.

Zero dependencies. Imports the shared core.
"""
from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))
import qthe_codec as q  # noqa: E402

M = q.MOMENTUM

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
NAMES = list(ARCHETYPES)


def resample(pattern: list[int], n: int) -> list[int]:
    return [pattern[min(len(pattern) - 1, int(i * len(pattern) / n))] for i in range(n)]


def path_hold(momentum: list[int], grid: int = 3) -> list[tuple[int, int]]:
    """The ex-10 hold-aware path: (clamped position, hold flag) per step."""
    pos, path = 0, []
    for m in momentum:
        m &= 3
        hold = 1 if m == 3 else 0
        if m == 2:
            pos += 1
        elif m == 0:
            pos -= 1
        elif m == 3:
            pos = 0
        pos = max(0, min(grid - 1, pos))
        path.append((pos, hold))
    return path


def bin_path(path: list[tuple[int, int]], k: int) -> list[tuple[int, int]]:
    """Fixed-K binning: average pos and majority hold over K equal bins."""
    n = len(path)
    out = []
    for b in range(k):
        seg = path[int(b * n / k):max(int((b + 1) * n / k), int(b * n / k) + 1)]
        pos = round(sum(p for p, _ in seg) / len(seg))
        hold = round(sum(h for _, h in seg) / len(seg))
        out.append((pos, hold))
    return out


def dist(a: list[tuple[int, int]], b: list[tuple[int, int]]) -> float:
    return sum(abs(pa - pb) + abs(ha - hb) for (pa, ha), (pb, hb) in zip(a, b))


def dtw(a: list[tuple[int, int]], b: list[tuple[int, int]]) -> float:
    """Full DTW over hold-aware paths. Band = Sakoe-Chiba |len diff| + 5."""
    n, m = len(a), len(b)
    band = abs(n - m) + 5
    INF = float("inf")
    prev = [INF] * (m + 1)
    prev[0] = 0.0
    for i in range(1, n + 1):
        cur = [INF] * (m + 1)
        lo, hi = max(1, i - band), min(m, i + band)
        for j in range(lo, hi + 1):
            c = abs(a[i - 1][0] - b[j - 1][0]) + abs(a[i - 1][1] - b[j - 1][1])
            cur[j] = c + min(prev[j], cur[j - 1], prev[j - 1])
        prev = cur
    return prev[m]


def synth_streams() -> dict:
    out = {}
    for name, pat in ARCHETYPES.items():
        for n in LENGTHS:
            out[(name, n)] = resample(pat, n)
    return out


def classify(streams, metric_fn, bin_k=None, exclude=None):
    """Leave-one-length-out nearest-centroid classification."""
    def feat(s):
        return bin_path(path_hold(s), bin_k) if bin_k else path_hold(s)
    feats = {key: feat(s) for key, s in streams.items()}
    hits = misses = 0
    miss_list = []
    for name in NAMES:
        for tn in LENGTHS:
            train = [n for n in LENGTHS if n != tn]
            if exclude is not None and tn != exclude:
                continue
            def score(other):
                return min(metric_fn(feats[(name, tn)], feats[(other, n)])
                           for n in train)
            best, bestd = None, float("inf")
            for other in NAMES:
                d = score(other)
                if d < bestd:
                    best, bestd = other, d
            if best == name:
                hits += 1
            else:
                misses += 1
                miss_list.append((name, tn, best, round(bestd, 2)))
    return hits, hits + misses, miss_list


def main() -> None:
    synth = synth_streams()
    streams = {(name, n): synth[(name, n)] for name in NAMES for n in LENGTHS}

    # P1: binned separation
    print("P1 fixed-K binned separation (min cross vs max within):")
    p1 = True
    for k in (8, 16, 24):
        binned = {key: bin_path(path_hold(s), k) for key, s in streams.items()}
        cross = min(
            dist(binned[(a, n)], binned[(b, n)])
            for i, a in enumerate(NAMES) for b in NAMES[i + 1:] for n in LENGTHS
        )
        within = max(
            dist(binned[(a, n1)], binned[(a, n2)])
            for a in NAMES for n1 in LENGTHS for n2 in LENGTHS if n1 != n2
        )
        ok = cross > 0
        p1 &= ok
        print(f"  K={k:2d}: cross_min={cross} within_max={within} "
              f"{'OK' if ok else 'COLLISION'}")
    print(f"  P1 {'SURVIVES' if p1 else 'FALSIFIED'}")

    # P2: leave-one-length-out classification, binned (24 trials = 8 names x 3 test lengths)
    print("P2 leave-one-length-out (binned, K=16):")
    hits = misses = 0
    miss = []
    feats = {key: bin_path(path_hold(s), 16) for key, s in streams.items()}
    for name in NAMES:
        for tn in LENGTHS:
            train = [n for n in LENGTHS if n != tn]
            best, bestd = None, float("inf")
            for other in NAMES:
                d = min(dist(feats[(name, tn)], feats[(other, n)]) for n in train)
                if d < bestd:
                    best, bestd = other, d
            if best == name:
                hits += 1
            else:
                misses += 1
                miss.append((name, tn, best, bestd))
    total = hits + misses
    print(f"  {hits}/{total} (ex-9 raw path: 11/24, ex-10: 0/24)")
    if miss:
        print("  misses:", miss[:6])
    print(f"  P2 {'SURVIVES' if hits > 11 else 'FALSIFIED'}")

    # P3: DTW separation
    print("P3 DTW separation:")
    paths = {key: path_hold(s) for key, s in streams.items()}
    cross = min(
        dtw(paths[(a, n1)], paths[(b, n2)])
        for i, a in enumerate(NAMES) for b in NAMES[i + 1:]
        for n1 in LENGTHS for n2 in LENGTHS
    )
    within = max(
        dtw(paths[(a, n1)], paths[(a, n2)])
        for a in NAMES for n1 in LENGTHS for n2 in LENGTHS if n1 != n2
    )
    print(f"  cross_min={cross} within_max={within} -> "
          f"{'SURVIVES' if cross > within else 'FALSIFIED'}")

    # P4: real-codec robustness
    print("P4 real-codec classification (nearest binned centroid, K=16):")
    binned_cent = {}
    for name in NAMES:
        for n in LENGTHS:
            if n != 24:
                continue
            binned_cent.setdefault(name, []).append(bin_path(path_hold(synth[(name, n)]), 16))
    hits4 = total4 = 0
    for text in TEXTS:
        data = q.data_encode(text)
        for name, pat in ARCHETYPES.items():
            tone = resample(pat, len(data))
            enc = q.encode(text, tone)
            dec_text, dec_tone = q.decode_bytes(enc)
            d = min(dist(bin_path(path_hold(dec_tone), 16), c)
                    for c in binned_cent[name])
            best, bestd = None, float("inf")
            for other in NAMES:
                dd = min(dist(bin_path(path_hold(dec_tone), 16), c)
                         for c in binned_cent[other])
                if dd < bestd:
                    best, bestd = other, dd
            total4 += 1
            if best == name:
                hits4 += 1
            elif len(TEXTS) <= 4 and name in ("oscillate", "flat-drift", "valley"):
                print(f"    miss: {text!r} {name} -> {best} (d={bestd:.1f})")
    print(f"  {hits4}/{total4} -> P4 {'SURVIVES' if hits4 >= 8 else 'FALSIFIED'}")


if __name__ == "__main__":
    main()
