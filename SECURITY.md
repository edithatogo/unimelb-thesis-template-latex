# Security

## Reporting a vulnerability

Use this repository's
[private vulnerability reporting form](https://github.com/edithatogo/unimelb-thesis-template-latex/security/advisories/new)
when GitHub offers it. Availability is a repository setting and is not established
merely by this policy file. If the form is unavailable, open a minimal issue
asking the maintainer for a private reporting channel; omit exploit details,
credentials and personal information from that public issue.

For a private report, provide the affected source commit or release, the toolchain,
impact and a minimal synthetic reproduction. Do not upload a private thesis or
real personal data to demonstrate a problem. Security fixes target the current
default branch; consult the release notes before relying on an older release.

## Build and supply-chain boundaries

LaTeX source, package configuration and bibliography inputs can influence build
execution. Only compile trusted source in an isolated environment. Do not enable
LaTeX shell escape or execute untrusted generated code. Treat fonts, packages,
images, bibliography data, reusable workflows and release credentials as
supply-chain inputs.

GitHub Actions must use immutable commit pins and the permissions needed for the
job. PR checks use read-only permissions by default and do not retain checkout
credentials. Security-analysis jobs may receive `security-events: write` solely
to upload their findings, without source-write or release permissions.
Publication credentials belong only in the tag-triggered release job, never in
the source tree or PR environment. Preserve the privacy and secret scans, and
investigate findings without publishing raw sensitive matches.

The standalone CodeQL CI gate analyzes Actions and Python, validates complete
SARIF results and fails on findings. It retains artifacts with read-only
permissions and disables native code-scanning uploads. Preserve the separate
GitHub-managed default setup; see
[CodeQL configuration](docs/repository-controls.md#codeql-configuration).

Validation must fail on compilation errors or invalid PDF output. Keep generated
artifacts separate from source and use `make verify` as documented in
[CONTRIBUTING.md](CONTRIBUTING.md). A successful build does not prove the safety
of arbitrary third-party TeX input or compliance with university policy.

## Maintenance and recovery

Hosted Renovate supplies dependency update PRs through the shared repository
preset. Review unexpected dependency origins and permissions before integration.
Do not suppress a failing security check merely to permit a merge.

The desired default-branch ruleset blocks force-push/deletion and requires stable
automated checks, with no mandatory human approval. Its configuration, owner
recovery path, actual enforcement evidence and outstanding settings gaps are
documented in [repository controls](docs/repository-controls.md). Committing a
ruleset JSON file does not activate it on GitHub.
