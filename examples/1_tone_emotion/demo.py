#!/usr/bin/env python3
"""
demo.py — example 1: the tone channel encodes EMOTIONAL TONE.

Twelve different meanings of the exact same three words — "I love you" —
each carried entirely in the 2 timbre bits that the byte was already paying
for. A plaintext reader sees the same sentence every time; a context-keyed
reader gets back the exact momentum trajectory, and with it the feeling.

Zero dependencies. Imports the shared reference codec by putting the repo
root on sys.path. Run from anywhere:

    python3 examples/1_tone_emotion/demo.py

Add --md to also emit the tone table as a markdown table (for the docs).
"""
from __future__ import annotations

import sys
from pathlib import Path

# the shared reference implementation lives at the repo root
REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))

import qthe_codec as q  # noqa: E402

M = q.MOMENTUM                      # {"down":0, "flat":1, "up":2, "hold":3}
LETTER = {0: "d", 1: "f", 2: "u", 3: "h"}   # down / flat / up / hold
NAME = {0: "down", 1: "flat", 2: "up", 3: "hold"}

# ─────────────────────────────────────────────────────────────────────────────
# THE DOZEN TONES OF "I LOVE YOU"
#
# A tone here is a MOMENTUM TRAJECTORY: one step per data token, where each
# step is down / flat / up / hold. What a voice does over time — not a label
# stapled to the sentence — is the signal.
#
# Token map of "I love you" (12 data tokens):
#   [UPPER] i  ' '  l  o  v  e  ' '  y  o  u  [EOS]
# ─────────────────────────────────────────────────────────────────────────────
TONES: dict[str, dict] = {
    "friendly statement": {
        "gloss": "calm and even; one gentle lift on the word that matters",
        "mom": [1, 1, 1, 2, 2, 2, 2, 1, 1, 1, 1, 1],
    },
    "question-thinks-yes": {
        "gloss": "flat statement, then the tail leans up and stays up: "
                 "\u201ctell me I\u2019m right\u201d",
        "mom": [1, 1, 1, 1, 1, 2, 2, 1, 2, 2, 2, 2],
    },
    "question-thinks-no": {
        "gloss": "a flicker of a rise, then the collapse: \u201csurely not\u201d",
        "mom": [1, 1, 2, 2, 2, 1, 1, 1, 0, 0, 0, 0],
    },
    "humorous-positive": {
        "gloss": "sing-song bounce all the way through — the ta-da rhythm of a wink",
        "mom": [2, 3, 2, 3, 2, 3, 2, 3, 2, 3, 2, 3],
    },
    "humorous-negative": {
        "gloss": "the same bounce as the wink, but it dies mid-air — "
                 "the roast lands in the fall",
        "mom": [2, 3, 2, 3, 2, 3, 2, 3, 0, 0, 0, 0],
    },
    "sarcasm": {
        "gloss": "overacted rise on \u201clove\u201d, the long drawl of the eye-roll, "
                 "then the dismissive drop",
        "mom": [1, 1, 2, 2, 2, 2, 3, 3, 0, 0, 0, 0],
    },
    "joy": {
        "gloss": "warmth builds from calm into one sustained bright line, "
                 "with sparkling little holds",
        "mom": [1, 2, 2, 2, 2, 3, 2, 2, 3, 2, 2, 2],
    },
    "excitement": {
        "gloss": "pinned high from the very first token; the holds are "
                 "breathless gasps, not calm",
        "mom": [2, 2, 2, 3, 2, 2, 2, 3, 2, 2, 2, 2],
    },
    "anger": {
        "gloss": "three hard downward strikes with clenched-silence holds between",
        "mom": [0, 0, 3, 0, 0, 0, 3, 3, 0, 0, 0, 0],
    },
    "doubt": {
        "gloss": "can\u2019t commit: each syllable leans up then backs off, "
                 "and the whole thing sags down at the end",
        "mom": [2, 0, 2, 0, 1, 2, 1, 0, 0, 0, 0, 0],
    },
    "calling-a-lover-back": {
        "gloss": "reach, wait, reach again — insistent rising, the holds are "
                 "the space you\u2019re calling across",
        "mom": [2, 2, 3, 2, 2, 2, 3, 2, 2, 2, 3, 2],
    },
    "letting-go": {
        "gloss": "one long slow descent — then open hold: the silence after release",
        "mom": [1, 1, 1, 0, 0, 0, 0, 0, 0, 3, 3, 3],
    },
}

