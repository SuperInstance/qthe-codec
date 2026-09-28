#!/usr/bin/env python3
"""
demo.py — example 2: CONDENSATION. The tone carries what the words leave behind.

One letter from a lighthouse keeper, at four levels of compression:

    page           the full letter (~700 chars)
    paragraph      the same letter, cut to ~300
    few sentences  three sentences (~120)
    one sentence   a single closing line (~37)

Every level is encoded with the same 6+2 QTHE byte: 6 bits of text token +
2 bits of timbre, riding free in space the byte already pays for. What
changes across the levels is WHO does the carrying.

On the page, the words carry almost everything; the tone channel is mostly
Ground (the datum). As the text condenses, words are shed — but their
MEANING is not. Every word the letter loses drops one momentum step (a
class: receding / drawing-near / unsaid) into a queue, in the order the
page had it, and the queue is poured onto the surviving tokens: filler
words, punctuation, even the spaces between words. By the single closing
line, two thirds of the byte stream IS tone, and the tone alone carries 23
of the letter's 24 meaning-classes — in the same order the page had them.

Same meaning. ~5% of the bytes. The difference rides in the top two bits,
which were free all along.

Zero dependencies. Imports the shared reference codec via sys.path:

    python3 examples/2_condensation/demo.py
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

# the shared reference implementation lives at the repo root
REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))

import qthe_codec as q  # noqa: E402

M = q.MOMENTUM                                  # {"down":0,"flat":1,"up":2,"hold":3}
M_DOWN, M_FLAT, M_UP, M_HOLD = M["down"], M["flat"], M["up"], M["hold"]
GLYPH = {M_DOWN: "v", M_FLAT: "-", M_UP: "^", M_HOLD: "o"}
NAME = {M_DOWN: "receding", M_FLAT: "datum", M_UP: "drawing-near", M_HOLD: "unsaid"}
CLASSES = [("receding", M_DOWN), ("drawing-near", M_UP), ("unsaid", M_HOLD)]

# ─────────────────────────────────────────────────────────────────────────────
# THE MEANING LEXICON (the "shadow" the tone casts)
#
# Each word the keeper uses carries one momentum class. "love" is
# deliberately absent: the word never appears anywhere in the letter. The
# ^ runs are the love — the tone says what the text does not.
LEXICON = {
    # receding (v): winter, distance, loss
    "winter": M_DOWN, "sea": M_DOWN, "taken": M_DOWN, "harbor": M_DOWN,
    "cold": M_DOWN, "dark": M_DOWN, "ships": M_DOWN, "pass": M_DOWN,
    "horizon": M_DOWN,
    # drawing-near (^): keeping, warmth, the beloved
    "darling": M_UP, "kept": M_UP, "keep": M_UP, "keeps": M_UP,
    "keeper": M_UP, "letter": M_UP, "lamplight": M_UP, "heart": M_UP,
    "light": M_UP, "spring": M_UP, "come": M_UP, "warm": M_UP, "sister": M_UP,
    # unsaid (o): the space where the words are not
    "still": M_HOLD, "perhaps": M_HOLD, "waits": M_HOLD,
}

# ─────────────────────────────────────────────────────────────────────────────
# THE FOUR CONDENSATION LEVELS (pure ASCII, so the codec roundtrips cleanly)
PAGE = (
    "My darling, the winter sea has taken the harbor again. The gulls went\n"
    "south in October, and the cold came in behind them like a debt. I have\n"
    "kept your last letter in the drawer with the brass key, and on the\n"
    "nights when the wind walks the point I read it by lamplight, though I\n"
    "know every word by heart. The light still turns. Ships pass and do not\n"
    "stop, and I watch each one go dark toward the horizon and think: next\n"
    "spring, perhaps. I have mended the glass, painted the rail, counted\n"
    "the stairs, because a keeper keeps what he can. The town says I should\n"
    "sell and come down to the warm country where my sister waits. But the\n"
    "sea and I have an understanding, and I have not yet told it about you."
)
PARAGRAPH = (
    "The winter sea has taken the harbor again. I keep your last letter by\n"
    "lamplight, and I know every word by heart. The light still turns;\n"
    "ships pass and do not stop. Next spring, perhaps. The town says come\n"
    "down to the warm country where my sister waits, but I have not told\n"
    "the sea about you."
)
FEW = (
    "I keep your letter by lamplight. Ships pass without stopping; next\n"
    "spring, perhaps. I have not told the sea about you."
)
ONE = "The sea does not know about you yet."

LEVELS = [
    ("page", PAGE),
    ("paragraph", PARAGRAPH),
    ("few sentences", FEW),
    ("one sentence", ONE),
]


# ─────────────────────────────────────────────────────────────────────────────
# CHAR -> TOKEN MAP. The codec emits >= 1 token per char (UPPER/SHIFT add
# prefixes), so we track which data tokens belong to which source char.
def char_tokens(text: str):
    spans, idx = [], 0
    for ch in text:
        c = ch.lower()
        if c in q.SYM_TO_IDX:
            k = 2 if (ch != c and ch.isupper()) else 1
        elif ch == "\n":
            k = 1
        else:
            k = 2  # SHIFT escape
        spans.append(list(range(idx, idx + k)))
        idx += k
    return spans, idx  # idx == number of data tokens before EOS


def page_concepts(text: str):
    """All lexicon words on the page, in order of first appearance, unique.
    This is the letter's full meaning inventory: 24 classes."""
    seen, out = set(), []
    for mch in re.finditer(r"[A-Za-z]+", text):
        w = mch.group(0).lower()
        if w in LEXICON and w not in seen:
            seen.add(w)
            out.append((w, LEXICON[w]))
    return out


