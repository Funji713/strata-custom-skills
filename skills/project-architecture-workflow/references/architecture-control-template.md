# Architecture Control Template

[Execution Protocol](execution-protocol.md), version 1.0.0, defines authority,
state/evidence and handoff semantics. Reuse equivalent existing artifact locations;
these filenames are defaults, not a reason to duplicate records. Create/extend only
when authorized. Remove sections unrelated to the critical flow.

## Architecture specification

```markdown
# Architecture: <project or feature>

## Control
- State: draft | approved | superseded
- Scope: <governed work>
- Spec revision: <revision or relevant-content digest>
- Updated: <timestamp>
- Work mode: plan | review | implement | debug
- Decision authority: <actual user request/delegated scope and source>
- Approval: <pending or actual actor/source/scope; never assumed>
- Status artifact: <existing path; default IMPLEMENTATION_STATUS.md>
- Observed baseline: <relevant code snapshot, not a correctness claim>

## Outcome
- User outcome: <observable result>
- Acceptance IDs: <AC1: measurable condition; AC2: measurable condition>
- Non-goals: <explicit exclusions>
- Constraints: <runtime/deployment/integration/data/privacy/performance/deadline>
- Facts: <evidence and references>
- Assumptions/open decisions: <unknown, early test and affected slices>

## Observed and intended flow
- Current flow: <input, validation, business rule, data or external effect>
- Target flow: <accepted behavior and differences>
- Error path: <caller/operator-visible behavior>
- Discrepancies: <stale documentation, defect or accepted migration>

## Boundaries
| Component | Owns | Inputs/outputs | Validation/errors | Data/dependencies |
| --- | --- | --- | --- | --- |
| <module> | <responsibility> | <contract> | <failure behavior> | <owner> |

## Data, operations and compatibility
- Schema/API/event/CLI/UI changes: <none or contract/compatibility window>
- Migration/recovery: <none or authorized transition/rollback/forward-fix>
- External APIs: <timeouts, bounded retries, duplicate effects, error mapping>
- Sensitive flows: <authorization owner, denied paths and redaction>
- Performance: <workload/environment/threshold if applicable>

## Decisions
| ID | State | Choice/reason | Rejected alternative | Authority/source | Revisit trigger |
| --- | --- | --- | --- | --- | --- |
| ADR-001 | proposed | <choice/evidence> | <alternative> | pending | <condition> |

## Slices
| ID | Outcome | Depends on | Modules/protected contracts | Acceptance | Validation | Risk |
| --- | --- | --- | --- | --- | --- | --- |
| S1 | <first verifiable flow> | none | <allowed/protected> | AC1 | <procedure> | R0 |

Detail ready work; later work retains unresolved items explicitly. No minimum
slice count. For an authorized disposable spike define question, finite budget,
observations, stop condition and separate production adoption criteria.

## Risks and blockers
| Risk/assumption | Early test | Owner | Result | Blocks which slices |
| --- | --- | --- | --- | --- |
| <unknown> | <small discriminating test> | <role> | pending | <IDs or none> |
```

## Execution status

```markdown
# Implementation Status: <project or feature>

## Current control
- Protocol version: 1.0.0
- Spec path/revision: <existing artifact/revision>
- Ledger owner: <one responsible agent/role; reconcile concurrent updates>
- Updated: <timestamp>
- Current slice: <ID>
- Overall state: <derived from all in-scope slices, not only the current slice>
- Blocker: <none or named prerequisite/decision/environment>

## Slice ledger
| Slice | State | Depends on | Spec/modules | Acceptance result | Evidence | Blocker/deviation |
| --- | --- | --- | --- | --- | --- | --- |
| S1 | planned | none | <section> | AC1 pending | none | none |

## Evidence ledger
| ID | Slice/AC | Spec revision | Covered snapshot/paths | Environment | Procedure/cwd | Expected/observed/executed | Artifact | Freshness |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| E1 | S1/AC1 | <revision> | <commit or relevant dirty-worktree manifest> | <safe identity> | <command/manual steps> | not_run | none | pending |

Include executed test counts where relevant, plus staged/unstaged/new/deleted
relevant files in snapshot identity. Record covered paths/exclusions. Exclude only
self-appended evidence content, not changes to acceptance. Redact sensitive data.

## Deviations
| ID | Slice | State | Proposal/reason/impact | Authority/source | Spec/check update | Evidence |
| --- | --- | --- | --- | --- | --- | --- |
| D1 | S1 | proposed | <change and why> | pending | <required update> | none |

## History/invalidations
| Event | Affected slices | Reason | Old evidence | Replacement/next check |
| --- | --- | --- | --- | --- |
| <timestamp> | <IDs> | <failure/relevant change/replacement> | <IDs> | <next step> |

## Next action
- <first unmet gate and smallest useful action>
```

## Gates

Before work check authority, effective spec, relevant worktree, dependencies, risk,
acceptance and validation. After work compare boundaries/final diff, inspect actual
execution evidence, update history and invalidate only affected downstream assumptions.
On resume repeat freshness/dependency checks rather than trusting saved progress.

Use planned/in_progress/blocked/needs_revalidation/verified/superseded per protocol.
Keep old history; normalize legacy `in progress` only when touching a record. A
blocked/waived/skipped check is not verified. Superseded slices retain replacement
links. Approval and implementation are separate from verified acceptance. Never
lower acceptance or overwrite concurrent edits merely to mark work complete.
