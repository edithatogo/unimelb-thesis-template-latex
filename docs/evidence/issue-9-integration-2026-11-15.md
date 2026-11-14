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
These source changes require validation together on the final commit.

## Acceptance status

| Item | Evidence / status |
| --- | --- |
| Shared commands | `make test`, `make verify`, `make replay`; validated output is `build/verification/Thesis.pdf`. No second harness or build/clean aliases are introduced. |
| Verifier coverage | Local integration run: 27 tests passed; coverage.py 7.17.3 reported 197 statements, 33 missing, 64 branches and 8 partial branches, with 84% branch-aware total coverage against the 80% floor. XML was generated at `build/coverage/coverage.xml`. Recheck and attach this evidence to the final commit; no hosted ingestion is claimed. |
| Full TeX verification and replay | Pending execution and recording against the final combined source and toolchain. |
| Local unit/lint checks | The integration working tree passed 27 tests and actionlint with ShellCheck; JSON parsing and whitespace checks passed. Final commit attribution remains pending. |
| Hosted checks | Pending final-head runs, exact check names, statuses and workflow URLs. Local or earlier component results cannot substitute. |
| CodeQL Actions baseline | Default-setup [run 43604179317](https://github.com/edithatogo/unimelb-thesis-template-latex/actions/runs/43604179317) passed on `d5f50731a038cd555ce04c2e158c3589a033473a`, completed `2026-11-14T14:37:26Z`. |
| CodeQL Python | Pending successful language adoption after the verifier reaches main. [Default setup auto-adds supported languages but can fall back after failure](https://docs.github.com/en/code-security/concepts/code-scanning/setup-types); Actions-only evidence does not prove Python analysis. |
| Codecov service | No external upload or badge configured; local/CI XML evidence does not establish service ingestion. The old no-executable-tests exclusion no longer applies to the Python verifier. |
| Ruleset enforcement | Still unapplied at the audited setting state. Preserve the reviewed owner `User` ID `15080672`, PR-only recovery bypass, two app-bound stable checks and zero human approvals. Authenticated administration and read-back remain required. |
| Offline security | Draft PR #13 retains its provisioning/validation hold; it is not integrated or made a merge gate. |

Before closure, replace pending execution rows with the actual commit, toolchain,
results and hosted links; verify Python code scanning; apply/read back the
ruleset and observe its checks on an ordinary PR. Keep #8 and #9 open while
settings or acceptance remain unverified. See [repository controls](../repository-controls.md)
and [quality checks](../quality-checks.md) for the authoritative procedures.
