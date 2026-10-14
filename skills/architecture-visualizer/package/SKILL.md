# architecture-visualizer

Version: 1.0.0

## Purpose

`architecture-visualizer` converts software projects and research papers into evidence-grounded, presentation-ready technical diagrams. It is not a generic Mermaid, UML, ERD, or code-documentation generator.

The core pipeline is:

`SOURCE -> EVIDENCE -> CANONICAL SEMANTIC MODEL -> PRESENTATION VIEW -> RENDER IR -> VISUAL`

Never skip directly from source material to SVG.

## When to use this skill

Use this skill when the user asks to:

- analyze a software repository, project folder, source code, API/backend, AI project, or monorepo and explain its architecture visually;
- turn a research paper, methodology section, model description, or experiment pipeline into a diagram;
- create a system architecture, data flow, AI pipeline, research methodology, model architecture, or sequence flow for presentation;
- simplify a complex technical system into a presentation-ready overview;
- generate PPT-ready architecture visuals, SVG diagrams, speaker notes, or slide narrative from technical sources.

Do not use this skill when the primary request is:

- full UML generation;
- ERD/class diagram generation;
- source-code documentation;
- infrastructure provisioning;
- pixel-art, 3D, or decorative illustration;
- a diagram unsupported by the evidence.

## Non-negotiable principles

### 1. Semantic fidelity

Presentation abstraction may merge or hide details, but it must not invent dependencies, alter causal order, change responsibilities, or promote uncertain information into verified information.

Allowed:

`Auth Controller + Auth Service + JWT Utility -> Authentication`

Not allowed:

`Frontend -> Queue -> Worker -> AI` becoming `Frontend -> AI` when the omitted steps materially change system behavior.

### 2. Evidence first

Every important semantic fact must be created together with evidence. Do not infer an architecture and then search for supporting evidence after the fact.

### 3. Presentation abstraction

Visualize responsibilities and interactions, not file trees. For research, visualize the research idea rather than reproducing the paper verbatim.

### 4. Unknown stays unknown

If evidence is insufficient, return `insufficient_evidence`, `simple_flow`, or `no_diagram_recommended` instead of fabricating architecture.

### 5. Secrets never enter artifacts

Credential values, API keys, tokens, passwords, private connection strings, and similar secrets must be redacted before any intermediate or final artifact is written.

---

# Pipeline

## Stage 1 — Source discovery

Determine the source class before deep analysis.

Supported source classes:

- `software_project`
- `research_paper`
- `technical_document`
- `mixed`

Produce `source-index.json` using `schemas/source-index.schema.json`.

For software sources, identify:

- project structure (`single_project`, `monorepo`, `unknown`);
- languages;
- frameworks;
- candidate entry points;
- candidate subsystems;
- high-priority paths;
- ignored or low-priority paths.

For research sources, identify:

- title;
- sections;
- figures and captions;
- equations;
- tables;
- likely method and experiment sections.

Do not perform full semantic interpretation during source discovery.

## Stage 2 — Repository or paper triage

### Software triage

Use progressive analysis:

1. tree scan;
2. manifest scan;
3. language/framework detection;
4. entry-point detection;
5. subsystem discovery;
6. symbol discovery;
7. focused source reading;
8. expand only when more evidence is required.

Default ignored or heavily deprioritized paths:

- `.git/`
- `node_modules/`
- `venv/`
- `dist/`
- `build/`
- `coverage/`
- `__pycache__/`
- generated code;
- compiled assets;
- binary files;
- vendor bundles.

Tests, examples, README files, and comments are low-priority evidence rather than architecture nodes.

### Research triage

Preferred reading order:

1. title;
2. abstract;
3. contribution statements;
4. method / proposed method;
5. figures + captions;
6. model / framework sections;
7. experiment setup;
8. results;
9. conclusion.

Related work and references are low priority unless the user explicitly asks for them.

## Stage 3 — Focused source analysis

Analyze symbols and responsibilities, not only files.

Relevant software units may include:

- classes;
- functions;
- routes;
- endpoints;
- services;
- models;
- imports;
- runtime calls;
- database reads/writes;
- external API calls.

A symbol is an analysis unit, not automatically a diagram node.

For papers, evidence may come from:

- text;
- figure;
- figure caption;
- equation;
- table.

## Stage 4 — Facts + evidence

Write `facts-evidence.json` using `schemas/fact-evidence.schema.json`.

Each important fact must include:

- stable fact ID;
- subject;
- relation;
- object;
- statement;
- evidence level;
- one or more evidence references when available.

Allowed evidence levels:

- `verified`
- `supported`
- `inferred`
- `uncertain`

Default policy for primary diagrams:

- `verified`: allowed;
- `supported`: allowed;
- `inferred`: only when important and clearly justifiable;
- `uncertain`: do not include by default.

Allowed evidence types:

- `runtime_reference`
- `configuration`
- `declaration`
- `route_definition`
- `dependency_manifest`
- `test_behavior`
- `documentation`
- `comment`
- `figure`
- `caption`
- `equation`
- `table`

Do not use fake numeric confidence scores such as `0.91` unless a future calibrated confidence model exists.

## Stage 5 — Canonical Semantic Model (CSM)

Build `semantic-model.json` using `schemas/semantic-model.schema.json`.

The CSM represents what the system or research actually means. It does not contain rendering coordinates.

Allowed entity types:

- `actor`
- `interface`
- `component`
- `service`
- `process`
- `model`
- `data`
- `dataset`
- `storage`
- `external_service`
- `experiment`
- `metric`
- `objective`
- `output`
- `concept`

Allowed relation types:

- `contains`
- `imports`
- `depends_on`
- `calls`
- `invokes`
- `routes_to`
- `reads`
- `writes`
- `produces`
- `consumes`
- `transforms`
- `triggers`
- `returns`
- `evaluates`
- `trains`
- `feeds`
- `compares`

Allowed relation modes:

- `static`
- `runtime`
- `conceptual`
- `experimental`

Stable identity is required. Prefer IDs derived from source or canonical concepts, such as:

- `project://backend/authentication`
- `project://ai/inference`
- `paper://method/pose_completion`
- `paper://experiment/dataset_a`

Avoid random IDs such as `node_1` or `component_a`.

## Stage 6 — Conflict resolution

When sources disagree, preserve the conflict before resolving it.

Examples:

- README says MySQL, active configuration says PostgreSQL;
- paper figure and method text disagree on operation order.

Use evidence context to resolve when possible. Store the conflict and selected interpretation in the CSM or architecture report. Never silently overwrite contradictory evidence.

## Stage 7 — User overrides

User presentation choices are applied after the CSM and must not mutate semantic truth.

Supported override concepts:

- hide;
- rename;
- merge;
- split;
- mark hero;
- pin;
- lock group;
- change view type;
- change detail level.

Conceptual flow:

`CSM + USER OVERRIDES -> VIEW PLANNER`

## Stage 8 — View planner

Create one or more `view-spec.json` files using `schemas/view-spec.schema.json`.

Supported v1 view types:

- `system_architecture`
- `data_flow`
- `ai_pipeline`
- `research_methodology`
- `model_architecture`
- `sequence_flow`

Reserved for future versions:

- `deployment_architecture`

The planner may also return:

- `simple_flow`
- `no_diagram_recommended`
- `insufficient_evidence`

Do not force a complex diagram for a simple script or poorly evidenced source.

### Default selection guidance

`system_architecture` signals:

- frontend;
- backend;
- service;
- database;
- API;
- worker;
- external service.

`ai_pipeline` signals:

- model;
- training;
- inference;
- embedding;
- CNN;
- Transformer;
- LLM;
- classification;
- segmentation.

`research_methodology` signals:

- paper source;
- proposed method;
- dataset;
- experiment;
- evaluation.

`model_architecture` signals:

- encoder;
- decoder;
- attention;
- backbone;
- fusion;
- head;
- loss/objective.

`data_flow` signals:

- dataset;
- ETL;
- preprocessing;
- feature;
- storage;
- transformation.

`sequence_flow` signals:

- multiple actors;
- runtime request/response interactions.

When multiple views are independently important, split them rather than overloading one visual. By default generate no more than three primary diagrams.

## Stage 9 — Audience and detail level

Audience and detail level are independent dimensions.

Allowed audiences:

- `general`
- `academic`
- `technical`
- `executive`

Allowed detail levels:

- `overview`
- `standard`
- `technical`

Supported v1 languages:

- `zh-TW`
- `en`

Reserved languages may include `ja` and `ko`, but v1 output behavior is only guaranteed for `zh-TW` and `en`.

## Stage 10 — Narrative planner

For every primary view, derive a presentation narrative:

- start;
- transformation;
- core idea;
- outcome;
- key message.

The narrative controls emphasis but never changes semantic truth.

Hero importance may consider:

- explicit contribution statements;
- semantic centrality;
- narrative importance;
- process position.

Allowed visual roles:

- `context`
- `supporting`
- `primary`
- `hero`

Use no more than two hero nodes per diagram.

## Stage 11 — Render IR

Convert each view to `render-ir.json` using `schemas/render-ir.schema.json`.

Render IR is the only format the renderer must understand. It must not contain repository-analysis logic.

Render IR contains:

- diagram metadata;
- nodes;
- groups;
- edges;
- annotations;
- semantic layout constraints;
- presentation metadata.

Allowed render node categories:

- `input`
- `process`
- `model`
- `service`
- `database`
- `external`
- `output`
- `evaluation`
- `interface`
- `decision`

Allowed edge types:

- `main`
- `data`
- `api`
- `dependency`
- `optional`
- `bidirectional`
- `control`
- `feedback`

Allowed layout archetypes:

- `linear`
- `layered`
- `branch_merge`
- `parallel`
- `hierarchical`
- `hub_spoke`
- `swimlane`
- `feedback_loop`

The LLM may specify semantic constraints such as `same_rank`, `keep_together`, and `before`, but must not output absolute pixel coordinates.

## Stage 12 — Layout

A deterministic graph layout engine should translate Render IR into coordinates. Suitable implementations include ELK, Dagre, or Graphviz; the skill does not require a specific library.

Required conceptual pipeline:

`Render IR -> Graph Layout -> Grid Alignment -> Group Expansion -> Edge Routing -> Text Placement -> Canvas Fitting`

Preferred edge routing is orthogonal. Avoid diagonal spaghetti and routes crossing node bodies or text.

Same Render IR + same theme + same export profile should produce stable layout whenever practical.

## Stage 13 — Visual complexity control

Do not decide complexity only by node count. Consider:

- node count;
- edge count;
- branch count;
- group count;
- text density;
- graph depth;
- edge crossings.

Node count heuristics:

- overview: roughly 4–8;
- standard: roughly 6–14;
- technical: roughly 10–25.

These are guidelines, not hard limits. When visual complexity is too high, simplify or split the view.

## Stage 14 — Text compression

Prefer shorter wording over smaller font sizes.

English preferred limits:

- node title: <= 4 words;
- node description: <= 10 words.

Traditional Chinese preferred limits:

- node title: <= 12 characters;
- node description: <= 24 characters.

Arrow labels should normally be 1–3 words or a short technical token such as `REST API`.

## Stage 15 — Visual design

Default theme: `themes/research-tech-light.json`.

Design intent:

- scientific;
- modern technical presentation;
- minimal SaaS clarity;
- presentation-first rather than documentation-first.

Semantic colors:

- input: blue;
- process: cyan;
- model: purple;
- external: orange;
- database/storage: green;
- output: pink;
- evaluation: yellow.

Color must never be the only category cue. Use labels and structure too.

Default cards are rounded rectangles with at most three information layers:

1. category;
2. module name;
3. short description.

Avoid heavy shadow, excessive neon, decorative 3D effects, and icon overload.

## Stage 16 — Export profile

Default profile: `profiles/ppt-16x9.json`.

The export profile, not the theme, owns:

- canvas size;
- safe margins;
- minimum font sizes;
- minimum stroke widths;
- SVG compatibility rules;
- slide readability constraints.

PPT-friendly SVG should favor:

- `rect`;
- `path`;
- `line`;
- `text`;
- `tspan`;
- simple gradients.

Avoid `foreignObject`, complex filters, advanced masks, unsupported CSS, and blend modes.

Preferred SVG outputs:

- `architecture-editable.svg`: preserves text when practical;
- `architecture-portable.svg`: favors visual consistency across machines.

## Stage 17 — Validation

A render is not complete until validation passes.

### Mechanical validation

Require:

- zero node overlap;
- zero text clipping;
- zero canvas overflow;
- zero edge-through-node collisions;
- zero invalid edges;
- zero duplicate IDs;
- zero unexplained orphan main nodes;
- valid main-path continuity;
- font size above export-profile minimum.

### Semantic validation

Require:

- no invented components;
- no invented relations;
- no changed causal order;
- no uncertain claim represented as verified;
- hero nodes tied to actual core flow or contribution.

### Presentation critique

Ask:

- Can a viewer understand the main flow quickly?
- Is the core idea obvious?
- Is anything unnecessary?
- Should nodes be merged?
- Does the figure tell one coherent story?

Allow at most two repair passes.

Repair order:

1. spacing adjustment;
2. text shortening;
3. node regrouping;
4. layout-archetype change;
5. diagram split.

Do not make all elements smaller as the first repair strategy.

## Stage 18 — Output

Recommended output structure:

```text
architecture-output/
├── source-index.json
├── facts-evidence.json
├── semantic-model.json
├── architecture-report.json
├── views/
│   ├── 01-system/
│   │   ├── view-spec.json
│   │   ├── render-ir.json
│   │   ├── architecture-editable.svg
│   │   ├── architecture-portable.svg
│   │   └── slide-content.json
│   └── 02-ai-pipeline/
└── summary.json
```

