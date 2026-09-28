#!/usr/bin/env python3
"""
QTHE example 3 - spatial sound.

The 2 timbre bits every QTHE byte already carries are re-keyed, contextually,
as a STEREO + ENVELOPE channel:

    momentum step        spatial / sonic reading
    -------------        -----------------------
    down   (0)           pan step LEFT    / envelope DECAY
    flat   (1)           pan step SUSTAIN / envelope SUSTAIN
    up     (2)           pan step RIGHT   / envelope ATTACK
    hold   (3)           no placement     / SILENCE  (the imaginary channel)

    pan   = the INTEGRAL of the trajectory (sum of the steps)
    sound = the SHAPE of the trajectory    (attack / ripple / decay / hold)

So a spoken line carries its own stereo placement AND its own non-verbal
sound (a knock, a laugh, a sigh, silence) in bits that were already paid
for - while the plaintext view shows nothing but the words.

Zero dependencies. Run:  python3 demo.py
"""
from __future__ import annotations

import os
import sys
from collections import Counter

_HERE = os.path.dirname(os.path.abspath(__file__))
_REPO = os.path.dirname(os.path.dirname(_HERE))
if _REPO not in sys.path:
    sys.path.insert(0, _REPO)

from qthe_codec import (
    MOMENTUM,
    SYM_TO_IDX,
    TIMBRE_NAME,
    data_encode,
    decode_bytes,
    encode,
    latin_timbre,
    plaintext_view,
)

DOWN, FLAT, UP, HOLD = (MOMENTUM[k] for k in ("down", "flat", "up", "hold"))

# ---------------------------------------------------------------------------
# The lexicon: one gesture per (pan, sound) cue. A gesture is the per-token
# momentum trajectory for the line; it is padded with FLAT (sustain).
GESTURES = {
    ("left", "knock"): [UP, DOWN, DOWN, DOWN],         # attack, fast decay, left
    ("right", "laugh"): [UP, DOWN, UP, DOWN, UP, UP],  # bouncing ripple, right
    ("left", "speech"): [DOWN, DOWN],                  # settled delivery, left
    ("space", "silence"): None,                        # all HOLD: offstage, unvoiced
    ("front", "sigh"): [FLAT, FLAT, DOWN],             # delayed decay, drifts center
}

SCENE = [
    (("left", "knock"), "Who's there?"),
    (("right", "laugh"), "Only the wind."),
    (("left", "speech"), "The wind doesn't laugh."),
    (("space", "silence"), "(a long pause)"),
    (("front", "sigh"), "Then come inside."),
    (("space", "silence"), "(curtain)"),
]


def gesture_stream(key, n):
    """The n-step momentum stream for a line of n data tokens."""
    prefix = GESTURES[key]
    if prefix is None:
        return [HOLD] * n
    assert n >= len(prefix), "line too short for cue %r (%d tokens)" % (key, n)
    return prefix + [FLAT] * (n - len(prefix))


def read_spatial(mom):
    """The renderer's grammar: momentum stream -> (pan, sound, drift)."""
    if all(m == HOLD for m in mom):
        return "space", "silence", 0
    steps = [(-1 if m == DOWN else 1 if m == UP else 0) for m in mom]
    drift = sum(steps)
    nz = [s for s in steps if s]
    ripples = sum(1 for a, b in zip(nz, nz[1:]) if a != b)
    lead = 0
    for m in mom:  # flat steps before the first moving step
        if m == FLAT:
            lead += 1
        else:
            break
    if ripples >= 2:
        sound = "laugh"                        # bouncing envelope
    elif nz and nz[0] == 1 and -1 in nz[1:4]:
        sound = "knock"                        # attack, then fast decay
    elif UP not in nz and lead >= 2:
        sound = "sigh"                         # delayed slow decay
    else:
        sound = "speech"                       # settled delivery
    pan = "right" if drift >= 2 else ("left" if drift <= -2 else "front")
    return pan, sound, drift


TRACE = {DOWN: "v", FLAT: "-", UP: "^", HOLD: "."}


def trace(mom):
    return "".join(TRACE[m] for m in mom)


def pan_bar(pan):
    if pan == "space":
        return "L . . . ~ ~ ~  offstage / ambient  ~ ~ ~ . . . R"
    cells = ["-"] * 21
    cells[{"left": 2, "front": 10, "right": 18}[pan]] = "o"
    if pan != "front":
        cells[10] = "|"
    return "L " + "".join(cells) + " R"


def rule(title):
    print("")
    print("--- %s %s" % (title, "-" * max(0, 66 - len(title))))


def main():
    print("=" * 70)
    print(" QTHE EXAMPLE 3 - SPATIAL SOUND")
    print(" stereo pan + sound envelopes riding the 2 timbre bits, for free")
    print("=" * 70)

    streams = []
    for key, text in SCENE:
        tone = gesture_stream(key, len(data_encode(text)))
        streams.append(encode(text, tone))

    rule("1. THE SCORE (what the director hears)")
    print(" #  pan     sound     line")
    for i, ((key, text), _) in enumerate(zip(SCENE, streams), 1):
        print(" %d  %-7s %-9s %s" % (i, key[0], key[1], text))

    rule("2. THE WIRE (the byte stream)")
    total = 0
    for i, st in enumerate(streams, 1):
        total += len(st)
        print(" line %d: %2d bytes  %s" % (i, len(st), " ".join("%02x" % b for b in st)))
    print(" total: %d bytes (6 data bits + 2 timbre bits each)" % total)

    rule("3. THE EAVESDROPPER'S VIEW (6-bit data plane only)")
    for (_, text), st in zip(SCENE, streams):
        assert plaintext_view(st) == text
        print(" " + plaintext_view(st))
    print(" [no pan, no sound, no staging - the spatial channel does not exist here]")

    rule("4. THE DECODED STAGE (what a spatial renderer recovers)")
    for i, ((_, _), st) in enumerate(zip(SCENE, streams), 1):
        back, mom = decode_bytes(st)
        pan, sound, drift = read_spatial(mom)
        print(' line %d  "%s"' % (i, back))
        print("   pan   : %-6s %s" % (pan.upper(), pan_bar(pan)))
        print("   sound : %-7s (drift %+d)" % (sound.upper(), drift))
        print("   trace : %s" % trace(mom))

    rule("5. WHY IT'S INVISIBLE")
    print(" the same LEFT step, keyed by different data contexts (Latin square):")
    for c in "ehs":
        ctx = SYM_TO_IDX[c] % 4
        print("   data '%s' (ctx %d): wire timbre %d" % (c, ctx, latin_timbre(DOWN, ctx)))
    hist = Counter(b >> 6 for st in streams for b in st)
    print(" wire timbre histogram over all %d bytes:" % total)
    print("   " + "  ".join("%s(%d):%d" % (TIMBRE_NAME[t], t, hist[t]) for t in range(4)))

    rule("VERIFICATION")
    for (key, text), st in zip(SCENE, streams):
        n = len(data_encode(text))
        back, mom = decode_bytes(st)
        assert back == text, "text roundtrip failed"
        assert mom == gesture_stream(key, n), "momentum roundtrip failed"
        assert plaintext_view(st) == text, "plaintext must hide the staging"
        assert read_spatial(mom)[:2] == key, "spatial decode mismatch"
    print(" all asserts passed: text + momentum roundtrip, staging hidden,")
    print(" spatial map decodes exactly to the director's score.")
    print("")
    print(" OK - the staging rode in the top 2 bits for free.")


if __name__ == "__main__":
    main()
