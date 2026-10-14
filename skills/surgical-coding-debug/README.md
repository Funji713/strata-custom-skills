# Surgical Coding and Debug

Implement scoped changes and debug reproducible, intermittent or test failures using evidence, bounded exploration and risk-based verification. Use after architecture decisions are settled. Do not use as the primary workflow for new-project design, module redesign or unresolved architecture decisions; route those to project-architecture-workflow.

[Workflow](SKILL.md) | [Execution protocol](references/execution-protocol.md) |
[Change log](CHANGELOG.md) | [Evaluation](evals/README.md)

## Install or update

The official skill guide lists `~/.agents/skills` for user-level local skills.
Documentation checked 2026-10-04; Git and Codex must already be installed.
PowerShell:

```powershell
New-Item -ItemType Directory -Force "$env:USERPROFILE\.agents\skills" | Out-Null
git clone https://github.com/Funji713/surgical-coding-debug.git "$env:USERPROFILE\.agents\skills\surgical-coding-debug"
```

For an existing checkout inspect local changes before a fast-forward-only update:

```powershell
git -C "$env:USERPROFILE\.agents\skills\surgical-coding-debug" status --short
git -C "$env:USERPROFILE\.agents\skills\surgical-coding-debug" pull --ff-only
```

POSIX: create `~/.agents/skills` and clone this repository into its `surgical-coding-debug` child.
Older installations may use `~/.codex/skills`; preserve local edits, confirm discovery
for your installed Codex version and deliberately move/disable the old copy before
installing a second active skill with the same name. Do not automatically delete it.
Record `codex --version` when testing compatibility; no Codex runtime version has
been execution-tested by package lint. Restart Codex if a skill is not discovered.
A normal clone/pull follows its configured branch; review an unmerged candidate by
explicitly checking out that branch, not by assuming it is on main.

[Official authoring and discovery guide](https://developers.openai.com/codex/skills/)

## Use

```text
$surgical-coding-debug Work on this task within the explicitly requested mode and acceptance criteria.
```

Planning/review does not authorize application changes. This package can operate
standalone for settled tasks. With `project-architecture-workflow` installed, use version 1.0.0 of the
shared protocol for explicit bidirectional handoff. Names are not fictitious API
calls. Missing/incompatible companions must be disclosed, not silently installed.
These are instructions, not an authorization sandbox or guarantee of compliance.

## Validate

Python 3.10+; standard library only. No model, API keys or dependency installation:

```sh
python scripts/validate.py
python -m unittest discover -s tests -v
python scripts/validate.py --peer /path/to/project-architecture-workflow
```

Optional receipt/gate flags and model evaluation procedure are in
[evals/README.md](evals/README.md); [ten behavioral scenarios](evals/cases.json) are
specifications marked not_run, not claimed successful trials. The validator checks
metadata, simple local links, exact receipt fields, declared state transitions and
peer consistency; it does not run inspected commands or authenticate evidence.
CI is configured for Linux/Windows and Python 3.10/3.13 with pinned actions and
read-only contents permission. A configured CI matrix is not a claim it has run.
