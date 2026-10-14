#!/usr/bin/env python3
"""Deterministic policy checker; recommends a route but never spawns a worker."""

from __future__ import annotations

import argparse
import json
from dataclasses import dataclass, replace

DIMENSIONS = ("scope", "reasoning", "ambiguity", "dependencies", "risk", "context")
PHASES = ("triage", "analysis", "design", "implementation", "verification")
EFFORTS = ("Low", "Medium", "High", "XHigh", "Max", "Ultra")
MODEL_PREFERENCES = {
    "Mechanical": ("gpt-6-luna", "gpt-5.6-luna", "gpt-6.1-sol", "gpt-6-sol", "gpt-5.6-sol", "gpt-5.6-terra"),
    "Workhorse": ("gpt-6.1-sol", "gpt-6-sol", "gpt-5.6-sol", "gpt-5.6-terra"),
    "Frontier": ("gpt-6-astra", "gpt-6.1-sol", "gpt-6-sol", "gpt-5.6-sol", "gpt-5.6-terra"),
}


@dataclass(frozen=True)
class RouteInput:
    scope: int
    reasoning: int
    ambiguity: int
    dependencies: int
    risk: int
    context: int
    phase: str = "analysis"
    large_mechanical: bool = False
    small_difficult: bool = False
    settled_plan: bool = False
    bounded_verification: bool = False
    execution_failure: bool = False
    missing_context: bool = False
    reasoning_failures: int = 0
    routing_capability: str = "subtask"
    technical_execution: bool = True
    available_models: tuple[str, ...] = (
        "gpt-6.1-sol", "gpt-6-astra", "gpt-6-sol", "gpt-6-luna",
        "gpt-5.6-sol", "gpt-5.6-terra", "gpt-5.6-luna", "gpt-5.5",
    )
    frontier_justified: bool = False
    frontier_evidence: str = ""
    explicit_model: str | None = None
    explicit_reasoning: str | None = None
    supported_reasoning: dict[str, tuple[str, ...]] | None = None

    @property
    def score(self) -> int:
        return sum(getattr(self, dimension) for dimension in DIMENSIONS)


def base_capability(score: int) -> str:
    if score <= 5:
        return "Mechanical"
    if score <= 15:
        return "Workhorse"
    return "Frontier candidate"


def frontier_eligible(task: RouteInput) -> bool:
    direct = task.score >= 16 and task.reasoning >= 3 and (
        task.ambiguity >= 3 or task.dependencies >= 3
    )
    exceptional = task.frontier_justified and bool(task.frontier_evidence.strip()) and task.reasoning >= 3
    return direct or exceptional


def validate_input(task: RouteInput) -> None:
    for name in DIMENSIONS:
        value = getattr(task, name)
        if type(value) is not int or not 0 <= value <= 4:
            raise ValueError(f"{name} must be an integer from 0 to 4")
    if task.phase not in PHASES or task.routing_capability not in ("subtask", "unavailable"):
        raise ValueError("invalid phase or routing capability")
    if type(task.reasoning_failures) is not int or task.reasoning_failures < 0:
        raise ValueError("reasoning_failures must be a nonnegative integer")
    if task.explicit_reasoning is not None and task.explicit_reasoning not in EFFORTS:
        raise ValueError(f"explicit_reasoning must be one of {EFFORTS}")
    if task.frontier_justified and not task.frontier_evidence.strip():
        raise ValueError("frontier_justified requires a concrete frontier_evidence rationale")
    if task.large_mechanical and task.small_difficult:
        raise ValueError("large_mechanical and small_difficult are contradictory")
    if task.settled_plan and task.phase != "implementation":
        raise ValueError("settled_plan applies only to implementation")
    if task.bounded_verification and task.phase != "verification":
        raise ValueError("bounded_verification applies only to verification")
    if task.supported_reasoning is not None:
        if not isinstance(task.supported_reasoning, dict):
            raise ValueError("supported_reasoning must map model identifiers to effort lists")
        for model, levels in task.supported_reasoning.items():
            if not isinstance(model, str) or not isinstance(levels, (list, tuple)) or any(level not in EFFORTS for level in levels):
                raise ValueError("supported_reasoning contains an invalid model or effort list")


def select_model(capability: str, task: RouteInput) -> str | None:
    if task.explicit_model is not None:
        return task.explicit_model if task.explicit_model in task.available_models else None
    return next((model for model in MODEL_PREFERENCES[capability] if model in task.available_models), None)


