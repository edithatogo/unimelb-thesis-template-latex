# Repository controls

## Desired policy and live enforcement

[Issue #8](https://github.com/edithatogo/unimelb-thesis-template-latex/issues/8)
requires automated merge gates that one maintainer can operate.
[The ruleset JSON](../.github/rulesets/solo-maintainer-main.json) defines the desired
configuration. **Committing this file does not activate a GitHub ruleset.**
The [dated drift receipt](evidence/issue-8-2026-11-15.md) records actual settings,
source dependencies, successful check evidence and unresolved blockers.
The [issue #9 integration receipt](evidence/issue-9-integration-2026-11-15.md)
reconciles the later verifier, coverage and CodeQL changes without rewriting that
historical baseline.

| Control | Desired behavior |
| --- | --- |
| Scope | The default branch, using `~DEFAULT_BRANCH` |
| History | Block branch deletion and force pushes |
| Changes | Require a pull request |
| Human approval | Zero approvals; no CODEOWNERS, last-push or team gate |
| Review conversations | Resolve conversations before merging; the solo maintainer may resolve them |
| Automated checks | The six qualified contexts below, bound to GitHub Actions app `15368` |
| Base freshness | Require checks against the latest base |
| Recovery | Only owner `edithatogo` (user ID `15080672`) has a pull-request-only bypass |

Existing merge, squash and rebase methods remain allowed. This does not add a
merge queue or change tag-only publication.

## Check and bot inventory

All six selected contexts passed on the final head of
[PR #15](https://github.com/edithatogo/unimelb-thesis-template-latex/pull/15),
`a7a7fcdbbff10a6b2c2b380cf19f00f9a19b10bf`, before its integration into main.
The original build and privacy contexts also passed on Renovate PR #11, as
recorded in the drift receipt. The four newer contexts run on ordinary PRs
without path filters or repository secrets. None requires human review.

| Exact context | Source | Successful PR evidence |
| --- | --- | --- |
| `compile / build` | GitHub Actions, app `15368` | [LaTeX build](https://github.com/edithatogo/unimelb-thesis-template-latex/actions/runs/43607792819/job/132486100090) |
| `privacy-and-secrets` | GitHub Actions, app `15368` | [Privacy/secret scan](https://github.com/edithatogo/unimelb-thesis-template-latex/actions/runs/43607792822/job/132486099603) |
| `Actionlint` | GitHub Actions, app `15368` | [Workflow lint](https://github.com/edithatogo/unimelb-thesis-template-latex/actions/runs/43607792807/job/132486100080) |
| `Dependency review` | GitHub Actions, app `15368` | [Dependency review](https://github.com/edithatogo/unimelb-thesis-template-latex/actions/runs/43607792784/job/132486098807) |
| `CodeQL CI (actions)` | GitHub Actions, app `15368` | [Actions analysis and findings gate](https://github.com/edithatogo/unimelb-thesis-template-latex/actions/runs/43607792742/job/132486100332) |
| `CodeQL CI (python)` | GitHub Actions, app `15368` | [Python analysis and findings gate](https://github.com/edithatogo/unimelb-thesis-template-latex/actions/runs/43607792742/job/132486100008) |

`LaTeX CI` is a workflow name, not the emitted context. Read check runs for the
current PR head and latest base; an empty legacy status list is not a failed
check, and a queued or cancelled run is not a pass.
The evidence above qualifies the names and their GitHub Actions provenance; it
does not establish that a later PR head passed. Recheck the actual final head
and current base before integration or settings activation. Dependency review
is PR-only, which is compatible with this policy because no merge queue is used.

Renovate is the active update bot. CodeRabbit and the Codex connector have
historical review comments, but neither is a required gate or bypass actor.
The managed `Analyze (actions)`/`CodeQL` results, `Python verifier coverage`,
`Codecov upload` and Codecov service checks are not added to this required-check proposal.
Qualify any additional context on the combined source before requiring it. The
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
required conversation resolution, app-bound checks and strict base freshness.
Review before saving.

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

The original typesetting-only baseline had no executable coverage suite. PR #15
adds a Python verifier, so that exclusion no longer applies to the delivered
tooling. `make coverage` now instruments statements and branches in both Python
helpers under `scripts/`, using
hash-pinned coverage.py, with an 80% branch-aware total floor and an XML artifact.
See [the setup and scope](../CONTRIBUTING.md#verifier-coverage). Measured local and
hosted results belong to the checked commit; the configured threshold is not a
passing result. TeX output quality still needs compilation and PDF inspection.

The coverage workflow configures a separate `Codecov upload` job after the local
coverage gate succeeds. It downloads the same run's XML artifact and sends only
that coverage report using [OIDC authentication](https://github.com/codecov/codecov-action#using-oidc).
Only this job receives `id-token: write`; repository contents remain read-only.
No stored upload token or owner-wide tokenless setting change is required.

Codecov onboarding and successful ingestion remain **pending verification**.
The [Codecov GitHub App needs access to this repository](https://docs.codecov.com/docs/quick-start).
A retained XML or successful upload step alone does not prove report processing:
record the exact commit, workflow run and populated Codecov report before
claiming activation. Do not upload fabricated/empty coverage, add an unverified
badge, or require a service check before its actual context is qualified.

## CodeQL configuration

Keep the already successful GitHub-managed default setup. Its Actions analysis
passed in [run 43604179317](https://github.com/edithatogo/unimelb-thesis-template-latex/actions/runs/43604179317)
on the audited main. PR #15 subsequently merged an additional SHA-pinned
CodeQL CI workflow. Retain it: Actions/Python analyses generate standalone SARIF,
with `upload: never` and `upload-database: false` to avoid competing native
code-scanning uploads. Its zero-findings gate and artifact retention complement
rather than replace GitHub-managed default setup. CI success is not equivalent
to publishing native security alerts.
GitHub [automatically adds supported languages](https://docs.github.com/en/code-security/concepts/code-scanning/setup-types)
when source changes, with fallback if the new configuration fails. Verify a
successful Python analysis after the verifier reaches main; do not infer it from
the earlier Actions-only success or add an unobserved check to the ruleset.

## References

The [UMTHESIS contract](https://github.com/edithatogo/unimelb-thesis-template-typst/issues/13)
and [central typesetting inventory](https://github.com/edithatogo/repository-standards/issues/5)
define the added governance context. Local issue #8 owns settings, context and
provider evidence; [issue #18](https://github.com/edithatogo/unimelb-thesis-template-latex/issues/18)
owns the new semantic/policy adapters. The dated receipt records the executable
helper and published-PDF applicability changes, remaining registry and
supply-chain evidence gaps, and their review boundary. It is not a replacement
for the canonical contract or an assertion that those gaps are complete.

- [GitHub ruleset REST API](https://docs.github.com/en/rest/repos/rules#create-a-repository-ruleset)
- [How rulesets and branch protection combine](https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/managing-rulesets/about-rulesets)
