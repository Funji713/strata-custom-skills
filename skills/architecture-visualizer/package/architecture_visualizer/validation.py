"""Mechanical, semantic, presentation, and security validation gates."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .security import contains_secret


def _schema_errors(document: dict, schema_path: Path) -> list[str]:
    try:
        from jsonschema import Draft202012Validator
    except ImportError:
        return []
    schema = json.loads(schema_path.read_text(encoding="utf-8"))
    return [f"{'.'.join(str(p) for p in error.absolute_path) or '$'}: {error.message}" for error in sorted(Draft202012Validator(schema).iter_errors(document), key=lambda e: list(e.absolute_path))]


def validate_schema(document: dict, schema_name: str, package_root: Path) -> list[str]:
    return _schema_errors(document, package_root / "schemas" / schema_name)


def _boxes_overlap(a: dict, b: dict) -> bool:
    return a["x"] < b["x"] + b["width"] and a["x"] + a["width"] > b["x"] and a["y"] < b["y"] + b["height"] and a["y"] + a["height"] > b["y"]


def _segment_hits_box(p1: list[float], p2: list[float], box: dict) -> bool:
    x1, y1 = p1; x2, y2 = p2
    epsilon = 0.1
    left, right = box["x"] + epsilon, box["x"] + box["width"] - epsilon
    top, bottom = box["y"] + epsilon, box["y"] + box["height"] - epsilon
    if abs(x1 - x2) < epsilon:
        return left < x1 < right and max(min(y1, y2), top) < min(max(y1, y2), bottom)
    if abs(y1 - y2) < epsilon:
        return top < y1 < bottom and max(min(x1, x2), left) < min(max(x1, x2), right)
    return True


def validate_layout(render_ir: dict, layout: dict, profile: dict) -> list[str]:
    errors: list[str] = []
    node_items = layout["nodes"]; boxes = {item["id"]: item["box"] for item in node_items}
    ids = [item["id"] for item in node_items]
    if len(ids) != len(set(ids)):
        errors.append("duplicate node IDs")
    width, height = layout["canvas"]["width"], layout["canvas"]["height"]
    for node_id, box in boxes.items():
        if box["x"] < 0 or box["y"] < 0 or box["x"] + box["width"] > width or box["y"] + box["height"] > height:
            errors.append(f"canvas overflow: {node_id}")
    for i, first in enumerate(ids):
        for second in ids[i+1:]:
            if _boxes_overlap(boxes[first], boxes[second]):
                errors.append(f"node overlap: {first}, {second}")
    degree = {node_id: 0 for node_id in ids}
    for edge in layout["edges"]:
        if edge["from"] not in boxes or edge["to"] not in boxes:
            errors.append(f"invalid edge: {edge['id']}")
            continue
        degree[edge["from"]] += 1; degree[edge["to"]] += 1
        for p1, p2 in zip(edge["points"], edge["points"][1:]):
            for node_id, box in boxes.items():
                if node_id in {edge["from"], edge["to"]}:
                    continue
                if _segment_hits_box(p1, p2, box):
                    errors.append(f"edge-through-node: {edge['id']} through {node_id}")
    errors.extend(f"unexplained orphan node: {node_id}" for node_id, count in degree.items() if count == 0)
    minimums = profile["font"]
    for item in node_items:
        if item["font_sizes"]["title"] < minimums["node_title_min_pt"] or item["font_sizes"]["description"] < minimums["node_description_min_pt"]:
            errors.append(f"font below profile minimum: {item['id']}")
        if len(item["title_lines"]) > 2 or len(item["description_lines"]) > 2:
            errors.append(f"text clipping risk: {item['id']}")
    return sorted(set(errors))


def validate_semantics(facts: dict, csm: dict, view: dict, render_ir: dict) -> list[str]:
    errors: list[str] = []
    fact_by_id = {fact["id"]: fact for fact in facts["facts"]}
    entity_by_id = {entity["id"]: entity for entity in csm["entities"]}
    relation_pairs = {(relation["source"], relation["target"]) for relation in csm["relations"]}
    for entity in csm["entities"]:
        if not entity["evidence_refs"] or any(ref not in fact_by_id for ref in entity["evidence_refs"]):
            errors.append(f"untraceable entity: {entity['id']}")
    for relation in csm["relations"]:
        if not relation["evidence_refs"] or any(ref not in fact_by_id for ref in relation["evidence_refs"]):
            errors.append(f"untraceable relation: {relation['id']}")
    for node in render_ir["nodes"]:
        if node["semantic_ref"] not in entity_by_id:
            errors.append(f"invented render node: {node['id']}")
    semantic_for_render = {node["id"]: node["semantic_ref"] for node in render_ir["nodes"]}
    for edge in render_ir["edges"]:
        pair = (semantic_for_render.get(edge["from"]), semantic_for_render.get(edge["to"]))
        if pair not in relation_pairs:
            errors.append(f"invented render relation: {edge['id']}")
        else:
            matching = [relation for relation in csm["relations"] if (relation["source"], relation["target"]) == pair]
            if all(any(fact_by_id[ref]["evidence_level"] == "uncertain" for ref in relation["evidence_refs"]) for relation in matching):
                errors.append(f"uncertain relation rendered as primary: {edge['id']}")
    degree = {entity_id: 0 for entity_id in view.get("included_entities", [])}
    for relation in csm["relations"]:
        if relation["source"] in degree and relation["target"] in degree:
            degree[relation["source"]] += 1; degree[relation["target"]] += 1
    for hero in view.get("hero_entities", []):
        if hero not in degree or degree[hero] == 0:
            errors.append(f"hero lacks core-flow evidence: {hero}")
    return sorted(set(errors))


def validate_security(*artifacts: Any) -> list[str]:
    return [f"secret-like content remains in artifact {index}" for index, artifact in enumerate(artifacts, 1) if contains_secret(artifact)]


def build_validation_report(*, schema_errors: list[str], semantic_errors: list[str], layout_errors: list[str], security_errors: list[str], render_ir: dict) -> dict:
    all_errors = schema_errors + semantic_errors + layout_errors + security_errors
    node_count, edge_count = len(render_ir["nodes"]), len(render_ir["edges"])
    critique = {
        "main_flow_quickly_understandable": bool(edge_count and node_count <= 25),
        "core_idea_obvious": bool(render_ir["presentation"].get("key_message")),
        "one_coherent_story": node_count <= 25 and edge_count <= 45,
        "hero_count": sum(node["visual_role"] == "hero" for node in render_ir["nodes"]),
    }
    return {"validation_version": "1.0.0", "passed": not all_errors, "errors": all_errors, "presentation_critique": critique, "repair_passes": 0}
