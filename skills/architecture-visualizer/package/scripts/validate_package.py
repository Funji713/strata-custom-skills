#!/usr/bin/env python3
"""Validate architecture-visualizer package schemas and shared enum consistency."""
from __future__ import annotations
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
SCHEMAS = ROOT / "schemas"


def load(name: str):
    return json.loads((SCHEMAS / name).read_text(encoding="utf-8"))


def enum(obj, *path):
    for key in path:
        obj = obj[key]
    return obj["enum"]


def main() -> int:
    errors: list[str] = []
    vocabulary = load("vocabulary.schema.json")["$defs"]

    for path in sorted(SCHEMAS.glob("*.json")):
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            try:
                from jsonschema import Draft202012Validator
                Draft202012Validator.check_schema(data)
            except ImportError:
                pass
        except Exception as exc:
            errors.append(f"{path.name}: {exc}")

    fact = load("fact-evidence.schema.json")
    semantic = load("semantic-model.schema.json")
    view = load("view-spec.schema.json")
    render = load("render-ir.schema.json")

    checks = [
        ("evidence_level", enum(fact, "properties", "facts", "items", "properties", "evidence_level")),
        ("evidence_type", enum(fact, "properties", "facts", "items", "properties", "evidence", "items", "properties", "type")),
        ("relation_type", enum(fact, "properties", "facts", "items", "properties", "relation")),
        ("relation_type", enum(semantic, "properties", "relations", "items", "properties", "relation")),
        ("relation_mode", enum(semantic, "properties", "relations", "items", "properties", "mode")),
        ("entity_type", enum(semantic, "properties", "entities", "items", "properties", "type")),
        ("view_type", enum(view, "properties", "view_type")),
        ("view_type", enum(render, "properties", "diagram", "properties", "view_type")),
        ("view_outcome", enum(view, "properties", "outcome")),
        ("audience", enum(view, "properties", "audience")),
        ("detail_level", enum(view, "properties", "level")),
        ("language", enum(view, "properties", "language")),
        ("language", enum(render, "properties", "diagram", "properties", "language")),
        ("layout_archetype", enum(view, "properties", "layout_archetype")),
        ("layout_archetype", enum(render, "properties", "diagram", "properties", "layout_archetype")),
        ("visual_role", enum(render, "properties", "nodes", "items", "properties", "visual_role")),
        ("render_node_category", enum(render, "properties", "nodes", "items", "properties", "category")),
        ("edge_type", enum(render, "properties", "edges", "items", "properties", "type")),
    ]

    for vocab_key, actual in checks:
        expected = vocabulary[vocab_key]["enum"]
        if actual != expected:
            errors.append(f"Enum mismatch for {vocab_key}: {actual!r} != {expected!r}")

    if errors:
        print("VALIDATION FAILED")
        for error in errors:
            print("-", error)
        return 1

    print("architecture-visualizer package validation: PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
