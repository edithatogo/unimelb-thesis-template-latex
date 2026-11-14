# Issue #9: integration acceptance receipt

Date: **15 November 2026, Australia/Brisbane**. This supplements the historical
[issue #8 receipt](issue-8-2026-11-15.md); it does not replace its observations.

## Sources reconciled

| Existing work | Inspected head | Integration treatment |
| --- | --- | --- |
| [PR #12](https://github.com/edithatogo/unimelb-thesis-template-latex/pull/12) | `9d463b46328d012c18f3a2b1cad44cb86be63cf6` | Reuse privacy reconciliation and the initial validation command. |
| [PR #15](https://github.com/edithatogo/unimelb-thesis-template-latex/pull/15) | `ea890310cd1724b2f6e214430f5cde2ae9bba45f` | Reuse the Python verifier/tests, fresh-build and replay workflow, lint, dependency review and release separation. |
| [PR #16](https://github.com/edithatogo/unimelb-thesis-template-latex/pull/16) | `5eb79fc818496c1c7e0aee7b8b74dd8b29ffda23` | Reuse canonical context, PR template, ruleset and application/read-back procedure. |

The parent integration reconciles command/output documentation, adds real Python
coverage instrumentation, and retains existing CodeQL default setup instead of
a competing advanced workflow. It also corrects the malformed PDF destination
and strengthens rejection of PDF-tool diagnostics and missing rendered content.
The local qualification below covers these changes together; final-head hosted
acceptance remains separate.

## Qualified implementation

The implementation is recorded in commit
[`9288b4245d65c5d333dd4965cd9bcc93c72c45fb`](https://github.com/edithatogo/unimelb-thesis-template-latex/commit/9288b4245d65c5d333dd4965cd9bcc93c72c45fb).
Its Git tree, `12bdeb0455169831287c6b85141e6923d65be0a7`, exactly matches the
locally qualified implementation tree. This receipt is the only subsequent
change before opening the integration PR; hosted results must still be checked
on that PR's current head.

Both `make verify` and `make replay` exited zero. Each command passed all 27
verifier tests. The standalone verification and the two independent replay
builds each produced 20 pages and 12,741 normalized text characters, with SHA-256
`b1916acdb956b3bc451f4b677ce785e1458f1c8390b78c15c58aac7bec5a7f53`.
All 15 compiler/source inputs remained unchanged across qualification. Replay
compares document text and page count, not byte-identical PDFs.

The local toolchain was LuaHBTeX 1.18.0 / TeX Live 2025-dev, latexmk 4.86,
Biber 2.20, makeglossaries 4.56 and qpdf 12.2.0, with
`SOURCE_DATE_EPOCH=1735689600`. These results do not stand in for the hosted
TeX Live 2026 container run. All three builds passed qpdf and strict
`pdfinfo`/`pdftotext` diagnostics checks. The malformed `FitV` opening destination
warning is absent after changing it to `Fit`. All 20 pages were rendered for
visual inspection; the bibliography, glossary, figures, tables, equations,
code listing and appendix were present and readable.

## Acceptance status

| Item | Evidence / status |
| --- | --- |
| Shared commands | `make test`, `make verify`, `make replay`; validated output is `build/verification/Thesis.pdf`. No second harness or build/clean aliases are introduced. |
| Verifier coverage | 27 tests passed; coverage.py 7.17.3 measured 164/197 statements (83.25%) and 54/64 branches (84.38%), with 8 partial branches. The branch-aware total rounds to 84%, above the 80% floor. Real XML was generated at `build/coverage/coverage.xml`; no hosted ingestion is claimed. |
| Full TeX verification and replay | Passed locally against the qualified implementation above: three independent fresh builds, 20 pages each, identical normalized text. Hosted container execution remains pending. |
| Local unit/lint checks | 27 tests passed; actionlint 1.7.12 with ShellCheck 0.10.0 passed. JSON parsing and whitespace checks passed. The published implementation tree matches the qualified local tree. |
| Hosted checks | Pending final-head runs, exact check names, statuses and workflow URLs. Local or earlier component results cannot substitute. |
| CodeQL Actions baseline | Default-setup [run 43604179317](https://github.com/edithatogo/unimelb-thesis-template-latex/actions/runs/43604179317) passed on `d5f50731a038cd555ce04c2e158c3589a033473a`, completed `2026-11-14T14:37:26Z`. |
| CodeQL Python | Pending successful language adoption after the verifier reaches main. [Default setup auto-adds supported languages but can fall back after failure](https://docs.github.com/en/code-security/concepts/code-scanning/setup-types); Actions-only evidence does not prove Python analysis. |
| Codecov service | No external upload or badge configured; local/CI XML evidence does not establish service ingestion. The old no-executable-tests exclusion no longer applies to the Python verifier. |
| Ruleset enforcement | Re-read before publication: rulesets `[]`, `main` unprotected at `d5f50731a038cd555ce04c2e158c3589a033473a`. The connector has no administration write capability, the CLI is unauthenticated, and the browser requires administrator sign-in. The reviewed JSON is ready with owner `User` ID `15080672`, PR-only recovery bypass, two app-bound stable checks and zero human approvals. Application and read-back remain required. |
| Offline security | Draft PR #13 retains its provisioning/validation hold; it is not integrated or made a merge gate. |

Before closure, record final-head hosted results and links; verify Python code
scanning; apply/read back the
ruleset and observe its checks on an ordinary PR. Keep #8 and #9 open while
settings or acceptance remain unverified. See [repository controls](../repository-controls.md)
and [quality checks](../quality-checks.md) for the authoritative procedures.

## Conflict reconciliation after PR #15 merged

`main` advanced to `805d7accbeb953aa121ba1d00d30055e8ff939e3` through
PR #15 while this integration branch remained based on `d5f50731a038cd555ce04c2e158c3589a033473a`.
The merge retains the newer main-only CodeQL workflow, standalone SARIF
validator and its 17 tests, alongside this branch's strict PDF diagnostics,
rendered-content assertions and coverage suite. The CodeQL workflow deliberately
disables native uploading, leaving GitHub-managed default setup unchanged.
These combined changes require fresh exact-head CI; earlier green checks on
separate parents do not establish that integration is green.
