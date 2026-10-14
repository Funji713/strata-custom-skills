"""Primary pipeline orchestration. Each semantic boundary remains explicit."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

from . import PACKAGE_ROOT
from .discovery import discover
from .errors import EXPORT_FAILURE, SEMANTIC_VALIDATION_FAILURE, VisualizerError
from .evidence import extract_facts
from .layout import layout_render_ir
from .render_ir import build_render_ir, build_slide_content
from .security import redact, redact_text
from .semantic import build_semantic_model
from .svg import render_svg
from .validation import build_validation_report, validate_layout, validate_schema, validate_security, validate_semantics
from .views import SUPPORTED_VIEWS, plan_views


@dataclass(frozen=True)
class PipelineOptions:
    audience: str = "technical"
    level: str = "standard"
    language: str = "en"
    views: tuple[str, ...] = ()
    theme: str = "research-tech-light"
    export_profile: str = "ppt-16x9"


def _load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    try:
        temporary.write_text(text, encoding="utf-8", newline="\n")
        temporary.replace(path)
    except OSError as exc:
        raise VisualizerError(EXPORT_FAILURE, f"Cannot write {path}: {exc}") from exc


def _write_json(path: Path, document: dict) -> None:
    safe = redact(document)
    _write_text(path, json.dumps(safe, indent=2, ensure_ascii=False, sort_keys=False) + "\n")


def _require_schema(document: dict, schema_name: str) -> None:
    errors = validate_schema(document, schema_name, PACKAGE_ROOT)
    if errors:
        raise VisualizerError(SEMANTIC_VALIDATION_FAILURE, f"{schema_name}: {'; '.join(errors)}")


def _report(source_index: dict, csm: dict, views: list[dict]) -> dict:
    components = [entity["name"] for entity in csm["entities"] if entity["type"] in {"component", "service", "model", "process", "storage", "interface"}]
    flow = [f"{relation['source']} {relation['relation']} {relation['target']}" for relation in csm["relations"] if relation["mode"] in {"runtime", "conceptual", "experimental"}]
    return {
        "schema_version": "1.0.0", "source_summary": csm.get("summary"),
        "detected_architecture": f"{source_index['project_structure']} {source_index['source_type']}",
        "core_components": list(dict.fromkeys(components)), "core_flow": flow,
        "assumptions": csm.get("assumptions", []),
        "conflicts": [f"{item['status']}: {', '.join(item['candidates'])}; {item['resolution_basis']}" for item in csm.get("conflicts", [])],
        "uncertainties": csm.get("uncertainties", []),
        "abstractions": ["Files and symbols are aggregated into evidenced responsibilities and interactions."],
        "diagram_decisions": [f"{view.get('view_type', view['outcome'])}: {view.get('reason') or 'No diagram'}" for view in views],
    }


def _validate_options(options: PipelineOptions) -> None:
    if options.audience not in {"general", "academic", "technical", "executive"}:
        raise ValueError(f"Unsupported audience: {options.audience}")
    if options.level not in {"overview", "standard", "technical"}:
        raise ValueError(f"Unsupported detail level: {options.level}")
    if options.language not in {"zh-TW", "en"}:
        raise ValueError(f"Unsupported language: {options.language}")
    if set(options.views) - set(SUPPORTED_VIEWS):
        raise ValueError("Unsupported view type")


def run_pipeline(source: str | Path, output: str | Path, options: PipelineOptions | None = None) -> dict:
    options = options or PipelineOptions(); _validate_options(options)
    output_path = Path(output).resolve(); output_path.mkdir(parents=True, exist_ok=True)

    discovery = discover(source)
    source_index = redact(discovery.index)
    _require_schema(source_index, "source-index.schema.json")
    _write_json(output_path / "source-index.json", source_index)

    facts = redact(extract_facts(discovery))
    _require_schema(facts, "fact-evidence.schema.json")
    _write_json(output_path / "facts-evidence.json", facts)

    csm = redact(build_semantic_model(source_index, facts))
    _require_schema(csm, "semantic-model.schema.json")
    _write_json(output_path / "semantic-model.json", csm)

    views = plan_views(csm, audience=options.audience, level=options.level, language=options.language, requested_views=options.views)
    for view in views:
        _require_schema(view, "view-spec.schema.json")
    architecture_report = _report(source_index, csm, views)
    _require_schema(architecture_report, "architecture-report.schema.json")
    _write_json(output_path / "architecture-report.json", architecture_report)

    theme = _load_json(PACKAGE_ROOT / "themes" / f"{options.theme}.json")
    profile = _load_json(PACKAGE_ROOT / "profiles" / f"{options.export_profile}.json")
    rendered_views: list[dict] = []
    diagram_index = 0
    for view in views:
        if view["outcome"] != "diagram":
            continue
        diagram_index += 1
        slug = view["view_type"].replace("_", "-")
        view_dir = output_path / "views" / f"{diagram_index:02d}-{slug}"
        _write_json(view_dir / "view-spec.json", view)
        render_ir = redact(build_render_ir(view, csm, theme=options.theme, export_profile=options.export_profile))
        _require_schema(render_ir, "render-ir.schema.json")
        _write_json(view_dir / "render-ir.json", render_ir)
        slide = redact(build_slide_content(render_ir)); _require_schema(slide, "slide-content.schema.json")
        _write_json(view_dir / "slide-content.json", slide)
        layout = layout_render_ir(render_ir, profile)
        editable = redact_text(render_svg(render_ir, layout, theme, profile, portable=False))
        portable = redact_text(render_svg(render_ir, layout, theme, profile, portable=True))
        schema_errors = []
        semantic_errors = validate_semantics(facts, csm, view, render_ir)
        layout_errors = validate_layout(render_ir, layout, profile)
        security_errors = validate_security(source_index, facts, csm, architecture_report, view, render_ir, slide, editable, portable)
        validation = build_validation_report(schema_errors=schema_errors, semantic_errors=semantic_errors, layout_errors=layout_errors, security_errors=security_errors, render_ir=render_ir)
        _write_json(view_dir / "validation-report.json", validation)
        if not validation["passed"]:
            raise VisualizerError(SEMANTIC_VALIDATION_FAILURE, f"Visual validation failed for {view['view_type']}: {'; '.join(validation['errors'])}")
        _write_text(view_dir / "architecture-editable.svg", editable)
        _write_text(view_dir / "architecture-portable.svg", portable)
        rendered_views.append({"view_type": view["view_type"], "directory": view_dir.relative_to(output_path).as_posix(), "validation": "passed", "nodes": len(render_ir["nodes"]), "edges": len(render_ir["edges"])})

    summary = {
        "version": "1.0.0", "source_type": source_index["source_type"], "outcomes": [view["outcome"] for view in views],
        "rendered_views": rendered_views, "semantic_artifacts_preserved": True,
        "pipeline": ["source-index", "facts-evidence", "semantic-model", "view-spec", "render-ir", "visual"],
        "status": "passed" if rendered_views else views[0]["outcome"],
    }
    _write_json(output_path / "summary.json", summary)
    return redact(summary)
