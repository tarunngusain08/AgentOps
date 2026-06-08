# AgentOps MVP Backlog

This backlog converts the portfolio plan into executable work. P0 scope maps only to the six required demo scenarios.

Priority definitions:

- P0: required for one of the six MVP demos.
- P1: polish after all P0 demos work.
- P2: Phase 2 or future work.

MVP completion rule:

```text
The MVP is complete when all six P0 demo scenarios work end-to-end.
No P1 or P2 item should delay MVP completion.
```

## P0 Epic Summary

| Epic | Demo scenario | Target outcome |
| --- | --- | --- |
| Repository Understanding | Explain repository architecture | User can ask "Explain this repository" and get grounded architecture output. |
| PR Review | Review a pull request | User can ask "Review PR #N" and get risk findings. |
| Documentation Assistant | Generate onboarding documentation | User can generate onboarding docs from repository context. |
| Incident Investigation | Investigate incident and RCA | User can investigate checkout latency spike fixture and get RCA. |
| Evaluation Framework | Execute evaluation suite | User can run golden tasks and see pass/fail scores. |
| Regression Reports | Compare versions and detect regressions | User can compare eval runs and identify regressions. |

## EPIC: Repository Understanding

| Field | Value |
| --- | --- |
| Feature | Repository architecture explanation |
| Story | As a user, I want the agent to explain repository architecture so that I can onboard quickly. |
| Acceptance Criteria | Repository can be registered by GitHub URL; selected files are fetched; planner creates analysis steps; Code Agent identifies components and important files; final answer includes architecture overview, component relationships, important files, and uncertainty notes; answer cites source files. |
| Estimated Effort | 5 days |
| Priority | P0 |

Implementation notes:

- Start with public repositories and read-only GitHub access.
- Prefer selected file fetching over full repository ingestion.
- Use source paths even before line-level citations are implemented.

## EPIC: PR Review

| Field | Value |
| --- | --- |
| Feature | GitHub PR risk review |
| Story | As a user, I want the agent to review a pull request and identify risks so that I can catch issues before merge. |
| Acceptance Criteria | User can provide repository and PR number; GitHub tool fetches PR metadata and changed files; Code Agent summarizes changed areas; agent identifies correctness, reliability, performance, security, and test risks; final answer includes severity, rationale, suggested fixes, and merge recommendation. |
| Estimated Effort | 5 days |
| Priority | P0 |

Implementation notes:

- Use GitHub PR changed-files API.
- Keep review output structured and concise.
- Do not implement PR commenting in MVP until the review workflow works.

## EPIC: Documentation Assistant

| Field | Value |
| --- | --- |
| Feature | Service onboarding documentation generator |
| Story | As a new engineer, I want the copilot to generate onboarding documentation so that I can understand a service quickly. |
| Acceptance Criteria | Repository docs and selected source files are indexed; Documentation Agent retrieves relevant context; generated doc includes service purpose, setup, architecture, key workflows, important files, and troubleshooting notes; claims include source attribution or uncertainty markers. |
| Estimated Effort | 4 days |
| Priority | P0 |

Implementation notes:

- Reuse repository RAG from architecture explanation.
- Output Markdown so it can become a future docs artifact.
- Avoid trying to generate every possible runbook section in MVP.

## EPIC: Incident Investigation

| Field | Value |
| --- | --- |
| Feature | Checkout latency RCA workflow |
| Story | As an engineer on call, I want the copilot to investigate a latency spike so that I can identify likely root cause and mitigation. |
| Acceptance Criteria | User can run the checkout latency spike scenario; incident fixture includes logs, deployment event, and risky PR/code change; Planner creates investigation steps; Incident Agent correlates symptoms with recent changes; final RCA includes impact, evidence, root cause, confidence, mitigation, and prevention. |
| Estimated Effort | 6 days |
| Priority | P0 |

Implementation notes:

- Use fixture data for MVP instead of real observability integrations.
- Make the RCA clear enough to demo in under 5 minutes.
- Seed one obvious regression, such as a connection pool configuration or inefficient query path.

## EPIC: Evaluation Framework

