#!/usr/bin/env python3
"""
qthe_codec.py — the reference implementation of the tone channel.

Zero dependencies, Python 3.8+. This is the SHARED core that every example in
examples/ imports. The whole point is that it is small enough to be read and
understood in one sitting — that IS the documentation.

THE PRIMITIVE (proven in quilt-gpu-lab D14):
    A QTHE byte is 6 bits of DATA (the token) + 2 bits of TIMBRE (the tone).
        byte = (timbre << 6) | data
    The two timbre bits are already paid for by the byte, so a ternary "tone"
    signal rides in them at ZERO additional bit-cost.

TIMBRE (4 states):
    Ground   (0) = flat / neutral / "the datum"
    Attract  (1) = forward / upward / leaning-toward
    Repel    (2) = backward / downward / leaning-away
    Abstain  (3) = the imaginary channel / "no information" / leaving space

TONE IS A TRAJECTORY, NOT A LABEL:
    A single word isn't "sarcastic" — a run of tokens has a MOMENTUM (rising,
    falling, flat, or holding space). The same 2 bits mean different things in
    different contexts, so the encoding is CONTEXT-KEYED.

THE LATIN-SQUARE ENCODING (the extractable tool from D14):
    - random permutations leak through fixed points (a naive reader gets a
      free hit per context)
    - derangements over-correct ("t != m" becomes itself 1 bit of info)
    - only a LATIN SQUARE is information-clean: every row is a bijection
      (invertible given context) AND every column covers all timbres (so the
      timbre marginal is uniform and I(M;T) = 0 exactly without context).
"""
from __future__ import annotations

# ── 6-bit data plane: a 64-symbol charset ─────────────────────────────────
# 6 bits = 64 symbols. a-z (26) + 0-9 (10) + a punctuation/space set, and a
# SHIFT mechanism for anything outside it.
LOW = "abcdefghijklmnopqrstuvwxyz0123456789 .,!?'-:;()\"/&*+=<>[]@#%"
n = len(LOW)
assert n <= 60, f"LOW has {n} symbols; must leave room for reserved 61-63"
# symbols 60..63 are reserved: 60=SHIFT, 61=UPPER, 62=NEWLINE, 63=EOS
SHIFT, UPPER, NEWLINE, EOS = 60, 61, 62, 63
SYM_TO_IDX = {c: i for i, c in enumerate(LOW)}
IDX_TO_SYM = {i: c for i, c in enumerate(LOW)}


def data_encode(text: str) -> list[int]:
    """Encode text to 6-bit data tokens. Lowercase-folds; UPPER is a prefix
    token; anything outside the 53-symbol set is escaped via SHIFT + index."""
    out = []
    for ch in text:
        c = ch.lower()
        if c in SYM_TO_IDX:
            if c != ch and ch.isupper():
                out.append(UPPER)
            out.append(SYM_TO_IDX[c])
        elif ch == "\n":
            out.append(NEWLINE)
        else:
            # escape: SHIFT then the ordinal folded into 0..63
            out.append(SHIFT)
            out.append(ord(ch) & 0x3F)
    out.append(EOS)
    return out


def data_decode(tokens: list[int]) -> str:
    out, upper = [], False
    i = 0
    while i < len(tokens):
        t = tokens[i]
        if t == EOS:
            break
        elif t == UPPER:
            upper = True
        elif t == NEWLINE:
            out.append("\n"); upper = False
        elif t == SHIFT:
            i += 1
            out.append(chr(tokens[i])); upper = False
        else:
            s = IDX_TO_SYM[t]
            out.append(s.upper() if upper else s)
            upper = False
        i += 1
    return "".join(out)


# ── 2-bit timbre plane: the tone trajectory ───────────────────────────────
TIMBRE = {"ground": 0, "attract": 1, "repel": 2, "abstain": 3}
TIMBRE_NAME = {0: "ground", 1: "attract", 2: "repel", 3: "abstain"}

# A "tone" is a sequence of momentum steps {-1,0,+1,A} applied over the token
# stream. The MOMENTUM is the true signal; the TIMBRE is its context-keyed
# encoding. We map momentum (4 states) to timbre (4 states) via a Latin square
# keyed by the context = the data token's value mod 4 (or any other public
# context the decoder also sees).
MOMENTUM = {"down": 0, "flat": 1, "up": 2, "hold": 3}  # hold = abstain space


def latin_timbre(momentum: int, context: int) -> int:
    """The Latin-square encoding: timbre = (context + momentum) mod 4.
    Row (fixed context) is a bijection; column (fixed momentum) covers all 4
    timbres => timbre marginal is uniform, I(M;T)=0 without context."""
    return (context + momentum) % 4


def latin_decode(timbre: int, context: int) -> int:
    """Invert the Latin square: momentum = (timbre - context) mod 4."""
    return (timbre - context) % 4


# ── the byte stream ───────────────────────────────────────────────────────
def encode(text: str, tone: list[int]) -> list[int]:
    """Encode (text, tone) -> QTHE byte stream. `tone` is a per-token momentum
    list (same length as data tokens); each entry in MOMENTUM {0..3}. Context
    for the Latin square is the data token value mod 4 (public, recoverable
    from the byte itself)."""
    data = data_encode(text)
    assert len(tone) == len(data), f"tone length {len(tone)} != data length {len(data)}"
    return [((latin_timbre(tone[i], data[i] % 4)) << 6) | data[i]
            for i in range(len(data))]


def decode_bytes(stream: list[int]) -> tuple[str, list[int]]:
    """Decode a QTHE byte stream -> (text, momentum list). Context is
    recovered from the byte's own data plane (public), so the contextual
    decoder needs no side channel."""
    data = [b & 0x3F for b in stream]
    timbre = [b >> 6 for b in stream]
    momentum = [latin_decode(timbre[i], data[i] % 4) for i in range(len(stream))]
    return data_decode(data), momentum


def to_bytes(stream: list[int]) -> bytes:
    return bytes(stream)


def from_bytes(b: bytes) -> list[int]:
    return list(b)


# ── a plaintext reader sees NOTHING (the whole point) ─────────────────────
def plaintext_view(stream: list[int]) -> str:
    """What a reader who only knows the 6-bit data plane sees. The tone is
    invisible here by construction."""
    return data_decode([b & 0x3F for b in stream])


def timbre_view(stream: list[int]) -> list[int]:
    """What a reader who can see the timbre bits (but not the context key)
    sees. Without context these are noise."""
    return [b >> 6 for b in stream]


# ── self-test (runs when the module is executed directly) ─────────────────
if __name__ == "__main__":
    text = "I love you"
    data = data_encode(text)
    # a simple "tone": rising toward the middle, then flat
    tone = [MOMENTUM["up"]] * 3 + [MOMENTUM["flat"]] * (len(data) - 3)
    stream = encode(text, tone)
    back, mom = decode_bytes(stream)
    assert back == text, f"roundtrip failed: {back!r}"
    assert mom == tone, "momentum roundtrip failed"
    assert plaintext_view(stream) == text, "plaintext view must hide tone"
    # without context, timbre carries ~0 info about momentum (uniform marginal)
    from collections import Counter
    print("roundtrip:", back)
    print("bytes:", len(stream), "->", stream)
    print("timbre:", timbre_view(stream))
    print("momentum (recovered w/ context):", mom)
    print("OK — the tone rode in the top 2 bits for free.")
