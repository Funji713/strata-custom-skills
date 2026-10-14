"""Evidence-preserving view selection and presentation narrative."""

from __future__ import annotations

from collections import Counter, defaultdict, deque
from typing import Iterable

SUPPORTED_VIEWS = (
    "system_architecture", "data_flow", "ai_pipeline", "research_methodology", "model_architecture", "sequence_flow",
)
_VIEW_TITLES = {
    "system_architecture": "System Architecture", "data_flow": "Data Flow", "ai_pipeline": "AI Pipeline",
    "research_methodology": "Research Methodology", "model_architecture": "Model Architecture", "sequence_flow": "Sequence Flow",
}
_LAYOUTS = {
    "system_architecture": "layered", "data_flow": "linear", "ai_pipeline": "linear",
    "research_methodology": "linear", "model_architecture": "hierarchical", "sequence_flow": "swimlane",
}
_MAX_NODES = {"overview": 8, "standard": 14, "technical": 25}


def _eligible(view_type: str, entity: dict, csm: dict) -> bool:
    typ = entity["type"]
    tags = set(entity.get("tags", []))
    name = entity["name"].lower()
    if view_type == "system_architecture":
        return typ in {"actor", "interface", "component", "service", "storage", "external_service", "output"}
    if view_type == "data_flow":
        return typ in {"data", "dataset", "storage", "process", "output", "metric"} or "data" in tags
    if view_type == "ai_pipeline":
        return typ in {"model", "dataset", "data", "metric", "objective", "output"} or "ai" in tags or any(term in name for term in ("train", "infer", "predict", "embedding"))
    if view_type == "research_methodology":
        return csm["source_type"] == "research_paper" and typ in {"process", "model", "dataset", "experiment", "metric", "objective", "output", "concept"}
    if view_type == "model_architecture":
        return typ in {"model", "objective"} or any(term in name for term in ("encoder", "decoder", "attention", "backbone", "fusion", "head", "loss"))
    if view_type == "sequence_flow":
        runtime_ids = {side for relation in csm["relations"] if relation["mode"] == "runtime" for side in (relation["source"], relation["target"])}
        return entity["id"] in runtime_ids
    return False


def _view_score(view_type: str, csm: dict) -> int:
    matching = [entity for entity in csm["entities"] if _eligible(view_type, entity, csm)]
    relation_kinds = Counter(relation["relation"] for relation in csm["relations"])
    if view_type == "system_architecture":
        return len(matching) + 2 * sum(relation_kinds[k] for k in ("routes_to", "calls", "depends_on"))
    if view_type == "data_flow":
        return len(matching) + 2 * sum(relation_kinds[k] for k in ("reads", "writes", "produces", "consumes", "transforms", "feeds"))
    if view_type == "ai_pipeline":
        return len(matching) + 3 * sum(entity["type"] == "model" for entity in matching) + 2 * sum(relation_kinds[k] for k in ("trains", "evaluates"))
    if view_type == "research_methodology":
        return (len(matching) + len(csm["relations"])) if csm["source_type"] == "research_paper" else 0
    if view_type == "model_architecture":
        return 2 * len(matching)
    if view_type == "sequence_flow":
        return len(matching) + 2 * sum(relation["mode"] == "runtime" for relation in csm["relations"])
    return 0


def _connected_selection(view_type: str, csm: dict) -> list[str]:
    base = {entity["id"] for entity in csm["entities"] if _eligible(view_type, entity, csm)}
    if not base:
        return []
    flow_relations = {
        "data_flow": {"reads", "writes", "produces", "consumes", "transforms", "feeds"},
        "ai_pipeline": {"trains", "evaluates", "feeds", "transforms", "produces", "consumes", "calls"},
        "research_methodology": {"feeds", "transforms", "trains", "evaluates", "compares", "produces", "depends_on"},
        "model_architecture": {"contains", "feeds", "transforms", "calls", "depends_on", "produces"},
        "sequence_flow": {"calls", "invokes", "routes_to", "returns", "triggers", "reads", "writes"},
    }.get(view_type)
    selected = set(base)
    for relation in csm["relations"]:
        if flow_relations is not None and relation["relation"] not in flow_relations:
            continue
        if relation["source"] in base or relation["target"] in base:
            selected.add(relation["source"]); selected.add(relation["target"])
    return sorted(selected)


def _ordered(ids: Iterable[str], csm: dict) -> list[str]:
    ids = set(ids)
    outgoing: dict[str, set[str]] = defaultdict(set)
    incoming: Counter[str] = Counter()
    degree: Counter[str] = Counter()
    for relation in csm["relations"]:
        source, target = relation["source"], relation["target"]
        if source in ids and target in ids and source != target:
            outgoing[source].add(target); incoming[target] += 1; degree[source] += 1; degree[target] += 1
    queue = deque(sorted((node for node in ids if not incoming[node]), key=lambda node: (-degree[node], node)))
    result: list[str] = []
    while queue:
        node = queue.popleft()
        if node in result:
            continue
        result.append(node)
        for target in sorted(outgoing[node]):
            incoming[target] -= 1
            if incoming[target] == 0:
                queue.append(target)
    result.extend(sorted(ids - set(result), key=lambda node: (-degree[node], node)))
    return result


