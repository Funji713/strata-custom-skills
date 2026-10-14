---
name: architecture-visualizer
description: Analyze a software project, source repository, research paper, or technical document and produce evidence-grounded, PowerPoint-ready architecture SVGs and traceable JSON artifacts. Use for system architecture, data flow, AI pipeline, research methodology, model architecture, or sequence-flow visuals; not for UML, ERDs, or decorative diagrams.
metadata:
  short-description: Evidence-grounded PPT architecture visuals
---

# Architecture Visualizer

Create trustworthy, presentation-ready technical diagrams from supplied source material.

## Required preparation

Before analyzing or rendering, read [the bundled v1.0.0 specification](package/SKILL.md) completely. Treat its schemas, prompts, theme, profile, and validation rules in `package/` as normative. The implementation and tests are bundled beside them for reference and verification.

## Operating rules

- Preserve the complete semantic pipeline: `Source Index -> Facts/Evidence -> Canonical Semantic Model -> View Spec -> Render IR -> Visual`.
- Use deterministic graph layout. Never have an LLM assign absolute pixel coordinates.
- Keep facts traceable to evidence and preserve `verified`, `supported`, `inferred`, and `uncertain` distinctions.
- Redact all secrets before any intermediate or final artifact is written.
- Generate only supported v1 views and return a structured non-diagram outcome when evidence is inadequate.
- Render PowerPoint-ready `ppt-16x9` SVG, then run semantic, layout, and security validation before delivery.

## Implementation path

When the bundled CLI fits the request, run it from `package/` and retain its JSON artifact tree with the SVG outputs. When adapting it to a target project or adding an analyzer, preserve the bundled schema contracts and execute the relevant validator and acceptance tests after each major module.

Do not substitute Mermaid, freehand SVG, or a source-to-LLM-to-SVG shortcut for this pipeline.
