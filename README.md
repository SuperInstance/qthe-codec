# qthe-codec — the tone layer: encoder · compiler · embedder · transformer

A proof-of-concept for the **zero-bit-cost, context-keyed tone channel** proven
in `quilt-gpu-lab` D14. QTHE's byte is 6 bits of data + 2 bits of timbre; the
two timbre bits are already paid for by the byte, so a ternary "tone" signal
rides in them for free — invisible to plaintext readers and to context-free
readers, recoverable only by a contextual (Latin-square) decoder.

This repo is the **documentation with working examples** for that channel,
organized as four stages — **all four now have a working reference module**:

| stage | module | status |
|---|---|---|
| encoder | `qthe_codec.py` | ✅ roundtrip green, 7-bit extension |
| compiler | `qthe_compiler.py` | ✅ pack+RLE+checksum, corruption-detecting |
| embedder | `qthe_embedder.py` | ✅ tone→vector, deterministic, separable |
| transformer | `qthe_transformer.py` | ✅ condense/spatialize/project |

*(the four stages were:)*

1. **encoder** — map human tone (sarcasm, joy, anger, doubt, …) + text → a
   stream of QTHE bytes (6-bit data + 2-bit timbre).
2. **compiler** — turn the byte stream into a compact, verifiable form
   (the codec: pack, run-length, checksum), and the reverse (decompile).
3. **embedder** — a vector reading of the tone stream that downstream
   models/games can consume (the "embedding" side of the channel).
4. **transformer** — reshape the stream: condense a page to a paragraph to a
   sentence to a word, spatialize it to stereo, or project it into a story
   space — all while the tone carries what the words shed.

## The primitive (from D14)
- Byte = `(timbre << 6) | data`. Timbre ∈ {Ground 0, Attract +1, Repel −1,
  Abstain i}. Data = 6-bit token.
- Tone is a **trajectory** (up / flat / down / abstain) over the token stream,
  and its meaning is **contextual** — the same 2 bits mean "up" in one context
  and "down" in another.
- **Latin-square encoding** is what makes it information-clean: each row a
  bijection, each column covering all timbres → I(M;T)=0 without context,
  2 bits with it.

## Working examples
Each example in `examples/` is deliberately **as different as possible** from
the others, and each includes a runnable script plus a prose explanation of
**exactly how it works** (not just what it does). See `examples/README.md`.

*(Built by the erised fleet, priced by experiment, not by LARP.)*
