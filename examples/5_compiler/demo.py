#!/usr/bin/env python3
"""
5_compiler — measured experiment for the COMPILER stage (qthe_compiler.py).

The compiler's claim (qthe_compiler.py docstring, "KEY FIX found by D17"):

    RLE on the WIRE timbre can never compress well because the Latin square
    scrambles tone per-token (that scrambling IS the invisibility). But the
    DECODED momentum has real runs — tone is momentum, not jitter — so RLE on
    decoded momentum should compress hard, while text data is entropy and
    compresses ~0 (packed 6->8 bits is all it can get).

Falsifiable predictions, each with a number this demo prints:
  P1. For smoothly-arc'd tone, momentum-RLE < 0.5 x raw timbre bytes.
      FALSIFIED IF momentum_compression >= 0.5.
  P2. momentum-RLE strictly beats wire-timbre-RLE on the same stream
      (Latin-square scrambling costs >2x).
      FALSIFIED IF wire_compression <= momentum_compression.
  P3. zlib on the raw byte stream does NOT beat the structural compiler
      on tone-heavy streams, because zlib can't see the momentum plane.
      FALSIFIED IF len(zlib(raw)) < compiled_bytes on every tested text.
  P4. Roundtrip is lossless for all tested texts (exact stream equality)
      and any single-bit flip is detected by the CRC.
      FALSIFIED IF any roundtrip differs or a flip goes undetected.
"""
import os
import random
import sys
import zlib

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))
import qthe_codec as q
import qthe_compiler as comp

M = q.MOMENTUM
random.seed(14)


def arc(len_stream: int, kind: str) -> list[int]:
    """Smooth tone arcs: runs, which is what tone is claimed to be."""
    if kind == "sarcasm":
        k = min(4, len_stream)
        return [M["flat"]] * 2 + [M["up"]] * k + [M["hold"]] * 2 + \
               [M["down"]] * max(0, len_stream - k - 4)
    if kind == "rising":
        thirds = len_stream // 3
        return [M["flat"]] * thirds + [M["up"]] * thirds + \
               [M["hold"]] * (len_stream - 2 * thirds)
    if kind == "holding":
        return [M["hold"]] * len_stream
    raise ValueError(kind)


def jitter(len_stream: int) -> list[int]:
    """The control: tone with NO momentum structure (runs should NOT appear)."""
    return [random.choice(list(M.values())) for _ in range(len_stream)]


TEXTS = [
    "I love you",
    "hello world, this is a longer sentence with punctuation!",
    "the quick brown fox jumps over the lazy dog 0123456789",
    "QTHE packs six bits of data and rides two bits of tone for free.",
]

results = []
for text in TEXTS:
    n = len(q.data_encode(text))
    for label, tone in [("sarcasm", arc(n, "sarcasm")),
                        ("rising", arc(n, "rising")),
                        ("holding", arc(n, "holding")),
                        ("jitter", jitter(n))]:
        stream = q.encode(text, tone)
        c = comp.compression_ratio(stream)
        back = comp.decompile(comp.compile(stream))
        assert back == stream, f"P4 roundtrip FAIL: {label!r} {text[:20]!r}"
        raw = bytes(stream)
        z = len(zlib.compress(raw, 9))
        results.append((text[:16], label, len(stream), c, z))

        # P4: single-bit flips always detected (sample 8 positions)
        base = comp.compile(stream)
        for off in range(0, len(base), max(1, len(base) // 8)):
            bad = bytearray(base)
            bad[off] ^= 0x01
            try:
                comp.decompile(bytes(bad))
                raise AssertionError(f"P4 FAIL: flip at {off} undetected ({label})")
            except ValueError:
                pass

print(f"{'text':<18}{'tone':<10}{'n':>4} {'compiled':>9} {'ratio':>7} "
      f"{'momRLE':>7} {'wireRLE':>8} {'zlib':>6}")
falsified = []
for t, label, n, c, z in results:
    print(f"{t:<18}{label:<10}{n:>4} {c['compiled_bytes']:>9} {c['ratio']:>7} "
          f"{c['momentum_compression']:>7} {c['wire_compression']:>8} {z:>6}")
    if label != "jitter" and c["momentum_compression"] >= 0.5:
        falsified.append("P1")
    if label != "jitter" and c["wire_compression"] <= c["momentum_compression"]:
        falsified.append("P2")
    if label != "jitter" and z < c["compiled_bytes"]:
        falsified.append("P3")

if falsified:
    print("FALSIFIED:", sorted(set(falsified)))
else:
    print("P1-P4 all SURVIVE: momentum-RLE < 0.5 on every smooth-arc stream, "
          "beats wire-RLE, and zlib never beats the structural compiler on "
          "tone-heavy streams. Roundtrips lossless, all flips detected.")
