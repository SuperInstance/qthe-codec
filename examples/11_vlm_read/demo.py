#!/usr/bin/env python3
"""
demo.py — example 11: can a VLM READ the tone channel from a rendered image?

The VISION.md layer-3 plan trains a LoRA to read tone from bytes. Before
spending GPU time, this cheap gate asks the simpler question: is the tone
trajectory VISUALLY legible at all to an off-the-shelf vision-language model?

What we render: each canonical tone as a colored-cell strip (one column per
momentum cell, 4 colors for down/flat/up/hold). No text, no labels — just the
trajectory as an image, the way a game would paint a speaker's tone aura.

Falsifiable claims (measured in RESULTS.md after VLM queries):
  P1: VLM accuracy naming the tone from a 4-choice menu exceeds 0.50
      (chance = 0.25) on CLEARLY DISTINCT tones.
  P2: VLM accuracy on SUBTLE tone pairs exceeds chance (0.50, 2 choices).
If the VLM sits at chance, the trajectory needs a learned reader (the LoRA)
before any downstream use — that is a real kill signal for the cheap path.

Zero dependencies (stdlib zlib/struct PNG writer). Renders images + ground
truth only; the VLM queries are done by the researcher agent.
Run: python3 examples/11_vlm_read/demo.py
"""
from __future__ import annotations

import json
import struct
import sys
import zlib
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))

OUT = Path(__file__).resolve().parent / "images"

# momentum palette: down=red, flat=gray, up=green, hold=blue
PALETTE = {0: (220, 60, 60), 1: (140, 140, 140), 2: (60, 180, 80), 3: (70, 110, 220)}

# The 12 canonical tones from example 4/1 ("i love you" 12-token stream)
TONES: dict[str, list[int]] = {
    "friendly":    [1, 1, 1, 2, 2, 2, 2, 1, 1, 1, 1, 1],
    "thinks-yes":  [1, 1, 1, 1, 1, 2, 2, 1, 2, 2, 2, 2],
    "thinks-no":   [1, 1, 2, 2, 2, 1, 1, 1, 0, 0, 0, 0],
    "wink":        [2, 3, 2, 3, 2, 3, 2, 3, 2, 3, 2, 3],
    "mocking":     [1, 2, 2, 2, 3, 3, 0, 0, 0, 0, 0, 0],
    "furious":     [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
    "grief":       [2, 1, 0, 0, 1, 0, 0, 0, 3, 3, 3, 0],
    "flat-facts":  [1] * 12,
    "awe":         [2, 2, 3, 2, 2, 3, 2, 2, 3, 2, 2, 2],
    "dread":       [1, 1, 0, 1, 0, 1, 0, 0, 3, 0, 0, 0],
    "coy":         [1, 2, 3, 2, 3, 1, 2, 3, 1, 2, 3, 1],
    "deletion":    [2, 2, 2, 3, 3, 3, 1, 1, 0, 0, 0, 3],
}

# test sets: 4 one-of-four easy probes + 4 one-of-two hard probes
EASY = ["furious", "wink", "friendly", "flat-facts"]
HARD = [("coy", "wink"), ("awe", "wink"), ("dread", "grief"), ("thinks-no", "deletion")]


def write_png(path: Path, pixels: list[list[tuple[int, int, int]]]) -> None:
    """Minimal truecolor PNG writer. pixels: rows of RGB tuples."""
    h, w = len(pixels), len(pixels[0])
    raw = b"".join(
        b"\x00" + bytes(v for px in row for v in px) for row in pixels
    )
    def chunk(tag: bytes, data: bytes) -> bytes:
        c = tag + data
        return struct.pack(">I", len(data)) + c + struct.pack(">I", zlib.crc32(c))
    png = (b"\x89PNG\r\n\x1a\n"
           + chunk(b"IHDR", struct.pack(">IIBBBBB", w, h, 8, 2, 0, 0, 0))
           + chunk(b"IDAT", zlib.compress(raw))
           + chunk(b"IEND", b""))
    path.write_bytes(png)


def render_tone(tone: list[int], cell: int = 28, height: int = 168) -> Path:
    """One column per momentum cell, colored by state; bottom-anchored bars."""
    w = len(tone) * cell
    px = [[(255, 255, 255)] * w for _ in range(height)]
    for i, m in enumerate(tone):
        color = PALETTE[m]
        # bar height encodes the momentum level too (redundant coding)
        bar = 30 + m * 30
        for y in range(height - bar, height):
            for x in range(i * cell, (i + 1) * cell):
                px[y][x] = color
    path = OUT / f"tone_{len(tone)}_{abs(hash(tuple(tone))) % 10000:04d}.png"
    path.parent.mkdir(exist_ok=True)
    write_png(path, px)
    return path


def main() -> None:
    OUT.mkdir(exist_ok=True)
    gt = {"easy": [], "hard": []}
    for name in EASY:
        # 4-way menu: furious / flat-facts / friendly / wink as decoy set
        path = render_tone(TONES[name])
        gt["easy"].append({"answer": name, "options": EASY, "image": path.name})
    for a, b in HARD:
        path = render_tone(TONES[a])
        gt["hard"].append({"answer": a, "options": [a, b], "image": path.name})
    (OUT / "ground_truth.json").write_text(json.dumps(gt, indent=2))
    print(f"rendered {len(gt['easy'])} easy + {len(gt['hard'])} hard probes -> {OUT}")
    print("chance: easy 0.25, hard 0.50")


if __name__ == "__main__":
    main()