def build_tone(text: str, inventory):
    """The condensation encoder.

    1. Words present at this level get their own lexicon momentum.
    2. Page concepts ABSENT here go into a shed queue (page order, unique).
    3. The queue is poured, one step per token, onto the surviving Ground
       tokens — filler words, punctuation, spaces. Nothing about the queue's
       order is shuffled: the emotional plot keeps the page's sequence.
    """
    spans, ntok = char_tokens(text)
    tone = [M_FLAT] * (ntok + 1)     # +1 for [EOS]; Ground = the datum
    note = [None] * (ntok + 1)       # which word each toned token serves

    present = set()
    for mch in re.finditer(r"[A-Za-z]+", text):
        w = mch.group(0).lower()
        if w in LEXICON:
            present.add(w)
            for j in range(mch.start(), mch.end()):
                for t in spans[j]:
                    tone[t] = LEXICON[w]
                    note[t] = w

    shed = [(w, m) for (w, m) in inventory if w not in present]
    qi = 0
    for t in range(ntok + 1):
        if tone[t] == M_FLAT and qi < len(shed):
            w, m = shed[qi]
            qi += 1
            tone[t] = m
            note[t] = "~" + w        # "~" marks a carried (shed) word
    assert qi == len(shed), "shed queue did not fully fit — deepen the level"
    return tone, sorted(present), shed, note


def stats(tone):
    n = len(tone)
    toned = sum(1 for t in tone if t != M_FLAT)
    # reversals = direction changes in the COLLAPSED toned sequence (flats and
    # gaps skipped): how busy the emotional arc is per unit of carrying.
    seq = [t for t in tone if t != M_FLAT]
    rev = sum(1 for i in range(1, len(seq)) if seq[i] != seq[i - 1])
    counts = {m: tone.count(m) for m in (M_DOWN, M_UP, M_HOLD)}
    return toned / n * 100.0, (rev / len(seq) * 100.0 if seq else 0.0), counts


def plot(tone, cap=72):
    s = "".join(GLYPH[t] for t in tone if t != M_FLAT)
    return s[:cap] + (".." if len(s) > cap else "")


def wrap(text, width=66, indent="  "):
    import textwrap
    return textwrap.indent(textwrap.fill(text, width), indent)


