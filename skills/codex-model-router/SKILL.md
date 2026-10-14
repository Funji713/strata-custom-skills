---
name: codex-model-router
description: When a technical task needs execution, automatically classify coding, debugging, repository analysis, implementation, architecture, refactor, test, API integration, and AI/ML engineering work, then spawn a subtask at the least costly suitable Codex model and reasoning effort. The parent task receives and reports the completed subtask result. Use for execution tasks, including explicit $codex-model-router requests; do not route merely informational explanations or recommendations.
---

# Codex Model Router

## Goal

Complete the task reliably with the least expensive combination of model capability, reasoning effort, context, and retries. Directly route execution through a selected subtask rather than merely recommending a setting. Prioritize correctness and reliability over cost or speed.

Use this skill with the domain skill that explains how to do the work. This skill decides the smallest justified capability and context budget; it does not replace `surgical-coding-debug`, `project-architecture-workflow`, test guidance, framework guidance, or security guidance.

## Runtime Contract

Treat routing capability as dynamic. Inspect the subtask tools and model choices available in the current host before routing a task.

### Execution-handoff sentinel

The parent must prepend `ROUTED_EXECUTION_SUBTASK: true` to every spawned worker's handoff. This sentinel is definitive: when it is present, the receiving agent is already the selected execution subtask. It must skip all routing-capability checks, must not call `spawn_agent`, and must perform the assigned implementation and validation directly in its own workspace. It must not treat the absence of a nested spawning tool as a blocker.

- Activate by default when the current request needs execution of a technical task. An explicit `$codex-model-router` request is also sufficient. This default applies across conversations for users who install the skill; do not require them to repeat the invocation. Do not route merely informational explanations or recommendations.
- When already running as a subtask, do not route again. Own the assigned implementation and validation locally; recursive delegation is prohibited.
- If the host can spawn a subtask with model and reasoning overrides, use that operation. Select the current host's identifier and reasoning enum that correspond to the policy tier.
- Spawn exactly one execution subtask at a time using the host's option for no inherited conversation (for `spawn_agent`, use `fork_turns: "none"`). Pass `model` and `reasoning_effort` explicitly when supported. Prepend the execution-handoff sentinel, then pass the original task, essential acceptance criteria, selected settings, workspace or project constraints, and the minimum already-gathered evidence.
- Require the subtask to own implementation and validation. Its final report must include completion status, changed paths or produced artifacts, validation commands and results, known limitations, and a concise handoff for the parent task.
- The parent task waits only when it needs the completed result, reviews the returned result or change artifact, then reports the outcome to the user. Do not duplicate the implementation in the parent task. Release the completed subtask if the host supports that operation.
- Never claim a subtask ran or routing occurred unless the spawn operation and completion result succeeded. Report the subtask identifier and selected settings after success.
- If the host cannot spawn a selected subtask, stop before implementation and report that automatic routing is unavailable. Do not fall back to advisory execution unless the user explicitly permits it.
- Respect an explicit user model or reasoning choice. It overrides automatic selection for that route.

Read [routing-policy.md](references/routing-policy.md) before a non-trivial classification. Use [route_task.py](scripts/route_task.py) when a deterministic score or a testable execution route is useful; it validates policy only and does not itself call host tools.

## Route The Task

1. Separate the request into independently verifiable phases when that reduces capability or reasoning requirements. Do not split a tightly coupled problem merely to use cheaper models.
2. For each phase, classify scope, reasoning, ambiguity, dependencies, risk, and context need. Do not infer complexity from prompt length or changed-file count alone.
3. Apply the score, override rules, and phase rules from `routing-policy.md`.
4. Start with Minimum Required Context: target files, then direct callers or imports, then the related module, then repository-wide search only when earlier stages cannot resolve a material unknown.
5. Select the lowest suitable current-host model and reasoning identifiers, then spawn one subtask. Prefer one subtask that owns the work over parallel duplication.
6. Wait only for the needed completion result. Review the subtask report or returned change artifact, then report the result from the parent task.
7. If spawning or completion fails, report the concrete failure and do not continue implementation in the parent task.

## Model Catalog And Defaults

Inspect the current host's choices at route time. Prefer the newest available family; never select a legacy identifier when its current-generation counterpart is available and suitable.