# the same machinery on a few more sentences
MORE: dict[str, dict] = {
    "Nice job.": {
        # token map: [UPPER] n i c e ' ' j o b . [EOS]  (11 tokens)
        "sincere": {"gloss": "flat praise with a warm rise on the payoff word",
                    "mom": [1, 1, 1, 1, 1, 1, 2, 2, 2, 2, 1]},
        "sarcastic": {"gloss": "the drawled fake rise, then the drop that "
                               "flips the meaning",
                      "mom": [3, 3, 1, 1, 2, 2, 2, 3, 3, 0, 0]},
    },
    "Sure.": {
        # token map: [UPPER] s u r e . [EOS]  (7 tokens)
        "confident": {"gloss": "dead flat: nothing to argue with",
                      "mom": [1, 1, 1, 1, 1, 1, 1]},
        "doubtful": {"gloss": "wobble, then sag: \u201c…if you say so\u201d",
                     "mom": [1, 2, 0, 2, 0, 0, 0]},
    },
    "Goodbye.": {
        # token map: [UPPER] g o o d b y e . [EOS]  (10 tokens)
        "a goodbye": {"gloss": "small rise on \u201cgood\u201d, fall through "
                               "\u201cbye\u201d, settle flat: complete",
                      "mom": [1, 2, 2, 2, 2, 0, 0, 0, 0, 1]},
    },
}


def mom_str(mom: list[int]) -> str:
    return " ".join(LETTER[m] for m in mom)


def hex_str(stream: list[int]) -> str:
    return " ".join(f"{b:02X}" for b in stream)


def lookup_name(mom: list[int]) -> str:
    """Reverse-map a recovered momentum trajectory back to its tone name —
    this is the payoff: the decoder recovers WHICH feeling, not just bits."""
    for name, spec in TONES.items():
        if spec["mom"] == mom:
            return name
    for txt, variants in MORE.items():
        for name, spec in variants.items():
            if spec["mom"] == mom:
                return f"{txt!r} as {name}"
    return "(unregistered trajectory)"


def show_tone(title: str, gloss: str, text: str, mom: list[int]) -> list[int]:
    stream = q.encode(text, mom)
    back, recovered = q.decode_bytes(stream)
    assert back == text, f"roundtrip failed for {title}: {back!r}"
    assert recovered == mom, f"momentum roundtrip failed for {title}"
    print(f"\n  {title}")
    print(f'    gloss    : {gloss}')
    print(f"    momentum : {mom_str(mom)}   (d=down f=flat u=up h=hold)")
    print(f"    bytes    : {hex_str(stream)}   ({len(stream)} bytes)")
    print(f"    timbre   : {' '.join(str(t) for t in q.timbre_view(stream))}"
          f"          <- top 2 bits, context-free = noise")
    print(f"    plaintext: {q.plaintext_view(stream)!r}"
          f"          <- identical for every tone")
    print(f"    decoded  : {mom_str(recovered)}"
          f"  = {lookup_name(recovered)}   <- recovered with context")
    return stream


def print_markdown_table() -> None:
    print("| # | tone (meaning of \u201cI love you\u201d) | momentum sequence "
          "(per token) | shape in words |")
    print("|---|---|---|---|")
    for i, (name, spec) in enumerate(TONES.items(), 1):
        words = "-".join(NAME[m] for m in spec["mom"])
        print(f"| {i} | {name} | `{mom_str(spec['mom'])}` | {words} |")


