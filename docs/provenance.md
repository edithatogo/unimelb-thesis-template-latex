# Verified PDF provenance sidecar

The existing `make verify` generates `build/verification/Thesis.pdf` and its
verification receipt. `scripts/provenance_manifest.py` adds a **separate,
optional evidence sidecar** from those final retained bytes. It does not alter
the existing verifier, class, release workflow, or required dependencies.

## Usage

With a complete TeX Live installation, qpdf and Poppler available:

```sh
make verify
python3 -m scripts.provenance_manifest
```

Successful execution writes `build/verification/provenance.json`. Its
`status: evidence-only` is intentionally **not** a claim of reproducible
builds, institutional acceptance, PDF/A, PDF/UA, manuscript validity or rights
clearance. It records:

- The source Git revision, tracked-dirty boolean and SHA-256 identities for
  the class, main synthetic example, bibliography, build configuration and
  current verifier and semantic helper
- The actual retained PDF SHA-256, byte count, page count, and normalized
  extracted-text digest from the **successful same-run** verification receipt
- The observed Poppler font inventory checksum and its agreement with the
  verifier's embedded-font count
- The first reported version line of LuaLaTeX, latexmk, Biber,
  makeglossaries, qpdf, pdfinfo, pdffonts and pdftotext
- The source-date epoch recorded by the existing verifier

A failing/missing receipt, changed PDF bytes, unsafe source symlink,
mismatching font count, invalid source epoch or missing tool version blocks
creation of a success sidecar. The CLI overwrites a prior success sidecar
with a failure marker if current validation fails. Its output path is
restricted to a direct child of `build/verification`; parent traversal and
symlink redirection are rejected.

The separate `Provenance manifest` GitHub Actions job runs a clean
`make verify` then collects this evidence with the same pinned TeX Live
image as the existing CI. The manifest is uploaded as a bounded-run artifact,
not published automatically or included in tags without a deliberate release
qualification.

## Limits

The digest proves identity of observed bytes, not that a scientific result,
PDF structure, human approval or rights claim is true. Font inventory checksum
does not include actual font-file bytes. This records the current Git revision
and tracked dirty status, not an independently clean rebuild on multiple
machines. The existing `make replay` measures normalized text and page count
in one environment and separately reports PDF byte equality. Independent
cross-platform and cross-engine reproducibility remain unqualified.

See [rendered semantic verification](rendered-semantics.md) and
[UMTHESIS requirements #18](https://github.com/edithatogo/unimelb-thesis-template-latex/issues/18).
