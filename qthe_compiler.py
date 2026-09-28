#!/usr/bin/env python3
"""
qthe_compiler.py — the COMPILER stage of the tone channel.

Takes the encoder's byte stream (6-bit data + 2-bit timbre per byte) and turns
it into a compact, VERIFIABLE form, plus the reverse (decompile).

The insight: the tone channel is where the signal lives, and tone runs — a
"sarcasm" arc is a long run of up-then-hold-then-down, not a random jitter. So
the compiler separates the two planes and RUN-LENGTH-ENCODES the timbre plane
(the tone) while keeping the data plane (the text) verbatim. A trailing
checksum makes the whole thing verifiable: a receiver can detect any bit flip
in either plane.

This is the "extract as its own a-ha" module: it is ~150 lines, zero-dep, and
it demonstrates that the tone channel compresses better than the text channel
precisely because tone is momentum (runs) while text is entropy (noise).

Layout of the compiled form (all big-endian):
    magic  : 4 bytes  "QTC1"
    w      : 1 byte   width of the payload bytes (8)
    n_data : 4 bytes  length of the data plane
    data   : n_data bytes   the 6-bit data tokens (verbatim)
    n_rle  : 4 bytes  length of the RLE stream
    rle    : n_rle bytes   run-length-encoded timbre plane
    crc32  : 4 bytes  checksum over everything before it
"""
from __future__ import annotations

import struct
import zlib

MAGIC = b"QTC1"


def _rle_encode(values: list[int]) -> bytes:
    """Run-length encode a list of small ints (0..3). Each run: (count<<2 | value)
    as one byte, count in 1..64. A run longer than 64 is split."""
    out = bytearray()
    i = 0
    n = len(values)
    while i < n:
        v = values[i]
        j = i
        while j < n and values[j] == v and (j - i) < 64:
            j += 1
        count = j - i
        out.append(((count - 1) << 2) | v)
        i = j
    return bytes(out)


def _rle_decode(b: bytes) -> list[int]:
    out = []
    for byte in b:
        count = (byte >> 2) + 1
        v = byte & 0b11
        out.extend([v] * count)
    return out


def compile(stream: list[int]) -> bytes:
    """Compile a QTHE byte stream -> bytes. Returns the compact verifiable form.

    KEY FIX (found by D17): the wire timbre (b>>6) is SCRAMBLED by the Latin
    square — that scrambling is what HIDES the tone from context-free readers,
    so RLE on the wire can never compress it (1 semantic run -> ~209 wire runs).
    To compress, we must DECODE the momentum first (using the data plane as
    context), RLE the DECODED momentum (which has the real runs), and pack the
    6-bit data tokens 4-per-3-bytes. The receiver re-encodes wire timbre from
    (momentum, data) on decompile."""
    data = [b & 0x3F for b in stream]
    timbre = [b >> 6 for b in stream]
    momentum = [(timbre[i] - data[i] % 4) % 4 for i in range(len(stream))]  # decode
    rle = _rle_encode(momentum)
    packed_data = _pack6(data)
    body = struct.pack(">I", len(data)) + packed_data + \
        struct.pack(">I", len(rle)) + rle
    crc = zlib.crc32(MAGIC + bytes([8]) + body) & 0xFFFFFFFF
    return MAGIC + bytes([8]) + body + struct.pack(">I", crc)


def _pack6(tokens: list[int]) -> bytes:
    """Pack 6-bit tokens 4-per-3-bytes (24 bits -> 3 bytes)."""
    out = bytearray()
    for i in range(0, len(tokens), 4):
        chunk = tokens[i:i + 4]
        while len(chunk) < 4:
            chunk.append(0)
        v = (chunk[0] << 18) | (chunk[1] << 12) | (chunk[2] << 6) | chunk[3]
        out += v.to_bytes(3, "big")
    return bytes(out)


def _unpack6(b: bytes, n: int) -> list[int]:
    out = []
    for i in range(0, len(b), 3):
        v = int.from_bytes(b[i:i + 3], "big")
        out += [(v >> 18) & 0x3F, (v >> 12) & 0x3F, (v >> 6) & 0x3F, v & 0x3F]
    return out[:n]


