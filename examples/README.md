# Working examples

Three runnable demonstrations of the tone channel, each deliberately **as
different as possible** from the others, each with a `HOW_IT_WORKS.md` that
explains **exactly how it works** (not just what it does). All are zero-dep
and import the shared `qthe_codec.py` from the repo root.

| example | what it proves | the one idea |
|---|---|---|
| `1_tone_emotion/` | the same text ("I love you") carries a dozen distinct tones | tone = a per-token **momentum trajectory** (up/down/flat/hold), hidden by the Latin square |
| `2_condensation/` | a page condenses to one sentence and the tone carries the shed words | as text shrinks, tone becomes **load-bearing** (tone density 18.5% → 68.4%) |
| `3_spatial_sound/` | a spoken line carries its own stereo position + sound envelope | the 2 timbre bits get a **second reading** — pan is the integral, envelope is the shape |

Run any: `python3 examples/<name>/demo.py`

## How they differ (deliberately)
- `1` varies **what the tone is** (12 feelings on identical words).
- `2` varies **how much text** the tone must carry (page → sentence).
- `3` varies **what the tone maps to** (space + sound, not feeling).

## How they're alike (the invariant)
All three ride the same primitive: 6 data bits + 2 timbre bits, context-keyed
by a Latin square so the tone is invisible to a plaintext reader and noise to
a context-free reader, and recoverable only with context. The invariant is
what makes the examples *obvious* — the same few lines of arithmetic do all
three jobs.
