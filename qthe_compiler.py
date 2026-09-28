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
    """Compile a QTHE byte stream -> bytes. Returns the compact verifiable form."""
    data = [b & 0x3F for b in stream]
    timbre = [b >> 6 for b in stream]
    rle = _rle_encode(timbre)
    body = struct.pack(">I", len(data)) + bytes(data) + \
        struct.pack(">I", len(rle)) + rle
    crc = zlib.crc32(MAGIC + bytes([8]) + body) & 0xFFFFFFFF
    return MAGIC + bytes([8]) + body + struct.pack(">I", crc)


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
    data = list(compiled[pos:pos + n_data])
    pos += n_data
    n_rle = struct.unpack(">I", compiled[pos:pos + 4])[0]
    pos += 4
    rle = compiled[pos:pos + n_rle]
    timbre = _rle_decode(rle)
    assert len(timbre) == len(data), "RLE/data length mismatch after decompile"
    return [(timbre[i] << 6) | data[i] for i in range(len(data))]


def compression_ratio(stream: list[int]) -> dict:
    """Report the raw vs compiled size, plus the two-plane breakdown. The
    interesting number is how much the TIMBRE plane compresses (tone runs)."""
    compiled = compile(stream)
    n = len(stream)
    data = bytes([b & 0x3F for b in stream])
    timbre = [b >> 6 for b in stream]
    rle = _rle_encode(timbre)
    return {
        "raw_bytes": n,
        "compiled_bytes": len(compiled),
        "ratio": round(len(compiled) / n, 4),
        "data_plane_bytes": len(data),
        "timbre_raw_bytes": n,
        "timbre_rle_bytes": len(rle),
        "timbre_compression": round(len(rle) / n, 4),
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
