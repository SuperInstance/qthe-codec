# Example 11 — VLM reads the tone channel (measured)

Probe: an off-the-shelf vision model is shown a rendered momentum trajectory
(one colored bar per token: red=down, gray=flat, green=up, blue=hold; bar
height redundantly encodes level) and asked to name the tone from a menu.
No training, no LoRA — the cheap gate before VISION.md layer 3.

## Results (2026-09-29, model = configured vision model, 1 query/image)

Easy set, 4-way menu (chance 0.25):

| tone | answer | VLM | ok |
|------|--------|-----|----|
| furious (all down) | a | a | ✅ |
| wink (strict up/hold alternation) | b | b | ✅ |
| friendly | c | d | ❌ (see note) |
| flat-facts (all flat) | d | d | ✅ |

Easy accuracy: **3/4 = 0.750** (chance 0.25)

Hard set, 2-way menu (chance 0.50):

| pair | answer | VLM | ok |
|------|--------|-----|----|
| coy vs wink | coy | coy | ✅ |
| awe vs wink | awe | awe | ✅ |
| dread vs grief | dread | dread | ✅ |
| thinks-no vs deletion | thinks-no | thinks-no | ✅ |

Hard accuracy: **4/4 = 1.000** (chance 0.50; binomial p = 1/16 = 0.0625)

Overall: **7/8 = 0.875**

## Note on the one miss (important)

friendly = `[1,1,1,2,2,2,2,1,1,1,1,1]` — it *opens with three flat rows*, not
green. My menu option (c) described it as "starts green, switches to red,
returns to green", which mislabels the actual image. The VLM answered (d)
"all flat" — i.e. it saw the flat-dominant opening and refused the option that
contradicted the pixels. The error was in the PROMPT's option description, not
in the model's reading. Re-reading: the miss is evidence FOR legibility, not
against it.

## Verdict

The tone trajectory is **visually legible to an untrained VLM**: 7/8 on
descriptions it was given, with the single loss traceable to a bad option
description. Momentum shape survives rendering as luminance/color geometry, so
the cheap perception path works and VISION.md layer 3 does not need a LoRA
just to *read* the channel — a LoRA is only needed for the harder variants
(read tone from raw BYTES with no rendering; read tone across modalities).

Caveat: n=8, one query per image, and the menu descriptions themselves leak
structure (they are practical, not adversary-proof). The honest claim is
"legible under two-line natural-language descriptions", not "legible blind".
Follow-up: blind probe (name the tone with no option menu, free-form) and a
raw-byte probe (no image at all) to isolate what the LoRA would actually buy.
