# Example 2 — Condensation: the tone carries what the words leave behind

**The claim:** you can shrink a page of text to 5% of its bytes and lose *none*
of its meaning — provided the tone channel picks up everything the shed words
were carrying. As the text condenses, the tone trajectory becomes richer and
more load-bearing. Compression isn't deletion; it's a *handoff*.

Run it:

```bash
python3 examples/2_condensation/demo.py
```

Zero dependencies. Imports the shared reference codec (`qthe_codec.py`) via
`sys.path`, exactly like example 1.

---

## 1. The setup

One letter from a lighthouse keeper, at four levels of compression:

| level | what it is |
|---|---|
| `page` | the full letter (~700 chars) |
| `paragraph` | the same letter, cut to ~300 |
| `few sentences` | three sentences (~120) |
| `one sentence` | a single closing line (~37) |

Every level is encoded with the *same* 6+2 QTHE byte: 6 bits of text token +
2 bits of timbre riding free in space the byte already pays for. Nothing about
the format changes across levels. What changes is **who does the carrying**.

Before condensing, the demo inventories the page: **24 lexicon classes**, each
a word mapped to a momentum class from the codec's own four states:

- `receding (v)` — *winter, sea, taken, harbor, cold, dark, ships, pass, horizon*
- `drawing-near (^)` — *darling, kept, keep, keeps, keeper, letter, lamplight,
  heart, light, spring, come, warm, sister*
- `unsaid (o)` — *still, perhaps, waits*
- (the fourth state, `flat -`, is Ground/the datum: tokens not doing tonal work)

`love` is deliberately **not** in the lexicon, because the word never appears
anywhere in the letter. The `^` runs are the love. The tone says what the text
does not — that is the whole game.

## 2. The mechanism: shed words become tone, in order

`build_tone()` in `demo.py` is the condensation encoder. Three steps:

1. **Words present at this level keep their own momentum.** `sea` is `v`
   wherever it survives; `letter` is `^` wherever it survives.

2. **Page concepts absent at this level enter a shed queue** — one momentum
   step per lost word, in the *page's order of first appearance*, deduplicated.
   This is the meaning the words leave behind, bagged.

3. **The queue is poured onto the surviving Ground tokens** — one step per
   token: filler words, punctuation, *even the spaces between words*. No
   shuffling, no randomness: the emotional plot keeps the page's sequence.

So a shed word never vanishes; it is *re-homed* onto whatever text remains.
The decoder doesn't need to know which — `decode_bytes()` recovers the exact
momentum list from the top 2 bits, context-keyed off each byte's own data
plane (the Latin square in `qthe_codec.latin_timbre`), no side channel.

**What tone carries, honestly:** the momentum *class* of each lost word and
its *position in the letter's emotional sequence* — not the lexical identity.
A reader of tone alone cannot recover the word "horizon", but can recover
"here the letter recedes" and *when*. For the feeling of a letter, that is
the meaning. (The demo's "carried:" annotations use our private knowledge of
which word fed which step; the byte stream itself carries only class + order.)

## 3. The numbers — how the load transfers

Actual demo output (Python 3.14, 2026-09-27):

```text
==============================================================================
CONDENSATION — one letter, four levels  (qthe_codec: 6 data + 2 tone bits)
==============================================================================
meaning inventory: 24 lexicon classes on the page

LEVEL           CHARS  QTHE BYTES  % OF PAGE  TONE DENSITY  REVERSALS/100toned
------------------------------------------------------------------------------
page              698         714     100.0%         18.5%               6.8
paragraph         291         299      41.9%         35.1%              14.3
few sentences     118         122      17.1%         50.8%              24.2
one sentence       36          38       5.3%         68.4%              30.8
```

Read the two right-hand columns together:

- **Tone density** — the fraction of bytes whose top 2 bits are doing
  meaning-carrying work (non-Ground). It climbs 18.5% → 35.1% → 50.8% → 68.4%.
  On the page, fewer than one byte in five is tonal; in the closing line,
  more than two in three are.
- **Reversals/100toned** — direction changes in the collapsed emotional arc
  (`^`↔`v`↔`o` ignoring gaps). The page's tone *swells* in long blocks
  (winter-sea-cold is one long recession); the condensed levels must interleave
  classes on adjacent tokens, so the arc gets busier per token as the bytes
  shrink.

