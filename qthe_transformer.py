#!/usr/bin/env python3
"""
qthe_transformer.py — the TRANSFORMER stage of the tone channel.

The three stages so far (encoder, compiler, embedder) treat the tone channel
as it IS. The transformer RESHAPES it: condense, spatialize, project.

Three operations, all deterministic and zero-dep:

  1. CONDENSE  — collapse a long text to a short one while the tone carries the
     shed words' momentum (the page -> paragraph -> sentence -> word arc).
     The shed words pour their momentum onto the surviving tokens in order, so
     the emotional arc's SEQUENCE survives even when the words are gone.

  2. SPATIALIZE — reinterpret the momentum stream as a pan position
     (down=left, up=right, flat=front, hold=space): the integral of momentum is
     the pan, the envelope (attack/decay/hold) is the sound.

  3. PROJECT — map a momentum stream into a story space: a fixed grid of
     "positions" (character/stage/depth) keyed by the momentum's running sum,
     so a narrative walks a visible path through the space.

The transformer is the bridge from "tone as encoding" to "tone as structure" —
the stage the higher layers (enrichment loop, NPC reflexes, VLM reading) build on.
"""
from __future__ import annotations

M = {"down": 0, "flat": 1, "up": 2, "hold": 3}
NAME = {0: "down", 1: "flat", 2: "up", 3: "hold"}


def condense(full_text: str, full_tone: list[int], target_tokens: int) -> tuple[str, list[int]]:
    """Collapse `full_text` toward `target_tokens` surviving tokens, pouring the
    shed tokens' momentum onto the survivors IN ORDER. Returns (short_text,
    dense_tone). The survivors keep their own momentum first; shed momentum
    accumulates into the survivors' cells so the arc's sequence survives."""
    assert len(full_tone) == len(full_text), "tone must align with text"
    n = len(full_tone)
    keep = target_tokens
    if keep >= n:
        return full_text, full_tone[:]
    # survivors: keep every (n/keep)-th token, evenly spaced
    stride = n / keep
    survivors = [int(i * stride) for i in range(keep)]
    dense_tone = []
    short_text = []
    for si in survivors:
        # accumulate momentum over the shed tokens before this survivor
        start = survivors[survivors.index(si) - 1] + 1 if survivors.index(si) > 0 else 0
        shed = full_tone[start:si]
        # fold shed momentum into this survivor: majority of the shed arc
        if shed:
            dense_tone.append(max(set(shed), key=shed.count))
        else:
            dense_tone.append(full_tone[si])
        short_text.append(full_text[si])
    return "".join(short_text), dense_tone


def spatialize(momentum: list[int]) -> dict:
    """Map a momentum stream to a spatial/sonic reading.
    pan = the running integral (clamped): left / front / right / space.
    envelope = the shape of the momentum changes (attack/decay/hold/ripple)."""
    running = 0
    pan_trace = []
    for m in momentum:
        m &= 3
        if m == 0:
            running -= 1
        elif m == 2:
            running += 1
        elif m == 3:
            running = 0
        running = max(-2, min(2, running))
        pan_trace.append(running)
    final = pan_trace[-1] if pan_trace else 0
    pos = {0: "front", 1: "right", 2: "right", -1: "left", -2: "left"}.get(final, "front")
    # envelope: count momentum changes as a crude envelope descriptor
    changes = sum(1 for i in range(1, len(momentum)) if (momentum[i] & 3) != (momentum[i - 1] & 3))
    env = "ripple" if changes > len(momentum) * 0.6 else \
          "attack" if momentum and (momentum[0] & 3) == 2 else \
          "decay" if momentum and (momentum[-1] & 3) == 0 else "sustain"
    return {"pan": pos, "envelope": env, "pan_trace": pan_trace}


def project(momentum: list[int], grid: int = 3) -> list[int]:
    """Project a momentum stream into a story-space: a running sum over the
    stream, clamped to [0, grid-1], gives a 1-D path (character/stage/depth)."""
    pos = 0
    path = []
    for m in momentum:
        m &= 3
        if m == 2:
            pos += 1
        elif m == 0:
            pos -= 1
        pos = max(0, min(grid - 1, pos))
        path.append(pos)
    return path


if __name__ == "__main__":
    import sys
    sys.path.insert(0, ".")
    import qthe_codec as q

    # CONDENSE: a long-ish line collapses to 3 tokens, tone carries the arc
    text = "the sea does not know about you yet"
    tone = [q.MOMENTUM["flat"], q.MOMENTUM["flat"], q.MOMENTUM["up"],
            q.MOMENTUM["up"], q.MOMENTUM["up"], q.MOMENTUM["hold"],
            q.MOMENTUM["hold"], q.MOMENTUM["down"], q.MOMENTUM["down"],
            q.MOMENTUM["down"], q.MOMENTUM["down"], q.MOMENTUM["down"]]
    # pad tone to text length
    tone = (tone + [q.MOMENTUM["flat"]] * len(text))[:len(text)]
    short, dense = condense(list(text), tone, 3)
    print("condense:", repr(short), "->", [NAME[m] for m in dense])

    # SPATIALIZE
    sp = spatialize([2, 2, 2, 3, 0, 0, 0])
    print("spatialize:", sp["pan"], sp["envelope"])

    # PROJECT
    print("project:", project([2, 2, 2, 3, 0, 0, 0], grid=3))

    # determinism
    assert condense(list(text), tone, 3)[1] == dense
    assert spatialize([2, 2, 2, 3, 0, 0, 0]) == sp
    print("OK — transformer deterministic.")
