# Agent instructions

This is a solo-maintainer LaTeX thesis template. This file is the canonical
instruction entry point for every coding assistant; tool-specific files must
link here rather than maintain conflicting instructions or stale task state.

## Scope and coordination

- `template/` contains the class and supporting styles; `example/` contains the
  example thesis; `.latexmkrc` and `Makefile` define the local build.
- Check the current default branch, open PRs and the working tree before editing.
  Preserve uncommitted work and use an isolated branch when another task is active.
- Keep changes focused on the requested issue. Reuse an existing implementation
  instead of adding a second validation command or competing dependency bot.
- Source examples must be public or synthetic. Do not commit personal thesis
  content, credentials or private records. Keep generated build output untracked
  unless the requested change explicitly updates a published example artifact.

## Validation and evidence

Run `make verify` **from the repository root** before proposing a change. It
runs the verifier tests, builds `example/Thesis.tex` in a fresh temporary directory
using LuaLaTeX with shell escape disabled, and validates the PDF and reference
material. The retained PDF is `build/verification/Thesis.pdf`. Use `make test`
for the fast suite and `make replay` for two clean builds. The required tools,
optional `make coverage` setup, and PDF inspection checklist are in
[CONTRIBUTING.md](CONTRIBUTING.md).

Compilation and PDF validation must fail closed. Do not ignore a failed command,
replace a missing tool with a successful no-op, or reuse a tracked demonstration
PDF as proof of a new build. Record the command, exit status, toolchain and exact
commit checked; distinguish a blocked local run from successful hosted evidence.
Formatting is opt-in and must not silently rewrite source during verification.

## Security and integration

- Keep CI read-only by default, actions pinned to full commit SHAs and checkout
  credentials unpersisted. Scope any necessary exception to its job, such as
  `security-events: write` for CodeQL results; PR jobs must not gain source-write
  or release permissions. Never enable LaTeX shell escape.
- Keep publication tag-only. An ordinary push or PR must never publish a release.
- Retain zero mandatory human approvals: no required reviewers, CODEOWNERS
  approval, last-push approval, or team gate. Review bots remain optional.
- Merge through a PR after inspecting checks on its current head and current base.
  Do not bypass a failing check as a routine way to merge.
- Follow [SECURITY.md](SECURITY.md) for vulnerability reporting and sensitive data.
- Follow [repository controls](docs/repository-controls.md) for the intended
  ruleset, stable check names, bot inventory and owner recovery. A committed
  ruleset file is a proposal until GitHub settings are applied and read back.
- Preserve the existing GitHub-managed CodeQL default setup. Do not add a
  competing advanced workflow; verify Python analysis after the verifier reaches
  main. Coverage applies to the Python verifier, not TeX source; a local XML report
  does not establish Codecov service integration.
- Update a dated drift receipt when settings or gate names change. Preserve
  unresolved blockers explicitly; do not close an issue on configuration intent
  alone. Offline security drafts remain unmerged until their stated provisioning
  and integration conditions are satisfied.
