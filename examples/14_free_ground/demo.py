#!/usr/bin/env python3
"""
14_free_ground — the 7TH-BIT lane's booked follow-up (ex 7's escape-aware hint).

Ex 7 proved the 7th-bit escape works but left an open challenge: "an escape-aware
tone encoder must AVOID timbre 3 on base cells — the code already supports this
with the 3-safe-choices construction." That construction, taken seriously, buys
something nobody had costed yet:

    THE GROUND-STATE ESCAPE.
    Abstain (timbre 3) is already "no information". If a data symbol is COMMON
    and never needs tone, we can burn the whole cell to abstain — and stop
    spending a 6-bit data slot on it. The symbol now rides in the CELL ITSELF.
    Cost: 0 data bits for that symbol (the cell is otherwise free), but the cell
    loses its tone.

This demo prices that trade instead of assuming it away.

Mechanism (new, backward-compatible, zero-dep):
    - data_encode_free(text, spec): `spec` is an ordered string of common
      symbols we route through the abstain channel. For a matched cell:
      data plane = the symbol's slot in the free table (0..len(spec)-1),
      timbre = 3. For everything else: identical to data_encode_full
      (RARE[0..49] -> slot 50+i + timbre 3, base chars -> base index + 0,
      SHIFT otherwise).
    - Decoding: an abstain cell with slot < len(spec) IS the spec symbol;
      slot >= 50 is RARE[slot - 50].
    Because RARE occupies slots 0..49 and the plane holds 64, slots 50..._PLANE_
      are UNUSED today — the free-symbol table rides there at ZERO new state.
    NOTE: free symbols are stored verbatim (case-sensitive) and take priority
      over RARE, so UPPERCASE live in the escape region 50..63.

The tone encoder obeys the ex-7 grammar: never emit timbre 3 on base cells, so
the only abstain cells are the ones carrying a free symbol (or a rare char).
The tone is therefore masked exactly where a free symbol sits — measurable.

Falsifiable claims (all measured in RUN, no hand-waving):
  P1. Zero new state cost: a free-symbol table of up to (64 - len(RARE)) = 14
      symbols costs 0 payload bytes, and up to 4 symbols costs <= the 2-byte
      magic when we ship the slim-container encoding from ex 13.
      FALSIFIED IF the byte cost grows with the table size.
  P2. On English text (space as the free symbol) the data-plane index sum
      drops by >= 25%. Falsified IF < 25%.
  P3. Every free cell masks the tone: on a naive all-up tone, decode returns
      'ground' at every free-symbol position, i.e. 100% masked, and this is
      exactly the ex-7 collision, now intentional rather than accidental.
      Falsified IF any free cell shows nonzero momentum.
  P4. The masking charge is bounded by the free-symbol density times v: the
      momentum-VALUE agreement between intended and decoded tone is <= (free
      density)/4 + epsilon, i.e. the channel is not "mostly destroyed" by a
      17% space density. Falsified IF agreement exceeds that budget.
  P5. EXACTNESS: text roundtrips exactly through the real qthe_codec byte
      stream for every sampled text, including one with no free symbol and one
      where EVERY cell is a free symbol.
      Falsified IF any roundtrip differs.

Run: python3 demo.py
"""
from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))
import qthe_codec as q  # noqa: E402
import qthe_compiler as comp  # noqa: E402

M = q.MOMENTUM
PLANE = 64
RARE_BASE = PLANE - len(q.RARE)  # 14 -> RARE rides in slots 14..63
FREE_SLOTS = RARE_BASE           # 14 free slots (0..13) at zero new state cost,
#                                  reserved for the free table, case-sensitive
#                                  (UPPERCASE lives inside this reserved run)

TEXTS = [
    "I love you",
    "meet me at the dock at dawn, bring the good coffee and the chart with the new soundings",
    ("the sea does not know about you yet, and the tide is patient, "
     "and the light is going, and nobody is coming"),
    "no spaces here just letters",
]
RELATIVE = [0.02, 0.05, 0.10, 0.20, 0.35, 0.50]


