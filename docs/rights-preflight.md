# Publication and public-deposit rights preflight

This implements a **conservative planning stage** for the UMTHESIS v1
`metadata.resources`, `metadata.rights` and publication/creative-resource
references. It is not a rights grant, a declaration form, a PDF-redaction
engine or a replacement for institutional review.

## Execute with synthetic data

```sh
python3 -m unittest discover -s tests -p 'test_rights_projection.py' -v
python3 -m scripts.rights_projection examples/public-rights-synthetic.json
```

The sample is fully synthetic and lists one owned graphic and one excluded
fictional paper. Its output is `status: plan-only`,
`release_authorized: false` and `requires_output_scan: true`; excluded
content is **not automatically removed**. For real use, first validate and
normalize the input against the **canonical, pinned UMTHESIS schema**. The
standalone CLI only performs defensive rights-specific structural checks; it
does not certify that the entire configuration is schema-valid.

## Decision semantics

- Every declared resource needs exactly one rights entry. Unknown, missing or
  duplicate resources/rights, ambiguous paths, and dangling publication
  references fail closed.
- `owned` is an **inclusion candidate**, not final release authorization.
  `excluded` requires an actual output substitution/redaction and final
  artifact verification. `licensed`, even with a `permission_ref`, and
  `permission-required` remain explicit human-review holds.
- A `deposit-public` plan cannot be substituted for an examination/full plan.
  Neither output is authorized by this preflight.
- `scan_text_surfaces` checks synthetic restricted sentinels in four supplied
  decoded text surfaces: PDF body text, metadata, bookmarks and attachments.
  Missing surfaces or a remaining sentinel fail. A successful text check still
  does not establish anything about raster images, hidden objects, associated
  files, PDF tagging, archives, licensed content or visual review.

## Required downstream steps

Rights approvals and signed declaration forms must stay separate from the
document; preserve provenance and independent human decisions. Implement a
real full/public projection in a qualified renderer, inspect the resulting
final PDF **and any archives**, verify page substitutions and accessible
representations, and check extraction from the post-processed final bytes.
Only then can institutional and copyright approvals be considered.

This module shares the v1 field semantics but intentionally creates no new
interchange schema. The canonical contract programme remains
[UMTHESIS #13](https://github.com/edithatogo/unimelb-thesis-template-typst/issues/13),
and LaTeX completion remains tracked in
[issue #18](https://github.com/edithatogo/unimelb-thesis-template-latex/issues/18).