def decompile(compiled: bytes) -> list[int]:
    """Decompile the compact form back to a QTHE byte stream, verifying the
    checksum. Raises ValueError on any corruption."""
    if compiled[:4] != MAGIC:
        raise ValueError("not a qthe-compiled stream (bad magic)")
    w = compiled[4]
    body_end = len(compiled) - 4
    crc_stored = struct.unpack(">I", compiled[body_end:])[0]
    crc_calc = zlib.crc32(compiled[:body_end]) & 0xFFFFFFFF
    if crc_stored != crc_calc:
        raise ValueError("checksum mismatch — stream corrupted")
    pos = 5
    n_data = struct.unpack(">I", compiled[pos:pos + 4])[0]
    pos += 4
    packed_len = ((n_data + 3) // 4) * 3
    data = _unpack6(compiled[pos:pos + packed_len], n_data)
    pos += packed_len
    n_rle = struct.unpack(">I", compiled[pos:pos + 4])[0]
    pos += 4
    rle = compiled[pos:pos + n_rle]
    momentum = _rle_decode(rle)
    assert len(momentum) == len(data), "RLE/data length mismatch after decompile"
    # re-encode wire timbre from (momentum, data) via the Latin square
    return [(((momentum[i] + data[i] % 4) % 4) << 6) | data[i] for i in range(len(data))]


def compression_ratio(stream: list[int]) -> dict:
    """Report the raw vs compiled size. The honest timbre number is the
    DECODED-momentum RLE (what the compiler actually stores) — the wire timbre
    RLE would be ~0.72 (the Latin square scrambles it; that scrambling IS the
    invisibility)."""
    compiled = compile(stream)
    n = len(stream)
    data = [b & 0x3F for b in stream]
    timbre = [b >> 6 for b in stream]
    momentum = [(timbre[i] - data[i] % 4) % 4 for i in range(n)]
    rle_momentum = _rle_encode(momentum)
    rle_wire = _rle_encode(timbre)
    return {
        "raw_bytes": n,
        "compiled_bytes": len(compiled),
        "ratio": round(len(compiled) / n, 4),
        "data_plane_packed_bytes": len(_pack6(data)),
        "momentum_rle_bytes": len(rle_momentum),
        "momentum_compression": round(len(rle_momentum) / n, 4),
        "wire_timbre_rle_bytes": len(rle_wire),
        "wire_compression": round(len(rle_wire) / n, 4),
    }


if __name__ == "__main__":
    import sys
    sys.path.insert(0, ".")
    import qthe_codec as q

    # a long sarcastic arc on a short text -> tone runs should compress hard
    text = "I love you"
    data = q.data_encode(text)
    # sarcasm: overacted rise, eye-roll hold, dismissive drop
    tone = [q.MOMENTUM["flat"]] * 2 + [q.MOMENTUM["up"]] * 4 + \
           [q.MOMENTUM["hold"]] * 2 + [q.MOMENTUM["down"]] * (len(data) - 8)
    stream = q.encode(text, tone)

    compiled = compile(stream)
    back = decompile(compiled)
    assert back == stream, "compile/decompile roundtrip failed"
    assert q.decode_bytes(back)[0] == text, "text did not survive the compiler"

    # corruption detection: flip one bit in the data plane
    bad = bytearray(compiled)
    bad[10] ^= 0x01
    try:
        decompile(bytes(bad))
        print("ERROR: corruption not detected")
    except ValueError as e:
        print("corruption detected:", e)

    r = compression_ratio(stream)
    print(f"raw {r['raw_bytes']} -> compiled {r['compiled_bytes']} bytes "
          f"(ratio {r['ratio']})")
    print(f"timbre plane: {r['timbre_raw_bytes']} raw -> "
          f"{r['timbre_rle_bytes']} rle ({r['timbre_compression']})")
    print("OK — compiler roundtrips and detects corruption.")
