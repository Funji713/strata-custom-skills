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

Automatic web selection update (same date and hardware): the opt-in package image
now inserts a skill-selection system message into the web chat request only when
Tools / MCP is on and `skills__read_skill` is ready. Ordinary API requests and
upstream sources remain unchanged; no backend builds were required.

`python -m unittest discover -s strata-custom-skills/tests -p test_auto_skills.py -v`
passed 3 tests on Windows with Node 24.19.0: idempotent patch/source preservation,
refusal on a missing/ambiguous anchor, and actual JavaScript request behavior.
The JavaScript test covers MCP off/absent/non-boolean, unavailable skills, preservation
of caller messages and explicit override text, plus the simple-Q&A policy.

`docker run --rm --entrypoint /bin/sh -v "${PWD}/strata-custom-skills:/input:ro" strata:local-custom-skills -c 'cp -a /input /tmp/skills-check; cd /tmp/skills-check; /opt/strata/.venv/bin/python tests/run_checks.py'`
passed 131 executed test cases; the additional JavaScript test was skipped in Docker
because that image has no Node. The Node test above passed separately. Source manifest
verification still matches all 82 originals byte-for-byte. The extracted deployed
web app passed `node --check`; HTTP `/web/app.js` contains the patch, and `/health`
reports the model loaded. The service was recreated using the existing localhost
compose bindings.

Live automatic selection: an unnamed Traditional Chinese debugging request about
`average([])` caused the real model to call `skills__read_skill`; server logs confirm
the call succeeded with 7,152 characters. It then successfully read the requested
source via `workspace__read_file`. Final prose was not awaited; the final image
deployment interrupted that request. This proves automatic invocation, not a
completed debugging task or selection accuracy across all six skills. Compact
evidence is in `AUTO_SKILLS_RECEIPT.json`; full local logs remain in the deployment's
`docker-local/skills-auto-live-server.log`.

The live run also showed that this model did not follow skill pagination before
reading the source. The final runtime therefore returns up to 200 lines for the
main SKILL.md (references retain 80-line pages). A focused Linux rerun of
`python -m unittest discover -s tests -p test_skills.py -v` passed all 6 tests,
including complete first activation of all six entries and every serialized
result below the default 20,000-character MCP budget. The final change adds one
executed test, for 133 unique checks passed across Linux and Windows, with the
Node test executed on Windows. The final image was rebuilt and deployed; the
post-adjustment full-entry behavior was tested deterministically, not by another
model invocation.

To repeat live validation:
Use `python tests/live_model.py --output test-results/live-model.json` against the
running local Strata endpoint. It calls a real read_skill tool through the same
strata_mcp opt-in API used by the web application.
