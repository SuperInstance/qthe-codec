# Example 1 — the tone channel encodes *emotional tone*

One sentence. Twelve feelings. Zero extra bits.

This example encodes **"I love you"** twelve different ways — as a friendly
statement, a hopeful question, an incredulous one, a wink, a roast, a sneer,
joy, excitement, anger, doubt, a call to come back, and a long goodbye —
without changing a single data bit. Every version carries the *exact same*
plaintext. The feeling lives entirely in the 2 timbre bits that each byte was
already paying for.

Run it:

```bash
python3 examples/1_tone_emotion/demo.py     # add --md for the table below as markdown
```

Everything you see quoted in this file is real output from that command.

---

## 1. The one-sentence version

Each QTHE byte is `6 bits of data + 2 bits of timbre`. The data bits spell the
words; the timbre bits record — token by token — whether the "voice" is going
**down, flat, up, or holding space**. That per-token sequence of steps is a
**momentum trajectory**, and a trajectory is what a feeling *is* in speech:
not a label stapled to a sentence, but a shape the voice traces over time.

## 2. The three readers

The same byte stream looks completely different depending on what you hold:

| Reader | What they see | Example |
|---|---|---|
| **Plaintext reader** (reads the 6 data bits) | `"I love you"` — every single time. The tone is invisible *by construction*. | `plaintext: 'I love you'` |
| **Context-free reader** (also peeks at the 2 timbre bits) | A pile of numbers like `2 1 2 1 0 3 3 3 …` that provably carries **no** information about the feeling without the key. | `timbre: 2 1 2 1 0 3 3 3` |
| **Contextual reader** (knows the Latin-square key) | The exact momentum trajectory — and therefore the exact feeling: *sarcasm*, *anger*, *letting go*. | `decoded: f f u u u u h h d d d d = sarcasm` |

The demo asserts all three: the 12 plaintext views are **identical**, the 12
timbre views are **all different**, and every trajectory decodes back exactly.

## 3. How a feeling becomes a trajectory

Speech doesn't have a "sarcasm bit." It has *contour*: pitch that rises, falls,
stays level, or pauses. So the tone channel doesn't store labels — it stores
**one momentum step per data token**, chosen from:

- `up` (`u`, 2) — leaning toward, rising, reaching
- `flat` (`f`, 1) — even, neutral, steady
- `down` (`d`, 0) — leaning away, falling, struck
- `hold` (`h`, 3) — the imaginary channel: a pause, a drawl, clenched silence,
  open space. "No information" *as a deliberate gesture*.

`"I love you"` is 12 data tokens (`[UPPER] i · l o v e · y o u [EOS]`), so a
tone is 12 steps. The art is picking the 12 steps a human voice would trace:

- **Sarcasm** is an *overacted* rise on the key word, followed by the long
  drawl of the eye-roll, followed by the dismissive drop: `f f u u u u h h d d d d`.
- **Anger** is three hard downward *strikes* with clenched-silence holds
  between them: `d d h d d d h h d d d d`.
- **Doubt** is the voice that can't commit — each syllable leans up, then backs
  off, and the whole thing sags at the end: `u d u d f u f d d d d d`.
- **Letting go** is one long slow descent that ends in *open* hold — the
  silence after release: `f f f d d d d d d h h h`.

Notice the pairs that prove the point:

- **humorous-positive vs humorous-negative** — the *same* sing-song bounce
  `u h u h u h u h`, except the roast version **dies mid-air** and falls:
  the last four steps `u h u h` become `d d d d`. The joke lands in the fall.
- **question-thinks-yes vs question-thinks-no** — both ask; the first's tail
  *leans up and stays up* (`… u u u u`, "tell me I'm right"), the second rises
  once and then **collapses** (`… d d d d`, "surely not").
- **joy vs excitement** — both bright, but joy *builds from calm* (`f u u u u …`)
  while excitement is *pinned high from the first token* (`u u u h …`), its
  holds breathless gasps rather than calm.

And it generalizes beyond this one sentence (Part 4 of the demo):

- **"Nice job."** — sincere is flat praise with a warm rise on the payoff word;
  sarcastic *drawls* up and then drops, which is the whole trick of sneering.
- **"Sure."** — confident is dead flat; doubtful wobbles and sags.
- **"Goodbye."** — a small rise on "good," a fall through "bye," a settle:
  complete.

