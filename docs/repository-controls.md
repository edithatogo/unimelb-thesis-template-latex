# Repository controls

## Desired policy and live enforcement

[Issue #8](https://github.com/edithatogo/unimelb-thesis-template-latex/issues/8)
requires automated merge gates that one maintainer can operate.
[The ruleset JSON](../.github/rulesets/solo-maintainer-main.json) defines the desired
configuration. **Committing this file does not activate a GitHub ruleset.**
The [dated drift receipt](evidence/issue-8-2026-11-15.md) records actual settings,
source dependencies, successful check evidence and unresolved blockers.

| Control | Desired behavior |
| --- | --- |
| Scope | The default branch, using `~DEFAULT_BRANCH` |
| History | Block branch deletion and force pushes |
| Changes | Require a pull request |
| Human approval | Zero approvals; no CODEOWNERS, last-push, team or review-thread gate |
| Automated checks | The six qualified contexts below, bound to GitHub Actions app `15368` |
| Base freshness | Require checks against the latest base |
| Recovery | Only owner `edithatogo` (user ID `15080672`) has a pull-request-only bypass |

Existing merge, squash and rebase methods remain allowed. This does not add a
merge queue or change tag-only publication.

## Check and bot inventory

The original build/privacy contexts passed on main `003a5cc11dfcd1c2763781bc5c535d3640fd987a`
and Renovate PR #11 head `2609b29b4cfa0690e8d3890ee59b7fa4dd995351`.
[PR #15](https://github.com/edithatogo/unimelb-thesis-template-latex/pull/15) then
qualified the current six repository-owned gates on final head
`a7a7fcdbbff10a6b2c2b380cf19f00f9a19b10bf`, merged as
`805d7accbeb953aa121ba1d00d30055e8ff939e3`.

| Exact required context | Source | Observed evidence |
| --- | --- | --- |
| `compile / build` | GitHub Actions, app `15368` | [Successful job](https://github.com/edithatogo/unimelb-thesis-template-latex/actions/runs/43607792819/job/132486100090) |
| `privacy-and-secrets` | GitHub Actions, app `15368` | [Successful job](https://github.com/edithatogo/unimelb-thesis-template-latex/actions/runs/43607792822/job/132486099603) |
| `Actionlint` | GitHub Actions, app `15368` | [Successful job](https://github.com/edithatogo/unimelb-thesis-template-latex/actions/runs/43607792807/job/132486100080) |
| `Dependency review` | GitHub Actions, app `15368` | [Successful job](https://github.com/edithatogo/unimelb-thesis-template-latex/actions/runs/43607792784/job/132486098807) |
| `CodeQL CI (actions)` | GitHub Actions, app `15368` | [Successful job](https://github.com/edithatogo/unimelb-thesis-template-latex/actions/runs/43607792742/job/132486100332) |
| `CodeQL CI (python)` | GitHub Actions, app `15368` | [Successful job](https://github.com/edithatogo/unimelb-thesis-template-latex/actions/runs/43607792742/job/132486100008) |

`LaTeX CI` is a workflow name, not the emitted context. Read check runs for the
current PR head and latest base; an empty legacy status list is not a failed
check, and queued/cancelled runs are not passes. Verify all six on the final
head before applying the proposal. Their events and failure thresholds are
specified in [the verification contract](quality-checks.md).

Renovate is the active updater. CodeRabbit and the Codex connector have optional
historical reviews and no bypass. The separate GitHub-managed `Analyze (actions)`
and `CodeQL` checks are not required here: the repository-owned CodeQL CI contexts
have explicit stable names and fail on findings/incomplete SARIF. The managed
native-alert configuration still needs owner inspection; standalone CI artifacts
do not prove native Python alerts are enabled. Preserve existing Default setup
until that decision is made, as described in the verification contract.

The tag-only release and unprovisioned offline-security draft
[PR #13](https://github.com/edithatogo/unimelb-thesis-template-latex/pull/13)
are not merge requirements. Do not add a coverage-service gate before actual
service operation is verified.

## Apply and verify the ruleset

Use the owner's authorized GitHub session. The REST operation requires repository
**Administration: write**; account ownership does not grant that permission to
an integration. Do not commit credentials or extend unrelated app permissions.

From the repository root, use an authenticated GitHub CLI to inspect all rules:

```sh
gh auth status
gh api --paginate repos/edithatogo/unimelb-thesis-template-latex/rulesets \
  --jq '.[] | {id, name, enforcement, source, source_type}'
```

Look for `solo-maintainer-main` and inspect other applicable rules. Rules are
cumulative. Stop and reconcile duplicate names; read an existing rule before
changing it. If the named rule is absent, create it:

```sh
gh api --method POST repos/edithatogo/unimelb-thesis-template-latex/rulesets \
  --input .github/rulesets/solo-maintainer-main.json
```

If it exists and the reviewed differences are intended, update that exact ID.
Replace `RULESET_ID` with the returned ID; never overwrite unrelated rules:

```sh
gh api repos/edithatogo/unimelb-thesis-template-latex/rulesets/RULESET_ID
gh api --method PUT repos/edithatogo/unimelb-thesis-template-latex/rulesets/RULESET_ID \
  --input .github/rulesets/solo-maintainer-main.json
```

The UI alternative is **Settings → Rules → Rulesets**. Match the JSON, including
active enforcement, default-branch scope, owner-only PR bypass, zero approvals,
app-bound checks and strict base freshness. Review before saving.

After either path, read back the saved rule and effective branch rules:

```sh
gh api repos/edithatogo/unimelb-thesis-template-latex/rulesets/RULESET_ID
gh api --paginate repos/edithatogo/unimelb-thesis-template-latex/rules/branches/main
gh api repos/edithatogo/unimelb-thesis-template-latex/branches/main \
  --jq '{name, head: .commit.sha, protected}'
```

Verify every field against the JSON and inspect any classic branch protection:
a ruleset does not remove an existing approval requirement. Do not test by
force-pushing or deleting main. Observe an ordinary PR to verify that the
required checks are present and enforced.

Record the inspected SHA, ruleset ID/read-back, effective rules, exact check-run
heads/links, bots, applicability decisions and unresolved blockers in a dated
drift receipt. A proposal, successful API write and verified enforcement are
different states. Repeat this comparison after settings changes, check renames
or bot migrations. Close the settings acceptance item only after read-back.

## Owner recovery

Normal merges must pass their checks. The owner-only PR bypass is for exceptional
repair of a broken gate, not accepting an ordinary build or security failure.
Record the broken gate, repair, exact commit and follow-up checks in the PR.

The bypass does not allow direct force pushes or deletion. The owner retains
administrative ability to repair the ruleset itself. Document any temporary
change, restore intended controls and read them back. Bots have no bypass.

## Dependency updates and coverage

Hosted Renovate access is demonstrated by
[Dependency Dashboard #10](https://github.com/edithatogo/unimelb-thesis-template-latex/issues/10)
and merged PR #11. `renovate.json` inherits `github>edithatogo/renovate-config` and
enables the dashboard. No Dependabot config existed at the audited baseline.
Verify actual replacement updates before removing an existing update service.

The starting typesetting-only tree had no executable tests, so Codecov was then
not applicable. **That baseline exclusion no longer applies:** PR #15 added 40
Python regression tests for `scripts/verify.py` and `scripts/check_codeql.py`.
Python helper coverage is meaningful and measurable; TeX line coverage remains
unsuitable as a document-correctness threshold.

Coverage collection and Codecov onboarding must be recorded separately. [PR #17](https://github.com/edithatogo/unimelb-thesis-template-latex/pull/17), the
#9 integration work, is coordinating coverage; this change does not claim that
an upload or the service is operational. Until an actual report/upload is verified,
mark service integration pending, upload no empty/fabricated coverage and require
no nonexistent Codecov check. Reconcile the current coverage work before closing
#8 or umbrella #9.

## References

- [GitHub ruleset REST API](https://docs.github.com/en/rest/repos/rules#create-a-repository-ruleset)
- [How rulesets and branch protection combine](https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/managing-rulesets/about-rulesets)
