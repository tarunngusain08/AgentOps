# Known Limitations

AgentOps is intentionally scoped as a deterministic, local-first Engineering Copilot evaluation project. This document states the current boundaries.

These limits are part of the design. The project is meant to be understandable, runnable, and reviewable as a portfolio system. It is not trying to become a hosted enterprise developer platform.

## Supported Languages For Static Intelligence

- Python
- TypeScript
- JavaScript
- Go

## Not Supported For Static Intelligence

- Java
- C#
- Rust
- C++
- Ruby
- PHP
- Kotlin
- Swift

Unsupported languages may still appear in repository file lists or high-level repository structure, but they do not receive first-class static symbol/import extraction.

If an unsupported language dominates a repository, AgentOps may still identify manifests, top-level structure, and some important files, but the `RepositoryIndex` will not provide rich symbols, imports, or test links for that language.

## Repository Intelligence Limits

AgentOps does not implement:

- call graphs
- type resolution
- semantic analysis
- language server integration
- Tree-sitter integration
- full dependency graph construction
- full repository cloning
- large-repository indexing beyond configured selection limits

The current repository analysis inspects selected files and uses a maximum file count and byte budget.

This means AgentOps is optimized for fast architecture understanding, not exhaustive repository indexing. Very large monorepos may be truncated, and truncation metadata should be treated as part of the output.

## Workflow Limits

Architecture reports, onboarding guides, PR review, and incident RCA are deterministic and heuristic-first. They are designed for demoable engineering workflows, not exhaustive production analysis.

PR review does not perform:

- code correctness verification
- security auditing
- vulnerability scanning
- performance analysis
- style enforcement
- GitHub review comment posting

Incident investigation currently uses the synthetic `checkout-latency@v1` fixture. It is not connected to Datadog, Prometheus, Grafana, OpenTelemetry collectors, logs, or production telemetry systems.

The RCA workflow is useful for demonstrating evidence modeling and deterministic reasoning. It is not an operational incident-management product.

## Evaluation Limits

Evaluation is golden-task based. It validates pinned fixtures and expected facts, not arbitrary repository quality.

The default suite is `mvp-demo-suite@v2`. It is useful for regression detection inside AgentOps, but it is not a public benchmark for all Engineering Copilot systems.

Scores should be interpreted as project-local quality signals. They should not be presented as external benchmark superiority claims.

## Runtime Limits

- `.agentops/` runtime artifacts are local and ignored by git.
- Run ids are unique only within the local runtime directory.
- Concurrent evaluation run generation is unsupported.
- Regression comparison requires matching suite id, suite version, task ids, and check ids.
- Execution traces are local JSON timelines, not provider-backed telemetry.

Deleting `.agentops/` removes local evaluation history. The tracked baseline files under `backend/app/evaluation/baselines/` remain in git.

## Platform Limits

AgentOps does not include:

- hosted deployment
- database persistence
- multi-repository workspace management
- authentication
- RBAC
- billing
- organization administration
- enterprise audit retention
