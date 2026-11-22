# UMTHESIS v1 — pinned LaTeX consumer (candidate)

This is an independent, **metadata-only native LaTeX qualification slice** of
[UMTHESIS v1](https://github.com/edithatogo/unimelb-thesis-template-typst/issues/13).
It uses the canonical Python validator and synthetic fixture inventory; it
does not create another metadata schema or claim institutional acceptance.

## Exact upstream inputs

- Canonical repository: `edithatogo/unimelb-thesis-template-typst`
- Checkout commit: `861a644f8d1e8ede866b213d32f70fdefde5bbe4`
- Contract version: `1.0.0`
- `contracts/thesis/v1/manifest.json` SHA-256:
  `338f93c64ce84621670f267c0919555d77c592e92e75f04e12afd6cab57cea7c`
- `contracts/thesis/v1/fixtures.json` SHA-256:
  `af82359a786b2be565e49de594e32a5d2edb3354221dfd5371d5d954b33c5757`
- `scripts/thesis_contract.py` SHA-256:
  `fdb89aa329357bc7a2325fbba791507d9e64784edce3e7fac0c8826fe5a77bb7`

The snapshot calls itself `candidate-schema-api`. Do not silently update
these pins or claim the complete contract is qualified. Updating requires a
reviewed source and fixture semantic diff, new tests and a distinct receipt.

## Run locally

From this repository root, place a clean checkout of the exact upstream commit
in `build/contract-upstream` (the directory is git-ignored) and install that
checkout's pinned `requirements-contract.txt` in a Python environment.
The CI job handles both steps without writing to another repository.

```sh
make test
make contract-check
```

`make contract-check` runs the ordinary unit test suite, validates the exact
checkout/revision/manifest/fixtures/validator identities, executes the
canonical fixture catalogue and independently checks each expected outcome
through the consumer. It then compiles **only** the synthetic
`doctoral-monograph` metadata fixture with LuaLaTeX, shell escape disabled,
and verifies its PDF structure, metadata and actual rendered title-page order.

A previous successful receipt is replaced with a running marker before each
attempt. A failed run writes `status: failed` and must not be reused as
successful evidence. A passing run writes
`build/contract/latex-native-report.json`, recording fixture identities,
actual document hash, source revisions and explicitly unqualified dimensions.

## Qualification boundary

- **Checked:** canonical normalization, unknown-field/date/ORCID/boolean
  negative fixtures, fixture integrity and precedence oracles; one actual
  synthetic PDF metadata rendering, with a document hash and page count.
- **Not checked:** all institutional requirements, accessibility (PDF/UA),
  archival standards (PDF/A), publication bibliography, signed contribution
  forms, permission and redaction rights, research validity, public HTML,
  cross-engine output equivalence or reproducibility across platforms.
- **Purpose:** a reusable cross-engine interface and a limited LaTeX native
  acceptance specimen, not a final thesis or submission checklist.
- **Security:** no third-party module executes until the exact Git revision,
  manifest, fixture manifest and canonical library file pass their pins.
  The canonical library validates all bundle members and their hashes.
  LaTeX executes without shell escape and renders literal text through a
  TeX-escaping boundary. Output paths are constrained under `build/contract`.

The existing `make verify` and `make replay` remain independent and required.
Failure of this optional candidate probe cannot justify relaxing those gates.
Further implementation and policy acceptance are tracked in
[LaTeX issue #18](https://github.com/edithatogo/unimelb-thesis-template-latex/issues/18)
and [canonical schema issue #14](https://github.com/edithatogo/unimelb-thesis-template-typst/issues/14).