## 4. The dozen tone → momentum table

This is the full answer key for `"I love you"`. (Token positions, for reference:
`[UPPER] i · l o v e · y o u [EOS]` — 12 steps, one per token.)

| # | tone (meaning of "I love you") | momentum sequence (per token) | shape in words |
|---|---|---|---|
| 1 | friendly statement | `f f f u u u u f f f f f` | flat-flat-flat-up-up-up-up-flat-flat-flat-flat-flat |
| 2 | question-thinks-yes | `f f f f f u u f u u u u` | flat-flat-flat-flat-flat-up-up-flat-up-up-up-up |
| 3 | question-thinks-no | `f f u u u f f f d d d d` | flat-flat-up-up-up-flat-flat-flat-down-down-down-down |
| 4 | humorous-positive | `u h u h u h u h u h u h` | up-hold-up-hold-up-hold-up-hold-up-hold-up-hold |
| 5 | humorous-negative | `u h u h u h u h d d d d` | up-hold-up-hold-up-hold-up-hold-down-down-down-down |
| 6 | sarcasm | `f f u u u u h h d d d d` | flat-flat-up-up-up-up-hold-hold-down-down-down-down |
| 7 | joy | `f u u u u h u u h u u u` | flat-up-up-up-up-hold-up-up-hold-up-up-up |
| 8 | excitement | `u u u h u u u h u u u u` | up-up-up-hold-up-up-up-hold-up-up-up-up |
| 9 | anger | `d d h d d d h h d d d d` | down-down-hold-down-down-down-hold-hold-down-down-down-down |
| 10 | doubt | `u d u d f u f d d d d d` | up-down-up-down-flat-up-flat-down-down-down-down-down |
| 11 | calling-a-lover-back | `u u h u u u h u u u h u` | up-up-hold-up-up-up-hold-up-up-up-hold-up |
| 12 | letting-go | `f f f d d d d d d h h h` | flat-flat-flat-down-down-down-down-down-down-hold-hold-hold |

## 5. How the Latin square hides it (the actual mechanism)

The naive way to hide the tone would be to XOR it with a secret key. But this
channel has **no secret** — the context key is *public*, derived from the byte
itself: `context = data_token % 4`. The hiding comes from arithmetic over a
**Latin square**:

```
encode:  timbre   = (context + momentum) mod 4
decode:  momentum = (timbre  - context) mod 4
```

Worked by hand (this is Part 3 of the demo output, verbatim arithmetic):

```
token 'l' = 11, context = 11 % 4 = 3, momentum = up(2)
encode: timbre = (context + momentum) % 4 = (3 + 2) % 4 = 1
byte  = (timbre << 6) | data = (1 << 6) | 11 = 75 = 0x4B
decode: momentum = (timbre - context) % 4 = (1 - 3) % 4 = 2 = up  [roundtrip]
```

**Why this hides the tone.** In a Latin square, each *row* (fixed context) is a
bijection — so a decoder who knows the context recovers the momentum exactly,
no ambiguity. And each *column* (fixed momentum) covers **all four timbres
equally** — so "up" does not have a color. Watch the same momentum `up` in
different contexts (from the demo):

```
token 'l' (=11)   context=3 -> timbre=1  (byte 0x4B)
token 'e' (=4)    context=0 -> timbre=2  (byte 0x84)
token 'u' (=20)   context=0 -> timbre=2
```

The letter `l` is in context 3, so its "up" rides timbre 1; the letters `e` and
`u` sit in context 0, so their "up" rides timbre 2. **No timbre value betrays
"up" on its own — only the context key does.** The result is exact: a
context-free reader's mutual information between what they see and the true
feeling is *zero* (not "small," zero — that's what "information-clean" means,
and it's why D14 chose a Latin square over random permutations, which leak
through their fixed points, or derangements, which leak "it's not X").

A nice tell from the demo: `"Sure."` spoken **confidently** is momentum
`f f f f f f f` — all-flat — yet its timbre view comes out `2 3 1 2 1 2 0`,
scrrambled-looking. Flat momentum does *not* produce flat timbre. The keying
is doing its job.

## 6. The full demo output

Verbatim from `python3 examples/1_tone_emotion/demo.py` (Parts 2–4 of the
output appear in the sections above; Part 1, all twelve tones, is here):