def main() -> None:
    text = "I love you"
    data = q.data_encode(text)
    ctx = [d % 4 for d in data]

    print("=" * 79)
    print("EXAMPLE 1 - THE TONE CHANNEL: twelve feelings, one sentence")
    print("=" * 79)
    print(f'\ntext: {text!r}')
    print(f"data tokens (6-bit): {data}")
    print("token map          : [UPPER] i ' ' l o v e ' ' y o u [EOS]")
    print(f"context per token (data % 4, public): {ctx}")
    print("\nlegend: d=down(0) f=flat(1) u=up(2) h=hold(3) "
          "| timbre bits: 0=ground 1=attract 2=repel 3=abstain")

    print("\n" + "-" * 79)
    print("PART 1 - a dozen tones of \u201cI love you\u201d")
    print("-" * 79)

    streams: dict[str, list[int]] = {}
    for name, spec in TONES.items():
        streams[name] = show_tone(name.upper(), spec["gloss"], text, spec["mom"])

    print("\n" + "-" * 79)
    print("PART 2 - the two-key property, proven across the dozen")
    print("-" * 79)
    plains = {name: q.plaintext_view(s) for name, s in streams.items()}
    timbres = {tuple(q.timbre_view(s)) for s in streams.values()}
    assert len(set(plains.values())) == 1, "plaintext views must be identical"
    assert len(timbres) == len(TONES), "timbre views must all differ"
    print(f"\nplaintext views across all 12: {set(plains.values())!r}  "
          f"-> {len(set(plains.values()))} distinct  (tone invisible)")
    print(f"timbre views across all 12   : {len(timbres)} distinct "
          f"(context-free readers can't tell them apart in MEANING; "
          f"with context each decodes exactly)")
    print(f"byte streams across all 12   : {len({tuple(s) for s in streams.values()})} "
          f"distinct byte streams from one sentence")

    print("\n" + "-" * 79)
    print("PART 3 - the Latin square, worked by hand on ONE token")
    print("-" * 79)
    tok = data[3]            # 'l' of "love"
    c = ctx[3]               # context = data % 4
    m = M["up"]
    t = q.latin_timbre(m, c)
    byte = (t << 6) | tok
    m_back = q.latin_decode(byte >> 6, (byte & 0x3F) % 4)
    print(f"\n  token 'l' = {tok}, context = {tok} % 4 = {c}, momentum = up({m})")
    print(f"  encode: timbre = (context + momentum) % 4 = ({c} + {m}) % 4 = {t}")
    print(f"  byte  = (timbre << 6) | data = ({t} << 6) | {tok} = {byte} = 0x{byte:02X}")
    print(f"  decode: momentum = (timbre - context) % 4 = ({byte >> 6} - {c}) % 4 "
          f"= {m_back} = up  [roundtrip]")
    print("\n  Same momentum 'up' in a DIFFERENT context rides a DIFFERENT timbre:")
    for label, tok2 in (("token 'e' (=4)", data[6]), ("token 'u' (=20)", data[10])):
        c2 = tok2 % 4
        t2 = q.latin_timbre(m, c2)
        print(f"    {label:17s} context={c2} -> timbre={t2}  "
              f"(byte 0x{(t2 << 6) | tok2:02X})")
    print("    -> no timbre value betrays 'up' on its own; only the context key does.")

    print("\n" + "-" * 79)
    print("PART 4 - same machinery, a few more sentences")
    print("-" * 79)
    for txt, variants in MORE.items():
        for name, spec in variants.items():
            show_tone(f"{txt!r} as {name.upper()}", spec["gloss"], txt, spec["mom"])

    print("\n" + "=" * 79)
    print("ALL ASSERTIONS PASSED - text roundtrips, tone roundtrips, "
          "plaintext identical, timbre views distinct.")
    print("The feeling rode in the top 2 bits for free.")
    print("=" * 79)

    if "--md" in sys.argv:
        print()
        print_markdown_table()


if __name__ == "__main__":
    main()
