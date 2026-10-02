#!/usr/bin/env python3
"""
EXAMPLE 7 — THE RARE-CHARSET TAX (the 7th-bit abstain-escape lane)

The 7th-bit extension trades tone for alphabet: a cell whose timbre is
ABSTAIN (3) stops carrying momentum and instead re-indexes its 6 data bits
into the RARE charset (uppercase, symbols). That sounds free — rare
characters are "special" — but the trade has three falsifiable costs:

  P1 (collision). Momentum 'hold' and the escape marker share timbre=3.
     A naive all-up tone can produce spurious escapes on base cells.
     Separation requires a tone grammar, not luck.

  P2 (tone-dead cells). Every rare cell's momentum decodes as pseudorandom
     (depends on data value mod 4). Measured: trajectory distortion vs
     rare density d. Refined prediction: distortion = 0.75 * d (because
     the decoded momentum matches 'up' with prob 1/4 by chance).

  P3 (net byte cost). Rare encoding never costs MORE bytes than base
     encoding (which pays an UPPER token per uppercase letter). Each
     tone slot lost = exactly one saved data token.
"""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))
import qthe_codec as q  # noqa: E402

HOLD = q.MOMENTUM["hold"]


def make_safe_tone_fn(cells):
    """Return tone_fn(alive_idx, total) that never emits timbre 3 on
    tone-alive cells, avoiding spurious escape collisions."""
    alive_pos = [i for i, (_, m) in enumerate(cells) if m == 0]

    def fn(alive_idx, _ntotal):
        data_val = cells[alive_pos[alive_idx]][0]
        for m in (q.MOMENTUM["up"], q.MOMENTUM["flat"], q.MOMENTUM["down"]):
            if q.latin_timbre(m, data_val % 4) != 3:
                return m
        return q.MOMENTUM["hold"]

    return fn


def base_encode_stream(text, tone_fn):
    """Plain 6-bit encode with UPPER tokens."""
    data = q.data_encode(text)
    tone = [tone_fn(i, len(data)) for i in range(len(data))]
    return q.encode(text, tone), len(data)


def rare_encode_stream(text, tone_fn):
    """7-bit encode: rare chars become abstain cells."""
    cells = q.data_encode_full(text)
    alive = [i for i, (_, m) in enumerate(cells) if m == 0]
    stream = []
    tone_i = 0
    for i, (data, mark) in enumerate(cells):
        if mark == 3:
            stream.append((3 << 6) | data)
        else:
            tone = tone_fn(tone_i, len(alive))
            stream.append((q.latin_timbre(tone, data % 4) << 6) | data)
            tone_i += 1
    return stream, cells


def decodable_momentum(stream):
    return [q.latin_decode(b >> 6, (b & 0x3F) % 4) for b in stream]


def hamming(a, b):
    return sum(x != y for x, y in zip(a, b))


def main():
    results = []
    texts = ["I love you", "The GPU costs $2,400",
             "hello world", "RESOLVE NOW: act #7"]

    # ── P1: naive tone collides, safe grammar fixes ──────────────────────
    naive = lambda i, n: q.MOMENTUM["up"]
    p1_collisions = 0
    for t in texts:
        s, _ = rare_encode_stream(t, naive)
        cells_ref = q.data_encode_full(t)
        for b, (_, m) in zip(s, cells_ref):
            if m == 0 and (b >> 6) == 3:
                p1_collisions += 1
    p1_pass = p1_collisions > 0
    print(f"  P1 — naive all-up tone produced {p1_collisions} spurious escapes"
          f" across {len(texts)} texts  [result: collision=real]")

    # Safe-tone roundtrip must pass for all texts
    for t in texts:
        cells = q.data_encode_full(t)
        sf = make_safe_tone_fn(cells)
        s2, _ = rare_encode_stream(t, sf)
        back = q.data_decode_full(
            [(b & 0x3F, 3 if b >> 6 == 3 else 0) for b in s2])
        assert back == t, f"safe-tone roundtrip failed on {t!r}: {back!r}"
    print(f"  P1 — safe-tone grammar: all {len(texts)} texts roundtrip exact")
    results.append(("P1 collision", p1_pass,
                    "escape needs tone grammar"))

    # ── P2: trajectory distortion == 0.75 * density ──────────────────────
    rising = lambda i, n: q.MOMENTUM["up"]
    print("\nP2 — trajectory distortion vs rare density (intended: all-up)")
    print("  text                              density distort 0.75*d   OK?")
    ok2 = True
    for t in ["i love you", "the Cost is 50%", "Half of THIS is Rare",
              "QTHE $ Codec == v2"]:
        stream, cells = rare_encode_stream(t, rising)
        d = sum(1 for _, m in cells if m == 3) / len(cells)
        seen = decodable_momentum(stream)
        intended = [q.MOMENTUM["up"]] * len(cells)
        dist = hamming(seen, intended) / len(cells)
        pred = 0.75 * d
        ok = abs(dist - pred) < 0.1
        ok2 &= ok
        print(f"  {t!r:34} {d:6.3f}  {dist:6.3f}  {pred:6.3f}  {'OK' if ok else 'FAIL'}")
    results.append(("P2 distortion ~ 3/4*density", ok2, "pseudorandom momentum on rare"))

    # ── P3: byte cost comparison ─────────────────────────────────────────
    print("\nP3 — stream length: base vs rare encoding")
    print("  text                              nbase   nrare   saved  slots lost")
    ok3a, ok3b = True, True
    for t in ["i love you", "Hello World", "ALL CAPS SHOUTING",
              "Mixed Case Sentence", "QTHE Codec v2"]:
        s_base, ntok = base_encode_stream(t, lambda i, n: HOLD)
        s_rare, cells = rare_encode_stream(t, lambda i, n: HOLD)
        saved = ntok - len(s_rare)
        tones_lost = sum(1 for _, m in cells if m == 3)
        if len(s_rare) > ntok:
            ok3a = False
        uppers = sum(1 for c in t if c.isupper())
        extras = sum(1 for c in t if c in q.RARE and c not in q.LOW
                     and not c.isupper())
        if tones_lost != uppers + extras:
            ok3b = False
        print(f"  {t!r:28} {ntok:5d}  {len(s_rare):5d}   {saved:5d}   {tones_lost}")
    results.append(("P3a rare never longer than base", ok3a, "byte dominance"))
    results.append(("P3b 1 slot per rare char", ok3b, "exact exchange"))

    # ── Final summary ────────────────────────────────────────────────────
    print("\n== SUMMARY ==")
    for name, val, meaning in results:
        status = "PASS" if val else "FAIL"
        print(f"  {name}: {status}   [{meaning}]")


if __name__ == "__main__":
    main()