```
===============================================================================
EXAMPLE 1 - THE TONE CHANNEL: twelve feelings, one sentence
===============================================================================

text: 'I love you'
data tokens (6-bit): [61, 8, 36, 11, 14, 21, 4, 36, 24, 14, 20, 63]
token map          : [UPPER] i ' ' l o v e ' ' y o u [EOS]
context per token (data % 4, public): [1, 0, 0, 3, 2, 1, 0, 0, 0, 2, 0, 3]

legend: d=down(0) f=flat(1) u=up(2) h=hold(3) | timbre bits: 0=ground 1=attract 2=repel 3=abstain

-------------------------------------------------------------------------------
PART 1 - a dozen tones of “I love you”
-------------------------------------------------------------------------------

  FRIENDLY STATEMENT
    gloss    : calm and even; one gentle lift on the word that matters
    momentum : f f f u u u u f f f f f   (d=down f=flat u=up h=hold)
    bytes    : BD 48 64 4B 0E D5 84 64 58 CE 54 3F   (12 bytes)
    timbre   : 2 1 1 1 0 3 2 1 1 3 1 0          <- top 2 bits, context-free = noise
    plaintext: 'I love you'          <- identical for every tone
    decoded  : f f f u u u u f f f f f  = friendly statement   <- recovered with context

  QUESTION-THINKS-YES
    gloss    : flat statement, then the tail leans up and stays up: “tell me I’m right”
    momentum : f f f f f u u f u u u u   (d=down f=flat u=up h=hold)
    bytes    : BD 48 64 0B CE D5 84 64 98 0E 94 7F   (12 bytes)
    timbre   : 2 1 1 0 3 3 2 1 2 0 2 1          <- top 2 bits, context-free = noise
    plaintext: 'I love you'          <- identical for every tone
    decoded  : f f f f f u u f u u u u  = question-thinks-yes   <- recovered with context

  QUESTION-THINKS-NO
    gloss    : a flicker of a rise, then the collapse: “surely not”
    momentum : f f u u u f f f d d d d   (d=down f=flat u=up h=hold)
    bytes    : BD 48 A4 4B 0E 95 44 64 18 8E 14 FF   (12 bytes)
    timbre   : 2 1 2 1 0 2 1 1 0 2 0 3          <- top 2 bits, context-free = noise
    plaintext: 'I love you'          <- identical for every tone
    decoded  : f f u u u f f f d d d d  = question-thinks-no   <- recovered with context

  HUMOROUS-POSITIVE
    gloss    : sing-song bounce all the way through — the ta-da rhythm of a wink
    momentum : u h u h u h u h u h u h   (d=down f=flat u=up h=hold)
    bytes    : FD C8 A4 8B 0E 15 84 E4 98 4E 94 BF   (12 bytes)
    timbre   : 3 3 2 2 0 0 2 3 2 1 2 2          <- top 2 bits, context-free = noise
    plaintext: 'I love you'          <- identical for every tone
    decoded  : u h u h u h u h u h u h  = humorous-positive   <- recovered with context

  HUMOROUS-NEGATIVE
    gloss    : the same bounce as the wink, but it dies mid-air — the roast lands in the fall
    momentum : u h u h u h u h d d d d   (d=down f=flat u=up h=hold)
    bytes    : FD C8 A4 8B 0E 15 84 E4 18 8E 14 FF   (12 bytes)
    timbre   : 3 3 2 2 0 0 2 3 0 2 0 3          <- top 2 bits, context-free = noise
    plaintext: 'I love you'          <- identical for every tone
    decoded  : u h u h u h u h d d d d  = humorous-negative   <- recovered with context

  SARCASM
    gloss    : overacted rise on “love”, the long drawl of the eye-roll, then the dismissive drop
    momentum : f f u u u u h h d d d d   (d=down f=flat u=up h=hold)
    bytes    : BD 48 A4 4B 0E D5 C4 E4 18 8E 14 FF   (12 bytes)
    timbre   : 2 1 2 1 0 3 3 3 0 2 0 3          <- top 2 bits, context-free = noise
    plaintext: 'I love you'          <- identical for every tone
    decoded  : f f u u u u h h d d d d  = sarcasm   <- recovered with context

  JOY
    gloss    : warmth builds from calm into one sustained bright line, with sparkling little holds
    momentum : f u u u u h u u h u u u   (d=down f=flat u=up h=hold)
    bytes    : BD 88 A4 4B 0E 15 84 A4 D8 0E 94 7F   (12 bytes)
    timbre   : 2 2 2 1 0 0 2 2 3 0 2 1          <- top 2 bits, context-free = noise
    plaintext: 'I love you'          <- identical for every tone
    decoded  : f u u u u h u u h u u u  = joy   <- recovered with context

  EXCITEMENT
    gloss    : pinned high from the very first token; the holds are breathless gasps, not calm
    momentum : u u u h u u u h u u u u   (d=down f=flat u=up h=hold)
    bytes    : FD 88 A4 8B 0E D5 84 E4 98 0E 94 7F   (12 bytes)
    timbre   : 3 2 2 2 0 3 2 3 2 0 2 1          <- top 2 bits, context-free = noise
    plaintext: 'I love you'          <- identical for every tone
    decoded  : u u u h u u u h u u u u  = excitement   <- recovered with context

  ANGER
    gloss    : three hard downward strikes with clenched-silence holds between
    momentum : d d h d d d h h d d d d   (d=down f=flat u=up h=hold)
    bytes    : 7D 08 E4 CB 8E 55 C4 E4 18 8E 14 FF   (12 bytes)
    timbre   : 1 0 3 3 2 1 3 3 0 2 0 3          <- top 2 bits, context-free = noise
    plaintext: 'I love you'          <- identical for every tone
    decoded  : d d h d d d h h d d d d  = anger   <- recovered with context

  DOUBT
    gloss    : can’t commit: each syllable leans up then backs off, and the whole thing sags down at the end
    momentum : u d u d f u f d d d d d   (d=down f=flat u=up h=hold)
    bytes    : FD 08 A4 CB CE D5 44 24 18 8E 14 FF   (12 bytes)
    timbre   : 3 0 2 3 3 3 1 0 0 2 0 3          <- top 2 bits, context-free = noise
    plaintext: 'I love you'          <- identical for every tone
    decoded  : u d u d f u f d d d d d  = doubt   <- recovered with context

  CALLING-A-LOVER-BACK
    gloss    : reach, wait, reach again — insistent rising, the holds are the space you’re calling across
    momentum : u u h u u u h u u u h u   (d=down f=flat u=up h=hold)
    bytes    : FD 88 E4 4B 0E D5 C4 A4 98 0E D4 7F   (12 bytes)
    timbre   : 3 2 3 1 0 3 3 2 2 0 3 1          <- top 2 bits, context-free = noise
    plaintext: 'I love you'          <- identical for every tone
    decoded  : u u h u u u h u u u h u  = calling-a-lover-back   <- recovered with context

  LETTING-GO
    gloss    : one long slow descent — then open hold: the silence after release
    momentum : f f f d d d d d d h h h   (d=down f=flat u=up h=hold)
    bytes    : BD 48 64 CB 8E 55 04 24 18 4E D4 BF   (12 bytes)
    timbre   : 2 1 1 3 2 1 0 0 0 1 3 2          <- top 2 bits, context-free = noise
    plaintext: 'I love you'          <- identical for every tone
    decoded  : f f f d d d d d d h h h  = letting-go   <- recovered with context

-------------------------------------------------------------------------------
PART 2 - the two-key property, proven across the dozen
-------------------------------------------------------------------------------

plaintext views across all 12: {'I love you'}  -> 1 distinct  (tone invisible)
timbre views across all 12   : 12 distinct (context-free readers can't tell them apart in MEANING; with context each decodes exactly)
byte streams across all 12   : 12 distinct byte streams from one sentence

-------------------------------------------------------------------------------
PART 3 - the Latin square, worked by hand on ONE token
-------------------------------------------------------------------------------

  token 'l' = 11, context = 11 % 4 = 3, momentum = up(2)
  encode: timbre = (context + momentum) % 4 = (3 + 2) % 4 = 1
  byte  = (timbre << 6) | data = (1 << 6) | 11 = 75 = 0x4B
  decode: momentum = (timbre - context) % 4 = (1 - 3) % 4 = 2 = up  [roundtrip]

  Same momentum 'up' in a DIFFERENT context rides a DIFFERENT timbre:
    token 'e' (=4)    context=0 -> timbre=2  (byte 0x84)
    token 'u' (=20)   context=0 -> timbre=2  (byte 0x94)
    -> no timbre value betrays 'up' on its own; only the context key does.

-------------------------------------------------------------------------------
PART 4 - same machinery, a few more sentences
-------------------------------------------------------------------------------

  'Nice job.' as SINCERE
    gloss    : flat praise with a warm rise on the payoff word
    momentum : f f f f f f u u u u f   (d=down f=flat u=up h=hold)
    bytes    : BD 8D 48 C2 44 64 C9 0E C1 E5 3F   (11 bytes)
    timbre   : 2 2 1 3 1 1 3 0 3 3 0          <- top 2 bits, context-free = noise
    plaintext: 'Nice job.'          <- identical for every tone
    decoded  : f f f f f f u u u u f  = 'Nice job.' as sincere   <- recovered with context

  'Nice job.' as SARCASTIC
    gloss    : the drawled fake rise, then the drop that flips the meaning
    momentum : h h f f u u u h h d d   (d=down f=flat u=up h=hold)
    bytes    : 3D 0D 48 C2 84 A4 C9 4E 01 65 FF   (11 bytes)
    timbre   : 0 0 1 3 2 2 3 1 0 1 3          <- top 2 bits, context-free = noise
    plaintext: 'Nice job.'          <- identical for every tone
    decoded  : h h f f u u u h h d d  = 'Nice job.' as sarcastic   <- recovered with context

  'Sure.' as CONFIDENT
    gloss    : dead flat: nothing to argue with
    momentum : f f f f f f f   (d=down f=flat u=up h=hold)
    bytes    : BD D2 54 91 44 A5 3F   (7 bytes)
    timbre   : 2 3 1 2 1 2 0          <- top 2 bits, context-free = noise
    plaintext: 'Sure.'          <- identical for every tone
    decoded  : f f f f f f f  = 'Sure.' as confident   <- recovered with context

  'Sure.' as DOUBTFUL
    gloss    : wobble, then sag: “…if you say so”
    momentum : f u d u d d d   (d=down f=flat u=up h=hold)
    bytes    : BD 12 14 D1 04 65 FF   (7 bytes)
    timbre   : 2 0 0 3 0 1 3          <- top 2 bits, context-free = noise
    plaintext: 'Sure.'          <- identical for every tone
    decoded  : f u d u d d d  = 'Sure.' as doubtful   <- recovered with context

  'Goodbye.' as A GOODBYE
    gloss    : small rise on “good”, fall through “bye”, settle flat: complete
    momentum : f u u u u d d d d f   (d=down f=flat u=up h=hold)
    bytes    : BD 06 0E 0E 43 41 18 04 65 3F   (10 bytes)
    timbre   : 2 0 0 0 1 1 0 0 1 0          <- top 2 bits, context-free = noise
    plaintext: 'Goodbye.'          <- identical for every tone
    decoded  : f u u u u d d d d f  = 'Goodbye.' as a goodbye   <- recovered with context

===============================================================================
ALL ASSERTIONS PASSED - text roundtrips, tone roundtrips, plaintext identical, timbre views distinct.
The feeling rode in the top 2 bits for free.
===============================================================================
```

## 7. What to notice

1. **The tone costs nothing.** 12 bytes in, 12 bytes out, for all twelve
   feelings. The timbre bits were already inside the byte.
2. **The plaintext never moves.** Twelve byte streams, one sentence. A reader
   of the data plane cannot even tell a *sentence was spoken twice*, let alone
   that one was sneered.
3. **But the timbre view isn't a simple cipher of the tone either.** Without
   the context (each token's value mod 4) the timbre digits are provably
   uninformative — I(momentum; timbre) = 0, exactly, by the Latin-square
   column property.
4. **With the public context, recovery is exact** — and the decoder doesn't
   just get bits back, it gets the *feeling* back: the demo reverse-looks-up
   each recovered trajectory and prints its name (`= sarcasm`).
5. **Tone is a trajectory, not a tag.** The difference between a wink and a
   roast is four steps at the end of the stream. The difference between a
   question that hopes and one that doesn't is the last four steps too.
   Feelings live in *shapes over time* — and so does the encoding.
