#!/usr/bin/env python3
"""
10_hold_fix — TRANSFORMER lane, round 2: does the booked fix rescue project()?

Example 9 falsified "project() is a narrative fingerprint" for two booked
reasons: (a) 'hold' is a no-op identical to no-move, so hold-vs-flat
archetypes collapse exactly; (b) clamp saturation adds length-dependent
variance for oscillating streams. The booked fix, tested here:

  FIX-1: project2() emits a (position, hold-state) pair per step — hold
     cells are MARKED, not invisible. Path becomes a sequence over an
     alphabet of 2*grid states, compared by Hamming distance.
  FIX-2: an UNBOUNDED position register alongside the clamped one, so
     oscillating streams are compared on true net displacement rather
     than clamp-crumpled paths.

Four falsifiable predictions:

  P1 (collision fix): valley vs hold-then-rise — the exact collision that
     killed example 9 (L1 = 0 at every length/grid) — has Hamming
     distance STRICTLY > 0 under project2() at every length tested
     (24/36/48). Any zero distance falsifies the fix.
  P2 (separation): under project2() with an 8-state alphabet (grid=4,
     pos x hold), min cross-archetype Hamming > max within-archetype
     Hamming across 8 archetypes x 3 lengths. If within >= across, the
     fix still fails to make the path a fingerprint.
  P3 (clamp tax): the unbounded register separates oscillate from
     flat-drift on net displacement at every length, and the clamped
     path cannot (their clamped paths collide or invert ordering).
  P4 (decisiveness): leave-one-length-out nearest-centroid classification
     under project2() improves over example 9's 11/24. Report the exact
     count.

Zero deps. Imports qthe_codec + qthe_transformer.
"""
from __future__ import annotations
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
import qthe_codec as q
from qthe_transformer import project, NAME

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
LENGTHS = [24, 36, 48]


def project2(momentum: list[int], grid: int = 4) -> list[tuple[int, int]]:
    """Booked fix: (clamped position, hold-flag) per step. hold-flag=1 means
    this step was a hold (abstain space), made VISIBLE in the path."""
    pos = 0
    path = []
    for m in momentum:
        m &= 3
        if m == 2:
            pos += 1
        elif m == 0:
            pos -= 1
        pos = max(0, min(grid - 1, pos))
        path.append((pos, 1 if m == 3 else 0))
    return path


def net_displacement(momentum: list[int]) -> int:
    """Unbounded running sum, final value."""
    return sum((m & 3) - 1 for m in momentum)  # down=-1 flat=0 up=+1 hold=+2


def hamming_p2(a: list[tuple[int, int]], b: list[tuple[int, int]]) -> int:
    n = min(len(a), len(b))
    return sum(1 for i in range(n) if a[i] != b[i])


def l1(a: list[int], b: list[int]) -> int:
    n = min(len(a), b and len(b))
    return sum(abs(a[i] - b[i]) for i in range(n))


def resample(pattern: list[int], n: int) -> list[int]:
    return [pattern[min(len(pattern) - 1, int(i * len(pattern) / n))] for i in range(n)]