def select_reasoning(task: RouteInput, capability: str, escalating: bool) -> str:
    if task.explicit_reasoning is not None:
        return task.explicit_reasoning
    if capability == "Frontier" or task.explicit_model == "gpt-6-astra":
        return "High"
    if capability == "Mechanical":
        return "Medium" if task.reasoning >= 2 and not task.large_mechanical else "Low"
    if task.settled_plan and not task.small_difficult and not escalating:
        return "Medium"
    return "High" if escalating or task.small_difficult or task.reasoning >= 3 or task.score >= 13 else "Medium"


def route_task(task: RouteInput) -> dict[str, object]:
    validate_input(task)
    result: dict[str, object] = {
        "mode": "subtask", "phase": task.phase, "score": task.score,
        "recommended_capability": None, "recommended_model": None,
        "recommended_reasoning": None, "host_reasoning_verified": False,
        "context_strategy": ("target", "target", "direct-dependencies", "module", "repository")[task.context],
        "action": "spawn a selected execution subtask, then report its completed result to the parent",
        "notes": [],
    }
    notes = result["notes"]
    if not task.technical_execution:
        result.update(mode="skipped", action="answer informational request without routing")
        return result
    capability = "Mechanical" if task.score <= 5 else "Workhorse"
    if frontier_eligible(task):
        capability = "Frontier"
        notes.append("direct Astra selection is justified by observed reasoning and ambiguity/dependencies or the supplied frontier evidence; no prior Sol failure is required")
    elif base_capability(task.score) == "Frontier candidate":
        notes.append("score alone does not justify Astra; use Workhorse High")
    if task.large_mechanical:
        capability = "Mechanical"
        notes.append("large mechanical work stays on the low tier with targeted validation")
    elif (task.small_difficult or task.reasoning >= 3) and capability == "Mechanical":
        capability = "Workhorse"
    if task.settled_plan and not task.large_mechanical:
        capability = "Workhorse"
        notes.append("implementation against a settled plan de-escalates the completed uncertain phase")
    elif task.bounded_verification and not task.small_difficult:
        capability = "Mechanical"
        notes.append("explicitly bounded verification uses the low tier")
    escalating = task.reasoning_failures >= 2 and not (task.execution_failure or task.missing_context)
    if escalating:
        if capability == "Mechanical":
            capability = "Workhorse"
        notes.append("two meaningful reasoning failures raise Workhorse reasoning to High; Astra still requires the complexity or evidence gate")
    if task.execution_failure:
        notes.append("recover execution conditions; this failure does not justify escalation")
        result["action"] = "recover execution conditions in the routed task"
    elif task.missing_context:
        notes.append("acquire the smallest missing context; this absence does not justify escalation")
        result["action"] = "acquire minimal missing context before spawning the execution subtask"
    model = select_model(capability, task)
    effort = select_reasoning(task, capability, escalating)
    result.update(recommended_capability=capability, recommended_model=model, recommended_reasoning=effort)
    if task.explicit_model or task.explicit_reasoning:
        notes.append("explicit user model or reasoning choice overrides automatic selection")
    elif model is not None and model != MODEL_PREFERENCES[capability][0]:
        notes.append("preferred model is unavailable; selected the first compatible fallback")
    if task.routing_capability == "unavailable":
        result.update(mode="unavailable", action="stop: automatic routing is unavailable")
    elif model is None:
        result.update(mode="blocked", action="stop: requested model or a compatible fallback is unavailable")
    elif task.supported_reasoning is not None:
        result["host_reasoning_verified"] = model in task.supported_reasoning
        if effort not in task.supported_reasoning.get(model, ()):
            result.update(mode="blocked", action="stop: selected reasoning is unsupported or unverified on this host")
    else:
        notes.append("verify the selected model's reasoning levels on the host before spawning")
    return result


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    for dimension in DIMENSIONS:
        parser.add_argument(f"--{dimension}", type=int, choices=range(5), default=0)
    parser.add_argument("--phase", choices=PHASES, default="analysis")
    for flag in ("large-mechanical", "small-difficult", "settled-plan", "bounded-verification", "execution-failure", "missing-context", "frontier-justified"):
        parser.add_argument(f"--{flag}", action="store_true")
    parser.add_argument("--reasoning-failures", type=int, default=0)
    parser.add_argument("--routing-capability", choices=("subtask", "unavailable"), default="subtask")
    parser.add_argument("--informational", dest="technical_execution", action="store_false")
    parser.add_argument("--available-models", default=",".join(RouteInput.available_models), help="comma-separated host model identifiers")
    parser.add_argument("--frontier-evidence", default="", help="exceptional complexity or capability-gap rationale for --frontier-justified")
    parser.add_argument("--explicit-model", help="user-selected model; must be available on this host")
    parser.add_argument("--explicit-reasoning", choices=EFFORTS, help="user-selected effort; overrides automatic defaults")
    parser.add_argument("--supported-reasoning", type=json.loads, help='host reasoning map, e.g. {"gpt-6-astra":["High","XHigh"]}')
    parser.add_argument("--self-test", action="store_true")
    return parser.parse_args()


