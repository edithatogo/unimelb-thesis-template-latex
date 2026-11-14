# Contributing

Use a focused branch and pull request. Check existing issues and PRs first so
parallel work shares the same build and validation tools. This repository is
maintained by one person; automated checks are the merge gate and no human,
CODEOWNERS or team approval is mandatory.

## Build and validate

Install a full TeX distribution providing `latexmk`, LuaLaTeX, `biber` and
`makeglossaries`, plus Python 3.10 or newer, GNU Make, `qpdf`, and Poppler's
`pdfinfo` and `pdftotext`. Python validation uses only the standard library.
The hosted LaTeX workflow is the reference for its container/toolchain; record
your local versions when they differ. Optional `chktex` and `latexindent` tools
do not replace the build gate.

From the repository root, run:

```sh
make verify
```

This runs the regression tests, compiles the supplied example in a fresh temporary
directory with shell escape disabled, and validates the PDF, final log, extracted
text, bibliography and glossary. See [the verification contract](docs/quality-checks.md)
for the complete failure conditions, finite timeouts and retained evidence.
A missing tool or failed test/build/output check must fail the command.

| Command | Purpose and output |
| --- | --- |
| `make` or `make build` | Authoring build in `example/out/` |
| `make test` | Fast Python regression tests; no TeX installation required |
| `make verify` | Tests and one clean build; PDF/evidence in `build/verification/` |
| `make replay` | Tests and two clean builds; compare normalized text/page count, with additional evidence in `build/replay/` |
| `make clean` | Clean authoring output; retain verification evidence under `build/` |

The verifier expects the supplied example's title and sections. Use `make build`
while writing a thesis with different content. Replay checks one toolchain's
text/page repeatability; it does not establish byte-identical PDFs across platforms.

Open the newly generated `build/verification/Thesis.pdf` and inspect the title,
front matter, contents, headings, representative mathematics/tables, bibliography,
glossary and appendix. Automated checks do not establish visual quality or current
university policy compliance. Document relevant visual limitations. Keep generated
PDFs and auxiliary files out of the PR unless the requested change explicitly
concerns a published example artifact.

## Pull-request evidence

Use the PR template to describe the problem, changed behavior and related issue.
Include the `make verify` result, toolchain, exact checked commit and hosted CI
links. If a command cannot run, state the missing prerequisite and actual exit
status; do not report it as passing. Recheck hosted results after updating the PR
or integrating a new base. Queued, skipped or unrelated successful runs are not
evidence that the current change passed.

Keep source changes separate from opt-in formatting and update documentation
when commands, outputs or requirements change. Python helper coverage is now
applicable because executable tests exist. Any report or coverage badge must use
real test execution; never upload empty or fabricated coverage. TeX line coverage
is not a document-correctness threshold. The service's actual integration status
is recorded in [repository controls](docs/repository-controls.md).

## Dependencies, security and releases

Hosted Renovate inherits `github>edithatogo/renovate-config`; preserve that preset
and justify overrides. Do not introduce a second updater without a deliberate
migration that preserves update coverage. Pin GitHub Actions to full commit SHAs
and keep PR jobs read-only by default. Scope any necessary permission exception
to its job; for example, uploading native security results may need
`security-events: write`. PR jobs must not receive source-write or release rights.
The current CodeQL CI gates retain standalone SARIF artifacts without native
Security-alert uploads; see [the CodeQL setup decision](docs/quality-checks.md#codeql-results-and-repository-setup).

Use public or synthetic examples. Report vulnerabilities through the private
route in [SECURITY.md](SECURITY.md), and omit secrets or private thesis content
from public issues and logs. Releases are explicit maintainer actions triggered
by version tags. See [repository controls](docs/repository-controls.md) for
required checks, settings verification and owner recovery.
