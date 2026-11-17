# UMTHESIS v1 LaTeX canonical metadata consumer (bounded)

This is an initial **source-only LaTeX-side consumer** of the shared
[UMTHESIS 1.0.0 contract](https://github.com/edithatogo/unimelb-thesis-template-typst/issues/13).
The Typst repository owns the canonical schema and five-layer normalization.
This adapter does **not** create a second policy schema and cannot validate
University approvals.

The canonical contract manifest SHA-256 is pinned as
338f93c64ce84621670f267c0919555d77c592e92e75f04e12afd6cab57cea7c.
Only the exact manifest version 1.0.0 and an exact canonical
configuration SHA-256 are accepted. SHA-256 checksums identify bytes; they
do not authenticate the author's statements or establish policy approval.

## Usage

Produce canonical normalized input in a trusted local checkout of the Typst
repository, with the matching contract digest:

    python scripts/thesis_contract.py normalize --metadata synthetic-metadata.json --output normalized.json

Then, in the LaTeX repository:

    python -m scripts.umthesis_contract_consumer --input normalized.json --output /tmp/umthesis-metadata.tex --report /tmp/umthesis-consumer.json
    make test

The generated fragment defines only standard class metadata setters:
title, authors, degree, submission date, school, and optional ORCID. It does
not compile a thesis, translate all scholarly content, insert abstract or
declaration pages, alter the existing public sample, or certify output.
Any unsupported purpose, layout, identity, language, bibliography, PDF
standard or optional metadata field is **refused** rather than dropped.

The output receipt intentionally contains hashes, scope and status only;
raw author metadata and the source path are not included. The output
must remain controlled if it contains actual personal information.

## Closure boundary

The current status is 'source-only-not-rendered'. Conformance to
[LaTeX issue #18](https://github.com/edithatogo/unimelb-thesis-template-latex/issues/18)
requires a separate actual LaTeX rendered-document adapter, shared positive
and negative fixtures, exact engine/source/contract receipt identities,
institutional policy checks and a complete cross-engine parity matrix.
The initial adapter does not satisfy these by itself. Work stays
local-first with no premium service, mandatory reviewer or new CI lane.
