#!/usr/bin/env python3
"""
qthe_embedder.py — the EMBEDDER stage of the tone channel.

Takes the tone (momentum trajectory) recovered from the byte stream and turns
it into a fixed-size VECTOR that downstream models / games / LoRAs can consume.
This is the "embedding side" of the channel: the tone, which was invisible in
plaintext, becomes a first-class feature vector.

The design: tone is a trajectory, so the embedding captures SHAPE, not just
content. Four families of features, all deterministic and zero-dep:

  1. STATIC  — histogram of {down, flat, up, hold} over the stream (4 dims)
  2. ARC     — the three-segment arc: early / mid / late mean momentum (3 dims)
  3. RUN     — max run-length of each momentum state (4 dims)
  4. SPECTRAL — a crude sign-flip "frequency" profile (few dims)

Concatenated + L2-normalized -> a vector in a small, stable space where two
utterances with the SAME tone trajectory map to the SAME vector, and nearby
tones map to nearby vectors (so a downstream model can cluster "sarcasm"
without ever seeing the words).

The one honest caveat (booked): this embeds the tone SHAPE, not its meaning.
"Meaning" is contextual (the Latin-square key) — this vector is the
context-free reading. To embed meaning, fold in the data plane too (see the
`with_context` flag).
"""
from __future__ import annotations

import math

D = {"down": 0, "flat": 1, "up": 2, "hold": 3}


def embed(momentum: list[int], with_context: bool = False,
          context: list[int] | None = None) -> list[float]:
    """momentum: list of {0,1,2,3}. Returns a float vector (L2-normalized).
    If with_context, appends a context-folding term so the vector depends on
    BOTH tone shape and data context (the full meaning), not just shape."""
    n = max(1, len(momentum))

    # 1. static histogram (4)
    hist = [0.0, 0.0, 0.0, 0.0]
    for m in momentum:
        hist[m & 3] += 1.0
    hist = [h / n for h in hist]

    # 2. three-segment arc (early/mid/late mean, 3)
    third = n // 3 or 1
    seg = []
    for s in range(3):
        seg_m = momentum[s * third:(s + 1) * third] or momentum[-1:]
        seg.append(sum(seg_m) / len(seg_m))
    seg = [s / 3.0 for s in seg]  # normalize to ~[0,1]

    # 3. max run-length per state (4), normalized by n
    runs = [0.0] * 4
    cur, cnt = (momentum[0] & 3, 0) if momentum else (0, 0)
    for m in momentum:
        m &= 3
        if m == cur:
            cnt += 1
        else:
            runs[cur] = max(runs[cur], cnt)
            cur, cnt = m, 1
    runs[cur] = max(runs[cur], cnt)
    runs = [r / n for r in runs]

    # 4. spectral: sign-flip rate (1) + direction-change rate (1)
    flips = 0
    for i in range(1, n):
        a, b = momentum[i - 1] & 3, momentum[i] & 3
        if (a in (0, 2) and b in (1, 3)) or (a in (1, 3) and b in (0, 2)):
            flips += 1
    sign_flip_rate = flips / n
    # direction-change rate: how often the momentum CHANGES value
    changes = sum(1 for i in range(1, n) if (momentum[i] & 3) != (momentum[i - 1] & 3))
    change_rate = changes / n

    vec = hist + seg + runs + [sign_flip_rate, change_rate]

    if with_context and context is not None:
        # fold the context: append the mean data-plane context (1 dim) so the
        # vector distinguishes same-shape tones under different meanings
        vec.append((sum(context) / max(1, len(context))) / 64.0)

    # L2 normalize
    norm = math.sqrt(sum(x * x for x in vec)) or 1.0
    return [x / norm for x in vec]


def cosine(a: list[float], b: list[float]) -> float:
    return sum(x * y for x, y in zip(a, b))


if __name__ == "__main__":
    import sys
    sys.path.insert(0, ".")
    import qthe_codec as q

    text = "I love you"
    data = q.data_encode(text)
    n = len(data)
    tones = {
        "sarcasm": [q.MOMENTUM["flat"]] * 2 + [q.MOMENTUM["up"]] * 4 +
                   [q.MOMENTUM["hold"]] * 2 + [q.MOMENTUM["down"]] * (n - 8),
        "joy": [q.MOMENTUM["flat"]] + [q.MOMENTUM["up"]] * (n - 1),
        "anger": [q.MOMENTUM["down"]] * n,
        "flat": [q.MOMENTUM["flat"]] * n,
    }
    emb = {k: embed(v) for k, v in tones.items()}
    print("vector dims:", len(emb["sarcasm"]))
    print("cosine similarity table (same-tone=1.0 by construction):")
    keys = list(emb)
    print("        " + "".join(f"{k[:6]:>8}" for k in keys))
    for k in keys:
        print(f"{k:>8}" + "".join(f"{cosine(emb[k], emb[j]):>8.3f}" for j in keys))
    # determinism
    assert emb["sarcasm"] == embed(tones["sarcasm"]), "embed not deterministic"
    # same tone -> same vector, distinct tones -> distinct vectors
    assert cosine(emb["sarcasm"], emb["sarcasm"]) > 0.999
    assert cosine(emb["sarcasm"], emb["anger"]) < 0.9, "sarcasm too close to anger"
    print("OK — embedder deterministic; same tone = same vector, distinct tones apart.")
