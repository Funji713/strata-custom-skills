"""Conservative source discovery; no architecture is invented here."""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

from .errors import SOURCE_PARSE_ERROR, UNSUPPORTED_SOURCE, VisualizerError
from .security import env_key_names

IGNORED_NAMES = {".git", "node_modules", "venv", ".venv", "dist", "build", "coverage", "__pycache__", "vendor"}
BINARY_SUFFIXES = {".png", ".jpg", ".jpeg", ".gif", ".webp", ".ico", ".zip", ".gz", ".exe", ".dll", ".so", ".pyc", ".class", ".woff", ".woff2"}
LANGUAGES = {
    ".py": "Python", ".js": "JavaScript", ".jsx": "JavaScript", ".mjs": "JavaScript",
    ".ts": "TypeScript", ".tsx": "TypeScript", ".java": "Java", ".kt": "Kotlin",
    ".go": "Go", ".rs": "Rust", ".cs": "C#", ".rb": "Ruby", ".php": "PHP",
    ".swift": "Swift", ".sql": "SQL", ".r": "R", ".scala": "Scala",
}
ENTRY_NAMES = {"main.py", "app.py", "manage.py", "server.py", "index.js", "index.ts", "main.ts", "main.js", "app.ts", "app.js", "program.cs"}
MANIFESTS = {"pyproject.toml", "requirements.txt", "package.json", "pom.xml", "build.gradle", "go.mod", "cargo.toml", "gemfile", "composer.json"}
FRAMEWORK_MARKERS = {
    "django": "Django", "flask": "Flask", "fastapi": "FastAPI", "react": "React", "next": "Next.js",
    "vue": "Vue", "angular": "Angular", "express": "Express", "nestjs": "NestJS", "spring": "Spring",
    "torch": "PyTorch", "tensorflow": "TensorFlow", "transformers": "Transformers", "sklearn": "scikit-learn",
    "pandas": "pandas", "airflow": "Apache Airflow", "spark": "Apache Spark",
}


@dataclass(frozen=True)
class DiscoveryResult:
    index: dict
    files: tuple[Path, ...]
    root: Path
    text: str | None = None


