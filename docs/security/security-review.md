# Security Review

Review date: 2026-06-19

Reviewed commit: `5ac6694fb16608a077877f539c45cafd4d0bfed4`

This review documents the M08.1 hardening work and residual risks visible in the current source tree.

## Mitigated Risks

### GitHub Token Protection

Status: Mitigated

Evidence:

- `backend/app/github/service.py` defines `PUBLIC_REPOSITORY_ERROR`.
- `GitHubService._get_public_repository_metadata` calls GitHub metadata with `use_token=False`.
- `GitHubService.load_repository` uses public metadata before tree and content loading.

Impact: A configured `GITHUB_TOKEN` is used only after the submitted repository has been confirmed public.

### Evaluation Identifier Validation

Status: Mitigated

Evidence:

- `backend/app/evaluation/identifiers.py` defines `SAFE_IDENTIFIER_RE`.
- `validate_evaluation_identifier` is applied to suite ids, suite versions, run ids, trace ids, and report ids through storage paths.

Impact: Inputs such as path traversal segments and glob characters are rejected before artifact path construction.

### Path Containment

Status: Mitigated

Evidence:

- `backend/app/evaluation/identifiers.py` defines `validate_contained_path`.
- `backend/app/evaluation/storage.py` calls path containment validation before run, trace, and regression report access.

Impact: Artifact paths must remain under the expected `.agentops` storage roots.

### Trace Lookup

Status: Mitigated

Evidence:

- `EvaluationStorage.load_trace` validates `trace_id`, then searches run directories by exact filename match.
- It does not use `Path.glob(f"*/{trace_id}.json")`.

Impact: Trace lookup does not allow wildcard trace id expansion.

### Evaluation Mutation Controls

Status: Mitigated

Evidence:

- `backend/app/api/routes.py` defines `AGENTOPS_ENABLE_EVALUATION_MUTATIONS`.
- `POST /api/v1/evaluations/run` and `POST /api/v1/evaluations/compare` call `_require_evaluation_mutations_enabled`.
- CLI evaluation commands call evaluation services directly and do not require this HTTP flag.

Impact: HTTP artifact creation is opt-in for local demos.

## Accepted Risks

### No Authentication System

AgentOps intentionally does not include users, sessions, OAuth, RBAC, or multi-tenant controls. The README documents this explicitly. This is accepted for a local-first portfolio project.

### Public GitHub API Dependency

GitHub-backed workflows depend on public GitHub API availability. This is accepted because M01-M04 target public repositories and M05-M07 use local fixtures for evaluation.

### Local Artifact Storage

Evaluation runs, traces, and regression reports are local JSON files under `.agentops/`. The system assumes single-process local evaluation execution. This is accepted for the current project scope.

## Out-Of-Scope Risks

- SaaS tenant isolation
- user authentication
- hosted secrets management
- production incident data ingestion
- vulnerability scanning
- static security analysis
- dependency vulnerability auditing
- sandboxed code execution

## Security Posture Summary

The v1.0.0 codebase is hardened for its stated local-first scope. The main security controls are public-repository-only GitHub access, strict evaluation artifact identifiers, path containment checks, exact trace lookup, and opt-in HTTP evaluation mutations.

