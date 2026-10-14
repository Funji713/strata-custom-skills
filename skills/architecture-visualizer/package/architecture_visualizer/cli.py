"""Command-line interface."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from .errors import VisualizerError
from .pipeline import PipelineOptions, run_pipeline
from .security import redact_text
from .views import SUPPORTED_VIEWS


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="architecture-visualizer", description="Create evidence-grounded PPT-ready architecture visuals.")
    parser.add_argument("source", help="Repository directory or research/technical document")
    parser.add_argument("--output", "-o", default="architecture-output", help="Output directory")
    parser.add_argument("--view", action="append", choices=SUPPORTED_VIEWS, default=[], help="Explicit v1 view type; repeatable")
    parser.add_argument("--audience", choices=("general", "academic", "technical", "executive"), default="technical")
    parser.add_argument("--level", choices=("overview", "standard", "technical"), default="standard")
    parser.add_argument("--language", choices=("zh-TW", "en"), default="en")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        summary = run_pipeline(Path(args.source), Path(args.output), PipelineOptions(audience=args.audience, level=args.level, language=args.language, views=tuple(args.view)))
    except VisualizerError as exc:
        print(json.dumps({"status": "failed", "error": exc.code, "message": redact_text(str(exc))}, ensure_ascii=False), file=sys.stderr)
        return 2
    except (ValueError, OSError) as exc:
        print(json.dumps({"status": "failed", "error": "SOURCE_PARSE_ERROR", "message": redact_text(str(exc))}, ensure_ascii=False), file=sys.stderr)
        return 2
    print(json.dumps(summary, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
