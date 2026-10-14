"""Evidence-first extraction for repositories and research text."""

from __future__ import annotations

import ast
import hashlib
import json
import re
import sys
from pathlib import Path
from typing import Iterable

from .discovery import DiscoveryResult
from .security import redact_text

_STDLIB = set(getattr(sys, "stdlib_module_names", ())) | {"typing", "pathlib", "dataclasses", "json", "re", "os", "sys"}
_DB_NAMES = {"postgres", "postgresql", "psycopg", "mysql", "mariadb", "sqlite", "mongodb", "mongo", "redis", "dynamodb"}
_AI_NAMES = {"torch", "pytorch", "tensorflow", "keras", "transformers", "sklearn", "xgboost", "lightgbm", "onnx"}
_DATA_NAMES = {"pandas", "polars", "spark", "pyspark", "airflow", "dbt", "numpy"}


def _slug(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-") or "unnamed"


def _fact_id(subject: str, relation: str, obj: str, source: str, location: str = "") -> str:
    digest = hashlib.sha1(f"{subject}|{relation}|{obj}|{source}|{location}".encode()).hexdigest()[:14]
    return f"fact://{relation}/{digest}"


def _evidence(kind: str, source: str, excerpt: str | None, location: str | None = None, symbol: str | None = None) -> dict:
    raw = excerpt or ""
    clean = redact_text(raw)[:500]
    return {"type": kind, "source": source, "symbol": symbol, "location": location, "excerpt": clean or None, "redacted": clean != raw}


def _fact(subject: str, relation: str, obj: str, mode: str, level: str, evidence: dict, notes: Iterable[str] = ()) -> dict:
    return {
        "id": _fact_id(subject, relation, obj, evidence["source"], evidence.get("location") or ""),
        "statement": f"{subject} {relation.replace('_', ' ')} {obj}", "subject": subject, "relation": relation,
        "object": obj, "relation_mode": mode, "evidence_level": level, "evidence": [evidence], "notes": list(notes),
    }


def _subsystem_for(path: Path, discovery: DiscoveryResult) -> tuple[str, str]:
    rel = path.relative_to(discovery.root)
    top = rel.parts[0] if len(rel.parts) > 1 else "root"
    for subsystem in discovery.index["subsystems"]:
        if subsystem.get("path") == ("." if top == "root" else top):
            return subsystem["id"], subsystem["name"]
    return "project://subsystem/root", discovery.root.name


def _dependency_id(name: str) -> tuple[str, str, list[str]]:
    normalized = name.split(".")[0].split("/")[-1].lower().replace("_", "-")
    tags: list[str] = []
    if normalized in _DB_NAMES:
        return f"project://storage/{_slug(normalized)}", "storage", ["slot=database", f"name={normalized}"]
    if normalized in _AI_NAMES:
        tags.append("ai")
    if normalized in _DATA_NAMES:
        tags.append("data")
    return f"project://external/{_slug(normalized)}", "external_service", [f"name={normalized}", *tags]


def _python_facts(path: Path, discovery: DiscoveryResult, text: str) -> list[dict]:
    facts: list[dict] = []
    rel = path.relative_to(discovery.root).as_posix()
    subject, subject_name = _subsystem_for(path, discovery)
    try:
        tree = ast.parse(text, filename=rel)
    except SyntaxError:
        return facts
    imports: dict[str, str] = {}
    for node in ast.walk(tree):
        if isinstance(node, (ast.Import, ast.ImportFrom)):
            names = [alias.name for alias in node.names] if isinstance(node, ast.Import) else ([node.module] if node.module else [])
            for full_name in filter(None, names):
                base = full_name.split(".")[0]
                imports[base] = full_name
                if isinstance(node, ast.ImportFrom) and node.level:
                    continue
                local_dir = discovery.root / base
                local_module = discovery.root / f"{base}.py"
                if local_dir.exists() or local_module.exists():
                    target = f"project://subsystem/{_slug(base)}"
                    notes = [f"subject_name={subject_name}", f"object_name={base}", "subject_type=component", "object_type=component"]
                    facts.append(_fact(subject, "imports", target, "static", "verified", _evidence("declaration", rel, ast.get_source_segment(text, node), f"line {node.lineno}"), notes))
                elif base not in _STDLIB and not base.startswith("_"):
                    target, target_type, tags = _dependency_id(base)
                    notes = [f"subject_name={subject_name}", f"object_name={base}", "subject_type=component", f"object_type={target_type}", *tags]
                    facts.append(_fact(subject, "depends_on", target, "static", "verified", _evidence("declaration", rel, ast.get_source_segment(text, node), f"line {node.lineno}"), notes))
        if isinstance(node, (ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef)):
            lowered = node.name.lower()
            if isinstance(node, ast.ClassDef) and any(term in lowered for term in ("model", "encoder", "decoder", "classifier", "network", "transformer")):
                target = f"project://model/{_slug(node.name)}"
                notes = [f"subject_name={subject_name}", f"object_name={node.name}", "subject_type=component", "object_type=model", "ai"]
                facts.append(_fact(subject, "contains", target, "static", "verified", _evidence("declaration", rel, f"class {node.name}", f"line {node.lineno}", node.name), notes))
            elif any(term in lowered for term in ("train", "predict", "infer", "preprocess", "transform", "extract", "evaluate", "load_data")):
                target = f"project://process/{_slug(node.name)}"
                relation = "trains" if "train" in lowered else ("evaluates" if "evaluat" in lowered else "contains")
                tags = ["ai"] if any(term in lowered for term in ("train", "predict", "infer")) else ["data"]
                notes = [f"subject_name={subject_name}", f"object_name={node.name}", "subject_type=component", "object_type=process", *tags]
                facts.append(_fact(subject, relation, target, "runtime" if relation != "contains" else "static", "verified", _evidence("declaration", rel, f"def {node.name}", f"line {node.lineno}", node.name), notes))
        if isinstance(node, ast.Call):
            name = ""
            if isinstance(node.func, ast.Attribute) and isinstance(node.func.value, ast.Name):
                name = f"{node.func.value.id}.{node.func.attr}"
            elif isinstance(node.func, ast.Name):
                name = node.func.id
            base = name.split(".")[0]
            if base in imports and (base not in _STDLIB):
                target, target_type, tags = _dependency_id(base)
                notes = [f"subject_name={subject_name}", f"object_name={base}", "subject_type=component", f"object_type={target_type}", *tags]
                facts.append(_fact(subject, "calls", target, "runtime", "verified", _evidence("runtime_reference", rel, ast.get_source_segment(text, node), f"line {node.lineno}", name), notes))
            if isinstance(node.func, ast.Attribute) and node.func.attr.lower() in {"read_csv", "read_parquet", "read_json", "load", "fit", "predict", "transform", "evaluate"}:
                op = node.func.attr.lower()
                process = f"project://process/{_slug(op)}"
                relation = "reads" if op.startswith("read") or op == "load" else ("trains" if op == "fit" else "transforms")
                notes = [f"subject_name={subject_name}", f"object_name={op}", "subject_type=component", "object_type=process", "data"]
                facts.append(_fact(subject, relation, process, "runtime", "verified", _evidence("runtime_reference", rel, ast.get_source_segment(text, node), f"line {node.lineno}", name), notes))
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            for decorator in node.decorator_list:
                if isinstance(decorator, ast.Call) and isinstance(decorator.func, ast.Attribute) and decorator.func.attr.lower() in {"route", "get", "post", "put", "delete", "patch"}:
                    route = None
                    if decorator.args and isinstance(decorator.args[0], ast.Constant) and isinstance(decorator.args[0].value, str):
                        route = decorator.args[0].value
                    route_name = route or node.name
                    target = f"project://interface/{_slug(route_name)}"
                    notes = [f"subject_name={subject_name}", f"object_name={route_name}", "subject_type=service", "object_type=interface", "api"]
                    facts.append(_fact(subject, "routes_to", target, "runtime", "verified", _evidence("route_definition", rel, ast.get_source_segment(text, decorator), f"line {node.lineno}", node.name), notes))
    return facts


def _javascript_facts(path: Path, discovery: DiscoveryResult, text: str) -> list[dict]:
    facts: list[dict] = []
    rel = path.relative_to(discovery.root).as_posix()
    subject, subject_name = _subsystem_for(path, discovery)
    for match in re.finditer(r"(?m)(?:import\s+.+?\s+from\s+|require\s*\(\s*)['\"]([^'\"]+)['\"]", text):
        name = match.group(1)
        if name.startswith("."):
            continue
        else:
            target, target_type, tags = _dependency_id(name)
        notes = [f"subject_name={subject_name}", f"object_name={name.split('/')[-1]}", "subject_type=component", f"object_type={target_type}", *tags]
        facts.append(_fact(subject, "imports", target, "static", "verified", _evidence("declaration", rel, match.group(0), f"offset {match.start()}"), notes))
    for match in re.finditer(r"\b(fetch|axios\.(?:get|post|put|delete|patch))\s*\(\s*['\"]([^'\"]+)", text):
        target = f"project://interface/{_slug(match.group(2))}"
        notes = [f"subject_name={subject_name}", f"object_name={match.group(2)}", "subject_type=component", "object_type=interface", "api"]
        facts.append(_fact(subject, "calls", target, "runtime", "verified", _evidence("runtime_reference", rel, match.group(0), f"offset {match.start()}"), notes))
    for match in re.finditer(r"\b(?:app|router)\.(get|post|put|delete|patch)\s*\(\s*['\"]([^'\"]+)", text):
        target = f"project://interface/{_slug(match.group(2))}"
        notes = [f"subject_name={subject_name}", f"object_name={match.group(2)}", "subject_type=service", "object_type=interface", "api"]
        facts.append(_fact(subject, "routes_to", target, "runtime", "verified", _evidence("route_definition", rel, match.group(0), f"offset {match.start()}"), notes))
    return facts


def _manifest_facts(path: Path, discovery: DiscoveryResult, text: str) -> list[dict]:
    rel = path.relative_to(discovery.root).as_posix()
    subject, subject_name = _subsystem_for(path, discovery)
    dependencies: set[str] = set()
    if path.name.lower() == "package.json":
        try:
            data = json.loads(text)
            dependencies.update(data.get("dependencies", {}))
            dependencies.update(data.get("devDependencies", {}))
        except json.JSONDecodeError:
            return []
    elif path.name.lower() == "requirements.txt":
        dependencies.update(re.split(r"[<>=!~\[]", line.strip(), maxsplit=1)[0] for line in text.splitlines() if line.strip() and not line.lstrip().startswith("#"))
    else:
        dependencies.update(marker for marker in (*_DB_NAMES, *_AI_NAMES, *_DATA_NAMES, "django", "fastapi", "flask", "react", "express") if re.search(rf"(?i)\b{re.escape(marker)}\b", text))
    facts: list[dict] = []
    for name in sorted(filter(None, dependencies)):
        target, target_type, tags = _dependency_id(name)
        notes = [f"subject_name={subject_name}", f"object_name={name}", "subject_type=component", f"object_type={target_type}", *tags]
        facts.append(_fact(subject, "depends_on", target, "static", "verified", _evidence("dependency_manifest", rel, name, "manifest"), notes))
    return facts


def _documentation_facts(path: Path, discovery: DiscoveryResult, text: str) -> list[dict]:
    if not path.name.lower().startswith("readme"):
        return []
    rel = path.relative_to(discovery.root).as_posix()
    subject, subject_name = _subsystem_for(path, discovery)
    facts: list[dict] = []
    for database in sorted(_DB_NAMES):
        match = re.search(rf"(?i)\b{re.escape(database)}\b", text)
        if match:
            target, target_type, tags = _dependency_id(database)
            notes = [f"subject_name={subject_name}", f"object_name={database}", "subject_type=component", f"object_type={target_type}", *tags]
            facts.append(_fact(subject, "depends_on", target, "static", "supported", _evidence("documentation", rel, text[max(0, match.start()-60):match.end()+60], f"offset {match.start()}"), notes))
    return facts


def extract_repository_facts(discovery: DiscoveryResult) -> dict:
    facts: list[dict] = []
    for path in discovery.files:
        rel = path.relative_to(discovery.root).as_posix()
        if rel in discovery.index.get("low_priority_paths", []) and not path.name.lower().startswith("readme"):
            continue
        try:
            text = path.read_text(encoding="utf-8", errors="replace")[:500_000]
        except OSError:
            continue
        suffix = path.suffix.lower()
        if suffix == ".py":
            facts.extend(_python_facts(path, discovery, text))
        elif suffix in {".js", ".jsx", ".ts", ".tsx", ".mjs"}:
            facts.extend(_javascript_facts(path, discovery, text))
        if path.name.lower() in {"package.json", "requirements.txt", "pyproject.toml", "pom.xml", "build.gradle", "go.mod", "cargo.toml"}:
            facts.extend(_manifest_facts(path, discovery, text))
        facts.extend(_documentation_facts(path, discovery, text))
    deduped = {fact["id"]: fact for fact in facts}
    return {"schema_version": "1.0.0", "facts": [deduped[key] for key in sorted(deduped)]}


def _paper_type(name: str) -> str:
    lowered = name.lower()
    if "dataset" in lowered or "data" == lowered:
        return "dataset"
    if any(token in lowered for token in ("encoder", "decoder", "model", "transformer", "network", "attention")):
        return "model"
    if any(token in lowered for token in ("metric", "accuracy", "f1", "auc", "evaluation")):
        return "metric"
    if any(token in lowered for token in ("output", "prediction", "result")):
        return "output"
    return "process"


def extract_document_facts(discovery: DiscoveryResult) -> dict:
    text = discovery.text or ""
    source = discovery.files[0].name
    facts: list[dict] = []
    for line_no, line in enumerate(text.splitlines(), 1):
        clean = re.sub(r"^[#*>\s-]+", "", line).strip()
        if not clean:
            continue
        if "->" in clean or "→" in clean:
            parts = [part.strip(" .:;[]()") for part in re.split(r"\s*(?:->|→)\s*", clean) if part.strip(" .:;[]()")]
            if 2 <= len(parts) <= 10:
                for left, right in zip(parts, parts[1:]):
                    subject = f"paper://concept/{_slug(left)}"; obj = f"paper://concept/{_slug(right)}"
                    notes = [f"subject_name={left}", f"object_name={right}", f"subject_type={_paper_type(left)}", f"object_type={_paper_type(right)}", "research"]
                    facts.append(_fact(subject, "feeds", obj, "conceptual", "verified", _evidence("documentation", source, clean, f"line {line_no}"), notes))
        pattern = re.search(r"(?i)^(.{2,80}?)\s+(uses|feeds|produces|transforms|trains|evaluates|compares)\s+(.{2,80}?)[.;]?$", clean)
        if pattern:
            left, verb, right = pattern.groups()
            relation = {"uses": "depends_on"}.get(verb.lower(), verb.lower())
            subject = f"paper://concept/{_slug(left)}"; obj = f"paper://concept/{_slug(right)}"
            notes = [f"subject_name={left}", f"object_name={right}", f"subject_type={_paper_type(left)}", f"object_type={_paper_type(right)}", "research"]
            facts.append(_fact(subject, relation, obj, "experimental" if relation in {"trains", "evaluates", "compares"} else "conceptual", "supported", _evidence("documentation", source, clean, f"line {line_no}"), notes))
    deduped = {fact["id"]: fact for fact in facts}
    return {"schema_version": "1.0.0", "facts": [deduped[key] for key in sorted(deduped)]}


def extract_facts(discovery: DiscoveryResult) -> dict:
    if discovery.index["source_type"] == "software_project":
        return extract_repository_facts(discovery)
    return extract_document_facts(discovery)
