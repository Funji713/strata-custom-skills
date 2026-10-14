# Change log

## 2.0.0 - 2026-10-04

Proposed skill revision, not a published GitHub release. Execution protocol 1.0.0
is versioned separately. Original skill names and explicit invocation are preserved.

- Separate planning/review authority, investigation lane and R0/R1/R2 risk.
- Add versioned bidirectional handoff, missing-companion fallback and scope gates.
- Add pre-fix baseline, controlled experiments and final diff/verification checks.
- Bind evidence to relevant spec/worktree identity; invalidate impacted dependencies.
- Distinguish accepted decisions, implementation and current verified acceptance.
- Reconcile current state on resume; reuse artifacts and avoid arbitrary slice counts.
- Add offline package/receipt/state lint, negative regression tests and ten behavioral
  scenario specifications per skill. Static passing is not proof of model compliance.
- Update installation guidance and add commit-pinned, read-only CI.

## Migration

Update companion checkouts together for protocol 1.0.0. Settled standalone work can
use one skill. Reuse existing artifact paths and history. Normalize legacy status
`in progress` to `in_progress` only when touching that record. Old `verified` requires
current evidence review; do not silently rewrite or approve historical records.
No automated migration, installation, remote write or model call occurs in validators.
Behavioral scenarios remain `not_run` until real reviewed trials are performed.