And the headline table, computed by the script:

```text
==============================================================================
THESIS
==============================================================================
  bytes:              714 -> 38  (5.3% of the page; 18.8x smaller)
  meaning coverage:   24/24 classes at EVERY level
  carried by tone:    0% -> 29% -> 71% -> 96%
  meaning per byte:   0.034 -> 0.632  (18.8x denser)

  The words left. The tone stayed. That was the trade.
  ("love" never appears in any level; the ^ runs are the love.)
```

Every level covers **24/24** meaning classes. The only thing that changes is
the split of the carrying:

| level | bytes | classes in plaintext | classes in tone only | tone's share |
|---|---|---|---|---|
| page | 714 | 24 | 0 | 0% |
| paragraph | 299 | 17 | 7 | 29% |
| few sentences | 122 | 8 | 17 | 71% |
| one sentence | 38 | 1 | 23 | 96% |

The closing line — *"The sea does not know about you yet."* — carries one
class in its plaintext (`sea`, receding) and **23 of 24 in its tone bits**,
in page order. The full compressed letter is 38 bytes:

```text
fd d3 c7 04 24 92 04 00 a4 43 0e 84 12 e4 4d 8e d3 24 0a 0d 0e 16 a4 80
c1 4e 54 13 64 58 ce 54 64 58 44 13 a5 3f
```

A plaintext reader (6-bit plane only) sees a wistful closing line. A
context-keyed reader also gets the whole emotional history of the page:
twelve beloved things drawing near, nine losses receding, three silences
held — *in the order the keeper felt them* — at 5.3% of the bytes.

## 4. Full demo output

