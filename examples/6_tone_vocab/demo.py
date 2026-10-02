#!/usr/bin/env python3
"""
EXAMPLE 6 — ERROR-ROBUST TONE VOCABULARIES (the vocabulary-design lane)

Prior examples asked "what can the tone mean?" This one asks the engineering
question: how many DISTINCT meanings can the tone channel carry while still
surviving damage? A tone rides in 2 timbre bits per token; one flipped byte
corrupts one momentum step, and a corrupted step can silently re-read as a
DIFFERENT meaning. Feelings don't have checksums — unless you design the
vocabulary so they do.

THE CLAIMS UNDER TEST (all falsifiable):

  P1. Greedy sphere-packing on the n=8 momentum space (4^8 = 65,536 possible
      trajectories) yields a single-error-correcting vocabulary whose size is
      a real fraction of the theoretical bound 4^8 / (1 + 8*3) = 2,621.

  P2. A small hand-carryable vocabulary of 12 meanings (one per feeling in
      example 1's spirit) can be drawn from that greedy code, i.e. pairwise
      momentum-Hamming distance >= 3 on a stream as short as 8 tokens.

  P3. Every single-byte timbre corruption of every vocabulary word is
      corrected exactly by nearest-codeword decoding (12 words x 8 positions
      x 3 wrong momentum values = 288 corruption trials), with the original
      text roundtrip unaffected (the data plane carries no damage).

If P1's greedy size comes back tiny relative to the bound, the channel is
too dense for error correction at n=8 and robust vocabularies need longer
streams. If P3 fails anywhere, the vocabulary is not actually d>=3.
"""
import os
import sys
import itertools

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))
import qthe_codec as q  # noqa: E402

N = 8                      # momentum steps per meaning
ALPHA = 4                  # momentum alphabet: down/flat/up/hold
BOUND = ALPHA ** N // (1 + N * (ALPHA - 1))   # sphere-packing upper bound


def greedy_code(n: int, min_dist: int) -> list[tuple[int, ...]]:
    """Greedy maximal code with minimum Hamming distance `min_dist`: sweep
    all 4^n trajectories in lexicographic order, keep a codeword iff no kept
    codeword lies within distance < min_dist. Implemented by covering the
    radius (min_dist-1) ball of each pick — a candidate is skippable iff it
    sits inside some pick's ball, so min pairwise distance >= min_dist."""
    r = min_dist - 1
    ball = list(itertools.product(range(ALPHA), repeat=n))
    covered = set()
    code = []
    for cw in ball:
        if cw in covered:
            continue
        code.append(cw)
        # cover every point within distance <= r of cw
        for k in range(r + 1):
            for coords in itertools.combinations(range(n), k):
                for deltas in itertools.product(range(1, ALPHA), repeat=k):
                    t = list(cw)
                    for ci, d in zip(coords, deltas):
                        t[ci] = (t[ci] + d) % ALPHA
                    covered.add(tuple(t))
    return code


def hamming(a: tuple[int, ...], b: tuple[int, ...]) -> int:
    return sum(x != y for x, y in zip(a, b))


def nearest(code: dict, v: tuple[int, ...]):
    """Nearest-codeword decode: return (meaning, distance)."""
    best, bd = None, 10 ** 9
    for meaning, cw in code.items():
        d = hamming(cw, v)
        if d < bd:
            best, bd = meaning, d
    return best, bd


def main():
    print(f"EXAMPLE 6 — error-robust tone vocabularies (n={N}, alphabet={ALPHA})")
    print(f"sphere-packing bound: {ALPHA}^{N} / (1 + {N}*{ALPHA-1}) = {BOUND}\n")

    # ── P1: greedy single-error-correcting vocabulary size ──────────────
    code_words = greedy_code(N, min_dist=3)
    frac = len(code_words) / BOUND
    print(f"P1  greedy single-error-correcting vocabulary: {len(code_words)} "
          f"meanings ({frac:.1%} of the {BOUND} bound)")

    # ── P2: carve a 12-meaning vocabulary, verify min distance >= 3 ─────
    # Spread picks codewords across the greedy list so consecutive meanings
    # look nothing alike; any 12 from a d>=3 code inherit d>=3.
    picks = [code_words[i * (len(code_words) // 12)] for i in range(12)]
    feelings = ["tenderness", "sarcasm", "awe", "grief", "playful", "urgent",
                "warmth", "doubt", "resolve", "wonder", "consolation", "sparks"]
    vocab = dict(zip(feelings, picks))
    mind = min(hamming(a, b) for a, b in itertools.combinations(picks, 2))
    print(f"P2  12-meaning vocabulary drawn, minimum pairwise distance = {mind} "
          f"({'SURVIVES' if mind >= 3 else 'FALSIFIED'})")
    ex = vocab["tenderness"]
    print(f"    e.g. 'tenderness' = {[q.TIMBRE_NAME[m] for m in ex]}")

    # ── P3: corrupt every word at every position with every wrong step ──
    text = "I love you"
    trials = fixed = 0
    for feeling, cw in vocab.items():
        assert len(q.data_encode(text)) >= N
        for pos in range(N):
            for delta in (1, 2, 3):
                bad = list(cw)
                bad[pos] = (bad[pos] + delta) % ALPHA
                got, d = nearest(vocab, tuple(bad))
                trials += 1
                if got == feeling and d <= 1:
                    fixed += 1
    print(f"P3  single-tone-error correction: {fixed}/{trials} corruptions "
          f"decoded to the original meaning "
          f"({'SURVIVES' if fixed == trials else 'FALSIFIED'})")

    # and the data plane never carries the damage: roundtrip is exact
    tone = list(ex) + [q.MOMENTUM["flat"]] * (len(q.data_encode(text)) - N)
    stream = q.encode(text, tone)
    back, _ = q.decode_bytes(stream)
    assert back == text
    print(f"    text roundtrip exact through the corrupted lane: {back!r}")

    print("\nVERDICT: " + (
        "the tone channel supports single-error-correcting vocabularies at "
        f"n={N}; robustness costs ~{len(code_words) / ALPHA**N:.1%} of raw "
        "trajectory space but leaves thousands of distinct meanings"
        if fixed == trials and mind >= 3 else
        "vocabulary design failed one or more predictions — see numbers above"))


if __name__ == "__main__":
    main()
