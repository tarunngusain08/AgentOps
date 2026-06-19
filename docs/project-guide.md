# AgentOps Project Guide

This guide explains the entire AgentOps project in one place. It is written for someone who wants to understand the product, the architecture, the evaluation model, the security boundaries, and the final v1.0.0 portfolio story without reading the source code first.

## 1. What AgentOps Is

AgentOps is a local-first Engineering Copilot reliability project. It combines practical engineering workflows with deterministic evaluation infrastructure.

The product side answers questions such as:

- What does this repository do?
- How should a new engineer navigate this codebase?
- What architecture-level risks does this pull request introduce?
- What likely caused this checkout latency incident?

The reliability side asks a different set of questions:

- Did the workflow output include the expected evidence?
- Did a change regress a P0 workflow?
- Can the evaluation result be reproduced locally and in CI?
- Can a reviewer inspect the run, checks, baseline, and regression report?

The key design choice is that AgentOps does not treat an LLM as the evaluator. Instead, it uses fixture-backed tasks, deterministic checks, baselines, and regression comparison.

## 2. Why The Project Exists

Many AI portfolio projects stop at a demo workflow. AgentOps goes further by showing how a team could make engineering-copilot workflows safer to change.

The project demonstrates these engineering capabilities:

- backend API design with FastAPI
- repository loading and lightweight code analysis
- deterministic static code intelligence
- evidence-backed report generation
- pull request risk review
- incident RCA modeling
- golden-task evaluation
- regression detection
- execution tracing
- GitHub Actions quality gates
- release readiness documentation

The result is not a generic chatbot. It is a small Engineering Copilot system with a quality layer around it.

## 3. Product Surface

AgentOps exposes six user-visible modes in the frontend:

1. Architecture Report
2. Onboarding Guide
3. PR Review
4. Incident RCA
5. Evaluation Suite
6. Regression Report

The first four are product workflows. The last two are reliability workflows.

Runtime screenshot evidence for these modes is linked from the README and stored under `docs/images/runtime/`.

### Architecture Report

Input:

```text
Public GitHub repository URL
```

Output:

- architecture overview
- technology stack
- components
- entry points
- important files
- high-level relationships
- assumptions
- code intelligence
- analysis metadata

This workflow is useful for quickly understanding the shape of a repository.

### Onboarding Guide

Input:

```text
Public GitHub repository URL
```

Output:

- project overview
- technology stack
- evidence-backed run instructions
- architecture summary
- key components
- Code Navigation
- common workflows
- useful files
- assumptions

This workflow is intentionally different from the architecture report. It is written for a new engineer who wants to start navigating and running the project.

### PR Review

Input:

```text
Public GitHub repository URL
Pull request number
```

Output:

- summary
- potential risks
- breaking changes
- files requiring attention
- testing concerns
- architecture impact
- evidence
- assumptions
- confidence

This is not a full code review system. It reviews repository-structure and architecture-level impact using changed files, patch metadata, and repository intelligence.

### Incident RCA

Input:

```text
Scenario id: checkout-latency
Optional public GitHub repository URL
```

Output:

- investigation overview
- timeline
- evidence grouped by metrics, logs, deployments, and code changes
- optional repository context
- suspected root cause
- mitigation
- prevention
- assumptions
- analysis metadata

The incident workflow is fixture-driven. It does not connect to production telemetry providers.

### Evaluation Suite

Input:

```text
Suite id: mvp-demo-suite@v2
```

Output:

- run id
- result hash
- fixture versions
- task scores
- check outcomes
- execution traces
- metadata

The suite is designed to verify AgentOps' own workflows, not to benchmark arbitrary external tools.

### Regression Report

Input:

```text
Baseline run id
Candidate run id
```

Output:

- comparison status
- pass/fail result
- task score deltas
- check changes
- regression reasons
- P0 regression count

Regression comparison requires matching suite id, suite version, task ids, and check ids.

## 4. Backend Architecture

The backend is organized by responsibility:

| Area | Purpose |
| --- | --- |
| `app/github/` | GitHub URL parsing, public metadata checks, repository and PR loading |
| `app/analyzer/` | file selection, repository analysis, repository index generation |
| `app/reporting/` | architecture report generation |
| `app/documentation/` | onboarding guide generation |
| `app/review/` | PR diff analysis and review generation |
| `app/incident/` | fixture loading, evidence collection, incident analysis, RCA generation |
| `app/evaluation/` | suites, fixtures, runner, scoring, storage, tracing, regression, CLI |
| `app/api/` | FastAPI route definitions |

