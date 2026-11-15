# Rendered-semantics implementation receipt — 15 November 2026

## Baseline and scope

The implementation extends the repaired font verifier from PR #22. Its source
and test blobs were checked against receiving main
`fd44d35ef5543261ca3068fb8c65e655cabd5c4d`; concurrent governance documentation
changes were retained. Issue #18 remains open for the wider contract programme.

This slice fixes title persistence, title-page date order, the declaration's
public title reference and bibliography/appendix order. It adds physical-page
observations and native PDF checksums to the existing verifier, without a new
CI lane, dependency, metadata schema or weakened gate.

## Executed local evidence

- The original PR #22 verifier module reproduced two errors and one failure
  because the build/replay fake returned no font inventory. The two-line fixture
  repair passed all 29 existing verifier tests and subsequently passed all seven
  hosted workflows before PR #22 was merged.
- New semantic checks were written before integration. The old verifier accepted
  incorrect title-page order and did not return semantic observations. The new
  gate rejects the incorrect ordering and records physical page positions.
- A real LuaLaTeX regression specimen reproduced the missing abstract title.
  The full example also reproduced a declaration reading the literal word
  `title` instead of the configured title. Both were corrected and rendered.
- Final `make test`: **74 tests passed** on Python 3.13.5. Branch-aware coverage
  with coverage.py 7.13.3: **89% overall**, **100%** for the new semantic helper.
- The full worked example compiled using LuaHBTeX 1.18, TeX Live 2025/dev/Debian,
  with shell escape disabled. Poppler extraction and the semantic checker placed
  the title, abstract and declaration on physical pages 1, 2 and 3; bibliography
  on page 18; appendix on page 19. The final log passed the existing hard-error
  checks and Poppler reported 18 embedded fonts.
- Local `make verify` correctly remained **blocked** at its required `qpdf`
  command, which is unavailable in this environment. No tool was stubbed or
  skipped to produce a passing full-build report. The full hosted pipeline is a
  separate final-head qualification requirement.
- One diagnostic RED run also hit the existing one-second subprocess-startup
  timing assertion. The subsequent changed-code full suite and instrumented
  full suite passed without modifying or skipping that test.

## Qualification boundary

The local toolchain is not the pinned hosted TeX Live 2026 environment. Local
rendering is supporting evidence, not a substitute for hosted structural,
security, coverage and compilation gates. Inspect the exact PR head and its
current base before merging. This receipt does not close institutional,
accessibility, rights, cross-engine or cross-platform reproducibility acceptance.
