# Benchmark Results

This benchmark records a local v1.0.0 readiness run of the deterministic `mvp-demo-suite@v2` evaluation suite.

## Reproducibility Metadata

| Field | Value |
| --- | --- |
| Benchmark timestamp | `2026-06-19T10:34:45Z` |
| Repository commit evaluated | `5ac6694fb16608a077877f539c45cafd4d0bfed4` |
| Local branch during run | `tgusain/v1-readiness-case-study` |
| Suite | `mvp-demo-suite@v2` |
| Baseline | `backend/app/evaluation/baselines/mvp-demo-suite@v2.json` |
| Candidate output | `.agentops/eval-runs/v1-readiness.json` |
| Regression report | `.agentops/regression-reports/regression-run-000001-vs-run-000011.json` |
| Python | `3.13.3` |
| Evaluation mode | `heuristic` |

The evaluation implementation reported `implementation_version=5ac6694fb16608a077877f539c45cafd4d0bfed4` in `.agentops/eval-runs/v1-readiness.json`.

## Commands

```bash
PYTHONPATH=backend backend/.venv/bin/python -m app.evaluation.cli run \
  --suite mvp-demo-suite@v2 \
  --version v1-readiness \
  --output .agentops/eval-runs/v1-readiness.json

PYTHONPATH=backend backend/.venv/bin/python -m app.evaluation.cli compare \
  --baseline backend/app/evaluation/baselines/mvp-demo-suite@v2.json \
  --candidate .agentops/eval-runs/v1-readiness.json \
  --fail-on-p0-regression
```

Both commands exited with status `0`.

## Evaluation Summary

| Metric | Value |
| --- | --- |
| Run id | `run-000011` |
| Result hash | `69daf289f1dd30819af1346cdc5869ceb58a200187edeb37be79698bc88da468` |
| Total tasks | `6` |
| Passed tasks | `6` |
| Failed tasks | `0` |
| Pass rate | `1.0` |
| Reported evaluation duration | `4 ms` |

## Task Results

| Task | Priority | Fixture | Score | Status |
| --- | --- | --- | --- | --- |
| `repository-architecture` | P0 | `python_app@v1` | 100 | Passed |
| `onboarding-guide` | P0 | `go_service@v1` | 100 | Passed |
| `pr-review` | P0 | `go_pr_static@v1` | 100 | Passed |
| `incident-rca` | P0 | `checkout-latency@v1` | 100 | Passed |
| `static-ts-index` | P0 | `ts_frontend@v1` | 100 | Passed |
| `repository-evolution` | P0 | `go_service_moved@v1` | 100 | Passed |

## Check Groups Covered

The v2 suite includes checks in these groups:

- `workflow`
- `retrieval`
- `static_intelligence`
- `regression`

The generated run showed all recorded checks passing.

## Regression Comparison

| Field | Value |
| --- | --- |
| Report id | `regression-run-000001-vs-run-000011` |
| Baseline run | `run-000001` |
| Candidate run | `run-000011` |
| Status | `NO_CHANGE` |
| Comparison passed | `true` |
| Total tasks compared | `6` |
| Regressed tasks | `0` |
| Improved tasks | `0` |
| Unchanged tasks | `6` |
| P0 regressions | `0` |

Each task comparison had baseline score `100`, candidate score `100`, score delta `0`, and status `NO_CHANGE`.

## Trace Evidence

The evaluation run produced six task trace files under `.agentops/traces/run-000011/`:

- `trace-run-000011-repository-architecture.json`
- `trace-run-000011-onboarding-guide.json`
- `trace-run-000011-pr-review.json`
- `trace-run-000011-incident-rca.json`
- `trace-run-000011-static-ts-index.json`
- `trace-run-000011-repository-evolution.json`

Trace files are local runtime artifacts and are not committed.

## Validation Output

Additional release validation completed before documentation generation:

- Backend tests: `89 passed, 1 warning`
- Frontend build: `npm run build` completed successfully with Vite `7.3.5`

## Interpretation

This benchmark shows that the current tracked v2 baseline and the v1-readiness candidate output match for all six P0 tasks. It does not claim production accuracy, broad repository coverage, user adoption, productivity lift, or arbitrary-repository benchmark performance.
