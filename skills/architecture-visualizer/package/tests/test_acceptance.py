from __future__ import annotations

import hashlib
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from architecture_visualizer.discovery import discover
from architecture_visualizer.evidence import extract_facts
from architecture_visualizer.pipeline import PipelineOptions, run_pipeline
from architecture_visualizer.layout import layout_render_ir
from architecture_visualizer.render_ir import build_render_ir
from architecture_visualizer.security import REDACTED, contains_secret, redact_text
from architecture_visualizer.semantic import build_semantic_model
from architecture_visualizer.svg import render_svg
from architecture_visualizer.validation import validate_layout
from architecture_visualizer.views import SUPPORTED_VIEWS, plan_views

TEST_TMP = Path(__file__).resolve().parent / ".tmp"
TEST_TMP.mkdir(exist_ok=True)


def write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def rich_csm(count: int = 0) -> dict:
    entities = [
        ("paper://component/client", "component", "Client", []),
        ("paper://interface/api", "interface", "API", []),
        ("paper://component/service", "service", "Service", []),
        ("paper://storage/store", "storage", "Store", ["data"]),
        ("paper://dataset/training", "dataset", "Training Dataset", ["data", "research"]),
        ("paper://process/preprocess", "process", "Preprocess", ["data", "ai", "research"]),
        ("paper://model/encoder", "model", "Encoder", ["ai", "research"]),
        ("paper://model/decoder", "model", "Decoder", ["ai", "research"]),
        ("paper://objective/loss", "objective", "Loss", ["ai", "research"]),
        ("paper://output/prediction", "output", "Prediction", ["ai", "research"]),
        ("paper://metric/accuracy", "metric", "Accuracy", ["research"]),
        ("paper://external/tool", "external_service", "External Tool", []),
    ]
    relations = [
        ("client", "api", "calls", "runtime"), ("api", "service", "routes_to", "runtime"),
        ("service", "store", "reads", "runtime"), ("training", "preprocess", "feeds", "conceptual"),
        ("preprocess", "encoder", "trains", "experimental"), ("encoder", "decoder", "feeds", "conceptual"),
        ("decoder", "prediction", "produces", "conceptual"), ("prediction", "accuracy", "evaluates", "experimental"),
        ("encoder", "loss", "depends_on", "conceptual"), ("service", "tool", "invokes", "runtime"),
    ]
    if count:
        entities = [(f"paper://process/step-{i}", "process", f"Step {i}", ["data", "research"]) for i in range(count)]
        relations = [(f"step-{i}", f"step-{i+1}", "feeds", "conceptual") for i in range(count - 1)]
    entity_docs = [{"id": i, "type": t, "name": n, "responsibility": "Grounded role", "subsystem": None, "evidence_refs": [f"fact://{i}"], "tags": tags} for i, t, n, tags in entities]
    lookup = {identifier.rsplit("/", 1)[-1]: identifier for identifier, *_ in entities}
    relation_docs = []
    for index, (source, target, relation, mode) in enumerate(relations):
        relation_docs.append({"id": f"relation://{index}", "source": lookup[source], "target": lookup[target], "relation": relation, "mode": mode, "evidence_refs": [f"fact://relation/{index}"], "label": None})
    return {"semantic_schema_version": "1.0.0", "source_type": "research_paper", "summary": "fixture", "entities": entity_docs, "relations": relation_docs, "conflicts": [], "assumptions": [], "uncertainties": []}


