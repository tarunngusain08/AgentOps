# AgentOps Case Study

## Problem

Engineering copilots are useful only when their outputs can be trusted, reviewed, and regression-tested. AgentOps explores that problem through a local-first portfolio project: deterministic repository workflows plus deterministic evaluation and CI gates.

## Constraints

AgentOps was built with these constraints:

- no LLM-as-judge scoring
- no external evaluation service
- no database
- public GitHub repositories only for user-submitted repository workflows
- local runtime artifacts
- reproducible golden-task evaluation
- one demoable capability per milestone

## Design

AgentOps has two connected halves.

The first half is the Engineering Copilot surface:

- repository architecture report
- onboarding guide
- PR review
- fixture-driven incident RCA

The second half is the reliability surface:

- versioned golden-task evaluation
- regression comparison
- execution traces
- GitHub Actions quality gates
- deterministic static repository intelligence

The design keeps the workflows small enough to inspect while adding the quality infrastructure needed to detect regressions.

## Challenges

### Evaluation Design

The evaluation system needed to avoid subjective scoring. AgentOps solves this with weighted checks, required checks, expected facts, fixture versions, canonical JSON, and result hashes.

Evidence:

- `backend/app/evaluation/suites.py`
- `backend/app/evaluation/runner.py`
- `backend/app/evaluation/hashing.py`

### Regression Detection

Regression comparison needed to distinguish task failures, score changes, and required-check changes. AgentOps implements same-suite, same-version comparison in `backend/app/evaluation/regression.py`.

### Repository Intelligence

Repository intelligence needed to improve workflow context without becoming a parser platform. AgentOps introduced `RepositoryIndex` for shallow Python, TypeScript/JavaScript, and Go extraction.

Evidence:

- `backend/app/analyzer/repository_index.py`
- `backend/tests/test_repository_index.py`

### Security Hardening

Security hardening needed to close local demo risks without adding a full auth system. AgentOps added public-repository-only GitHub access, strict artifact identifiers, path containment, exact trace lookup, and opt-in HTTP evaluation mutation endpoints.

Evidence:

- `backend/app/github/service.py`
- `backend/app/evaluation/identifiers.py`
- `backend/app/evaluation/storage.py`
- `backend/app/api/routes.py`

## Results

The v1-readiness run produced:

- backend tests: `89 passed, 1 warning`
- frontend build: passed
- evaluation suite: `6` total tasks, `6` passed, `0` failed
- regression report: `NO_CHANGE`
- P0 regressions: `0`

Evidence:

- `.agentops/eval-runs/v1-readiness.json`
- `.agentops/regression-reports/regression-run-000001-vs-run-000011.json`
- `docs/evaluation/benchmark-results.md`

These are local project results, not production adoption metrics or productivity claims.

## Lessons Learned

- Deterministic checks are easier to gate in CI than model-judged scores.
- Versioned fixtures and baselines make evaluation changes reviewable.
- A shallow repository index can improve workflows without adding parser framework complexity.
- Security posture can be improved with narrow controls before adding authentication.
- Portfolio projects benefit from explicit non-goals because they keep scope understandable.

## Future Directions

Future work should be evaluated against the current scope. Plausible additions include richer fixtures, case-study polish, or benchmark documentation. The project should avoid adding major platform capabilities unless the product goal changes.