def run_self_test() -> None:
    ordinary = RouteInput(1, 2, 1, 1, 2, 1)
    boundary = RouteInput(3, 3, 2, 3, 2, 3)  # 16, reasoning and dependencies gate
    cases = (
        ("score 5", RouteInput(1, 1, 1, 1, 1, 0), "Mechanical", "gpt-6-luna", "Low"),
        ("score 6", RouteInput(1, 1, 1, 1, 1, 1), "Workhorse", "gpt-6.1-sol", "Medium"),
        ("ordinary", ordinary, "Workhorse", "gpt-6.1-sol", "Medium"),
        ("score 12", RouteInput(2, 2, 2, 2, 2, 2), "Workhorse", "gpt-6.1-sol", "Medium"),
        ("score 13", RouteInput(3, 2, 2, 2, 2, 2), "Workhorse", "gpt-6.1-sol", "High"),
        ("score 15", replace(boundary, scope=2), "Workhorse", "gpt-6.1-sol", "High"),
        ("score 16 direct", boundary, "Frontier", "gpt-6-astra", "High"),
        ("ambiguity gate", RouteInput(3, 3, 3, 2, 2, 3), "Frontier", "gpt-6-astra", "High"),
        ("high score low reasoning", RouteInput(4, 2, 4, 4, 4, 4), "Workhorse", "gpt-6.1-sol", "High"),
        ("high score bounded contracts", RouteInput(4, 4, 2, 2, 4, 4), "Workhorse", "gpt-6.1-sol", "High"),
        ("max score", RouteInput(4, 4, 4, 4, 4, 4), "Frontier", "gpt-6-astra", "High"),
        ("small exceptional", RouteInput(0, 4, 2, 2, 2, 2, small_difficult=True, frontier_justified=True, frontier_evidence="novel lock-free algorithm requires proving two interacting invariants"), "Frontier", "gpt-6-astra", "High"),
        ("small difficult preserves Astra", replace(boundary, small_difficult=True), "Frontier", "gpt-6-astra", "High"),
        ("ordinary difficult", replace(ordinary, small_difficult=True), "Workhorse", "gpt-6.1-sol", "High"),
        ("mechanical override", replace(boundary, large_mechanical=True), "Mechanical", "gpt-6-luna", "Low"),
        ("settled plan", replace(boundary, phase="implementation", settled_plan=True), "Workhorse", "gpt-6.1-sol", "Medium"),
        ("hard implementation", replace(boundary, phase="implementation"), "Frontier", "gpt-6-astra", "High"),
        ("bounded verification", replace(ordinary, phase="verification", bounded_verification=True), "Mechanical", "gpt-6-luna", "Medium"),
        ("workhorse failures", replace(ordinary, reasoning_failures=2), "Workhorse", "gpt-6.1-sol", "High"),
        ("mechanical failures", RouteInput(0, 0, 0, 0, 0, 0, reasoning_failures=2), "Workhorse", "gpt-6.1-sol", "High"),
        ("environment failure", replace(ordinary, reasoning_failures=2, execution_failure=True), "Workhorse", "gpt-6.1-sol", "Medium"),
        ("missing context", replace(ordinary, reasoning_failures=2, missing_context=True), "Workhorse", "gpt-6.1-sol", "Medium"),
        ("explicit Astra", replace(ordinary, explicit_model="gpt-6-astra"), "Workhorse", "gpt-6-astra", "High"),
        ("explicit Astra on mechanical", RouteInput(0, 0, 0, 0, 0, 0, explicit_model="gpt-6-astra"), "Mechanical", "gpt-6-astra", "High"),
        ("small high reasoning", RouteInput(0, 4, 0, 0, 0, 0), "Workhorse", "gpt-6.1-sol", "High"),
        ("mechanical settled plan", replace(boundary, large_mechanical=True, phase="implementation", settled_plan=True), "Mechanical", "gpt-6-luna", "Low"),
        ("evidence without hard reasoning", replace(ordinary, frontier_justified=True, frontier_evidence="multiple services but a known contract"), "Workhorse", "gpt-6.1-sol", "Medium"),
        ("explicit Luna", replace(boundary, explicit_model="gpt-6-luna", explicit_reasoning="Low"), "Frontier", "gpt-6-luna", "Low"),
        ("explicit effort", replace(boundary, explicit_reasoning="XHigh"), "Frontier", "gpt-6-astra", "XHigh"),
        ("Astra fallback", replace(boundary, available_models=("gpt-6.1-sol",)), "Frontier", "gpt-6.1-sol", "High"),
        ("previous workhorse fallback", replace(boundary, available_models=("gpt-6-sol",)), "Frontier", "gpt-6-sol", "High"),
        ("legacy fallback", replace(ordinary, available_models=("gpt-5.6-terra",)), "Workhorse", "gpt-5.6-terra", "Medium"),
        ("Luna fallback", RouteInput(0, 0, 0, 0, 0, 0, available_models=("gpt-5.6-luna",)), "Mechanical", "gpt-5.6-luna", "Low"),
        ("Luna workhorse fallback", RouteInput(0, 0, 0, 0, 0, 0, available_models=("gpt-6.1-sol",)), "Mechanical", "gpt-6.1-sol", "Low"),
        ("explicit legacy", replace(ordinary, explicit_model="gpt-5.5"), "Workhorse", "gpt-5.5", "Medium"),
    )
    count = 0
    for label, task, capability, model, effort in cases:
        result = route_task(task)
        assert (result["recommended_capability"], result["recommended_model"], result["recommended_reasoning"]) == (capability, model, effort), (label, result)
        assert result["mode"] == "subtask", (label, result)
        count += 1
    for task in (replace(ordinary, routing_capability="unavailable"), replace(ordinary, routing_capability="unavailable", execution_failure=True), replace(ordinary, routing_capability="unavailable", missing_context=True)):
        result = route_task(task)
        assert result["mode"] == "unavailable" and result["action"] == "stop: automatic routing is unavailable", result
        count += 1
    for task in (replace(ordinary, available_models=()), replace(ordinary, available_models=("gpt-5.5",)), replace(ordinary, explicit_model="absent"), replace(boundary, supported_reasoning={"gpt-6-astra": ("Low",)}), replace(boundary, supported_reasoning={}), replace(boundary, explicit_reasoning="Ultra", supported_reasoning={"gpt-6-astra": ("High",)})):
        result = route_task(task)
        assert result["mode"] == "blocked" and result["action"].startswith("stop:"), result
        count += 1
    for task in (replace(boundary, technical_execution=False), replace(ordinary, technical_execution=False, explicit_model="gpt-6-astra")):
        result = route_task(task)
        assert result["mode"] == "skipped" and result["recommended_model"] is None, result
        count += 1
    verified = route_task(replace(boundary, supported_reasoning={"gpt-6-astra": ("High", "XHigh")}))
    assert verified["mode"] == "subtask" and verified["host_reasoning_verified"] is True, verified
    count += 1
    for task in (replace(ordinary, scope=5), replace(ordinary, reasoning_failures=-1), replace(ordinary, frontier_justified=True), replace(ordinary, large_mechanical=True, small_difficult=True), replace(ordinary, settled_plan=True), replace(ordinary, bounded_verification=True), replace(ordinary, supported_reasoning={"gpt-6.1-sol": ("invalid",)})):
        try:
            route_task(task)
        except ValueError:
            count += 1
        else:
            raise AssertionError(f"invalid input was accepted: {task}")
    print(f"self-test passed: {count} routing, availability, scope, and input cases")


def main() -> None:
    args = parse_args()
    if args.self_test:
        run_self_test()
        return
    route_input = RouteInput(
        **{field: getattr(args, field) for field in RouteInput.__dataclass_fields__ if field != "available_models"},
        available_models=tuple(model.strip() for model in args.available_models.split(",") if model.strip()),
    )
    try:
        result = route_task(route_input)
    except ValueError as error:
        raise SystemExit(str(error)) from error
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