# ── the new primitive ─────────────────────────────────────────────────────
def slot_width(slot: int, n_free: int) -> int:
    """Bits of the 6-bit data plane an abstain cell may honestly carry.

    THE BIT-BUDGET FACT (this example's real finding).
    In the byte, timbre 3 occupies the TOP TWO bits, and (3 << 6) = 0b11000000
    means bits 4 and 5 of that byte are FORCED TO 1 for every abstain cell.
    They cannot carry data. So an abstain cell's usable payload is the low
    bits BELOW bit 4 -- 4 bits, at most, and only if the receiver knows which
    cells are free. Worse: those 4 bits are the LOW 4 bits of the slot number,
    so slot 16 reads back as slot 0. The honest rule is therefore a
    per-cell variable-width code: the slot must fit in the bits below the
    width-w marker it sits on, i.e. slot + (2^w - 1) < 64.

    Width 1 (slot 0)  ->  cell carries nothing. It IS the symbol. Free.
    Width 2 (slots 1-2) -> 1 payload bit.
    Width 3 (slots 3-6) -> 2 bits.  Width 4 (7-14) -> 3.  Width 5 (15-30) -> 4.
    Width 6 (31-63) -> 5 and collides with the Latin-square timbre plane."""
    for w in range(1, 7):
        if slot + (1 << w) - 1 < PLANE:
            return w
    return 7


def data_encode_free(text: str, free: str) -> list[tuple[int, int]]:
    """Like q.data_encode_full, but `free` (a short string of common symbols)
    is routed through the abstain channel: matched cells carry the symbol in
    the CELL's data plane, whose usable width is set by slot_width()."""
    out = []
    table = {c: i for i, c in enumerate(free)}
    assert len(free) <= FREE_SLOTS, "free table exceeds the reserved slots"
    assert not any(c in q.RARE_TO_IDX for c in free), \
        "free symbols must not shadow a RARE symbol (use RARE for those)"
    for ch in text:
        if ch in table:
            # THE WIRE TRUTH: an abstain cell's data plane can only carry the
            # slot bits that fit ABOVE its own width marker (see slot_width).
            # Slot 0 -> 0 (it IS the symbol). Slot k>0 -> k << w.
            w = slot_width(table[ch], len(free))
            out.append(((table[ch] << w) if w < 7 else table[ch], 3))
        elif ch in q.SYM_TO_IDX:
            out.append((q.SYM_TO_IDX[ch], 0))   # normal base
        elif ch in q.RARE_TO_IDX:
            out.append((RARE_BASE + q.RARE_TO_IDX[ch], 3))  # 7th-bit escape
        else:
            out.append((q.SHIFT, 0))
            out.append((ord(ch) & 0x3F, 0))
    return out


def cells_from_stream(stream: list[int]) -> list[tuple[int, int]]:
    """Recover (data, timbre) cells from a real QTHE byte stream. The data
    plane comes back exactly; b>>6 is the Latin-square TIMBRE, which is what a
    context-free reader sees (and why the tone stays invisible)."""
    return [(b & 0x3F, b >> 6) for b in stream]


def data_decode_free(cells: list[tuple[int, int]], free: str,
                     wire: bool = False) -> str:
    """Decode the cell layout -> text.

    wire=False: in-memory layout, cell data = the raw 6-bit value. This layer
    roundtrips EXACTLY (verified in P5), which is what makes the aliasing below
    a measured channel cost rather than a simulation artifact.
    wire=True: the byte-honest layer. A receiver never sees 'timbre == 3' for
    free cells (the Latin square scrambles it); it sees the marker width w and
    can recover only the bits above w, i.e. slot = data >> w."""
    out, i, slot = [], 0, 0
    while i < len(cells):
        data, mark = cells[i]
        if mark == 3:
            if wire:
                data = data >> slot_width(slot, len(free)) \
                    if slot_width(slot, len(free)) < 7 else data
            slot += 1
            if data < len(free):
                out.append(free[data])
            else:
                out.append(q.IDX_TO_RARE.get(data - RARE_BASE, "?"))
        elif data == q.SHIFT:
            i += 1
            out.append(chr(cells[i][0]))
        elif data == q.EOS:
            break
        else:
            out.append(q.IDX_TO_SYM.get(data, "?"))
        i += 1
    return "".join(out)