| Field | Value |
| --- | --- |
| Feature | Golden-task evaluation runner |
| Story | As a builder of AI agents, I want to run repeatable golden tasks so that I can detect whether agent behavior is reliable. |
| Acceptance Criteria | MVP eval suite contains golden tasks for the demo workflows; eval runner executes tasks against the agent; scoring checks required facts, expected tool calls, source attribution, policy compliance, latency, and cost; results are persisted and summarized. |
| Estimated Effort | 5 days |
| Priority | P0 |

Implementation notes:

- Start with deterministic scoring.
- Add optional LLM judge only after required facts and tool checks are stable.
- Keep eval output readable in CLI before building dashboard polish.

## EPIC: Regression Reports

| Field | Value |
| --- | --- |
| Feature | Evaluation run comparison |
| Story | As a maintainer, I want to compare two agent versions so that regressions are visible before shipping. |
| Acceptance Criteria | User can compare two eval runs; report shows pass-rate change, regressed tasks, improved tasks, latency change, cost change, and policy violations; P0 task pass-to-fail regression is flagged; report can be used in GitHub Actions output. |
| Estimated Effort | 3 days |
| Priority | P0 |

Implementation notes:

- Store version labels with eval runs.
- Keep thresholds simple.
- CI integration can initially print the report to logs.

## Supporting P0 Foundations

These foundations are P0 only because they directly enable the six demos.

| Feature | Acceptance Criteria | Effort | Priority |
| --- | --- | --- | --- |
| FastAPI backend shell | Health endpoint, basic settings, typed API models, test setup | 1 day | P0 |
| LangGraph runtime shell | Planner and one agent node can execute with persisted run state | 2 days | P0 |
| GitHub tool layer | Read-only tools for repo metadata, files, PRs, commits | 3 days | P0 |
| PostgreSQL + pgvector setup | Local database, migrations, repository/chunk tables | 2 days | P0 |
| Basic trace events | Agent run timeline captures planner, tool, retrieval, and final answer events | 2 days | P0 |
| Minimal dashboard | Run form, run timeline, eval summary, regression report | 4 days | P0 |
| GitHub Actions quality gate | Tests and eval command run in CI | 2 days | P0 |

## P1 Polish After MVP Works

| Feature | Acceptance Criteria | Effort | Priority |
| --- | --- | --- | --- |
| README demo guide | README explains value, setup, six demos, and architecture | 1 day | P1 |
| Screenshots or GIFs | Dashboard and sample outputs are captured | 1 day | P1 |
| PR comment output | GitHub Action posts regression summary as PR comment | 1-2 days | P1 |
| Better line citations | Source references include line ranges where available | 1-2 days | P1 |
| Demo data reset command | Fixtures and eval runs can be reset locally | 1 day | P1 |

## P2 Deferred Scope

| Feature | Reason deferred |
| --- | --- |
| Jira integration | Not required for six demos. |
| Confluence integration | Repository docs are enough for MVP. |
| Real log/metrics integrations | Incident fixture is enough for portfolio demo. |
| RBAC and multi-tenancy | Enterprise SaaS complexity without MVP demo value. |
| Plugin framework | Adds abstraction before repeated tool patterns exist. |
| Advanced policy DSL | Simple policy limits are enough for MVP. |
| Kubernetes deployment | Local Docker Compose and CI are enough. |
| Advanced dashboard analytics | Minimal trace/eval views are enough. |
| Billing and usage plans | No portfolio value for MVP. |

## Definition Of Done

For every P0 story:

- Workflow can be triggered from API or dashboard.
- Output can be demonstrated in under 5 minutes.
- Trace events are recorded.
- At least one golden task covers the workflow.
- Failure mode is documented.
- No unrelated enterprise feature was added to complete it.

## Suggested Build Order

1. FastAPI backend shell.
2. LangGraph runtime shell.
3. GitHub repository tools.
4. Repository Understanding demo.
5. RAG and source attribution.
6. Documentation Assistant demo.
7. GitHub PR tools.
8. PR Review demo.
9. Incident fixture.
10. Incident Investigation demo.
11. Evaluation runner.
12. Regression reports.
13. Minimal dashboard.
14. GitHub Actions quality gate.
15. README and interview polish.
