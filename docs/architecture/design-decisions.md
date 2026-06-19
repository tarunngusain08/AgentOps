# AgentOps Design Decisions

This document captures the main v1.0.0 architecture decisions in ADR style.

## Decision: No LLM-as-Judge

Status: Accepted

Context: Evaluation must be reproducible and suitable for CI. LLM judges can vary across model versions, prompts, providers, and sampling behavior.

Alternatives:

- GPT-based judge
- human-only review
- deterministic checks

Decision: AgentOps uses deterministic expected-fact matching, weighted checks, and required-check gates.

Consequences:

- Positive: reproducible local and CI behavior.
- Positive: failed checks can show expected and actual values.
- Negative: scoring is less nuanced than expert human review.
- Evidence: `backend/app/evaluation/matcher.py`, `runner.py`, and `suites.py`.

## Decision: Local-First Execution

Status: Accepted

Context: AgentOps is a portfolio-grade system intended to run without hosted infrastructure.

Alternatives:

- hosted SaaS
- database-backed service
- local artifacts

Decision: AgentOps stores evaluation runs, traces, and regression reports under `.agentops/`.

Consequences:

- Positive: easy local demo and CI execution.
- Positive: no database is required.
- Negative: run ids are local to the runtime directory.
- Evidence: `.gitignore`, `backend/app/evaluation/storage.py`.

## Decision: No Vector Database In v1

Status: Accepted

Context: Current workflows are intentionally lightweight and fixture-backed. The repo does not need semantic retrieval to demonstrate evaluation, regression, and quality gates.

Alternatives:

- pgvector
- Pinecone or Qdrant
- deterministic selected-file analysis

Decision: v1 uses selected files, repository structure, manifests, fixtures, and shallow static intelligence.

Consequences:

- Positive: smaller operational surface.
- Positive: deterministic behavior is easier to explain.
- Negative: AgentOps is not a semantic search product.
- Evidence: `backend/app/analyzer/file_selection.py`, `backend/app/analyzer/repository_index.py`.

## Decision: RepositoryIndex Instead Of Tree-sitter

Status: Accepted

Context: M08 needed reusable static code intelligence without parser dependency complexity.

Alternatives:

- Tree-sitter
- language server protocol
- shallow regex and AST extraction

Decision: AgentOps uses Python `ast` for Python and shallow deterministic extraction for TypeScript/JavaScript and Go.

Consequences:

- Positive: no parser framework dependency.
- Positive: simple fixtures can test symbol, import, and test-link extraction.
- Negative: no full syntax tree, type resolution, or call graph.
- Evidence: `backend/app/analyzer/repository_index.py`, `backend/tests/test_repository_index.py`.

## Decision: Versioned Evaluation Baselines

Status: Accepted

Context: Evaluation results should be comparable over time, but suite changes must not silently invalidate older baselines.

Alternatives:

- one moving suite
- unversioned snapshots
- versioned suites and baselines

Decision: AgentOps keeps `mvp-demo-suite@v1` readable and defaults to `mvp-demo-suite@v2` with a tracked baseline file.

Consequences:

- Positive: older results remain understandable.
- Positive: CI can compare against a pinned baseline.
- Negative: suite changes require baseline review.
- Evidence: `backend/app/evaluation/suites.py`, `backend/app/evaluation/baselines/mvp-demo-suite@v2.json`.

## Decision: CI Quality Gates

Status: Accepted

Context: The project needs to demonstrate that Engineering Copilot regressions can block a change like ordinary tests.

Alternatives:

- local-only evaluation
- manual reviewer judgment
- GitHub Actions quality gate

Decision: `.github/workflows/agentops-quality.yml` runs tests, build, evaluation, and baseline comparison.

Consequences:

- Positive: regressions are visible on pull requests.
- Positive: generated artifacts are uploaded for inspection.
- Negative: the gate only covers the versioned golden-task suite.
- Evidence: `.github/workflows/agentops-quality.yml`.