def _make_view(view_type: str, included: list[str], all_selected: list[str], csm: dict, audience: str, level: str, language: str, segment: tuple[int, int] | None = None) -> dict:
    entity_by_id = {entity["id"]: entity for entity in csm["entities"]}
    degree: Counter[str] = Counter()
    for relation in csm["relations"]:
        if relation["source"] in included and relation["target"] in included:
            degree[relation["source"]] += 1; degree[relation["target"]] += 1
    heroes = sorted(included, key=lambda node: (-degree[node], node))[:2]
    names = [entity_by_id[node]["name"] for node in included]
    title = _VIEW_TITLES[view_type]
    segment_text = f" segment {segment[0]} of {segment[1]}" if segment else ""
    start = names[0] if names else None; outcome = names[-1] if names else None
    key_message = f"{title}{segment_text}: {start} to {outcome}." if start and outcome else f"{title}{segment_text}."
    layout = "feedback_loop" if view_type == "ai_pipeline" and any(relation["relation"] in {"feeds", "triggers"} and relation["target"] in included and relation["source"] in included for relation in csm["relations"] if relation["target"] < relation["source"]) else _LAYOUTS[view_type]
    return {
        "view_schema_version": "1.0.0", "outcome": "diagram", "view_type": view_type,
        "audience": audience, "level": level, "language": language,
        "focus": [title] + ([f"segment {segment[0]} of {segment[1]}"] if segment else []),
        "hero_entities": heroes, "included_entities": included,
        "excluded_entities": sorted(set(all_selected) - set(included)), "layout_archetype": layout,
        "narrative": {"start": start, "transformation": "Evidence-backed interactions", "core": names[len(names)//2] if names else None, "outcome": outcome, "key_message": key_message},
        "reason": "Selected from evidenced entity and relation signals; dense content is split before rendering." if segment else "Selected from evidenced entity and relation signals.",
    }


def _insufficient(audience: str, level: str, language: str, reason: str) -> dict:
    return {
        "view_schema_version": "1.0.0", "outcome": "insufficient_evidence", "audience": audience, "level": level,
        "language": language, "focus": [], "hero_entities": [], "included_entities": [], "excluded_entities": [],
        "narrative": {"start": None, "transformation": None, "core": None, "outcome": None, "key_message": None}, "reason": reason,
    }


def _simple_flow(audience: str, level: str, language: str) -> dict:
    return {
        "view_schema_version": "1.0.0", "outcome": "simple_flow", "audience": audience, "level": level,
        "language": language, "focus": ["single script"], "hero_entities": [], "included_entities": [], "excluded_entities": [],
        "narrative": {"start": "script input", "transformation": "single evidenced execution unit", "core": "script", "outcome": "script output", "key_message": "A simple flow is more faithful than an inflated architecture."},
        "reason": "Source discovery found a small single-script project without enough evidence for a multi-component diagram.",
    }


def plan_views(csm: dict, *, audience: str = "technical", level: str = "standard", language: str = "en", requested_views: Iterable[str] | None = None) -> list[dict]:
    if not csm.get("relations"):
        if "Source discovery identified a small single-script project." in csm.get("assumptions", []):
            return [_simple_flow(audience, level, language)]
        return [_insufficient(audience, level, language, "No evidenced semantic relation can support a diagram.")]
    requested = list(requested_views or [])
    if requested:
        unknown = sorted(set(requested) - set(SUPPORTED_VIEWS))
        if unknown:
            raise ValueError(f"Unsupported v1 view type(s): {', '.join(unknown)}")
        candidates = requested
    else:
        scored = sorted(((view, _view_score(view, csm)) for view in SUPPORTED_VIEWS), key=lambda item: (-item[1], SUPPORTED_VIEWS.index(item[0])))
        candidates = [view for view, score in scored if score >= 4][:3]
    if not candidates:
        return [_insufficient(audience, level, language, "Available facts do not meet a supported view threshold.")]
    result: list[dict] = []
    limit = _MAX_NODES[level]
    for view_type in candidates:
        selected = _ordered(_connected_selection(view_type, csm), csm)
        if len(selected) < 2:
            continue
        chunks = [selected[i:i + limit] for i in range(0, len(selected), limit)]
        if len(chunks) > 1 and len(chunks[-1]) == 1:
            chunks[-2].extend(chunks.pop())
        for index, chunk in enumerate(chunks, 1):
            result.append(_make_view(view_type, chunk, selected, csm, audience, level, language, (index, len(chunks)) if len(chunks) > 1 else None))
    return result or [_insufficient(audience, level, language, "Selected view lacks two connected evidenced concepts.")]
