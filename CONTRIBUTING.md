# Contributing

Use a focused branch and pull request. Check existing issues and PRs first so
parallel work can share the same build and validation tools. This repository is
maintained by one person; automated checks are the merge gate and no human,
CODEOWNERS or team approval is mandatory.

## Build and validate

Install a full TeX distribution providing `latexmk`, LuaLaTeX and `biber`, plus
GNU Make, `qpdf`, and Poppler's `pdfinfo` and `pdftotext`. The hosted LaTeX workflow
is the reference for its TeX Live version; record your local version when it
differs. Optional `chktex` and `latexindent` tools do not replace the build gate.

From the repository root, run:

```sh
make verify
```

The command forces a new LuaLaTeX build with shell escape disabled and validates
`example/out/Thesis.pdf`: a nonempty file, structural validity, readable metadata,
and nonblank extracted text. A compilation error, missing tool or failed PDF
check must produce a failing exit status. Use `make build` for compilation alone
and `make clean` to remove generated build files. Keep generated PDFs and
auxiliary files out of the PR unless the requested change explicitly concerns
a published example artifact.

Open the newly generated PDF and check the title and front matter, contents,
chapter headings, representative mathematics/tables, bibliography and appendix.
Automated PDF checks do not establish visual quality or current university
policy compliance. Document any relevant visual limitation.

## Pull-request evidence

Use the PR template to describe the problem, changed behavior and related issue.
Include the `make verify` result, toolchain, exact checked commit and hosted CI
links. If a command cannot run, state the missing prerequisite and the actual
exit status; do not report it as passing. Recheck hosted results after updating
the PR or integrating a new base. A queued, skipped or unrelated successful run
is not evidence that the current change passed.

Keep source changes separate from opt-in formatting. Update documentation when
build commands, outputs or requirements change. Do not add coverage badges or
upload empty coverage for this typesetting template. Reassess coverage if an
executable test suite is introduced, as described in
[repository controls](docs/repository-controls.md).

## Dependencies, security and releases

Hosted Renovate inherits `github>edithatogo/renovate-config`; preserve that preset
and justify any repository-specific overrides. Do not introduce a second update
bot without a deliberate migration that preserves update coverage. Pin GitHub
Actions to full commit SHAs and keep PR jobs read-only by default. A job that
uploads security results may receive the narrowly scoped `security-events: write`
permission; that is not permission to modify source or publish a release.

Use public or synthetic examples. Report security vulnerabilities using the
private route described in [SECURITY.md](SECURITY.md), and never include secrets
or sensitive thesis content in public issues or build logs.

Releases are an explicit maintainer action triggered by a version tag. Ordinary
branch pushes and PRs validate the template without publishing it. See
[repository controls](docs/repository-controls.md) for required checks, settings
verification and owner recovery.
