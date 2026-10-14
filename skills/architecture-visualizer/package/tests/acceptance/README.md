# Acceptance Tests

The skill should pass these minimum scenarios.

| # | Case | Expected behavior |
|---|---|---|
| 1 | Django + React app | Produce `system_architecture`; detect frontend/backend boundaries without turning files into nodes. |
| 2 | AI web application | Produce system architecture plus AI pipeline when both are central. |
| 3 | Pure ML repository | Prefer `ai_pipeline`; avoid inventing frontend/database. |
| 4 | Transformer research paper | Produce research methodology and/or model architecture based on evidence. |
| 5 | ETL/data repository | Prefer `data_flow`; show transformations and storage only when evidenced. |
| 6 | API-heavy backend | Produce architecture and optionally `sequence_flow` for request/response behavior. |
| 7 | Small single script | Return `simple_flow` rather than an inflated system architecture. |
| 8 | Monorepo | Discover subsystems first; produce overall architecture and split views when needed. |
| 9 | Incomplete repository | Preserve unknowns; allow `insufficient_evidence`. |
| 10 | Paper without explicit architecture | Do not hallucinate a model architecture. |
| 11 | Agent/tool loop | Support `feedback_loop` and feedback edges. |
| 12 | README/code conflict | Record conflict and choose only with explicit resolution basis. |
| 13 | Repository containing `.env` | Detect useful service names but redact all secret values from artifacts. |
| 14 | Static import without runtime use | Do not misrepresent an import as a runtime sequence. |
| 15 | Figure/text conflict in paper | Preserve conflict; never silently pick one interpretation. |
| 16 | Dense graph | Simplify or split based on visual complexity instead of only node count. |

## Semantic pass criteria

- no invented core components;
- no invented core relations;
- important relations link to evidence;
- static/runtime modes are not conflated;
- stable semantic IDs are used.

## Render pass criteria

- zero node overlaps;
- zero text clipping;
- zero canvas overflow;
- zero edge-through-node collisions;
- main flow is continuous;
- hero nodes correspond to real core concepts.

## Presentation pass criteria

- main flow is understandable quickly;
- one coherent story per view;
- core contribution is visually obvious when applicable;
- text remains readable under `ppt-16x9` profile;
- diagrams that become too dense are split rather than globally shrunk.