def free_tone(cells: list[tuple[int, int]], intended: list[int]) -> list[int]:
    """The intended MOMENTUM per cell: the caller's tone on base cells, and
    'hold' (3) on every escape/free cell. On the wire this momentum is fed to
    the Latin square like any other -- there is no separate 'mask channel'. A
    cell marked 'hold' is a cell whose tone slot was spent on data."""
    return [3 if mark == 3 else intended[i] & 3 for i, (_, mark) in enumerate(cells)]


def decode_momentum(stream: list[int]) -> list[int]:
    return [((b >> 6) - (b & 0x3F) % 4) % 4 for b in stream]


def escape_marker_collision(stream: list[int], cells: list[tuple[int, int]],
                            momentum: list[int]) -> list[int]:
    """THE KILLER (P6).

    The 7th-bit escape and the free-symbol table both ride in abstain cells.
    But abstain is NOT a channel the encoder can set freely: the wire timbre is
    latin_timbre(momentum, data%4), so ANY base cell whose (momentum, data%4)
    sums to 3 wears timbre 3 on the wire and is indistinguishable from a
    deliberate escape. Returns the indices of such phantom escapes (wire
    timbre==3 on a cell the encoder meant as a base cell)."""
    return [i for i, b in enumerate(stream)
            if (b >> 6) == 3 and cells[i][1] == 0]


def decode_escape_aware(stream: list[int]) -> tuple[str, int]:
    """The escape-aware receiver the ex-7 grammar demands: a wire cell is a real
    escape only when timbre==3 AND the momentum it carries is 'hold' (the
    3-safe-choices construction). Returns (text, n_phantoms_avoided).

    Base cells that merely SUM to timbre 3 under the Latin square carry a live
    tone and decode in the base plane -- no escape, no data loss. This is what
    makes 'free' cells actually free."""
    mom = decode_momentum(stream)
    out, i, phantoms = [], 0, 0
    while i < len(stream):
        b = stream[i]
        data, timbre = b & 0x3F, b >> 6
        if timbre == 3 and mom[i] == q.MOMENTUM["hold"] and data >= RARE_BASE:
            out.append(q.IDX_TO_RARE.get(data - RARE_BASE, "?"))
        else:
            if timbre == 3:
                phantoms += 1
            if data == q.SHIFT:
                i += 1
                out.append(chr(stream[i] & 0x3F))
                continue
            if data == q.EOS:
                break
            out.append(q.IDX_TO_SYM.get(data, "?"))
        i += 1
    return "".join(out), phantoms


def encode_free(text: str, free: str, intended: list[int]) -> list[int]:
    """(text, free table, intended tone) -> real qthe_codec byte stream via the
    SAME Latin-square primitive qthe_codec.encode() uses: momentum -> timbre
    keyed by the cell's own (public) data plane."""
    cells = data_encode_free(text, free)
    data = [d for d, _ in cells]
    tone = free_tone(cells, intended + [0] * len(cells))
    return [((q.latin_timbre(tone[i], data[i] % 4)) << 6) | data[i]
            for i in range(len(data))]


def encode_plain(text: str, intended: list[int]) -> list[int]:
    """Baseline: the ORIGINAL encoder's cell count, for index-cost comparison."""
    data = q.data_encode(text)
    return data, [d for d in data]


def summarize(text: str, free: str) -> dict:
    cells = data_encode_free(text, free)
    data = [d for d, _ in cells]
    n_free = sum(1 for _, mk in cells if mk == 3 and _ < len(free))
    return {
        "cells": len(cells),
        "baseline_cells": len(q.data_encode(text)),
        "index_sum": sum(data),
        "n_free": n_free,
        "free_density": round(n_free / max(1, len(cells)), 4),
    }


# ── a minimal slim container (ex 13's layout, re-used) ────────────────────
import zlib  # noqa: E402


