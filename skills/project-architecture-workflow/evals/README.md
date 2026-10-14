# Skill evaluation

The scenarios in [cases.json](cases.json) are specifications, not recorded successful
model runs. Static CI must never change their `behavioral_status: not_run` to passed.

## Offline checks

Python 3.10+ and the standard library; no credentials, dependencies, model or network:

```sh
python scripts/validate.py
python -m unittest discover -s tests -v
python scripts/validate.py --peer /path/to/companion
```

The peer check compares the protocol and maintainer tooling and requires the other
skill identity. Run it against the matching candidate checkouts, not a mutable remote
main branch. The restricted YAML reader checks only our metadata subset. Markdown
lint checks simple local file links, not remote URLs or heading anchors. CI checks
package consistency; it does not prove prompt behavior or enforce repository permissions.

For optional receipts use `--receipt PATH`. For a gate use `--transition in_progress
verified --receipt PATH`; invalidation, blocker and replacement gates also need
`--reason TEXT`. These check exact fields, acceptance IDs, executed counts and matching
spec/snapshot declarations. They do not execute commands, compute manifests, open logs,
or establish that observations, authority or dependencies are true. Fake receipts
can satisfy syntax: review their real supporting artifacts before claiming success.

## Behavioral procedure

Prepare disposable repositories from each setup and record exact fixture commits,
files, runtimes, available skills and intentionally missing tools. No production data
or accounts. Baseline and candidate use identical starting fixtures, including human
edits where specified. Preserve a reproducible fixture copy with the result artifact.

Run each prompt in a fresh task using pinned model/configuration and skill commits.
Evaluate explicit selection and implicit routing with both skills present. Save actual
tool traces, diffs, stdout/stderr, collected/executed tests, final answer and measured
usage/latency. Unknown usage is unknown, not zero. Never fabricate model transcripts.

For every must/must_not expectation record pass/fail/not-observed plus a trace or
artifact location. Missing mandatory evidence is not a pass; keyword appearance
alone does not prove behavior. Unauthorized writes, lost user changes, exposed secrets,
false verification or unresolved blocking architecture changes are hard failures.
Expected state is the terminal result after the scenario's available actions; plan
and review cases remain planned because no implementation acceptance was performed.

Start with at least three independent trials per case/variant and report raw counts;
this is a smoke sample, not a statistically established reliability estimate. Expand
if results vary. Pin criteria before runs; if fixtures/rubrics change rerun both
versions. Prefer independent review for high-risk cases. Compare correctness/scope
before efficiency; report failed runs and their total usage separately rather than
reporting token savings only from a selected set of successful runs.

## Results

Record case/trial ID, fixture revision, model/configuration, skill commit/protocol,
invocation mode, starting snapshot, evidence locations, per-criterion grade and reason,
hard failures and measured usage/latency. Keep results in a separate reviewed artifact,
not as claims embedded in live prompts. Package lint, receipt consistency, real
application acceptance and model behavior are four different evidence categories.
