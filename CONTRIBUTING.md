# Contributing

Use a focused branch and pull request. Check existing issues and PRs first so
parallel work can share the same build and validation tools. This repository is
maintained by one person; automated checks are the merge gate and no human,
CODEOWNERS or team approval is mandatory.
Resolve review conversations before merging; the maintainer can do so without
an approving review or a second reviewer.

## Build and validate

Install Python 3.10 or newer, GNU Make, a full TeX distribution providing
`latexmk`, LuaLaTeX, `biber` and `makeglossaries`, plus `qpdf` and Poppler's
`pdfinfo` and `pdftotext`. The hosted LaTeX workflow pins its TeX container by
digest; record your local toolchain when it differs. Optional `chktex` and
`latexindent` tools do not replace the build gate.

From the repository root, run:

```sh
make test    # Verifier regression tests; no TeX installation required
make verify  # Tests, fresh compilation, and output validation
make replay  # Tests and two fresh builds; compare text and page count
```

Verification builds in a fresh temporary directory with shell escape disabled.
It retains the validated PDF, selected logs and JSON report in
`build/verification/`; replay also retains evidence in `build/replay/`.
Compilation errors, PDF-tool diagnostics, missing sections, unresolved references
and incomplete bibliography/glossary output fail the command. Temporary build
files are cleaned automatically. Keep generated PDFs and auxiliary files out of
the PR unless the requested change explicitly concerns a published example.

Open `build/verification/Thesis.pdf` and check the title and front matter, contents,
chapter headings, representative mathematics/tables, bibliography and appendix.
Automated PDF checks do not establish visual quality or current university
policy compliance. Document any relevant visual limitation.

## Verifier coverage

Coverage is an optional local tooling step and a CI gate for the Python helpers
in `scripts/`, including the build verifier and CodeQL results gate.
Using Python 3.11 or newer, install the hash-pinned development dependency in a
virtual environment:

```sh
python3 -m venv .venv
. .venv/bin/activate
python -m pip install --require-hashes -r requirements-dev.txt
make coverage
```

This runs the tests under coverage.py 7.17.3, measures statements and branches,
requires at least 80% branch-aware total coverage, and writes
`build/coverage/coverage.xml`. This local command does not measure TeX output
correctness or upload to Codecov. Report the actual result; no percentage is implied by the
configured floor. See [quality checks](docs/quality-checks.md) for the gates.

CI retains this XML and configures a separate `Codecov upload` job to send the
same run's artifact using OIDC, without a stored upload token. Service onboarding
and processing of the exact commit's report must be verified before claiming
successful integration; see [repository controls](docs/repository-controls.md#dependency-updates-and-coverage).

## Pull-request evidence

Use the PR template to describe the problem, changed behavior and related issue.
Include the `make verify` result, toolchain, exact checked commit and hosted CI
links. If a command cannot run, state the missing prerequisite and the actual
exit status; do not report it as passing. Recheck hosted results after updating
the PR or integrating a new base. A queued, skipped or unrelated successful run
is not evidence that the current change passed.

Keep source changes separate from opt-in formatting. Update documentation when
build commands, outputs or requirements change. Use real verifier coverage
reports; do not add an external-service badge or claim successful Codecov upload
without verifying that integration. See
[repository controls](docs/repository-controls.md) for its current status.

## Dependencies, security and releases

Hosted Renovate inherits `github>edithatogo/renovate-config`; preserve that preset
and justify any repository-specific overrides. Do not introduce a second update
bot without a deliberate migration that preserves update coverage. Pin GitHub
Actions to full commit SHAs and keep PR jobs read-only by default. A job that
uploads security results may receive the narrowly scoped `security-events: write`
permission; that is not permission to modify source or publish a release.
The standalone CodeQL CI workflow keeps native uploads disabled and retains
SARIF artifacts with read-only permissions. Preserve GitHub-managed default
setup separately; see [CodeQL configuration](docs/repository-controls.md#codeql-configuration).

Use public or synthetic examples. Report security vulnerabilities using the
private route described in [SECURITY.md](SECURITY.md), and never include secrets
or sensitive thesis content in public issues or build logs.

Releases are an explicit maintainer action triggered by a version tag. Ordinary
branch pushes and PRs validate the template without publishing it. See
[repository controls](docs/repository-controls.md) for required checks, settings
verification and owner recovery.
