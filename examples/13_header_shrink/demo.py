#!/usr/bin/env python3
"""
13_header_shrink — the COMPILER lane's booked follow-up from ex 5.

Ex 5's verdict: the structural compiler loses to zlib on short streams purely
on container overhead ("I love you", n=12: zlib 20 vs compiled 27-30) because
the header is 17 bytes (4 magic + 1 width + 4 + 4 lengths + 4 CRC).

Booked fix, tested here: a slim container
    magic "QC2" (2 bytes) + varint n_data + varint n_rle
    + packed data + momentum RLE + 4-byte CRC32
=> 8 bytes of header on any stream with both planes < 128 elements, i.e. 9
bytes saved. CRC32 is kept full-width: ex 5 P4 showed every single-bit flip
caught, and we refuse to trade that away for 2 more bytes.

Falsifiable predictions:
  P1. Slim roundtrips exactly (stream equality) for all tested texts, and
      every sampled single-bit flip is caught by the CRC.
      FALSIFIED IF any roundtrip differs or any flip goes undetected.
  P2. Slim beats the OLD 17-byte container on EVERY tested stream by
      exactly the header delta (9 bytes when both planes < 128).
      FALSIFIED IF any stream shows a smaller gain.
  P3. On short streams where old-compiler lost to zlib (n=12 "I love you"
      sarcasm: zlib 20 vs 27), the slim container now WINS or TIES.
      FALSIFIED IF slim_bytes > zlib_bytes on those exact streams.
  P4. Slim does not lose to zlib on ANY tested stream with n >= 55 that the
      old container already won (ex 5 said compiler wins/ties there).
      FALSIFIED IF slim loses where old won.

Run: python3 demo.py
"""
import os
import random
import sys
import zlib

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))
import qthe_codec as q
import qthe_compiler as comp

M = q.MOMENTUM
MAGIC2 = b"QC"
random.seed(14)


def _varint(n: int) -> bytes:
    """LEB128 unsigned."""
    out = bytearray()
    while True:
        b = n & 0x7F
        n >>= 7
        if n:
            out.append(b | 0x80)
        else:
            out.append(b)
            return bytes(out)


def _read_varint(b: bytes, pos: int) -> tuple[int, int]:
    shift = 0
    val = 0
    while True:
        byte = b[pos]
        pos += 1
        val |= (byte & 0x7F) << shift
        if not byte & 0x80:
            return val, pos
        shift += 7


def slim_compile(stream: list[int]) -> bytes:
    data = [b & 0x3F for b in stream]
    timbre = [b >> 6 for b in stream]
    momentum = [(timbre[i] - data[i] % 4) % 4 for i in range(len(stream))]
    rle = comp._rle_encode(momentum)
    packed = comp._pack6(data)
    body = _varint(len(data)) + packed + _varint(len(rle)) + rle
    crc = zlib.crc32(MAGIC2 + body) & 0xFFFFFFFF
    return MAGIC2 + body + crc.to_bytes(4, "big")


def slim_decompile(blob: bytes) -> list[int]:
    if blob[:2] != MAGIC2:
        raise ValueError("bad magic")
    body_end = len(blob) - 4
    if zlib.crc32(blob[:body_end]) & 0xFFFFFFFF != \
            int.from_bytes(blob[body_end:], "big"):
        raise ValueError("checksum mismatch")
    n_data, pos = _read_varint(blob, 2)
    packed_len = ((n_data + 3) // 4) * 3
    data = comp._unpack6(blob[pos:pos + packed_len], n_data)
    pos += packed_len
    n_rle, pos = _read_varint(blob, pos)
    momentum = comp._rle_decode(blob[pos:pos + n_rle])
    assert len(momentum) == len(data)
    return [(((momentum[i] + data[i] % 4) % 4) << 6) | data[i]
            for i in range(n_data)]


def arc(n: int, kind: str) -> list[int]:
    if kind == "sarcasm":
        k = min(4, n)
        return [M["flat"]] * 2 + [M["up"]] * k + [M["hold"]] * 2 + \
            [M["down"]] * max(0, n - k - 4)
    if kind == "rising":
        t = n // 3
        return [M["flat"]] * t + [M["up"]] * t + \
            [M["hold"]] * (n - 2 * t)
    if kind == "holding":
        return [M["hold"]] * n
    raise ValueError(kind)


TEXTS = ["I love you", "hello world", "meet me at the dock at dawn, bring the "
         "good coffee and the chart with the new soundings", 
         "I love you".upper() * 3]

# headline pair from ex 5's P3 falsification:
SHORT_PAIR = ("I love you", "sarcasm")   # zlib 20 vs compiled 27
LONG_PAIR = (TEXTS[2], "rising")          # n>=55, compiler won there


def main() -> None:
    random.seed(14)
    streams = []
    for text in TEXTS:
        for kind in ("sarcasm", "rising", "holding"):
            data = q.data_encode(text)
            streams.append((text, kind, q.encode(text, arc(len(data), kind))))

    # P1: roundtrip + corruption detection
    flips_total = flips_caught = 0
    for _, _, s in streams:
        assert slim_decompile(slim_compile(s)) == s, "roundtrip broke"
        blob = bytearray(slim_compile(s))
        for i in random.sample(range(len(blob)), min(8, len(blob))):
            flips_total += 1
            bad = bytearray(blob)
            bad[i] ^= 1 << random.randrange(8)
            try:
                slim_decompile(bytes(bad))
            except ValueError:
                flips_caught += 1
    print(f"P1: 8 roundtrips exact; CRC caught {flips_caught}/{flips_total} "
          f"single-bit flips")
    p1 = (flips_caught == flips_total) and flips_total > 0

    # P2: slim vs old, byte delta
    deltas = []
    for _, _, s in streams:
        deltas.append(len(comp.compile(s)) - len(slim_compile(s)))
    print(f"P2: old-minus-slim deltas: {deltas}")
    p2 = all(d == 9 for d in deltas)

    # P3: the short-stream loss, re-fought
    text, kind = SHORT_PAIR
    s = q.encode(text, arc(len(q.data_encode(text)), kind))
    slim_b = len(slim_compile(s))
    old_b = len(comp.compile(s))
    z_b = len(zlib.compress(bytes(s), 9))
    print(f"P3: n={len(s)} '{text}' {kind}: slim {slim_b} | old {old_b} | "
          f"zlib {z_b}")
    p3 = slim_b <= z_b

    # P4: long streams slim must not lose where old won
    text, kind = LONG_PAIR
    s = q.encode(text, arc(len(q.data_encode(text)), kind))
    slim_b, old_b = len(slim_compile(s)), len(comp.compile(s))
    z_b = len(zlib.compress(bytes(s), 9))
    print(f"P4: n={len(s)} long text {kind}: slim {slim_b} | old {old_b} | "
          f"zlib {z_b}")
    p4 = (old_b <= z_b) and (slim_b <= z_b)

    # sweep: where is the zlib crossover now?
    print("crossover sweep (holding tone):")
    for text in TEXTS:
        s = q.encode(text, arc(len(q.data_encode(text)), "holding"))
        print(f"  n={len(s):3d}  slim {len(slim_compile(s)):3d}  "
              f"zlib {len(zlib.compress(bytes(s), 9)):3d}")

    print(f"\nVERDICT: P1={'SURVIVES' if p1 else 'FALSIFIED'} "
          f"P2={'SURVIVES' if p2 else 'FALSIFIED'} "
          f"P3={'SURVIVES' if p3 else 'FALSIFIED'} "
          f"P4={'SURVIVES' if p4 else 'FALSIFIED'}")


if __name__ == "__main__":
    main()
