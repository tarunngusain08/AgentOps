# AgentOps

AgentOps is a Production Engineering Copilot with Built-In Agent Reliability.

M01 implements the first demo capability: a user submits a public GitHub repository URL and receives a lightweight architecture report generated from deterministic repository analysis.

## M01: Repository Understanding

The current milestone supports:

- Public GitHub repository URL parsing.
- Read-only GitHub metadata and file loading.
- Lightweight file selection with hard limits.
- Deterministic language, framework, module, entry-point, and component detection.
- A source-grounded architecture report that works without a model API key.
- A minimal React UI for Demo #1.

M01 intentionally does not include a database, vector search, RAG, tracing, evaluation, PR review, incident investigation, or multi-agent orchestration.

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

The frontend runs at `http://localhost:5173` and calls the backend at `http://localhost:8000` by default.

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

## M01 Limits

Repository analysis is intentionally lightweight:

- Maximum 100 files inspected.
- Maximum 2 MB fetched file content.
- README is optional and not trusted as the primary signal.
- Repositories are not cloned locally.
- Analysis favors file structure, manifests, entry points, and directory hierarchy.
