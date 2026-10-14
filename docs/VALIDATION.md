# Validation

Date: 2026-10-14. Environment: Linux Docker, Python 3.12, local NVIDIA RTX 4070,
Strata Qwen3.8-Flash-Next IQ2_XS. Tests below exercise Python tooling; no GPU
backend sources were modified. No claim of general model accuracy or speed.

| Check | Executed result |
| --- | --- |
| `tests/test_skills.py` | 5 passed: six-skill pagination, reference loading/path rejection, advisory router, actual SVG+JSON output and symlink rejection, MCP wire exchange |
| `tests/test_install.py` | 2 passed: backup/idempotent add/remove, refusal to overwrite unrelated MCP entry |
| router `--self-test` | 54 policy/input/availability cases passed |
| project-architecture-workflow validator tests | 28 passed |
| surgical-coding-debug validator tests | 28 passed |
| architecture-visualizer acceptance tests | 12 passed, including deterministic SVG, secret redaction, CLI and all supported view types |
| `tests/verify_sources.py` | 82 original files match inventory, length and SHA256 |

129 executable test cases passed. Original suites ran from a disposable writable
copy in Docker so their scratch directories did not modify imported sources.
Repeat using `python tests/run_checks.py` from a writable Linux checkout.

Initial failures retained: the first integration fixture used two trivial Python
files and expected an SVG. The original pipeline correctly returned a non-diagram
outcome. The fixture was replaced with an evidenced ETL workload; the actual SVG
assertion then passed. Installer tests first hit Windows sandbox temporary-directory
permission errors; their unchanged tests passed in Linux Docker. Early health probes
during model startup returned connection refused; service readiness must be checked
after the normal model/cache load.

Public-content review: only package code, six custom skill trees and reference
assets are included. Text/source scan found no actual credentials or absolute
personal filesystem paths. Synthetic secret strings in original security tests
are fixtures. Four benchmark PNGs were visually reviewed: aggregate statistics,
without personal identifiers or credentials. Imported sources have no license file;
NOTICE.md records that limitation without assigning an invented license.

Installed-image verification: all 82 original files match the source manifest inside
`strata:local-custom-skills`. `/health` returned `ok`, model loaded. `/mcp` returned
workspace ready with 5 tools and skills ready with 4 tools. Existing workspace
integration also passed: actual code edit, valid 3-slide PPTX, path escape refused.

Live Qwen invocation passed through `/v1/chat/completions` with `strata_mcp: true`:
the model called `skills__read_skill` for `surgical-coding-debug/SKILL.md`; matching
call/result IDs confirmed `ok: true`, 7152 returned characters, not truncated, and
the model gave an accurate Traditional Chinese purpose summary. The skill was
paginated at line 81; this test proves invocation, not completion of a coding task.
See `LIVE_MODEL_RECEIPT.json` for the compact public receipt. The full raw local
response remains in the deployment's `docker-local/skills-live-validation.json`.
Runtime and test snapshot hashes are recorded in `VALIDATED_FILES.json`.

To repeat live validation:
Use `python tests/live_model.py --output test-results/live-model.json` against the
running local Strata endpoint. It calls a real read_skill tool through the same
strata_mcp opt-in API used by the web application.
