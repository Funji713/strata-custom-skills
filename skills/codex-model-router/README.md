# Codex Model Router

Automatically classifies requests requiring technical execution, then runs each phase in one selected Codex subtask with the least costly suitable model and reasoning effort. The parent task receives the subtask's validated handoff and reports the result. Informational explanations and recommendations do not activate routing.

## Install

Run this in PowerShell to install directly into your local Codex skills directory:

```powershell
git clone https://github.com/Funji713/codex-model-router.git "$env:USERPROFILE\.codex\skills\codex-model-router"
```

To update an existing installation:

```powershell
git -C "$env:USERPROFILE\.codex\skills\codex-model-router" pull --ff-only
```

Start a new Codex task after installation if the current task does not discover the skill. Once discovered, the skill is eligible for automatic invocation across conversations whenever a request needs technical execution.

## Use

The skill automatically routes requests that need technical execution. You can also explicitly invoke it with the task that should be routed:

```text
$codex-model-router Investigate the failing checkout integration, implement the smallest verified fix, and run the focused tests.
```

The parent scores scope, reasoning, ambiguity, dependencies, risk, and context need. Mechanical work uses `gpt-6-luna`; ordinary engineering uses `gpt-6.1-sol`. Complex work can directly select `gpt-6-astra` High at score 16+ when reasoning is 3+ and ambiguity or dependencies is 3+. A smaller task can qualify with reasoning 3+ and a documented exceptional-complexity rationale. Prior Sol failures are not required; Astra never automatically implies XHigh. `gpt-6-sol` and 5.x models provide compatibility fallbacks. These thresholds are policy heuristics rather than benchmarked model-quality guarantees.

Explicit user settings override automatic selection when the host supports them. The execution subtask implements and validates, then returns changed paths, test results, and limitations. Once the uncertain phase is complete, implementation against a settled plan returns to Workhorse Medium and bounded mechanical work can use Luna.

If the current host cannot create a selected subtask, the skill stops rather than silently executing with an unselected model.

See [SKILL.md](SKILL.md) for the routing contract and [routing-policy.md](references/routing-policy.md) for the scoring and escalation policy.

The deterministic helper checks the policy without spawning workers. Supply observed host availability before acting on its recommendation:

```powershell
python scripts/route_task.py --self-test
python scripts/route_task.py --scope 3 --reasoning 3 --ambiguity 2 --dependencies 3 --risk 2 --context 3 --available-models gpt-6.1-sol,gpt-6-astra --supported-reasoning '{"gpt-6.1-sol":["Medium","High"],"gpt-6-astra":["High","XHigh"]}'
```

The second example returns Astra High at score 16. For a smaller exceptional task, add `--frontier-justified --frontier-evidence "concrete rationale"`. User overrides use `--explicit-model` / `--explicit-reasoning`; `--informational` skips routing. Unsupported user settings or missing compatible models return a blocked route.

## Benchmark snapshot

The following small, descriptive benchmark compares the router with a fixed `Terra+XHigh` baseline. It is included to make the observed effect of routing inspectable, not to claim universal quality or cost gains.

### Visual summary

![Benchmark task design](docs/assets/benchmark-task-design.png)

![Integrity and quality scores](docs/assets/benchmark-quality-score.png)

![Route composition](docs/assets/benchmark-route-composition.png)

![Five-hour usage deltas](docs/assets/benchmark-usage.png)

### Results and method

- **Design:** 3 rounds × 7 fixed tasks = 21 tasks. The router always ran first, so order and time confounding remain possible.
- **Public tests:** Router 48/48; fixed `Terra+XHigh` baseline 48/48. This is a ceiling effect, not evidence that the systems are universally equivalent.
- **Hidden tests:** Router 5/6; baseline 4/6. Only two hidden assertions were available, so this is a very small signal.
- **Descriptive composite:** Router 91.7 vs baseline 83.3.
- **Router route composition:** `Luna+Low` 8/21, `Terra+Medium` 1/21, `Sol+High` 12/21.
- **Five-hour account-window usage delta:** Router average 12.33 percentage points, median 13pp; baseline average 15.00pp, median 16pp; median reduction 3pp.

Account-window percentage-point deltas are not token counts. The measurements are small-sample/descriptive only; no statistical significance claim is made (Fisher two-sided p=1.00 from the available evidence). Withheld test answers are intentionally not disclosed.
