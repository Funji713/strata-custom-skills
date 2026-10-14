# View Planner Prompt

Input: Canonical Semantic Model + optional user overrides.

Choose the smallest set of views that explains the system or research clearly. Supported v1 views are `system_architecture`, `data_flow`, `ai_pipeline`, `research_methodology`, `model_architecture`, and `sequence_flow`.

Do not force a diagram. Allowed outcomes include `simple_flow`, `no_diagram_recommended`, and `insufficient_evidence`.

Respect audience and detail level independently. Prefer one coherent story per visual. Split overloaded views rather than shrinking content. Select a layout archetype from the allowed enum. Output only fields valid under `view-spec.schema.json`.
