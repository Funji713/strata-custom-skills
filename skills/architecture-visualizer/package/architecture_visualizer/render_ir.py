"""Convert a View Spec and CSM to the renderer-only contract."""

from __future__ import annotations

from collections import defaultdict

from .errors import SEMANTIC_VALIDATION_FAILURE, VisualizerError

_CATEGORY = {
    "actor": "input", "interface": "interface", "component": "service", "service": "service", "process": "process",
    "model": "model", "data": "input", "dataset": "input", "storage": "database", "external_service": "external",
    "experiment": "process", "metric": "evaluation", "objective": "evaluation", "output": "output", "concept": "process",
}
_EDGE = {
    "imports": "dependency", "depends_on": "dependency", "calls": "api", "invokes": "control", "routes_to": "api",
    "reads": "data", "writes": "data", "produces": "data", "consumes": "data", "transforms": "main",
    "triggers": "control", "returns": "api", "evaluates": "control", "trains": "control", "feeds": "main",
    "compares": "control", "contains": "dependency",
}
_TITLES = {
    "system_architecture": "System Architecture", "data_flow": "Data Flow", "ai_pipeline": "AI Pipeline",
    "research_methodology": "Research Methodology", "model_architecture": "Model Architecture", "sequence_flow": "Sequence Flow",
}


def _compress(text: str | None, words: int = 10) -> str | None:
    if not text:
        return None
    parts = text.split()
    return " ".join(parts[:words]) + ("…" if len(parts) > words else "")


def build_render_ir(view: dict, csm: dict, *, theme: str = "research-tech-light", export_profile: str = "ppt-16x9") -> dict:
    if view["outcome"] != "diagram":
        raise VisualizerError(SEMANTIC_VALIDATION_FAILURE, "Render IR requires a diagram View Spec")
    entity_by_id = {entity["id"]: entity for entity in csm["entities"]}
    included = list(view.get("included_entities", []))
    missing = sorted(set(included) - set(entity_by_id))
    if missing:
        raise VisualizerError(SEMANTIC_VALIDATION_FAILURE, f"View contains unknown semantic entities: {missing}")
    node_id_for = {semantic_id: f"render://node/{index:02d}" for index, semantic_id in enumerate(included, 1)}
    group_members: dict[str, list[str]] = defaultdict(list)
    nodes: list[dict] = []
    for semantic_id in included:
        entity = entity_by_id[semantic_id]
        group = entity.get("subsystem") if entity.get("subsystem") in included else None
        group_id = f"render://group/{len(group_members) + 1:02d}" if group and group not in group_members else None
        if group:
            if group not in group_members:
                group_members[group] = []
            group_members[group].append(node_id_for[semantic_id])
        nodes.append({
            "id": node_id_for[semantic_id], "semantic_ref": semantic_id, "label": _compress(entity["name"], 4) or entity["name"],
            "category": _CATEGORY[entity["type"]], "description": _compress(entity.get("responsibility"), 10),
            "visual_role": "hero" if semantic_id in view["hero_entities"] else ("primary" if entity["type"] in {"component", "service", "process", "model"} else "supporting"),
            "group": None, "icon": None,
        })
    groups: list[dict] = []
    group_ids: dict[str, str] = {}
    for index, (semantic_group, members) in enumerate(sorted(group_members.items()), 1):
        if len(members) < 2:
            continue
        group_id = f"render://group/{index:02d}"; group_ids[semantic_group] = group_id
        groups.append({"id": group_id, "label": entity_by_id[semantic_group]["name"], "order": index - 1, "members": members})
    for node in nodes:
        semantic = entity_by_id[node["semantic_ref"]]
        if semantic.get("subsystem") in group_ids:
            node["group"] = group_ids[semantic["subsystem"]]

    edges: list[dict] = []
    for relation in csm["relations"]:
        if relation["source"] not in node_id_for or relation["target"] not in node_id_for:
            continue
        edge_type = "feedback" if view["layout_archetype"] == "feedback_loop" and relation["relation"] in {"feeds", "triggers", "returns"} else _EDGE[relation["relation"]]
        edges.append({"id": f"render://edge/{len(edges)+1:02d}", "from": node_id_for[relation["source"]], "to": node_id_for[relation["target"]], "type": edge_type, "label": relation.get("label") or relation["relation"].replace("_", " ")})
    if not edges:
        raise VisualizerError(SEMANTIC_VALIDATION_FAILURE, "View selection produced no evidenced relation")
    annotations = []
    if view.get("excluded_entities"):
        annotations.append({"id": "render://annotation/01", "type": "note", "target": None, "text": f"{len(view['excluded_entities'])} concepts moved to another segment or omitted for readability."})
    before = [[edge["from"], edge["to"]] for edge in edges if edge["type"] in {"main", "data", "api", "control"} and edge["from"] != edge["to"]]
    presentation_order = [node_id_for[item] for item in included]
    return {
        "render_ir_version": "1.0.0",
        "diagram": {"title": _TITLES[view["view_type"]], "subtitle": view["reason"], "view_type": view["view_type"], "layout_archetype": view["layout_archetype"], "theme": theme, "export_profile": export_profile, "language": view["language"]},
        "nodes": nodes, "groups": groups, "edges": edges, "annotations": annotations,
        "constraints": {"same_rank": [], "keep_together": [group["members"] for group in groups], "before": before},
        "presentation": {"key_message": view["narrative"]["key_message"], "speaker_notes": [view["reason"]], "presentation_order": presentation_order},
    }


def build_slide_content(render_ir: dict) -> dict:
    diagram = render_ir["diagram"]; presentation = render_ir["presentation"]
    return {"schema_version": "1.0.0", "title": diagram["title"], "subtitle": diagram.get("subtitle"), "key_message": presentation["key_message"], "speaker_notes": presentation["speaker_notes"], "presentation_order": presentation["presentation_order"]}
