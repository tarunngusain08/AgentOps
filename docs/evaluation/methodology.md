# Evaluation Methodology

AgentOps evaluates Engineering Copilot workflows with deterministic, fixture-backed checks. It does not use LLM-as-judge scoring.

## Why LLM-as-Judge Was Rejected

LLM-as-judge scoring was rejected because AgentOps needs local and CI results that are reproducible from source, fixtures, and baselines. The current evaluator uses expected facts, match types, check weights, and required checks.

Evidence:

- `backend/app/evaluation/suites.py`
- `backend/app/evaluation/matcher.py`
- `backend/app/evaluation/runner.py`

## Golden Task Design

An evaluation suite contains versioned tasks. Each task pins a fixture version and runs one workflow.

`mvp-demo-suite@v2` contains:

| Task | Fixture | Purpose |
| --- | --- | --- |
| `repository-architecture` | `python_app@v1` | Architecture report and Python static intelligence |
| `onboarding-guide` | `go_service@v1` | Onboarding guide and Go navigation |
| `pr-review` | `go_pr_static@v1` | PR review enrichment from indexed files |
| `incident-rca` | `checkout-latency@v1` | Fixture-driven incident RCA |
| `static-ts-index` | `ts_frontend@v1` | TypeScript symbol/import/test extraction |
| `repository-evolution` | `go_service_moved@v1` | Stable static intelligence after source movement |

## Deterministic Scoring

Checks use the match types implemented in `backend/app/evaluation/matcher.py`:

- `contains`
- `equals`
- `list_contains`
- `exists`

Scores are weighted in `backend/app/evaluation/runner.py`. A task passes when:

- weighted score is at or above the task threshold
- every required check passes

The default threshold used by the suite definitions is `80`.

## Regression Detection

Regression comparison in `backend/app/evaluation/regression.py` requires:

- same suite id
- same suite version
- matching task ids
- matching check ids

Comparison status can be:

- `NO_CHANGE`
- `IMPROVEMENT`
- `REGRESSION`
- `MIXED`

CI fails when a candidate has a P0 task failure or a P0 regression.

## Baseline Versioning

Tracked baselines live under `backend/app/evaluation/baselines/`.

- `mvp-demo-suite@v1.json` remains readable for older runs.
- `mvp-demo-suite@v2.json` is the default CI baseline.

Baseline validation checks result hash integrity, suite id/version, and the P0 task list.

## Failure Analysis

Evaluation failures should be debugged from:

1. failed task id
2. failed check id
3. expected fact
4. workflow output
5. fixture version
6. execution trace for the task
7. regression report if comparing against a baseline

The CLI writes evaluation output to `.agentops/eval-runs/` and regression output to `.agentops/regression-reports/`.

## Score Interpretation

- `100`: all weighted checks passed.
- `80-99`: task passed, but at least one non-required weighted check may have failed.
- below `80`: task failed unless the threshold was explicitly lower.
- any failed required check: task failed regardless of weighted score.

