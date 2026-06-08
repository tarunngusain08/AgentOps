# AgentOps

AgentOps is a Production Engineering Copilot with Built-In Agent Reliability.

The current product surface is intentionally small and demo-first: a user submits a public GitHub repository URL, then chooses either an architecture report or a new-engineer onboarding guide generated from deterministic repository analysis.

## M01: Repository Understanding

The current milestone supports:

- Public GitHub repository URL parsing.
- Read-only GitHub metadata and file loading.
- Lightweight file selection with hard limits.
- Deterministic language, framework, module, entry-point, and component detection.
- A source-grounded architecture report that works without a model API key.
- A minimal React UI for Demo #1.

M01 intentionally does not include a database, vector search, RAG, tracing, evaluation, PR review, incident investigation, or multi-agent orchestration.

## M02: Documentation Assistant

M02 adds the second demo capability: a user submits a public GitHub repository URL and receives a source-grounded onboarding guide for new engineers.

The onboarding guide includes:

- Project overview.
- Technology stack.
- Evidence-backed how-to-run guidance.
- Architecture summary.
- Key components.
- Common workflows.
- Useful files.
- Assumptions.

How-to-run guidance is generated only from inspected evidence such as `package.json`, `pyproject.toml`, `requirements.txt`, `pom.xml`, `build.gradle`, `Dockerfile`, or `docker-compose.yml`. If no inspected file supports a run instruction, AgentOps states that assumption instead of inventing a command.

## Local Setup

### Backend

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -e ".[test]"
uvicorn app.main:app --reload
```

The backend runs at `http://localhost:8000`.

Useful endpoints:

- `GET /health`
- `POST /api/v1/repositories/analyze`
- `POST /api/v1/repositories/guides/onboarding`

Optional environment variable:

```bash
export GITHUB_TOKEN=...
```

If no token is configured, AgentOps uses unauthenticated GitHub API calls for public repositories.

### Frontend

```bash
cd frontend
npm install
npm run dev
```

The frontend runs at `http://localhost:5173` and calls the backend at `http://localhost:8000` by default. Use the mode selector to switch between Architecture Report and Onboarding Guide.

To point it at a different backend:

```bash
VITE_API_BASE_URL=http://localhost:8000 npm run dev
```

## Demo #1

Start the backend and frontend, then submit a public repository URL such as:

```text
https://github.com/fastapi/fastapi
```

Expected report sections:

- Architecture overview.
- Technology stack.
- Components.
- Entry points.
- Important files.
- High-level relationships.
- Assumptions.
- Analysis metadata.

## Demo #2

Start the backend and frontend, choose **Onboarding Guide**, then submit a public repository URL such as:

```text
https://github.com/fastapi/fastapi
```

Expected guide sections:

- Project Overview.
- Technology Stack.
- How To Run.
- Architecture Summary.
- Key Components.
- Common Workflows.
- Useful Files.
- Assumptions.
- Analysis metadata.

## Current Limits

Repository analysis is intentionally lightweight:

- Maximum 100 files inspected.
- Maximum 2 MB fetched file content.
- README is optional and not trusted as the primary signal.
- Repositories are not cloned locally.
- Analysis favors file structure, manifests, entry points, and directory hierarchy.
- Onboarding guides use heuristic generation and do not require a model API key.
- The system does not persist repositories, create embeddings, or perform full dependency/call-graph analysis.
