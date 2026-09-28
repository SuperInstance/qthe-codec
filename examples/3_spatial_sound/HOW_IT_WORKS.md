# Example 3 — Spatial Sound

**The idea:** the 2 timbre bits a QTHE byte already carries get re-keyed, contextually, as a **stereo + envelope channel**. A spoken line carries its own stereo placement and its own non-verbal sound — a knock, a laugh, a sigh, silence — in bits that were already paid for. The plaintext view shows nothing but the words.

Run it:

```bash
cd examples/3_spatial_sound
python3 demo.py        # zero deps; imports qthe_codec from the repo root
```

---

## 1. The re-keying

The shared core (`qthe_codec.py`) defines a per-token **momentum** in `{down=0, flat=1, up=2, hold=3}` and hides it in the top 2 bits of each byte via the Latin square `timbre = (context + momentum) mod 4`, where `context = data_token % 4`.

In examples 1–2 that momentum was *tone*. Here the exact same 4-state stream is read as **staging**. Nothing in the codec changes — only the lexicon the renderer applies:

| momentum step | tonal reading (examples 1–2) | spatial/sonic reading (this example) |
|---|---|---|
| `down` (0) | falling | pan step **LEFT** / envelope **decay** |
| `flat` (1) | neutral | envelope **sustain** (pan holds) |
| `up` (2) | rising | pan step **RIGHT** / envelope **attack** |
| `hold` (3) | abstain / imaginary | **SPACE** — offstage, ambient, unvoiced / **silence** |

This is the contextual point of the whole system: **the same 2 bits mean different things in different contexts.** "Hold" was the imaginary channel — the act of leaving space. Here it becomes literal space: the offstage, the unvoiced stage direction. Silence costs the same as every other state: 2 bits, already paid.

## 2. One stream, two readings

Each line of the scene is one **gesture**: the per-token momentum trajectory (padded with `flat`). A gesture is read two ways at once:

- **Pan = the *integral* of the trajectory.** Steps sum as `up=+1, down=−1, flat=hold=0`:
  - drift ≥ +2 → **RIGHT**, drift ≤ −2 → **LEFT**, otherwise → **FRONT** (a small drift reads as a center-stage voice leaning, not a move)
  - all `hold` → **SPACE** (nothing is placed; the line is ambient)
- **Envelope = the *shape* of the trajectory.** The renderer's grammar, applied in order:
  1. all `hold` → **SILENCE**
  2. ≥ 2 sign reversals among moving steps → **LAUGH** (a bouncing ripple)
  3. first moving step is `up` and a `down` follows within 3 steps → **KNOCK** (attack, then fast decay)
  4. no `up` at all, after ≥ 2 leading `flat` steps → **SIGH** (a delayed slow decay)
  5. otherwise → **SPEECH** (settled delivery)

So `^vvv-------` is simultaneously "left speaker" (integral −2) and "a knock" (attack-then-decay shape). `--v-------` is "front/center" (integral −1) and "a sigh" (decay after a hold). The demo's `read_spatial()` is this grammar in 15 lines; the encoder's `GESTURES` table is its inverse.

Because the signal is per-token, a line doesn't merely *sit* somewhere — it can *move*. This demo keeps the reading discrete and deterministic (static L/F/R/Space), but the trace `^ - v` could equally be interpolated by a renderer as continuous pan automation: a line that walks from one speaker to the other as it is spoken.

## 3. Why it's invisible