| Model identifier | Position | Default reasoning | Use it for |
| --- | --- | --- | --- |
| `gpt-6-luna` | Fast, low-cost execution | Low | Deterministic one-file edits, formatting, straightforward test changes, narrow verification, and bounded mechanical migrations. Use Medium only when the task remains well-bounded but needs a little local reasoning. |
| `gpt-6.1-sol` | Default workhorse | Medium | Normal implementation, API and integration work, multi-file changes with known contracts, ordinary debugging, refactors, and code review fixes. Use High for genuinely non-obvious root causes or consequential design choices. |
| `gpt-6-astra` | Complex reasoning specialist | High | Directly select for score 16+ with reasoning 3+ and ambiguity or dependencies 3+, or for a smaller task with documented exceptional complexity and reasoning 3+. Prior Sol failures are not required. XHigh or higher requires a separate written justification or an explicit user choice. |
| `gpt-6-sol` | Previous-generation workhorse | Medium | Compatibility fallback only when `gpt-6.1-sol` is unavailable or a user explicitly requests it. Match the `gpt-6.1-sol` route but do not prefer it automatically. |
| `gpt-5.6-sol`, `gpt-5.6-terra`, `gpt-5.6-luna`, `gpt-5.5` | Legacy models | Match the closest current tier | Compatibility fallback only for a host that lacks the current-generation choices, or on explicit user request. Prefer `gpt-5.6-sol` for normal work, `gpt-5.6-luna` for mechanical work, and never select `gpt-5.5` automatically. |

The policy tiers are **Luna** (`gpt-6-luna`), **Workhorse** (`gpt-6.1-sol`), and **Frontier** (`gpt-6-astra`). Do not treat model labels as a rigid mapping: apply large-but-mechanical and small-but-difficult overrides before escalating.

## Failure And Phase Control

- Treat command errors, missing packages, permissions, bad test setup, and syntax mistakes as execution failures. Fix the execution issue; do not raise model tier or reasoning effort.
- Before escalating a reasoning failure, first check whether evidence or context is missing. Do not replace missing callers, error traces, schemas, contracts, or tests with deeper reasoning.
- After two meaningful, evidence-backed attempts at the same reasoning level fail, route one follow-up subtask at an appropriate higher setting. Raise Workhorse Medium to High when it remains suitable; select Astra directly whenever the complexity gate or a documented capability gap justifies it. Prior Sol attempts are an escalation signal, not a prerequisite for Astra. Do not retry unchanged hypotheses indefinitely.
- De-escalate once the uncertain phase is complete. Architecture analysis can require `gpt-6.1-sol` High or `gpt-6-astra`, while implementation against an approved plan generally uses `gpt-6.1-sol` Medium; deterministic cleanup can use `gpt-6-luna` Low.

## Task-Specific Routing

- Route focused bug fixes through `surgical-coding-debug`. Reproduce, inspect the smallest relevant context, test the hypothesis, patch the proven cause, and validate narrowly.
- Route architecture work through `project-architecture-workflow`. Use `gpt-6.1-sol` High for bounded architecture or migration decisions; directly select `gpt-6-astra` High when interacting contracts, unresolved tradeoffs, or novel reasoning meet the policy gate. A small service addition is usually `gpt-6.1-sol` Medium.
- Treat normal Python, Django, Django REST Framework, FastAPI, REST API, JavaScript, HTML/CSS, Docker, database, standard inference API, and known-contract integration work as `gpt-6.1-sol` Medium by default, not Astra.
- Treat AI/ML pipeline architecture, multi-model orchestration, model serving design, and unexplained inference behavior according to observed complexity. Use Workhorse High for bounded analysis and Astra High directly when the policy gate is met.

## User-Facing Messages

Keep classification details internal. Report actual routing concisely:

```text
Subtask `agent_...` completed using `gpt-6.1-sol` + High reasoning. It changed `...`, passed `...`, and returned the following limitation: `...`.
```

```text
This host cannot spawn a subtask with the selected model settings, so I stopped before execution rather than run the task using an unselected model.
```

## Avoid

- Beginning with a full repository scan.
- Defaulting normal work to Astra, High, XHigh, Max, or Ultra reasoning.
- Escalating because many files need the same mechanical change.
- Staying at a high tier after the hard planning or investigation phase is complete.
- Re-reading unchanged files or repeating already rejected hypotheses.
- Executing the routed work in the parent after spawning its subtask.
- Passing the entire parent conversation when a compact handoff is sufficient.
- Treating a failed or unavailable subtask route as a successful model switch.
