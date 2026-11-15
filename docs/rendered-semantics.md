# Rendered document checks

The existing `make verify` command now checks the generated example's PDF
metadata and physical page order, in addition to its existing citation,
glossary, font, structural and text checks. `make test` exercises positive and
negative synthetic extraction cases without requiring TeX.

## What is checked

The PDF title and author must match the example's expected plain-text values.
The first physical page must contain the title, author, degree, submission date,
department and school in that order. The abstract and declaration must retain
the title and author after the title page has been produced. The bibliography
must precede the appendix and contain real example content: a contents-page
entry or an empty heading cannot substitute for those rendered sections.

`template/Thesis.cls` exposes `\thesistitle` for use after `\maketitle`.
The example declaration uses this public command rather than the internal
`\@title` token. Existing author metadata commands remain unchanged.

The expected values in `scripts/verify.py::EXAMPLE_METADATA` describe the
synthetic worked example. Update those assertions deliberately when adapting
the example. They are not a new metadata interchange schema. Shared contract
and adapter qualification remain in [issue #18](https://github.com/edithatogo/unimelb-thesis-template-latex/issues/18)
and the linked canonical contract workstream.

## Evidence

Successful `build/verification/report.json` records `document_semantics` with
one-based physical page positions, plus `pdf_sha256` and `pdf_bytes` for the
validated PDF. A digest identifies bytes; it does not prove authorship,
scientific validity, accessibility or institutional approval.

`make replay` still requires equal normalized text and page count from two
fresh builds in the same environment. Its `replay.pdf_bytes_equal` field reports
byte equality separately. A false value does not fail this explicitly semantic
replay gate; it must not be described as byte reproducibility. No cross-platform
or cross-engine byte-equality claim is made. Failed verification remains failed
and cannot be replaced by an older committed example PDF.

## Policy relationship and limits

The document-order and title-page-order changes follow sections 3.8 and 3.9 of
[Preparation of graduate research theses](https://gradresearch.unimelb.edu.au/processes/preparation-of-graduate-research-theses),
reviewed on 15 November 2026 (page authorisation date: 17 June 2026).

These are selected checks, not the complete institutional requirements. The
worked example is explicitly a synthetic draft: its empty ORCID is not a valid
submission record, its declarations require author completion, and its abstract
is not an institutional word-count specimen. Required funding statements,
publication permissions, approval decisions, complete front-matter sequencing,
PDF/UA/PDF/A qualification and the central versioned schemas remain separate
work. The selected-page checks are specific to this example and its known
headings/content, not a general PDF understanding or accessibility validator.
