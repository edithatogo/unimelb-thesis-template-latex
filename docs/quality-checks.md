# Testing and CI applicability

This is the issue [#7](https://github.com/edithatogo/unimelb-thesis-template-latex/issues/7)
audit and verification contract. The starting commit was
`d5f50731a038cd555ce04c2e158c3589a033473a`. It contained a TeX template,
three workflows, Renovate configuration, and no executable validation suite or
Makefile. The earlier two-workflow inventory in the issue was outdated.

## Run the checks

Run commands from the repository root. A full TeX Live installation must provide
LuaLaTeX, latexmk, Biber and makeglossaries. Also install Python 3.10 or newer,
GNU Make, qpdf and Poppler (`pdfinfo`, `pdffonts`, `pdftotext`). Python validation uses only
the standard library.

```sh
make test    # Fast verifier regression tests; no TeX installation required
make verify  # Tests, clean thesis compilation, and output validation
make replay  # Tests and two clean builds; compare extracted document text
```

Optional local `make coverage` uses hash-pinned coverage.py 7.17.3 and Python
3.11+; installation is described in [CONTRIBUTING.md](../CONTRIBUTING.md).
The ordinary verifier and test commands retain their Python 3.10+ requirement.

`make verify` compiles the example into a new temporary directory. Neither the
tracked example PDFs nor a previous successful build can satisfy the check.
It fails on a compiler or tool error, PDF-tool diagnostics, missing or empty
required output, invalid PDF structure, zero pages, nonembedded/missing fonts, blank extracted text,
missing required sections or rendered example content,
unresolved references or citations, or incomplete bibliography/glossary
processing. Build and PDF-tool subprocesses have finite timeouts. Non-fatal
typographic warnings remain visible in the retained log; these are not silently
converted into claims of publication-ready layout.

Verification does not run a formatter or modify TeX source. TeX shell escape is
disabled. Biber and makeglossaries run explicitly as ordinary build tools.
Evidence directories must not be symlinks: the verifier rejects unsafe paths
before clearing its own previous output. On POSIX systems, a timeout terminates
the whole compiler process group, not only the latexmk parent.

## Gates and evidence

| Gate | Events | Bound / threshold | Evidence |
| --- | --- | --- | --- |
| `compile / build` | Every PR, main push, merge group, manual; weekly replay | 20-minute job; 300 seconds per compile; 30 seconds per PDF command; zero hard validation failures | Validated PDF and verification logs/JSON, retained 14 days |
| `Actionlint` | Every PR, main push, manual | 5 minutes; zero workflow/ShellCheck errors | Actionlint output in the job log |
| `Python verifier coverage` | PR/main coverage workflow | Statement/branch instrumentation; branch-aware total at least 80% | Actual report and `build/coverage/coverage.xml`; no Codecov upload |
| CodeQL default setup | GitHub-managed eligible pushes/PRs and schedule | GitHub-managed native analysis; independently confirm Python adoption | GitHub code-scanning results for the actual commit |
| CodeQL CI standalone | PR/main push/schedule/manual | Actions and Python, complete SARIF and zero findings; uploads disabled to avoid default-setup conflict | Workflow status and retained SARIF artifacts |
| `Dependency review` | Every PR | 5 minutes; newly introduced known vulnerabilities at low severity or above fail | Dependency review job summary |
| Privacy and secrets | Existing PR/main/merge-group/manual/weekly triggers | Existing 30-minute limit and Gitleaks/Presidio policy | Existing privacy job output; raw findings are not uploaded |
| Release verification | Version tags only | The same verification workflow and thresholds as PRs | The exact verified PDF is downloaded by the publication job |

PRs perform one clean build. The weekly/manual replay path performs two fresh
builds with the same fixed source date and compares normalized extracted text
and page count. It checks repeatability in one toolchain. It does **not**
establish PDF byte identity across platforms, TeX distributions, fonts, or
future tool upgrades.

The verification receipt records the embedded font count, as reported by Poppler. It is a PDF portability check, not PDF/UA or PDF/A conformance testing.

The local evidence directories are `build/verification/` and, for replay,
`build/replay/`. Only the generated example PDF and explicitly selected
verification logs, bibliography/glossary outputs and JSON reports are retained.
Failure evidence is uploaded even when validation fails; a PDF artifact is
uploaded only after successful verification. Evidence belongs to the workflow's
commit and run, not to a permanent release certification.

## Security and update decisions

Workflows default to `contents: read`. Checkouts do not persist credentials.
Security-result upload permission belongs only to the relevant analysis job.
The publication job alone
receives `contents: write`; it does not check out or execute repository source.
Normal pushes cannot publish. PR/main runs cancel obsolete work; releases
serialize by tag without cancelling a publication already in progress.

Repository-defined external actions are pinned to full commit SHAs. The local reusable workflow is
resolved from the caller's commit. The TeX container is pinned to its registry
digest; this avoids the upstream action's mapping of the current year to a
moving `latest` image. qpdf/Poppler are installed from the container's Debian
repositories, so the entire toolchain is not claimed to be hermetic.
Actionlint's release archive is verified against a committed SHA-256 before
execution. Update its version and checksum together after checking the official
release. Review container digest changes with a replay run.

GitHub-managed CodeQL default setup is retained. Its Actions analysis passed in
[run 43604179317](https://github.com/edithatogo/unimelb-thesis-template-latex/actions/runs/43604179317)
on `d5f50731a038cd555ce04c2e158c3589a033473a`. Since that audit,
PR #15 merged a separate SHA-pinned CodeQL CI for Actions and Python into main.
It uses `upload: never`, `upload-database: false`, and a local complete-SARIF,
zero-findings gate, retaining artifacts without attempting a competing native
code-scanning upload. Keep the GitHub-managed default setup unchanged; do not
mistake standalone CI evidence for native GitHub security alerts.
[New supported languages are detected automatically](https://docs.github.com/en/code-security/concepts/code-scanning/setup-types),
but a failed new configuration falls back to the preceding configuration.
Consequently Python scanning needs successful post-integration evidence; the
earlier Actions-only run cannot satisfy that acceptance item.

Renovate already extends `github>edithatogo/renovate-config` and is active:
[PR #11](https://github.com/edithatogo/unimelb-thesis-template-latex/pull/11)
updated the release action and was merged into the audited starting commit.
Retain Renovate instead of introducing a second version-update bot. GitHub
[documents the need to avoid competing dependency-management integrations](https://docs.github.com/en/code-security/reference/supply-chain-security/supported-ecosystems-and-repositories).

Dependency review is warranted because GitHub parses both action and reusable
workflow `uses` entries. Its coverage is limited: GitHub
[documents that Actions alerts depend on semantic versions rather than SHA pins](https://docs.github.com/en/code-security/reference/supply-chain-security/dependency-graph-supported-package-ecosystems).
Immutable pins remain required. TeX Live/CTAN packages, image contents and
transitive action dependencies are not fully represented by this repository's
dependency graph; a passing review is not a comprehensive vulnerability audit.

## Exclusions and ownership

| Technique or setting | Applicability decision |
| --- | --- |
| CodeQL for TeX/Perl | These languages are not supported. Actions and Python are supported; existing default setup has demonstrated Actions analysis, while Python adoption remains to be verified. See the [official language table](https://codeql.github.com/docs/codeql-overview/supported-languages-and-frameworks/). |
| Duplicate Dependabot version-update configuration | Excluded while the existing Renovate integration is active. |
| Property/fuzz, broad mutation, distributed simulation, load and browser suites | No corresponding product runtime, concurrency model, API or browser interface exists. Bounded failure-oriented verifier tests and actual thesis compilation cover the demonstrated risks. Reassess if the repository gains such runtime code. |
| TeX line-coverage percentage | Not a meaningful correctness threshold for document output. The Python verifier has real statement/branch coverage through `make coverage`; its 80% floor is a configured gate, not an asserted result. External Codecov onboarding/upload is unconfigured and is not implied by the XML artifact. |
| Pixel-perfect or byte-identical PDF snapshots | Font, TeX and PDF metadata differences make them unsuitable as an unqualified cross-platform gate. Inspect the retained PDF when changing layout; replay compares extracted text in one toolchain. |
| Required human approvals, CODEOWNERS or team gates | Prohibited by this repository's solo-maintainer instructions. Automated checks provide the proposed gate names. |
| Repository rulesets, bot permissions, context/PR templates | Owned by [#8](https://github.com/edithatogo/unimelb-thesis-template-latex/issues/8). This issue supplies stable automated check names and a real `make verify` command without changing settings. |
| Offline security infrastructure | Draft [PR #13](https://github.com/edithatogo/unimelb-thesis-template-latex/pull/13) remains subject to its own provisioning and validation hold. No runners, credentials or model services are provisioned here. |
| Umbrella closure | [#9](https://github.com/edithatogo/unimelb-thesis-template-latex/issues/9) also depends on #8 and must not be closed solely on this work. |

The example's missing bibliography registration, broken table reference and
unbuilt glossary were concrete defects exposed by the stricter output contract.
They are fixed with the check, rather than exempted from it.