The backend intentionally remains a modular monolith. There are no services, queues, workers, databases, event buses, or deployment orchestration layers.

## 5. Frontend Architecture

The frontend is a small Vite/React app. It keeps all workflow modes on a single surface so the demo remains simple.

Important frontend responsibilities:

- selecting the workflow mode
- collecting repository URL, PR number, scenario id, suite id, or run ids
- calling backend APIs through `frontend/src/api.ts`
- rendering reports, guide sections, findings, RCA evidence, evaluation results, traces, and regression reports

The frontend is intentionally not a dashboard analytics product.

## 6. Repository Intelligence

`RepositoryIndex` is the reusable static-intelligence artifact introduced in M08.

It captures:

- indexed files
- language
- file role
- directory group
- shallow symbols
- imports
- source-to-test links
- truncation metadata

Supported languages:

- Python
- TypeScript
- JavaScript
- Go

Not supported:

- call graphs
- type resolution
- semantic analysis
- Tree-sitter
- language servers
- embeddings

The purpose of the index is to enrich existing workflows without turning AgentOps into a static-analysis platform.

## 7. Evaluation Model

The evaluation framework is built around versioned suites.

The default suite is:

```text
mvp-demo-suite@v2
```

Each task contains:

- id
- priority
- workflow
- fixture id
- pass threshold
- weighted checks
- required checks

Task score is deterministic. A task passes only when:

- the weighted score meets the threshold
- all required checks pass

The current v2 suite has six P0 tasks:

- `repository-architecture`
- `onboarding-guide`
- `pr-review`
- `incident-rca`
- `static-ts-index`
- `repository-evolution`

## 8. Regression And Tracing

Evaluation runs are persisted under `.agentops/eval-runs/`.

Regression reports are persisted under `.agentops/regression-reports/`.

Execution traces are persisted under `.agentops/traces/`.

Trace spans are flat and local. They are useful for understanding evaluation execution, but they are not a production telemetry integration.

## 9. CI Quality Gates

The GitHub Actions workflow runs on pull requests and pushes to `main`.

The quality gate performs:

- backend dependency install
- frontend dependency install
- backend tests
- frontend build
- `mvp-demo-suite@v2` run
- baseline comparison
- artifact upload

CI fails if:

- backend tests fail
- frontend build fails
- baseline integrity is invalid
- a candidate P0 task fails
- a P0 regression is detected

## 10. Security Boundaries

AgentOps is a local-first project. It does not include authentication, sessions, OAuth, RBAC, tenant isolation, or enterprise audit retention.

Current hardening includes:

- public-repository-only GitHub workflows
- unauthenticated public metadata check before token-backed GitHub fetches
- strict evaluation artifact identifier validation
- path containment checks under `.agentops`
- exact trace lookup instead of glob lookup
- opt-in HTTP evaluation mutation endpoints

HTTP evaluation mutation endpoints require:

```bash
export AGENTOPS_ENABLE_EVALUATION_MUTATIONS=true
```

The CLI evaluation workflow does not require this flag.

## 11. How To Read The Repository

Recommended reading order:

1. `README.md`
2. `docs/project-guide.md`
3. `docs/architecture/system-overview.md`
4. `docs/architecture/design-decisions.md`
5. `docs/evaluation/methodology.md`
6. `docs/evaluation/benchmark-results.md`
7. `docs/security/security-review.md`
8. `docs/limitations/known-limitations.md`
9. `docs/case-study/agentops-case-study.md`
10. `docs/release/v1-readiness-review.md`

Recommended source-code reading order:

1. `backend/app/api/routes.py`
2. `backend/app/github/service.py`
3. `backend/app/analyzer/repository_analyzer.py`
4. `backend/app/analyzer/repository_index.py`
5. `backend/app/evaluation/suites.py`
6. `backend/app/evaluation/runner.py`
7. `backend/app/evaluation/regression.py`
8. `frontend/src/App.tsx`

## 12. Project Status

AgentOps is feature-complete as a portfolio project at v1.0.0.

Future work should focus on:

- presentation quality
- demo rehearsal
- benchmark explanation
- interview narrative
- case-study polish

Future work should not add new infrastructure unless the project goal changes.
