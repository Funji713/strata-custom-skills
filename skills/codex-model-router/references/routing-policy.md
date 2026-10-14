# Routing Policy

## Activation And Runtime

Automatically route requests requiring technical execution, including explicit `$codex-model-router` requests. Do not route informational explanations or recommendations, even when they name the skill or a model. UI metadata keeps `allow_implicit_invocation: true`.

Inspect the host's spawning tool, available model identifiers, and each selected model's supported reasoning levels. If the host cannot create the selected subtask, stop and report that routing is unavailable. An unavailable explicit choice must be reported; never silently substitute another model or effort.

The helper recommends settings; it does not invoke host tools or establish host availability. Supply `--available-models` and, when available, `--supported-reasoning` from the actual host. Without a reasoning map, its output is unverified and the parent must check the host before spawning. With a supplied map, unsupported or omitted selected-model reasoning blocks the route.

## Parent And Subtask Contract

Spawn one execution worker at a time with model and effort overrides and minimal inherited context. For `spawn_agent`, use `fork_turns: "none"`, `model`, and `reasoning_effort`; adapt enum casing to the host. Prepend `ROUTED_EXECUTION_SUBTASK: true`, then provide the task, acceptance criteria, selected settings, project constraints, and minimum evidence.

The sentinel tells the worker to implement and validate locally without routing again. Its final response includes completion status, changed paths/artifacts, validation commands and results, and remaining limitations. The parent reviews and reports the returned result without repeating implementation. Release the worker if the host supports that operation.

## Model Selection Order

Unless the user explicitly chooses a model, select the first available model in the chosen tier:

| Tier | Model preference order | Automatic reasoning |
| --- | --- | --- |
| Mechanical | `gpt-6-luna`, `gpt-5.6-luna`, `gpt-6.1-sol`, `gpt-6-sol`, `gpt-5.6-sol`, `gpt-5.6-terra` | Low; Medium for bounded local reasoning |
| Workhorse | `gpt-6.1-sol`, `gpt-6-sol`, `gpt-5.6-sol`, `gpt-5.6-terra` | Medium; High at score 13+, reasoning 3+, small difficult work, or two meaningful reasoning failures |
| Frontier | `gpt-6-astra`, `gpt-6.1-sol`, `gpt-6-sol`, `gpt-5.6-sol`, `gpt-5.6-terra` | High, including fallback |

Do not automatically select `gpt-5.5`. Honor an explicit user choice only if available. Compatibility fallbacks preserve the required reasoning effort; no compatible model or supported effort means a blocked route.

Model capability and reasoning effort are separate choices. Astra eligibility never automatically raises effort to XHigh. XHigh, Max, or Ultra requires a separate written rationale for the added reasoning or an explicit user choice. The helper's `--explicit-model` and `--explicit-reasoning` represent user choices; do not use them to bypass automatic gates without that authorization.

## Complexity Score

Score each dimension from 0 to 4 using concrete evidence; intermediate values represent intermediate difficulty. Missing files, traces, or contracts call for gathering context, rather than inflated ambiguity scores.

| Dimension | 0 | 2 | 4 |
| --- | --- | --- | --- |
| Scope | One local edit | Several related files | Cross-cutting repository change |
| Reasoning | Mechanical | Non-obvious local logic | Novel or multi-stage reasoning |
| Ambiguity | Exact acceptance criteria | Some assumptions needed | Competing requirements or behavior remain unclear after inspection |
| Dependencies | Isolated code | One internal or external dependency | Multiple interacting services, frameworks, or contracts |
| Risk | Easily reversible | Behavior or data change | Security, migration, production, or irreversible risk |
| Context | Target file supplied | Direct dependencies needed | History, architecture, or broad discovery required |

| Total | Starting route |
| --- | --- |
| 0–5 | Mechanical / Low; difficult reasoning still overrides this route |
| 6–12 | Workhorse / Medium |
| 13–15 | Workhorse / High |
| 16–24 | Astra / High when the direct selection gate below is met; otherwise Workhorse / High |

### Direct Astra Selection

Select Astra High immediately when **all** of these hold:

- Total score is at least **16**.
- Reasoning is at least **3**.
- Ambiguity **or** dependencies is at least **3**.

Record the concrete evidence supporting the qualifying dimensions. This permits direct selection for a coupled architecture, difficult multi-system failure, or novel design; a failed Sol attempt is not required.

For a smaller task that misses the total or supporting-dimension threshold, select Astra High when reasoning is at least 3 and there is a written exceptional-complexity rationale. Examples include a novel concurrency proof, a difficult algorithm with interacting invariants, or a demonstrated Workhorse capability gap after relevant evidence is present. In the helper, supply both `--frontier-justified` and `--frontier-evidence "concrete rationale"`. A bare flag is rejected.

These thresholds are an operational heuristic, not a measured model-quality guarantee. File count, high stakes, broad context, or domain names alone do not establish Astra eligibility.

## Overrides And Phases

Apply explicit user settings to the final route; automatic overrides below govern the underlying capability need:

| Situation | Route |
| --- | --- |
| Large mechanical rename or generated migration with settled contracts | Mechanical / Low with targeted validation; `--large-mechanical` overrides total score. |
| Small difficult concurrency, security, integrity, or algorithm work | Workhorse / High minimum; keep Astra if its evidence gate is met. Use `--small-difficult`; reasoning 3+ also prevents a Mechanical route. |
| Known framework or standard API with clear contracts | Usually Workhorse / Medium; a framework name adds no automatic complexity. |
| Implementation after the uncertain phase is resolved | Workhorse / Medium when the plan is settled; `--phase implementation --settled-plan` makes this explicit. Difficult unresolved implementation still qualifies for Astra. |
| Focused, bounded verification | Mechanical / Low or Medium using `--phase verification --bounded-verification`; keep difficult diagnosis at its required tier. |
| Two meaningful failed reasoning attempts | Raise Mechanical to Workhorse High or Workhorse Medium to High; Astra still requires its complexity/evidence gate. |
| Command, environment, dependency, permission failure | Recover the execution condition; do not escalate because of this failure. |
| Missing information | Gather the smallest missing context before spawning or escalating. |

Mechanical work remains Mechanical when it is also implementation against a settled plan. Do not label unresolved contracts or remaining difficult diagnosis as mechanical/bounded. The unavailable-host stop condition takes precedence over recovery and context actions.

For triage and root-cause analysis, score the actual phase. Architecture/design can select Astra directly when eligible. De-escalate once its uncertain work is complete, and avoid splitting tightly coupled reasoning just to obtain a cheaper route.

## Minimum Required Context

Read target files, errors, and failing tests first; then direct callers/imports/tests; then the related module boundary; then broader history or repository evidence only for a material unresolved question. Stop when the phase is sufficiently bounded.

## Compact Internal Record

Keep this record internal unless the user asks for it:

```text
phase=<triage|analysis|design|implementation|verification>
score=<0-24>; capability=<Mechanical|Workhorse|Frontier>; model=<host identifier>; reasoning=<host enum>
astra_evidence=<qualifying dimensions and concrete observations, or exceptional rationale>
context=<target|direct-dependencies|module|repository>; mode=<subtask|unavailable|blocked|skipped>
next=<single evidence-based next action>
```
