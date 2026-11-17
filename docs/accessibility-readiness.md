# Tagged PDF package-readiness inventory

This is a **source-level diagnostic**, not an accessible-PDF generator or a
PDF/UA/PDF/A validation result. Run:

```sh
python3 -m unittest discover -s tests -p 'test_tagging_inventory.py' -v
python3 -m scripts.tagging_inventory
```

The program inventories direct `\\usepackage` and `\\RequirePackage`
declarations in `template/Thesis.cls` and the optional
`template/thesis-science.sty`. It strips ordinary TeX comments, supports
package lists/options and fails on ambiguous commands or missing input files.

## Source-dated compatibility observations

Source: [LaTeX tagging project package status](https://latex3.github.io/tagging-project/tagging-status/).
Reviewed **17 November 2026**. This is a **mutable upstream status list**;
individual statuses and exact TeX package versions must be reviewed again
before any tagging migration or conformance claim. Current notable results:

| Package | Upstream classification | Scope |
| --- | --- | --- |
| `caption`, `subcaption` | currently-incompatible | Base class |
| `algorithm2e`, `pgfplots`, `pdfpages` | currently-incompatible | Optional scientific pack |
| `biblatex`, `amsmath`, `tikz`, `tcolorbox` | partially-compatible | Base or optional |
| `glossaries` | unchecked | Base class |
| `fancyhdr`, `longtable` | compatible | Base class |

A direct package not in this curated, source-backed status set is
**unreviewed**, never assumed compatible. Current classified blockers are
recorded in the output, and `pdf_ua_qualified` and
`pdf_a_qualified` are always `false`. Upstream compatibility is not
a substitute for testing the actual class, package versions and PDF.

## Actual accessibility acceptance remains open

1. Qualify an exact LaTeX kernel, font set, renderer and tagging profile.
2. Replace or isolate incompatible packages for that profile; optional
   embedded PDFs, scientific plots and algorithms require separate
   equivalence/alternative-text strategies.
3. Compile representative real synthetic fixtures with tagging enabled.
4. Run independent automated PDF/UA validation (e.g. veraPDF) **against the
   exact final bytes** and inspect reading order, mathematical interpretation,
   figure descriptions, tables, bookmarks and citations with human review.
5. Record failures/unsupported cases and do not release a PDF/UA label until
   all mandatory checks and manual decisions are complete.

This inventory is not a replacement for `make verify` or the
[UMTHESIS shared policy contract](https://github.com/edithatogo/unimelb-thesis-template-typst/issues/13).
Acceptance stays under [LaTeX issue #18](https://github.com/edithatogo/unimelb-thesis-template-latex/issues/18).