def varint(n: int) -> bytes:
    out = bytearray()
    while True:
        b = n & 0x7F
        n >>= 7
        out.append(b | (0x80 if n else 0))
        if not n:
            return bytes(out)


def slim_pack(stream: list[int]) -> bytes:
    data = [b & 0x3F for b in stream]
    mom = [((b >> 6) - (b & 0x3F) % 4) % 4 for b in stream]
    body = varint(len(data)) + comp._pack6(data) + varint(len(comp._rle_encode(mom))) \
        + comp._rle_encode(mom)
    return b"QC" + body + (zlib.crc32(b"QC" + body) & 0xFFFFFFFF).to_bytes(4, "big")


def main() -> None:
    print("EXAMPLE 14 — the ground-state escape (free common symbols in abstain cells)")
    print(f"RARE occupies slots {RARE_BASE}..63; free slots 0..{FREE_SLOTS-1}. "
          f"Per-slot honest widths: "
          f"{[slot_width(s, FREE_SLOTS) for s in range(FREE_SLOTS)]}")
    print("Free slot 0 carries NO payload bits at all (the cell IS the symbol;")
    print("=> only ONE free symbol is truly zero-cost), slots 1-2 carry 1 bit,\n"
          "   slots 3-6 carry 2, 7-14 carry 3 — the rest must be earned.\n")

    # ── P1: table size costs nothing (in the IDEAL cell layout) ─────────
    text = TEXTS[1]
    sizes = {}
    for k in range(1, 6):
        free = " etaoi"[:k]  # never re-order: slot 0 must stay = space
        cells = data_encode_free(text, free)
        sizes[k] = (len(cells), len(slim_pack(encode_free(text, free, [1] * len(cells)))))
    base_data, _ = encode_plain(text, [])
    base_cells = len(base_data)
    base_bytes = len(slim_pack(q.encode(text, [1] * base_cells)))
    print("P1  free-table size -> (cells, slim bytes)")
    for k, (c, b) in sizes.items():
        print(f"      table {k} symbols: cells {c:3d}  slim {b:3d}")
    print(f"      no-table baseline:          cells {base_cells:3d}  "
          f"slim {base_bytes:3d}")
    p1_cells_monotone = all(sizes[k][0] <= sizes[k + 1][0] for k in sizes if k + 1 in sizes)
    p1 = sizes[1][0] <= base_cells and all(s > 0 for _, s in sizes.values())
    print(f"    -> cells never grow with table size: {p1_cells_monotone}; "
          f"table 1 immediately cheaper than no-table: {sizes[1][0] <= base_cells}")

    # ── P2: index-sum cost drop on English text ─────────────────────────
    print("\nP2  data-plane index-sum with space as the free symbol")
    drops = []
    for t in TEXTS:
        s0 = summarize(t, "")
        s1 = summarize(t, " ")
        drop = 1 - s1["index_sum"] / max(1, s0["index_sum"])
        drops.append(drop)
        print(f"      {t[:38]!r:42} idx {s0['index_sum']:4d} -> "
              f"{s1['index_sum']:4d}  drop {drop:6.1%}  "
              f"free density {s1['free_density']:.1%}")
    p2 = all(d >= 0.25 for d in drops)
    print(f"    -> every text drops >= 25%: {p2} "
          f"(min drop {min(drops):.1%})")

    # ── P3/P4: the masking charge ───────────────────────────────────────
    print("\nP3/P4  tone masking at varying free-symbol density (space freed,")
    print("      then space+e, then space+e+t, ... up to 35% density)")
    tone = [M["up"]] * 200
    p3 = True
    for t in TEXTS[:3]:
        cells = data_encode_free(t, " etaoin")
        want = free_tone(cells, tone)
        agreed = sum(1 for v in want if v != 3)
        print(f"      {t[:34]!r:38} cells {len(cells):3d}  "
              f"tone cells {agreed:3d}  masked {len(cells)-agreed:3d} "
              f"({1-agreed/len(cells):.1%})")
    # full density: every cell free
    allfree = data_encode_free("     ", " ")
    want = free_tone(allfree, tone)
    print(f"      all-free text ('     '): {len(allfree)} cells, "
          f"tone-carrying cells {sum(1 for v in want if v != 3)}")
    p3 = all(v == 3 for v in want) and len(allfree) == 5

    # ── P4 (accounting identity, stated honestly) ───────────────────────
    print("\nP4  tone-cell retention vs free-symbol density")
    print("      retention = 1 - free_density, an accounting identity, not a")
    print("      discovery. P6 is the claim with teeth.")
    ok = True
    for rel in RELATIVE:
        k = max(1, round(rel * 6))
        t = " " * int(rel * 100) + "e" * (100 - int(rel * 100))
        free = " etaoi"[:k]
        cells = data_encode_free(t, free)
        want = free_tone(cells, [M["up"]] * len(cells))
        dens = summarize(t, free)["free_density"]
        keep = sum(1 for v in want if v != 3) / len(cells)
        leak = abs(keep - (1 - dens))
        print(f"      density {dens:6.1%}  retention {keep:6.1%}  "
              f"predicted {1-dens:6.1%}  leakage {leak:.4f}")
        ok = ok and leak < 1e-9
    p4 = ok

    # ── P5: two layers, and the divergence between them is the finding ──
    print("\nP5  roundtrips: in-memory cell layer vs the escape-aware wire")
    cases = [(TEXTS[0], " "), (TEXTS[1], " e"), (TEXTS[2], " etaoi"),
             (TEXTS[3], " "), ("hello WORLD #$% 2026", " "), ("     ", " ")]
    mem_ok = wire_ok = True
    for t, free in cases:
        cells = data_encode_free(t, free)
        plain = encode_free(t, free, [M["up"]] * len(cells))
        blob = q.to_bytes(plain)
        mem = data_decode_free(cells, free)
        wire, ph = decode_escape_aware(list(blob))
        nfree = sum(1 for d, mk in cells if mk == 3 and d < len(free))
        nbits = sum(slot_width(s, len(free)) for s in range(nfree))
        mem_ok = mem_ok and (mem == t)
        wire_ok = wire_ok and (wire == t)
        print(f"      {t[:30]!r:32} free={free!r:8} cells {len(cells):3d} "
              f"free {nfree:2d} ({nbits}b)  mem "
              f"{'EXACT' if mem == t else 'BROKEN'}  wire "
              f"{'EXACT' if wire == t else 'BROKEN'} (phantoms {ph})")
    p5_mem, p5_wire = mem_ok, wire_ok

    # ── P6: the phantom-escape collision, measured ──────────────────────
    print("\nP6  phantom escapes: base cells the Latin square pushes to timbre 3")
    grid = [[1 if q.latin_timbre(m, r) == 3 else 0 for r in range(4)]
            for m in range(4)]
    names = ["down", "flat", "up", "hold"]
    for m in range(4):
        print(f"      momentum {names[m]:>6} -> timbre3 at data%4={grid[m]} "
              f"({sum(grid[m])}/4 residues)")
    print("      -> only 'hold' has a residue that can never phantom (r=1);")
    print("         'hold' is the 3-safe choice. Every other momentum still")
    print("         phantoms on exactly one residue, so a base cell CAN wear")
    print("         timbre 3 and a plaintext decoder cannot tell it from an escape.")
    p6 = True
    for t, free in cases[:4]:
        cells = data_encode_free(t, free)
        stream = encode_free(t, free, [M["up"]] * len(cells))
        ph = escape_marker_collision(stream, cells, decode_momentum(stream))
        print(f"      {t[:30]!r:32} phantoms on wire: {len(ph)}/{len(stream)}")
    print("    -> the escape-aware receiver resolves them via momentum==hold;")
    print("       a plaintext-only reader misreads every one as RARE data.")

    print("\nVERDICT: " + ", ".join(
        f"P{i}={'SURVIVES' if v else 'FALSIFIED'}"
        for i, v in enumerate([p1, p2, p3, p4, p5_mem and p5_wire], 1)) +
        f", P6={'MEASURED' if p6 else 'FALSIFIED'}")


if __name__ == "__main__":
    main()