- **Plaintext readers** get the 6-bit data plane only (`plaintext_view`). They see the words; the staging channel does not exist for them.
- **Wire-level readers** see the timbre bits, but the Latin square still applies: the same LEFT step produces *different* wire bits on different data contexts (`timbre = (data%4 + step) mod 4` — a fixed permutation would leak one free hit per fixed point; the square can't). Without the context key the timbre marginal is noise; across the 99 bytes of the demo it scatters across all four values.

## 4. The scene

A six-line radio-play moment, one **cue** (stream) per line — the natural unit for a renderer:

| # | pan | sound | line | gesture (padded with `-`) |
|---|---|---|---|---|
| 1 | left | knock | `Who's there?` | `^vvv` |
| 2 | right | laugh | `Only the wind.` | `^v^v^^` |
| 3 | left | speech | `The wind doesn't laugh.` | `vv` |
| 4 | space | silence | `(a long pause)` | `......` (all hold) |
| 5 | front | sigh | `Then come inside.` | `--v` |
| 6 | space | silence | `(curtain)` | `........` (all hold) |

## 5. Demo output (verbatim)

```
======================================================================
 QTHE EXAMPLE 3 - SPATIAL SOUND
 stereo pan + sound envelopes riding the 2 timbre bits, for free
======================================================================

--- 1. THE SCORE (what the director hears) ----------------------------
 #  pan     sound     line
 1  left    knock     Who's there?
 2  right   laugh     Only the wind.
 3  left    speech    The wind doesn't laugh.
 4  space   silence   (a long pause)
 5  front   sigh      Then come inside.
 6  space   silence   (curtain)

--- 2. THE WIRE (the byte stream) -------------------------------------
 line 1: 14 bytes  fd 96 c7 8e a9 d2 64 13 07 44 91 44 68 3f
 line 2: 16 bytes  fd 8e cd cb 98 a4 13 07 44 64 d6 48 8d 03 a5 3f
 line 3: 25 bytes  7d d3 07 44 64 d6 48 8d 03 64 03 ce 44 d2 8d a9 13 64 0b 40 54 c6 07 a5 3f
 line 4: 15 bytes  2d c0 e4 8b 4e 0d 46 e4 8f c0 d4 52 c4 6e bf
 line 5: 19 bytes  bd 13 c7 44 8d 64 c2 ce 4c 44 64 48 8d d2 48 03 44 a5 3f
 line 6: 10 bytes  2d 42 d4 11 93 c0 c8 0d 6e bf
 total: 99 bytes (6 data bits + 2 timbre bits each)

--- 3. THE EAVESDROPPER'S VIEW (6-bit data plane only) ----------------
 Who's there?
 Only the wind.
 The wind doesn't laugh.
 (a long pause)
 Then come inside.
 (curtain)
 [no pan, no sound, no staging - the spatial channel does not exist here]

--- 4. THE DECODED STAGE (what a spatial renderer recovers) -----------
 line 1  "Who's there?"
   pan   : LEFT   L --o-------|---------- R
   sound : KNOCK   (drift -2)
   trace : ^vvv----------
 line 2  "Only the wind."
   pan   : RIGHT  L ----------|-------o-- R
   sound : LAUGH   (drift +2)
   trace : ^v^v^^----------
 line 3  "The wind doesn't laugh."
   pan   : LEFT   L --o-------|---------- R
   sound : SPEECH  (drift -2)
   trace : vv-----------------------
 line 4  "(a long pause)"
   pan   : SPACE  L . . . ~ ~ ~  offstage / ambient  ~ ~ ~ . . . R
   sound : SILENCE (drift +0)
   trace : ...............
 line 5  "Then come inside."
   pan   : FRONT  L ----------o---------- R
   sound : SIGH    (drift -1)
   trace : --v----------------
 line 6  "(curtain)"
   pan   : SPACE  L . . . ~ ~ ~  offstage / ambient  ~ ~ ~ . . . R
   sound : SILENCE (drift +0)
   trace : ..........

--- 5. WHY IT'S INVISIBLE ---------------------------------------------
 the same LEFT step, keyed by different data contexts (Latin square):
   data 'e' (ctx 0): wire timbre 0
   data 'h' (ctx 3): wire timbre 3
   data 's' (ctx 2): wire timbre 2
 wire timbre histogram over all 99 bytes:
   ground(0):22  attract(1):30  repel(2):22  abstain(3):25

--- VERIFICATION ------------------------------------------------------
 all asserts passed: text + momentum roundtrip, staging hidden,
 spatial map decodes exactly to the director's score.

 OK - the staging rode in the top 2 bits for free.
```

Every line of section 4 is recovered from the bytes alone — the demo's verification asserts that the decoded `(pan, sound)` equals the director's score for all six lines, that text and momentum round-trip, and that `plaintext_view` hides the staging completely.

## 6. Design notes

- **Cost:** 0 bits. The spatial channel is carried entirely in the 2 timbre bits each byte already had.
- **Capacity:** 2 bits per token is 4 states, which is why the pan vocabulary is L/F/R/Space and the envelope vocabulary is attack/sustain/decay/silence. Richer palettes (5.1 surround, full ADSR) would need either more states per token (fewer data bits) or longer gestures — the trajectory already supports *motion* within a line for free.
- **Framing:** the codec is per-stream; this example frames each dialogue line as its own cue stream, which is what a spatial renderer wants anyway (one placement decision per cue). A continuous stream with `NEWLINE` tokens would work too; the grammar would just re-anchor per line.
- **Extensibility:** the decoder grammar (ripples → laugh, attack/decay → knock, delayed decay → sigh) is a tiny, deterministic first layer. Any richer lexicon — footsteps (regular attack bursts), rain (dense alternating ripple), a door creak (slow rising sustain) — is just more shapes on the same 4-state alphabet, decodable by the same public grammar.
