# Package Manifest

## Core
- `SKILL.md` — authoritative execution contract
- `README.md` — installation and usage guide
- `VERSION` — package version

## Schemas
- `source-index.schema.json`
- `fact-evidence.schema.json`
- `semantic-model.schema.json`
- `view-spec.schema.json`
- `render-ir.schema.json`
- `architecture-report.schema.json`
- `slide-content.schema.json`
- `vocabulary.schema.json`

## Prompts
- `repository-discovery.md`
- `paper-discovery.md`
- `semantic-extraction.md`
- `conflict-resolution.md`
- `view-planner.md`
- `narrative-planner.md`

## Presentation system
- `themes/research-tech-light.json`
- `profiles/ppt-16x9.json`

## Quality
- `scripts/validate_package.py`
- `tests/acceptance/README.md`
- `tests/test_acceptance.py` — executable semantic, render, safety, CLI, and deterministic regression coverage

## Executable MVP
- `architecture_visualizer/` — source discovery through validated SVG orchestration
- `pyproject.toml` — Python package and CLI entry point
- `ARCHITECTURE.md` — implementation boundaries and decisions
- `IMPLEMENTATION_STATUS.md` — slice ledger and validation evidence
- `examples/demo-ai-service/` — reproducible evidenced input
- `examples/demo-output/` — validated PPT-ready example artifacts
