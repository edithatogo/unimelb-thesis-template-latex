# Verified PDF provenance sidecar

`scripts/provenance_manifest.py` wraps the existing native verifier with
a **new clean, same-run build and source-identity check**. It refuses to reuse
a PDF from another source revision or a dirty checkout. It then generates a
separate optional evidence sidecar from the newly verified output bytes.
The class, native verifier and release workflow remain unchanged.

## Usage

With a complete TeX Live installation, qpdf and Poppler available:

```sh
make test
python3 -m scripts.provenance_manifest
```

The Python command performs a fresh native `verify.verify` build itself after
checking the source revision and an entirely clean Git worktree, then checks
the revision and worktree again. It rejects untracked inputs as well as tracked
changes. It will fail rather than attaching a previously built PDF to a later
checkout.

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
restricted to the literal `build/verification/provenance.json` filename;
parent traversal, symlink redirection, and overwriting verifier inputs are rejected.

The separate `Provenance manifest` GitHub Actions job runs a clean
`make test`, then invokes the source-bound fresh verifier and evidence
generator with the same pinned TeX Live image as the existing CI. The manifest is uploaded as a bounded-run artifact,
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
