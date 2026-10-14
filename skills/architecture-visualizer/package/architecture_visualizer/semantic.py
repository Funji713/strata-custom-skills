"""Canonical Semantic Model generation and conflict preservation."""

from __future__ import annotations

import hashlib
from collections import defaultdict

from .errors import SEMANTIC_VALIDATION_FAILURE, VisualizerError

_ENTITY_TYPES = {"actor", "interface", "component", "service", "process", "model", "data", "dataset", "storage", "external_service", "experiment", "metric", "objective", "output", "concept"}


def _notes(fact: dict) -> dict[str, str | bool]:
    parsed: dict[str, str | bool] = {}
    for note in fact.get("notes", []):
        if "=" in note:
            key, value = note.split("=", 1)
            parsed[key] = value
        else:
            parsed[note] = True
    return parsed


def _infer_type(identifier: str, explicit: str | None) -> str:
    if explicit in _ENTITY_TYPES:
        return explicit
    mapping = {"subsystem": "component", "interface": "interface", "model": "model", "process": "process", "storage": "storage", "external": "external_service", "concept": "concept"}
    prefix = identifier.split("//", 1)[-1].split("/", 1)[0]
    return mapping.get(prefix, "concept")


def _infer_name(identifier: str, explicit: str | None) -> str:
    if explicit:
        return explicit.strip()
    return identifier.rstrip("/").split("/")[-1].replace("-", " ").replace("_", " ").title()


def build_semantic_model(source_index: dict, facts_document: dict) -> dict:
    facts = facts_document.get("facts", [])
    entities: dict[str, dict] = {}
    relations: list[dict] = []
    for fact in facts:
        notes = _notes(fact)
        for side, name_key, type_key in (("subject", "subject_name", "subject_type"), ("object", "object_name", "object_type")):
            identifier = fact[side]
            entity = entities.setdefault(identifier, {
                "id": identifier, "type": _infer_type(identifier, str(notes.get(type_key, ""))),
                "name": _infer_name(identifier, str(notes.get(name_key, ""))), "responsibility": None,
                "subsystem": fact["subject"] if side == "object" and fact["subject"].startswith("project://subsystem/") else None,
                "evidence_refs": [], "tags": [],
            })
            entity["evidence_refs"].append(fact["id"])
            for tag in ("ai", "data", "api", "research"):
                if notes.get(tag) and tag not in entity["tags"]:
                    entity["tags"].append(tag)
            slot = notes.get("slot")
            if isinstance(slot, str) and f"slot:{slot}" not in entity["tags"]:
                entity["tags"].append(f"slot:{slot}")
        relation_digest = hashlib.sha1(f"{fact['subject']}|{fact['relation']}|{fact['object']}|{fact.get('relation_mode', 'conceptual')}".encode()).hexdigest()[:14]
        relations.append({
            "id": f"relation://{fact['relation']}/{relation_digest}", "source": fact["subject"], "target": fact["object"],
            "relation": fact["relation"], "mode": fact.get("relation_mode", "conceptual"), "evidence_refs": [fact["id"]], "label": None,
        })
    for entity in entities.values():
        entity["evidence_refs"] = sorted(set(entity["evidence_refs"]))
        entity["tags"] = sorted(set(entity["tags"]))
        if entity["type"] == "component":
            entity["responsibility"] = "Evidence-bearing subsystem"
        elif entity["type"] == "interface":
            entity["responsibility"] = "Observed request or route boundary"
        elif entity["type"] == "model":
            entity["responsibility"] = "Declared model responsibility"
        elif entity["type"] == "process":
            entity["responsibility"] = "Observed transformation or execution step"
    merged_relations: dict[tuple, dict] = {}
    for relation in relations:
        key = (relation["source"], relation["target"], relation["relation"], relation["mode"])
        if key in merged_relations:
            merged_relations[key]["evidence_refs"].extend(relation["evidence_refs"])
            merged_relations[key]["evidence_refs"] = sorted(set(merged_relations[key]["evidence_refs"]))
        else:
            merged_relations[key] = relation

    conflicts: list[dict] = []
    slot_candidates: dict[tuple[str, str], list[tuple[str, dict]]] = defaultdict(list)
    fact_by_id = {fact["id"]: fact for fact in facts}
    for entity in entities.values():
        for tag in entity["tags"]:
            if tag.startswith("slot:") and entity.get("subsystem"):
                slot_candidates[(entity["subsystem"], tag[5:])].append((entity["id"], entity))
    for (owner, slot), candidates in sorted(slot_candidates.items()):
        ids = sorted({item[0] for item in candidates})
        if len(ids) < 2:
            continue
        evidence_refs = sorted({ref for _, item in candidates for ref in item["evidence_refs"]})
        ranked = sorted(ids, key=lambda identifier: min((0 if fact_by_id[ref]["evidence_level"] == "verified" else 1 for ref in entities[identifier]["evidence_refs"]), default=2))
        best_rank = min((0 if fact_by_id[ref]["evidence_level"] == "verified" else 1 for ref in entities[ranked[0]]["evidence_refs"]), default=2)
        equally_best = [identifier for identifier in ranked if min((0 if fact_by_id[ref]["evidence_level"] == "verified" else 1 for ref in entities[identifier]["evidence_refs"]), default=2) == best_rank]
        resolved = len(equally_best) == 1
        digest = hashlib.sha1(f"{owner}|{slot}".encode()).hexdigest()[:12]
        conflicts.append({
            "id": f"conflict://{slot}/{digest}", "status": "resolved" if resolved else "unresolved", "candidates": ids,
            "selected": equally_best[0] if resolved else None,
            "resolution_basis": "Executable/dependency evidence outranks documentation." if resolved else "Evidence levels do not distinguish the candidates.",
            "evidence_refs": evidence_refs,
        })

    entity_ids = set(entities)
    dangling = [r["id"] for r in merged_relations.values() if r["source"] not in entity_ids or r["target"] not in entity_ids]
    if dangling:
        raise VisualizerError(SEMANTIC_VALIDATION_FAILURE, f"Dangling semantic relations: {dangling}")
    summary = None if not entities else f"{len(entities)} evidenced concepts and {len(merged_relations)} evidenced relations"
    small_script = (
        source_index.get("source_type") == "software_project"
        and source_index.get("project_structure") == "single_project"
        and len(source_index.get("entry_points", [])) <= 1
        and len(source_index.get("subsystems", [])) <= 1
        and len(facts) <= 2
    )
    return {
        "semantic_schema_version": "1.0.0", "source_type": source_index["source_type"], "summary": summary,
        "entities": [entities[key] for key in sorted(entities)],
        "relations": [merged_relations[key] for key in sorted(merged_relations)], "conflicts": conflicts,
        "assumptions": (["Source discovery identified a small single-script project."] if small_script else []),
        "uncertainties": (["No important semantic relations were evidenced."] if not merged_relations else []),
    }