`architecture-report.json` should conform to `schemas/architecture-report.schema.json` and summarize:

- source summary;
- detected architecture;
- core components;
- core flow;
- assumptions;
- conflicts;
- uncertainties;
- abstractions;
- diagram decisions.

`slide-content.json` should conform to `schemas/slide-content.schema.json` and include:

- title;
- subtitle;
- key message;
- speaker notes;
- presentation order.

---

# Security rules

1. Never write raw secrets into any artifact.
2. `.env` may be inspected for key names, but secret values must be replaced with `<redacted>` before reasoning artifacts are serialized.
3. Private connection strings and tokens must not appear in labels, evidence excerpts, or speaker notes.
4. If sensitive content is not necessary for architecture understanding, omit it entirely.

---

# Error taxonomy

Use these error codes consistently:

- `SOURCE_PARSE_ERROR`
- `UNSUPPORTED_SOURCE`
- `UNSUPPORTED_LANGUAGE`
- `INSUFFICIENT_EVIDENCE`
- `SEMANTIC_CONFLICT`
- `SEMANTIC_VALIDATION_FAILURE`
- `LAYOUT_FAILURE`
- `RENDER_FAILURE`
- `EXPORT_FAILURE`

Failure behavior:

- Do not fabricate a successful diagram after a semantic failure.
- If evidence is insufficient, return a structured insufficient-evidence outcome and explain the missing evidence.
- If rendering fails but semantic analysis is valid, preserve and return the semantic artifacts.

---

# Schema and enum consistency

The following enums are authoritative and must match the JSON schemas exactly.

## Source types

`software_project`, `research_paper`, `technical_document`, `mixed`

## Evidence levels

`verified`, `supported`, `inferred`, `uncertain`

## Evidence types

`runtime_reference`, `configuration`, `declaration`, `route_definition`, `dependency_manifest`, `test_behavior`, `documentation`, `comment`, `figure`, `caption`, `equation`, `table`

## CSM entity types

`actor`, `interface`, `component`, `service`, `process`, `model`, `data`, `dataset`, `storage`, `external_service`, `experiment`, `metric`, `objective`, `output`, `concept`

## Relation types

`contains`, `imports`, `depends_on`, `calls`, `invokes`, `routes_to`, `reads`, `writes`, `produces`, `consumes`, `transforms`, `triggers`, `returns`, `evaluates`, `trains`, `feeds`, `compares`

## Relation modes

`static`, `runtime`, `conceptual`, `experimental`

## View types

`system_architecture`, `data_flow`, `ai_pipeline`, `research_methodology`, `model_architecture`, `sequence_flow`

Reserved: `deployment_architecture`

## View outcomes

`diagram`, `simple_flow`, `no_diagram_recommended`, `insufficient_evidence`

## Audiences

`general`, `academic`, `technical`, `executive`

## Detail levels

`overview`, `standard`, `technical`

## Languages guaranteed in v1

`zh-TW`, `en`

## Layout archetypes

`linear`, `layered`, `branch_merge`, `parallel`, `hierarchical`, `hub_spoke`, `swimlane`, `feedback_loop`

## Visual roles

`context`, `supporting`, `primary`, `hero`

## Render node categories

`input`, `process`, `model`, `service`, `database`, `external`, `output`, `evaluation`, `interface`, `decision`

## Edge types

`main`, `data`, `api`, `dependency`, `optional`, `bidirectional`, `control`, `feedback`

---

# Definition of done

The v1 implementation is complete only when all of the following are true.

## Correctness

- Important components are traceable to evidence.
- Important relations are traceable to evidence.
- No unsupported architecture is hallucinated.

## Abstraction

- Files/classes/functions are not mechanically turned into diagram nodes.
- Complex projects can be summarized by responsibilities and subsystem boundaries.

## Presentation

- Output can be placed directly on a 16:9 PowerPoint slide.
- Main flow and core contribution are visually obvious.
- Manual redesign is not required for a normal supported case.

## Rendering

- No overlap.
- No clipping.
- No overflow.
- No obvious edge spaghetti.

## Stability

- Same input and settings produce stable semantic identities and reasonably stable layout.
- Schemas are versioned.
- Golden/regression rendering tests exist.

## Safety

- Secret values never enter artifacts.
- Unknown information is never presented as known.

---

# Final rule

Never collapse the architecture into:

`SOURCE -> LLM -> SVG`

Always preserve the separation:

`SOURCE -> EVIDENCE -> CSM -> VIEW -> RENDER IR -> VISUAL`


# Package self-validation

Before release or after changing schemas, run `python scripts/validate_package.py`. The package is not considered internally consistent if this validator fails.
