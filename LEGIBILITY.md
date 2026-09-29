# Legibility

Added by a read-only audit. Nothing else in this repository was touched.

## What this does NOT do

- There is no CI configuration in this repository, so nothing here is checked
  automatically on push. _(no `.github/workflows/` or equivalent found)_
- It ships no automated tests, so the example command is the only check available.
  _(no test or spec files found)_
- It carries no LICENSE file. _(no LICENSE or COPYING file found)_
- No standard build or test file is present, so there is no canonical command to point a
  reader at. _(no `Makefile`, `justfile`, `package.json`, `pyproject.toml`, `Cargo.toml` or `go.mod` found)_

## What still needs a human

- **The receipt.** Which command produces the output that proves this works? It cannot be
  derived from a file listing, and guessing it is how a completer invents one.
- **Failure modes.** When a call goes wrong, what does a reader do? Also not derivable.
