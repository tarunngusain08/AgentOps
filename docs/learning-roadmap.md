# AgentOps Learning Roadmap

This roadmap is designed for a solo backend engineer building AgentOps in 4-6 weeks. Learn only what directly unlocks the next demo.

The rule is simple:

```text
Learn just enough to ship the next demoable milestone.
```

## Week 0: Project Orientation

Goal: understand the product story before writing application code.

Learn:

- What Engineering Copilots do differently from generic chatbots.
- The six AgentOps demos and how they connect.
- Basic agent reliability concepts: traces, evals, regressions, policies.
- The modular monolith approach.

Build outcome:

- README and docs are clear enough to explain the project in 30 seconds.
- Local repo structure is ready for backend and frontend work.

Practice prompts:

- "Explain this repository architecture."
- "Review this PR for reliability risks."
- "Investigate checkout latency spike."

## Week 1: FastAPI, LangGraph, And Tool Calling

Goal: build the foundation for the first demo: repository architecture explanation.

Learn:

- FastAPI routing, request models, dependency injection, and error handling.
- LangGraph state, nodes, edges, conditional routing, and graph execution.
- Tool calling patterns: typed inputs, typed outputs, error handling, retries.
- GitHub API basics: repository metadata, file tree, file content.

Build outcome:

- Backend health endpoint.
- Basic React run form or simple API-only demo.
- LangGraph workflow with Planner and Code Agent.
- GitHub tool that can read repo metadata and selected files.
- First answer for "Explain this repository."

Suggested resources:

- FastAPI official docs for routing and Pydantic models.
- LangGraph official quickstart and state graph examples.
- GitHub REST API docs for repository contents and pull requests.

Stop learning when:

- You can run a graph that calls a GitHub tool and returns a source-grounded architecture summary.

## Week 2: Repository RAG And Source Attribution

Goal: improve repository understanding and onboarding documentation.

Learn:

- Chunking strategies for README, docs, config, and source files.
- Embedding generation.
- pgvector table setup and similarity search.
- Context assembly and source attribution.
- When to mark something as inference instead of fact.

Build outcome:

- Repository indexing endpoint.
- PostgreSQL + pgvector local setup.
- Document chunk storage.
- Semantic repository search.
- Source-grounded architecture explanation.
- Documentation Assistant workflow for onboarding docs.

Suggested resources:

- pgvector docs.
- PostgreSQL indexing basics.
- Embedding model docs from the provider used in the project.
- RAG source attribution examples.

Stop learning when:

- The agent can cite repository files and generate onboarding docs from indexed context.

## Week 3: PR Review And Incident Investigation

Goal: make the product feel like an Engineering Copilot, not a search UI.

Learn:

- GitHub pull request APIs: changed files, diffs, commits, comments.
- Code review heuristics: correctness, reliability, performance, security, tests.
- Incident RCA structure: impact, timeline, root cause, mitigation, prevention.
- Fixture-driven demos for production-like incidents.

Build outcome:

- PR Review workflow.
- PR risk classifier.
- Incident fixture for checkout latency spike.
- Incident Agent workflow that reads logs, recent changes, and code context.
- RCA output format.

Suggested resources:

- GitHub PR API docs.
- Incident postmortem templates from SRE literature.
- Examples of production PR review checklists.

Stop learning when:

- The project can demo both "Review this PR" and "Investigate checkout latency spike" end-to-end.

## Week 4: Evaluation And Regression Testing

Goal: make reliability visible and repeatable.

Learn:

- Golden-task evaluation.
- Required fact checks.
- Expected tool-use checks.
- Basic output quality scoring.
- Regression thresholds.
- Version labels for eval runs.

Build outcome:

- MVP eval suite with golden tasks for all six demos.
- Eval runner command.
- Eval result persistence.
- Regression comparison between two eval runs.
- Clear pass/fail report.

Suggested resources:

- Evaluation design notes from OpenAI, LangSmith, DeepEval, or RAGAS docs.
- Software regression testing patterns.

Stop learning when:

- You can run an eval suite and compare two versions with a regression report.

## Week 5: OpenTelemetry, Dashboard, And CI

Goal: make the reliability story visible in a live demo and automated in GitHub.

Learn:

- OpenTelemetry spans, attributes, and traces.
- Redaction of prompts, secrets, and tool payloads.
- React dashboard basics for timelines and summary views.
- GitHub Actions workflow syntax.
- PR quality gates.

Build outcome:

- Trace events for planner, agents, tools, retrieval, model calls, and eval scoring.
- Minimal dashboard with run timeline, tool calls, eval summary, and regression report.
- GitHub Action that runs tests and eval suite.
- PR output with regression status.

Suggested resources:

- OpenTelemetry Python docs.
- GitHub Actions docs.
- Simple React data-fetching and table/timeline UI examples.

Stop learning when:

- A PR can run an evaluation suite and the dashboard can show traces for an agent run.

## Week 6: Demo Polish And Interview Preparation

Goal: turn the project into an interview-ready portfolio asset.

Learn:

- How to explain agent architecture clearly.
- How to discuss tradeoffs and future scaling.
- How to write strong resume bullets.
- How to prepare a 5-minute and 15-minute demo.

Build outcome:

- Demo script for all six scenarios.
- README with screenshots or short GIFs.
- Architecture diagram.
- Interview-prep notes.
- Clean backlog showing MVP complete and Phase 2 deferred.

Stop learning when:

- You can demo AgentOps live and explain why each technical decision was made.

## Learning Priorities By Demo

| Demo | Learn first | Avoid until later |
| --- | --- | --- |
| Explain repository | GitHub file APIs, LangGraph basics | Deep static analysis engines |
| Review PR | PR diffs, review heuristics | Full code execution sandboxes |
| Onboarding docs | RAG, source attribution | Complex doc-generation pipelines |
| Incident RCA | Fixture design, RCA format | Real observability integrations |
| Eval suite | Golden tasks, deterministic scoring | Large benchmark frameworks |
| Regression report | Compare eval runs, thresholds | Statistical eval platforms |

## Anti-Patterns To Avoid

- Reading every framework guide before building.
- Implementing a generic agent framework.
- Building dashboards before workflows work.
- Adding integrations beyond GitHub in MVP.
- Spending a full week on schema design.
- Treating evaluation as a research project before golden tasks exist.

## Weekly Checkpoint Questions

At the end of every week, answer:

- What can I demo now that I could not demo last week?
- Which of the six scenarios moved closer to end-to-end?
- What did I defer to protect MVP completion?
- Is the project still finishable in 4-6 weeks?
- What is the strongest resume bullet unlocked so far?
