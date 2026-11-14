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
| Automated checks | The two proven contexts below, bound to GitHub Actions app `15368` |
| Base freshness | Require checks against the latest base |
| Recovery | Only owner `edithatogo` (user ID `15080672`) has a pull-request-only bypass |

Existing merge, squash and rebase methods remain allowed. This does not add a
merge queue or change tag-only publication.

## Check and bot inventory

Both selected contexts passed on main commit
`003a5cc11dfcd1c2763781bc5c535d3640fd987a` and on the final head of
[Renovate PR #11](https://github.com/edithatogo/unimelb-thesis-template-latex/pull/11),
`2609b29b4cfa0690e8d3890ee59b7fa4dd995351`.

| Exact context | Source | Successful PR evidence |
| --- | --- | --- |
| `compile / build` | GitHub Actions, app `15368` | [LaTeX build](https://github.com/edithatogo/unimelb-thesis-template-latex/actions/runs/43531035885/job/132248501501) |
| `privacy-and-secrets` | GitHub Actions, app `15368` | [Privacy/secret scan](https://github.com/edithatogo/unimelb-thesis-template-latex/actions/runs/43531035592/job/132248500644) |

`LaTeX CI` is a workflow name, not the emitted context. Read check runs for the
current PR head and latest base; an empty legacy status list is not a failed
check, and a queued or cancelled run is not a pass.

Renovate is the active update bot. CodeRabbit and the Codex connector have
historical review comments, but neither is a required gate or bypass actor.
New checks need their own successful evidence before becoming required. The
tag-only release and unprovisioned offline-security draft
[PR #13](https://github.com/edithatogo/unimelb-thesis-template-latex/pull/13)
are not merge requirements.

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

Codecov is **not applicable to the inspected typesetting-only baseline**, which
has no instrumented executable test suite. PDF validation does not produce source
line coverage. Do not upload empty/fabricated coverage or require a nonexistent
coverage check. Reassess when executable tooling/tests arrive through
[issue #7](https://github.com/edithatogo/unimelb-thesis-template-latex/issues/7),
[issue #9](https://github.com/edithatogo/unimelb-thesis-template-latex/issues/9)
or other work: identify meaningful coverage that can be collected, or record a
specific evidence-backed exclusion. Do not carry forward the no-tests rationale
without checking the delivered source.

## References

- [GitHub ruleset REST API](https://docs.github.com/en/rest/repos/rules#create-a-repository-ruleset)
- [How rulesets and branch protection combine](https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/managing-rulesets/about-rulesets)