```text
──────────────────────────────────────────────────────────────────────────────
── page  (698 chars, 714 QTHE bytes)
──────────────────────────────────────────────────────────────────────────────
  My darling, the winter sea has taken the harbor again. The gulls
  went south in October, and the cold came in behind them like a
  debt. I have kept your last letter in the drawer with the brass
  key, and on the nights when the wind walks the point I read it by
  lamplight, though I know every word by heart. The light still
  turns. Ships pass and do not stop, and I watch each one go dark
  toward the horizon and think: next spring, perhaps. I have mended
  the glass, painted the rail, counted the stairs, because a keeper
  keeps what he can. The town says I should sell and come down to
  the warm country where my sister waits. But the sea and I have an
  understanding, and I have not yet told it about you.

tone: density 18.5% | reversals/100toned 6.8 | v:48 ^:67 o:17 (of 714 tokens)
plot: ^^^^^^^vvvvvvvvvvvvvvvvvvvvvvvv^^^^^^^^^^^^^^^^^^^^^^^^^^^^^ooooovvvvvvv..
carried by tone alone: 0 of 24 classes (0%) — the rest are still in the plaintext
recovered meaning (tone-only reading, with our private key):
  receding     (v) x48   in text: cold, dark, harbor, horizon, pass, sea, ships, taken, winter | carried: —
  drawing-near (^) x67   in text: come, darling, heart, keeper, keeps, kept, lamplight, letter, light, sister, spring, warm | carried: —
  unsaid       (o) x17   in text: perhaps, still, waits | carried: —

──────────────────────────────────────────────────────────────────────────────
── paragraph  (291 chars, 299 QTHE bytes)
──────────────────────────────────────────────────────────────────────────────
  The winter sea has taken the harbor again. I keep your last letter
  by lamplight, and I know every word by heart. The light still
  turns; ships pass and do not stop. Next spring, perhaps. The town
  says come down to the warm country where my sister waits, but I
  have not told the sea about you.

tone: density 35.1% | reversals/100toned 14.3 | v:35 ^:53 o:17 (of 299 tokens)
plot: ^v^vvvvvvvv^vvv^vvvvvvvvvvv^^^^^^^^^^^^^^^^^^^^^^^^^^^^^ooooovvvvvvvvv^^..
carried by tone alone: 7 of 24 classes (29%) — the rest are still in the plaintext
recovered meaning (tone-only reading, with our private key):
  receding     (v) x35   in text: harbor, pass, sea, ships, taken, winter | carried: cold, dark, horizon
  drawing-near (^) x53   in text: come, heart, keep, lamplight, letter, light, sister, spring, warm | carried: darling, kept, keeper, keeps
  unsaid       (o) x17   in text: perhaps, still, waits | carried: —

──────────────────────────────────────────────────────────────────────────────
── few sentences  (118 chars, 122 QTHE bytes)
──────────────────────────────────────────────────────────────────────────────
  I keep your letter by lamplight. Ships pass without stopping; next
  spring, perhaps. I have not told the sea about you.

tone: density 50.8% | reversals/100toned 24.2 | v:19 ^:34 o:9 (of 122 tokens)
plot: ^vv^^^^vv^^^o^^^^^^vv^^^^^^^^^^^^^vvvvvv^vvvvo^^^^^^ooooooovvv
carried by tone alone: 17 of 24 classes (71%) — the rest are still in the plaintext
recovered meaning (tone-only reading, with our private key):
  receding     (v) x19   in text: pass, sea, ships | carried: winter, taken, harbor, cold, dark, horizon
  drawing-near (^) x34   in text: keep, lamplight, letter, spring | carried: darling, kept, heart, light, keeper, keeps, come, warm, sister
  unsaid       (o) x9    in text: perhaps | carried: still, waits

──────────────────────────────────────────────────────────────────────────────
── one sentence  (36 chars, 38 QTHE bytes)
──────────────────────────────────────────────────────────────────────────────
  The sea does not know about you yet.

tone: density 68.4% | reversals/100toned 30.8 | v:11 ^:12 o:3 (of 38 tokens)
plot: ^vvvvvvv^^^^^ovvvv^o^^^^^o
carried by tone alone: 23 of 24 classes (96%) — the rest are still in the plaintext
recovered meaning (tone-only reading, with our private key):
  receding     (v) x11   in text: sea | carried: winter, taken, harbor, cold, ships, pass, dark, horizon
  drawing-near (^) x12   in text: — | carried: darling, kept, letter, lamplight, heart, light, spring, keeper, keeps, come, warm, sister
  unsaid       (o) x3    in text: — | carried: still, perhaps, waits

the entire compressed letter, byte for byte (38 bytes):
  fd d3 c7 04 24 92 04 00 a4 43 0e 84 12 e4 4d 8e d3 24 0a 0d 0e 16 a4 80 c1 4e 54 13 64 58 ce 54 64 58 44 13 a5 3f
```

Note the `~` prefix convention inside `demo.py`: while building the tone, each
token is annotated with the word it serves, and `~word` marks a step poured in
from the shed queue. The annotation is for *us*; the stream carries only the
momentum class and its position.

## 5. Why this is the point of the codec

The 2 timbre bits cost nothing — they exist in every byte whether used or
not. Example 1 showed them carrying twelve tones of one unchanging sentence.
This example shows the other superpower: **they are a compression reserve.**
When the text plane shrinks, the tone plane absorbs the load, and the pair
(6-bit text, 2-bit tone) keeps delivering the same meaning at a fraction of
the bytes. The plaintext reader loses nothing they'd have noticed; the keyed
reader loses nothing at all.

Three properties fall out of the construction, free:

1. **Graceful degradation** — strip the tone and each level is still a valid,
   readable condensation of the letter. The tone is pure surplus meaning.
2. **Order preservation** — the shed queue is poured in page order onto
   tokens in reading order, so the emotional arc's *sequence* survives even
   when every word that made it is gone.
3. **Invisible to the casual reader** — `plaintext_view()` is bit-identical
   at every level; the demo asserts it, along with full text+momentum
   roundtrips, on all four streams.

## 6. Things to try

- Raise the compression further: condense to a **single word** and pour all
  24 classes onto ~8 tokens — the arc saturates and *reversal density* becomes
  the honest measure of the remaining signal.
- Different keys: re-key the Latin square per level (`context = data % 4` is
  the reference default) and compare tone-only readings across keys.
- A real lexicon: swap the hand-built 24-class lexicon for a scored sentiment
  lexicon and condense *any* page, not just this letter.