class AcceptanceTests(unittest.TestCase):
    def test_provider_and_quoted_secrets_are_redacted(self):
        samples = [
            '"api_key": "' + 'value-that-must-not-survive' + '"',
            "AKIA" + "A" * 16,
            "AIza" + "A" * 24,
            "Bearer " + "opaque-token-value",
            "postgres://name:password-value@example.test/db",
        ]
        for sample in samples:
            clean = redact_text(sample)
            self.assertIn(REDACTED, clean)
            self.assertFalse(contains_secret(clean))

    def test_django_react_system_sequence_redaction_and_stability(self):
        with tempfile.TemporaryDirectory(dir=TEST_TMP) as tmp:
            root = Path(tmp) / "app"
            secret = "unit-test-" + "secret-value"
            write(root / "backend" / "requirements.txt", "django\npsycopg\nrequests\n")
            write(root / "backend" / "app.py", f"from django.urls import path\nimport requests\ndef items():\n    return requests.get('https://service.example/items', headers={{'Authorization': 'Bearer {secret}'}})\n")
            write(root / "frontend" / "package.json", json.dumps({"dependencies": {"react": "1.0.0", "axios": "1.0.0"}}))
            write(root / "frontend" / "index.js", "import React from 'react'; fetch('/items');")
            write(root / ".env", f"API_KEY={secret}\nDATABASE_URL=postgres://name:{secret}@localhost/db\n")
            out1, out2 = Path(tmp) / "out1", Path(tmp) / "out2"
            options = PipelineOptions(views=("system_architecture", "sequence_flow"))
            first = run_pipeline(root, out1, options); second = run_pipeline(root, out2, options)
            self.assertTrue(first["rendered_views"])
            self.assertEqual(first["rendered_views"], second["rendered_views"])
            svg1 = next(out1.rglob("architecture-editable.svg")).read_bytes()
            svg2 = next(out2.rglob("architecture-editable.svg")).read_bytes()
            self.assertEqual(hashlib.sha256(svg1).hexdigest(), hashlib.sha256(svg2).hexdigest())
            all_artifacts = "\n".join(path.read_text(encoding="utf-8") for path in out1.rglob("*") if path.is_file())
            self.assertNotIn(secret, all_artifacts)
            self.assertIn("API_KEY", all_artifacts)
            facts = json.loads((out1 / "facts-evidence.json").read_text(encoding="utf-8"))["facts"]
            self.assertTrue(any(f["relation_mode"] == "static" for f in facts))
            self.assertTrue(any(f["relation_mode"] == "runtime" for f in facts))
            self.assertTrue(all(json.loads(path.read_text(encoding="utf-8"))["passed"] for path in out1.rglob("validation-report.json")))

    def test_pure_ml_prefers_ai_without_invented_ui_or_database(self):
        with tempfile.TemporaryDirectory(dir=TEST_TMP) as tmp:
            root = Path(tmp) / "ml"
            write(root / "requirements.txt", "torch\npandas\n")
            write(root / "main.py", "import torch\nimport pandas\nclass EncoderModel: pass\ndef train_model():\n    return torch.zeros(1)\n")
            out = Path(tmp) / "out"; summary = run_pipeline(root, out)
            types = [item["view_type"] for item in summary["rendered_views"]]
            self.assertIn("ai_pipeline", types)
            semantic = json.loads((out / "semantic-model.json").read_text(encoding="utf-8"))
            self.assertFalse(any(entity["type"] in {"interface", "storage"} for entity in semantic["entities"]))

    def test_research_document_supports_methodology_and_model_views(self):
        with tempfile.TemporaryDirectory(dir=TEST_TMP) as tmp:
            paper = Path(tmp) / "paper.md"
            write(paper, "# Grounded Transformer\n## Abstract\nA method.\n## Methodology\nDataset -> Preprocess -> Encoder -> Attention Model -> Decoder -> Prediction\n## Experiments\nPrediction evaluates Accuracy.\n## Conclusion\nDone.\n")
            out = Path(tmp) / "out"
            summary = run_pipeline(paper, out, PipelineOptions(audience="academic", views=("research_methodology", "model_architecture")))
            self.assertEqual({item["view_type"] for item in summary["rendered_views"]}, {"research_methodology", "model_architecture"})

    def test_etl_prefers_data_flow(self):
        with tempfile.TemporaryDirectory(dir=TEST_TMP) as tmp:
            root = Path(tmp) / "etl"
            write(root / "requirements.txt", "pandas\n")
            write(root / "main.py", "import pandas as pd\ndef transform_data():\n    frame = pd.read_csv('input.csv')\n    return frame.transform(lambda x: x)\n")
            summary = run_pipeline(root, Path(tmp) / "out")
            self.assertIn("data_flow", [item["view_type"] for item in summary["rendered_views"]])

    def test_small_script_returns_simple_flow(self):
        with tempfile.TemporaryDirectory(dir=TEST_TMP) as tmp:
            root = Path(tmp) / "script"; write(root / "main.py", "print('hello')\n")
            summary = run_pipeline(root, Path(tmp) / "out")
            self.assertEqual(summary["status"], "simple_flow")
            self.assertFalse(summary["rendered_views"])

    def test_monorepo_boundaries_and_incomplete_repository(self):
        with tempfile.TemporaryDirectory(dir=TEST_TMP) as tmp:
            root = Path(tmp) / "mono"
            write(root / "apps" / "package.json", "{\"dependencies\": {\"react\": \"1\"}}")
            write(root / "services" / "requirements.txt", "fastapi\n")
            result = discover(root)
            self.assertEqual(result.index["project_structure"], "monorepo")
            self.assertGreaterEqual(len(result.index["subsystems"]), 2)
            empty = Path(tmp) / "empty"; empty.mkdir()
            summary = run_pipeline(empty, Path(tmp) / "empty-out")
            self.assertEqual(summary["status"], "insufficient_evidence")

    def test_readme_code_conflict_is_preserved_and_resolved_by_evidence(self):
        with tempfile.TemporaryDirectory(dir=TEST_TMP) as tmp:
            root = Path(tmp) / "conflict"
            write(root / "pyproject.toml", "dependencies = ['psycopg']\n")
            write(root / "README.md", "The application uses MySQL for persistence.\n")
            discovery = discover(root); facts = extract_facts(discovery); csm = build_semantic_model(discovery.index, facts)
            self.assertEqual(len(csm["conflicts"]), 1)
            self.assertEqual(csm["conflicts"][0]["status"], "resolved")
            self.assertIn("psycopg", csm["conflicts"][0]["selected"])

    def test_static_import_is_not_runtime_invocation(self):
        with tempfile.TemporaryDirectory(dir=TEST_TMP) as tmp:
            root = Path(tmp) / "static"; write(root / "main.py", "import requests\n")
            facts = extract_facts(discover(root))["facts"]
            self.assertTrue(any(f["relation"] == "depends_on" and f["relation_mode"] == "static" for f in facts))
            self.assertFalse(any(f["relation"] == "calls" for f in facts))

    def test_all_six_view_types_and_dense_split(self):
        csm = rich_csm()
        views = plan_views(csm, requested_views=SUPPORTED_VIEWS)
        self.assertEqual({view["view_type"] for view in views}, set(SUPPORTED_VIEWS))
        package_root = Path(__file__).resolve().parents[1]
        profile = json.loads((package_root / "profiles" / "ppt-16x9.json").read_text(encoding="utf-8"))
        theme = json.loads((package_root / "themes" / "research-tech-light.json").read_text(encoding="utf-8"))
        for view in views:
            render_ir = build_render_ir(view, csm)
            layout = layout_render_ir(render_ir, profile)
            self.assertFalse(validate_layout(render_ir, layout, profile), view["view_type"])
            svg = render_svg(render_ir, layout, theme, profile)
            self.assertIn('viewBox="0 0 1920 1080"', svg)
            self.assertNotIn("foreignObject", svg)
        dense = plan_views(rich_csm(18), level="overview", requested_views=("research_methodology",))
        self.assertGreater(len(dense), 1)
        self.assertTrue(all(len(view["included_entities"]) <= 9 for view in dense))

    def test_cli_end_to_end(self):
        with tempfile.TemporaryDirectory(dir=TEST_TMP) as tmp:
            root = Path(tmp) / "api"
            write(root / "requirements.txt", "fastapi\nrequests\n")
            write(root / "app.py", "from fastapi import FastAPI\nimport requests\napp=FastAPI()\n@app.get('/items')\ndef items(): return requests.get('https://example.test/items')\n")
            output = Path(tmp) / "out"
            result = subprocess.run([sys.executable, "-m", "architecture_visualizer", str(root), "--output", str(output), "--view", "system_architecture"], cwd=Path(__file__).resolve().parents[1], capture_output=True, text=True, check=False)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(json.loads(result.stdout)["status"], "passed")
            self.assertTrue((output / "summary.json").exists())

    def test_agent_feedback_loop_is_supported(self):
        csm = rich_csm()
        csm["entities"] = [
            {"id": "paper://model/agent", "type": "model", "name": "Agent", "responsibility": "Plans", "subsystem": None, "evidence_refs": ["f1"], "tags": ["ai"]},
            {"id": "paper://process/tool", "type": "process", "name": "Tool", "responsibility": "Acts", "subsystem": None, "evidence_refs": ["f2"], "tags": ["ai"]},
        ]
        csm["relations"] = [
            {"id": "r1", "source": "paper://model/agent", "target": "paper://process/tool", "relation": "invokes", "mode": "runtime", "evidence_refs": ["f1"], "label": None},
            {"id": "r2", "source": "paper://process/tool", "target": "paper://model/agent", "relation": "feeds", "mode": "runtime", "evidence_refs": ["f2"], "label": None},
        ]
        view = plan_views(csm, requested_views=("ai_pipeline",))[0]
        self.assertEqual(view["layout_archetype"], "feedback_loop")


if __name__ == "__main__":
    unittest.main()
