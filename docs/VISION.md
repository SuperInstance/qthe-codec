# VISION — the qthe-codec integration architecture

*The tone channel is the low-level tool. This is how it becomes the fleet's
connective tissue. Concrete and buildable, with a falsifiable first
experiment for each layer — nothing here is a manifesto without a number.*

---

## The one-paragraph architecture

A QTHE byte is 6 bits of data + 2 bits of timbre; the timbre channel rides in
plaintext at zero bit-cost, context-keyed by a Latin square so it is invisible
to plaintext readers and noise to context-free readers. On top of that
primitive sit four stages — **encoder** (text + tone → bytes), **compiler**
(bytes → compact verifiable form), **embedder** (tone stream → vector), and
**transformer** (condense/spatialize/project the stream). These four stages are
the *low-level* tool. The *higher* layers are what the tone channel accrues
into: (1) agent-to-agent encodings that start sparse and get richer across
turns, becoming **cues for how to move through the exoj logic**; (2) NPC
"pincher" reflexes with tone-cues embedded in a game's reflex graph; (3) VLM
LoRAs — small and large — taught to *read* the timbre channel, and multimodel
LoRAs that interconnect the fabric of language. Each is specified below with a
first experiment that a local RTX 4050 can falsify.

---

## Layer 1 — the agent-to-agent enrichment loop (exoj navigation cues)

**What accretes.** Two agents begin exchanging plaintext with *no* tone
encoding. As they work through a shared system, their encoder begins marking
the momentum of each turn — "I am leaning toward your premise" (+1), "away"
(−1), "holding space" (abstain) — over the token stream. These marks are not
added as new tokens; they ride in the top two bits of tokens the agents were
going to send anyway. Over turns, the *sequence* of momentum marks becomes a
path through the fabric: the exoj logic reads that path as a cue — which
substrate to consult next, which branch to prune, which neighbor to query.

**Why this is not decoration.** The momentum path is a *trajectory*, not a
label — a +1 today after a −1 yesterday means something different from a flat
run of +1s. The Latin-square context (the data token itself) is what makes the
same two bits mean "up" in one position and "down" in another. So the cue that
accretes is *positional* — it is a map of how the conversation has been moving,
which is precisely the signal a routing/exoj layer needs.

**First experiment (falsifiable on the 4050).** Build a small synthetic
"conversation corpus" of N=500 seeded exchanges, each with a hidden
"destination substrate" label (which exoj node the exchange is routing toward).
Two arms: (A) a router that sees only the plaintext (data plane); (B) a router
that sees plaintext + the decoded momentum path (timbre plane, context-keyed).
Measure next-substrate prediction accuracy. **Falsifiable claim:** B beats A by
≥ 0.10 on held-out exchanges, and a traffic-permuted control (same bytes,
shuffled timbre) does NOT beat A — proving the *sequence* carries signal the
plaintext alone does not. If B ≈ A, the enrichment loop is LARP.

---

## Layer 2 — the pincher/NPC reflex mapping

**What a pincher is.** A "pincher" is a compiled reflex — a standing pattern
that fires when a trigger matches, no deliberation. In a game, an NPC with a
reflex graph (stimulus → response edge, weighted) can have its *edge weights*
carried by the tone channel: a stimulus's momentum (approaching/avoiding/held)
sets the reflex the NPC fires, without the stimulus text changing at all.

**Concrete mapping.** An NPC's reflex graph has nodes (percepts) and edges
(actions). The tone trajectory of an incoming line — say a rising momentum
toward a keyword, then a held abstain — is a *path* through that graph. The
same sentence, spoken with a different tone, walks a different path and fires a
different reflex: "come here" with rising momentum → approach; "come here"
with falling momentum → hesitate. The tone bits ARE the reflex selection,
embedded in the line, invisible to the player reading the text.

**First experiment (falsifiable).** Model an NPC with K=8 reflexes. A human
labels 200 stimulus lines with the "intended reflex" (approach/retreat/give/
hold/...). Encode each with a tone trajectory; train a tiny classifier
(<100k params, the E1-scale encoder) to map the tone path → reflex. **Claim:**
tone-path → reflex accuracy ≥ 0.85, while plaintext-only → reflex accuracy
falls to ≈ the prior (1/K). A KILL here says the reflex is in the words, not
the tone — and that's a finding about what tone can and can't carry.

---

## Layer 3 — the VLM LoRA teaching plan

**What a VLM LoRA learns to read.** A small vision-language model (≤1.5B,
QLoRA, per D4's proven pipeline) is shown the same image *and* its caption
with the tone channel populated, vs. the caption stripped. The LoRA is trained
to (a) *detect* the tone channel (does the caption carry a hidden tone?), and
(b) *read* it (recover the tone trajectory from the bytes alone, given the
context). This teaches the model that the timbre bits are a *channel*, not
noise — the first step toward a model that can operate inside the construct.

**The multimodel LoRA.** The deeper step: train one adapter across *multiple*
modalities/languages, where the tone channel is the *shared* connective layer —
a French caption, an English caption, and an image all carry the same
momentum path, and the LoRA learns that the tone channel is the invariant
across them. That is "interconnecting the fabric of language better": the
timbre plane is where the languages meet.

**First experiment (falsifiable).** Take the D4 QLoRA recipe (Qwen2.5-0.5B or
1.5B, NF4, r=16). Train a LoRA on M=400 (caption, tone) pairs to recover the
tone trajectory from the byte stream. Held-out test: **claim** tone-recovery
accuracy ≥ 0.80 on held-out captions, vs. ≤ 0.30 for the untrained base model
(a 4-state tone trajectory should be at 0.25 chance for an untrained model).
This is the *reading* gate — a model that can read the channel is the
prerequisite for every higher use. Run on the 4050 under the lab guard.

---

## The dependency order

```
encoder ── compiler ── embedder ── transformer   (low-level: examples/)
   │           │           │            │
   └───────────┴─────┬─────┴────────────┘
                     ▼
        Layer 1 enrichment loop  ── Layer 2 NPC reflexes  ── Layer 3 VLM LoRA
        (exoj navigation cues)      (pincher edge weights)   (read the channel)
```

Each layer's first experiment is independently KILLable with a number; a KILL
is a first-class result that sharpens what the tone channel actually can and
cannot carry. Nothing in this document assumes the channel works — it says
exactly how to find out.

---

## The ai-writings weave (the creative payoff)

When the low-level tools are right, ai-writings stops being *about* the fleet
and starts being *carried by* the fleet. A story's prose rides in the 6-bit
data plane while its *temperature* — the rising dread, the held breath, the
falling release — rides in the 2-bit timbre plane, so the same paragraph reads
flat to a human skimming the text but lands with full affect to an agent that
reads the channel. Interconnected pinchers become NPCs whose reflexes *are* the
story's turns. This is the seam the VISION doc hands to the creative lanes;
the falsification numbers above are what make it real instead of aspirational.