def main() -> None:
    print("=== 10_hold_fix — does marking holds rescue the story path? ===\n")

    synth = {a: {n: resample(p, n) for n in LENGTHS} for a, p in ARCHETYPES.items()}

    # P1: the example-9 collision, valley vs hold-then-rise
    print("P1 — valley vs hold-then-rise under project2 (was L1=0):")
    p1_ok = True
    for n in LENGTHS:
        d = hamming_p2(project2(synth["valley"][n]), project2(synth["hold-then-rise"][n]))
        old = l1(project(synth["valley"][n]), project(synth["hold-then-rise"][n]))
        print(f"  n={n}: old L1={old}  new Hamming={d}")
        if d == 0:
            p1_ok = False
    print(f"  P1 {'SURVIVES' if p1_ok else 'FALSIFIED'}\n")

    # P2: full cross/within separation under project2, grid=4 (8-state alphabet)
    print("P2 — separation under project2 (grid=4, 8-state alphabet):")
    across_min = 10**9
    across_pairs = []
    within_max = 0
    within_pair = None
    arch = list(ARCHETYPES)
    for i in range(len(arch)):
        for j in range(i + 1, len(arch)):
            for n in LENGTHS:
                d = hamming_p2(project2(synth[arch[i]][n]), project2(synth[arch[j]][n]))
                if d < across_min:
                    across_min = d
                    across_pairs = [(arch[i], arch[j], n)]
                elif d == across_min:
                    across_pairs.append((arch[i], arch[j], n))
    for a in arch:
        for n1 in LENGTHS:
            for n2 in LENGTHS:
                if n1 == n2:
                    continue
                d = hamming_p2(project2(synth[a][n1]), project2(synth[a][n2]))
                if d > within_max:
                    within_max = d
                    within_pair = (a, n1, n2)
    print(f"  min cross-archetype Hamming = {across_min} at {across_pairs}")
    print(f"  max within-archetype Hamming = {within_max} at {within_pair}")
    p2_ok = across_min > within_max
    print(f"  P2 {'SURVIVES' if p2_ok else 'FALSIFIED'}\n")

    # P3: clamp tax — oscillate vs flat-drift net displacement
    print("P3 — unbounded register for oscillate vs flat-drift:")
    print("  length  clamped-path-final(osc, flat)  net-disp(osc, flat)")
    p3_ok = True
    for n in LENGTHS:
        co = project(synth["oscillate"][n])[-1]
        cf = project(synth["flat-drift"][n])[-1]
        no = net_displacement(synth["oscillate"][n])
        nf = net_displacement(synth["flat-drift"][n])
        print(f"  n={n}: ({co},{cf})  ({no},{nf})")
        if no == nf:
            p3_ok = False
    # do the clamped paths collide anywhere?
    collide = any(
        project(synth["oscillate"][n])[-1] == project(synth["flat-drift"][n])[-1]
        for n in LENGTHS
    )
    print(f"  clamped final-cell collision at some length: {collide}")
    print(f"  P3 {'SURVIVES' if p3_ok else 'FALSIFIED'}\n")

    # P4: leave-one-length-out nearest-centroid under project2
    print("P4 — leave-one-length-out classification under project2:")
    def encode_path(path):
        return path  # list of (pos, hold) tuples

    correct = 0
    total = 0
    misses = []
    for a in arch:
        for n_test in LENGTHS:
            # centroid for each other archetype: median per-step over the two held-in lengths
            best_a, best_d = None, 10**9
            for a2 in arch:
                if a2 == a:
                    continue
                # distance = min over held-in lengths of the other archetype
                d = min(hamming_p2(project2(synth[a][n_test]), project2(synth[a2][n_h]))
                        for n_h in LENGTHS if n_h != n_test)
                if d < best_d:
                    best_d, best_a = d, a2
            if best_a == a:
                correct += 1
            else:
                misses.append((a, n_test, best_a, best_d))
            total += 1
    print(f"  classified {correct}/{total} exactly (example 9 baseline: 11/24)")
    for m in misses:
        print(f"    miss: {m[0]} @n={m[1]} -> {m[2]} (d={m[3]})")
    p4_ok = correct > 11
    print(f"  P4 {'SURVIVES' if p4_ok else 'FALSIFIED'}\n")

    # Challenger: the same paths under the UNBOUNDED register (pos, hold),
    # since the P4 misses are d=0 at equal lengths — the clamp signature.
    def project2u(momentum):
        pos = 0
        path = []
        for m in momentum:
            m &= 3
            pos += {0: -1, 2: 1, 3: 2}.get(m, 0)
            path.append((pos, 1 if m == 3 else 0))
        return path

    u_across_min = 10**9
    u_within_max = 0
    for i in range(len(arch)):
        for j in range(i + 1, len(arch)):
            for n in LENGTHS:
                d = hamming_p2(project2u(synth[arch[i]][n]), project2u(synth[arch[j]][n]))
                u_across_min = min(u_across_min, d)
    for a in arch:
        for n1 in LENGTHS:
            for n2 in LENGTHS:
                if n1 != n2:
                    u_within_max = max(u_within_max,
                        hamming_p2(project2u(synth[a][n1]), project2u(synth[a][n2])))
    print(f"  UNBOUNDED challenger: min cross={u_across_min}  max within={u_within_max}")
    print(f"  unbounded separation: {'HOLDS' if u_across_min > u_within_max else 'FAILS'}")
    u_correct = 0
    for a in arch:
        for n_test in LENGTHS:
            best_a, best_d = None, 10**9
            for a2 in arch:
                if a2 == a:
                    continue
                d = min(hamming_p2(project2u(synth[a][n_test]), project2u(synth[a2][n_h]))
                        for n_h in LENGTHS if n_h != n_test)
                if d < best_d:
                    best_d, best_a = d, a2
            if best_a == a:
                u_correct += 1
    print(f"  UNBOUNDED leave-one-length-out: {u_correct}/24 exact")

    print("VERDICT:", "the hold-marking fix is real" if p1_ok and p2_ok else
          "the fix does not rescue the path as a fingerprint")


if __name__ == "__main__":
    main()
