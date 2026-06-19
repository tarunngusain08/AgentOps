# Known Limitations

AgentOps is intentionally scoped as a deterministic, local-first Engineering Copilot evaluation project. This document states the current boundaries.

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

## Evaluation Limits

Evaluation is golden-task based. It validates pinned fixtures and expected facts, not arbitrary repository quality.

The default suite is `mvp-demo-suite@v2`. It is useful for regression detection inside AgentOps, but it is not a public benchmark for all Engineering Copilot systems.

## Runtime Limits

- `.agentops/` runtime artifacts are local and ignored by git.
- Run ids are unique only within the local runtime directory.
- Concurrent evaluation run generation is unsupported.
- Regression comparison requires matching suite id, suite version, task ids, and check ids.
- Execution traces are local JSON timelines, not provider-backed telemetry.

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