# ─────────────────────────────────────────────────────────────────────────────
def main():
    inventory = page_concepts(PAGE)
    total = len(inventory)
    print("=" * 78)
    print("CONDENSATION — one letter, four levels  (qthe_codec: 6 data + 2 tone bits)")
    print("=" * 78)
    print(f"meaning inventory: {total} lexicon classes on the page\n")

    # collect everything first so the summary table can be printed up front
    reports = []
    for label, text in LEVELS:
        tone, present, shed, note = build_tone(text, inventory)
        stream = q.encode(text, tone)
        back, mom = q.decode_bytes(stream)
        # hard proofs, every level:
        assert back == text, f"[{label}] text roundtrip failed"
        assert mom == tone, f"[{label}] momentum roundtrip failed"
        assert q.plaintext_view(stream) == text, f"[{label}] tone leaked into plaintext"
        density, rev100, counts = stats(tone)
        reports.append(dict(label=label, text=text, tone=tone, stream=stream,
                            present=present, shed=shed, note=note,
                            density=density, rev100=rev100, counts=counts))

    page_bytes = len(reports[0]["stream"])
    hdr = (f"{'LEVEL':<15}{'CHARS':>6}{'QTHE BYTES':>12}{'% OF PAGE':>11}"
           f"{'TONE DENSITY':>14}{'REVERSALS/100toned':>20}")
    print(hdr)
    print("-" * len(hdr))
    for r in reports:
        b = len(r["stream"])
        print(f"{r['label']:<15}{len(r['text']):>6}{b:>12}{b / page_bytes * 100:>10.1f}%"
              f"{r['density']:>13.1f}%{r['rev100']:>18.1f}")
    print()

    for r in reports:
        label, text, tone = r["label"], r["text"], r["tone"]
        b = len(r["stream"])
        print("─" * 78)
        print(f"── {label}  ({len(text)} chars, {b} QTHE bytes)")
        print("─" * 78)
        print(wrap(text))
        c = r["counts"]
        print(f"\ntone: density {r['density']:.1f}% | reversals/100toned {r['rev100']:.1f}"
              f" | v:{c[M_DOWN]} ^:{c[M_UP]} o:{c[M_HOLD]} (of {len(tone)} tokens)")
        print(f"plot: {plot(tone)}")
        tone_share = len(r["shed"]) / total * 100.0
        print(f"carried by tone alone: {len(r['shed'])} of {total} classes"
              f" ({tone_share:.0f}%) — the rest are still in the plaintext")
        print("recovered meaning (tone-only reading, with our private key):")
        for cname, cm in CLASSES:
            in_text = [w for w in r["present"] if LEXICON[w] == cm]
            carried = [w for w, m in r["shed"] if m == cm]
            n = c[cm]
            if n == 0:
                continue
            print(f"  {NAME[cm]:<13}({GLYPH[cm]}) x{n:<4} in text: "
                  f"{', '.join(in_text) if in_text else '—'}"
                  f" | carried: {', '.join(carried) if carried else '—'}")
        if label == "one sentence":
            hx = " ".join(f"{x:02x}" for x in r["stream"])
            print(f"\nthe entire compressed letter, byte for byte ({b} bytes):")
            print(f"  {hx}")
        print()

    one_b = len(reports[-1]["stream"])
    print("=" * 78)
    print("THESIS")
    print("=" * 78)
    print(f"  bytes:              {page_bytes} -> {one_b}  ({one_b / page_bytes * 100:.1f}%"
          f" of the page; {page_bytes / one_b:.1f}x smaller)")
    print(f"  meaning coverage:   {total}/{total} classes at EVERY level")
    tone_shares = " -> ".join(f"{len(r['shed']) / total * 100:.0f}%" for r in reports)
    print(f"  carried by tone:    {tone_shares}")
    print(f"  meaning per byte:   {total / page_bytes:.3f} -> {total / one_b:.3f}"
          f"  ({page_bytes / one_b:.1f}x denser)")
    print("\n  The words left. The tone stayed. That was the trade.")
    print('  ("love" never appears in any level; the ^ runs are the love.)')


if __name__ == "__main__":
    main()