def _slug(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-") or "root"


def _relative(path: Path, root: Path) -> str:
    return path.relative_to(root).as_posix() if path != root else "."


def _walk(root: Path) -> tuple[list[Path], list[str]]:
    files: list[Path] = []
    ignored: set[str] = set()
    for path in sorted(root.rglob("*"), key=lambda p: p.as_posix().lower()):
        rel_parts = path.relative_to(root).parts
        ignored_part = next((part for part in rel_parts if part.lower() in IGNORED_NAMES), None)
        if ignored_part:
            ignored.add(f"{ignored_part}/")
            continue
        if path.is_file() and path.suffix.lower() not in BINARY_SUFFIXES:
            files.append(path)
    return files, sorted(ignored)


def _read_bounded(path: Path, limit: int = 250_000) -> str:
    try:
        return path.read_text(encoding="utf-8", errors="replace")[:limit]
    except OSError as exc:
        raise VisualizerError(SOURCE_PARSE_ERROR, f"Cannot read {path}: {exc}") from exc


def _frameworks(files: Iterable[Path]) -> list[str]:
    corpus: list[str] = []
    for path in files:
        if path.name.lower() in MANIFESTS:
            corpus.append(_read_bounded(path, 100_000).lower())
    joined = "\n".join(corpus)
    return sorted({label for marker, label in FRAMEWORK_MARKERS.items() if re.search(rf"\b{re.escape(marker)}\b", joined)})


def _subsystems(root: Path, files: list[Path]) -> list[dict]:
    buckets: dict[str, list[Path]] = {}
    for path in files:
        rel = path.relative_to(root)
        top = rel.parts[0] if len(rel.parts) > 1 else "root"
        buckets.setdefault(top, []).append(path)
    meaningful = []
    for name, members in sorted(buckets.items()):
        code_count = sum(member.suffix.lower() in LANGUAGES for member in members)
        has_manifest = any(member.name.lower() in MANIFESTS for member in members)
        if name == "root" or code_count or has_manifest:
            meaningful.append({
                "id": f"project://subsystem/{_slug(name)}",
                "name": root.name if name == "root" else name,
                "path": "." if name == "root" else name,
                "description": f"Evidence-bearing source boundary ({code_count} code files)",
            })
    return meaningful


def _is_monorepo(root: Path, files: list[Path]) -> bool:
    manifests = [p for p in files if p.name.lower() in MANIFESTS]
    distinct_parents = {p.relative_to(root).parts[0] for p in manifests if len(p.relative_to(root).parts) > 1}
    package = root / "package.json"
    if package.exists():
        try:
            data = json.loads(_read_bounded(package))
            if data.get("workspaces"):
                return True
        except json.JSONDecodeError:
            pass
    return len(distinct_parents) >= 2


def discover_repository(root: Path) -> DiscoveryResult:
    root = root.resolve()
    if not root.is_dir():
        raise VisualizerError(UNSUPPORTED_SOURCE, f"Repository source is not a directory: {root}")
    files, ignored = _walk(root)
    languages = sorted({LANGUAGES[p.suffix.lower()] for p in files if p.suffix.lower() in LANGUAGES})
    entries = sorted(_relative(p, root) for p in files if p.name.lower() in ENTRY_NAMES)
    manifests = sorted(_relative(p, root) for p in files if p.name.lower() in MANIFESTS)
    env_notes: list[str] = []
    for path in files:
        if path.name == ".env" or path.name.startswith(".env."):
            keys = env_key_names(path)
            env_notes.append(f"Secret-bearing file {_relative(path, root)} exposes key names only: {', '.join(keys) if keys else 'none detected'}")
    high = sorted(dict.fromkeys(manifests + entries))
    low = sorted(_relative(p, root) for p in files if p.name.lower().startswith("readme") or any(part.lower() in {"test", "tests", "example", "examples"} for part in p.relative_to(root).parts))
    structure = "monorepo" if _is_monorepo(root, files) else ("single_project" if files else "unknown")
    index = {
        "schema_version": "1.0.0", "source_type": "software_project", "project_structure": structure,
        "title": root.name, "languages": languages, "frameworks": _frameworks(files), "entry_points": entries,
        "subsystems": _subsystems(root, files), "high_priority_paths": high, "ignored_paths": ignored,
        "low_priority_paths": low, "sections": [], "figures": [], "equations": [], "tables": [],
        "analysis_notes": env_notes,
    }
    return DiscoveryResult(index=index, files=tuple(files), root=root)


def _extract_pdf(path: Path) -> str:
    try:
        from pypdf import PdfReader
    except ImportError as exc:
        raise VisualizerError(UNSUPPORTED_SOURCE, "PDF input requires the optional pypdf package") from exc
    try:
        return "\n".join(page.extract_text() or "" for page in PdfReader(str(path)).pages)
    except Exception as exc:
        raise VisualizerError(SOURCE_PARSE_ERROR, f"Cannot parse PDF: {exc}") from exc


def discover_document(path: Path) -> DiscoveryResult:
    path = path.resolve()
    if path.suffix.lower() == ".pdf":
        text = _extract_pdf(path)
    elif path.suffix.lower() in {".md", ".txt", ".rst"}:
        text = _read_bounded(path, 2_000_000)
    else:
        raise VisualizerError(UNSUPPORTED_SOURCE, f"Unsupported document type: {path.suffix}")
    headings = re.findall(r"(?m)^#{1,6}\s+(.+?)\s*$", text)
    research_markers = sum(bool(re.search(rf"(?im)^#*\s*{term}\b", text)) for term in ("abstract", "method", "methodology", "experiment", "results", "conclusion"))
    source_type = "research_paper" if research_markers >= 2 else "technical_document"
    figures = [line.strip()[:200] for line in text.splitlines() if re.match(r"(?i)^\s*(figure|fig\.)\s*\d+", line)][:50]
    tables = [line.strip()[:200] for line in text.splitlines() if re.match(r"(?i)^\s*table\s*\d+", line)][:50]
    equations = [line.strip()[:200] for line in text.splitlines() if "$$" in line or re.match(r"^\s*\\\[", line)][:50]
    index = {
        "schema_version": "1.0.0", "source_type": source_type, "project_structure": "not_applicable",
        "title": headings[0] if headings else path.stem, "languages": [], "frameworks": [], "entry_points": [],
        "subsystems": [], "high_priority_paths": [path.name], "ignored_paths": [], "low_priority_paths": [],
        "sections": list(dict.fromkeys(headings)), "figures": figures, "equations": equations, "tables": tables,
        "analysis_notes": [],
    }
    return DiscoveryResult(index=index, files=(path,), root=path.parent, text=text)


def discover(source: str | Path) -> DiscoveryResult:
    path = Path(source)
    if not path.exists():
        raise VisualizerError(UNSUPPORTED_SOURCE, f"Source does not exist: {path}")
    return discover_repository(path) if path.is_dir() else discover_document(path)
