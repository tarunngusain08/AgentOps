from fastapi.testclient import TestClient

from app.github.service import GitHubFile, ParsedRepository, RepositorySnapshot
from app.github.service import GitHubError
from app.incident.fixtures import FixtureValidationError
from app.main import app


class FakeGitHubService:
    def ensure_public_repository(self, repository_url: str) -> ParsedRepository:
        assert repository_url == "https://github.com/example/service"
        return ParsedRepository(owner="example", name="service")

    def load_repository(self, repository_url: str) -> RepositorySnapshot:
        assert repository_url == "https://github.com/example/service"
        return RepositorySnapshot(
            owner="example",
            name="service",
            default_branch="main",
            html_url="https://github.com/example/service",
            description="Example service",
            primary_language="Python",
            topics=[],
            tree_paths=["pyproject.toml", "app/main.py", "app/services/checkout.py", "tests/test_checkout.py"],
            top_level_directories=["app"],
            selected_paths=["pyproject.toml", "app/main.py", "app/services/checkout.py", "tests/test_checkout.py"],
            files=[
                GitHubFile("pyproject.toml", 'dependencies = ["fastapi"]', 25, "manifest"),
                GitHubFile("app/main.py", "from fastapi import FastAPI", 27, "entry_point"),
                GitHubFile(
                    "app/services/checkout.py",
                    "class CheckoutService:\n    def process_checkout(self):\n        return True\n",
                    72,
                    "source_code",
                ),
                GitHubFile(
                    "tests/test_checkout.py",
                    "from app.services.checkout import CheckoutService\n\ndef test_process_checkout():\n    assert CheckoutService\n",
                    97,
                    "test_code",
                ),
            ],
            truncated=False,
        )

    def request_json(self, path: str):
        if path == "/repos/example/service/pulls/8":
            return {
                "number": 8,
                "title": "Add review workflow",
                "state": "open",
                "html_url": "https://github.com/example/service/pull/8",
                "base": {"ref": "main"},
                "head": {"ref": "feature/review"},
                "user": {"login": "developer"},
                "changed_files": 3,
            }
        if path == "/repos/example/service/pulls/8/files?per_page=100&page=1":
            return [
                {
                    "filename": "pyproject.toml",
                    "status": "modified",
                    "additions": 2,
                    "deletions": 1,
                    "changes": 3,
                    "patch": "@@ dependency",
                },
                {
                    "filename": "app/main.py",
                    "status": "modified",
                    "additions": 8,
                    "deletions": 2,
                    "changes": 10,
                    "patch": "@@ entry",
                },
                {
                    "filename": "README.md",
                    "status": "modified",
                    "additions": 2,
                    "deletions": 0,
                    "changes": 2,
                    "patch": "@@ docs",
                },
            ]
        raise AssertionError(f"Unexpected path: {path}")


def test_health_endpoint():
    client = TestClient(app)

    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_analyze_endpoint_uses_github_service_and_returns_report(monkeypatch):
    import app.api.routes as routes

    monkeypatch.setattr(routes, "GitHubService", FakeGitHubService)
    client = TestClient(app)

    response = client.post(
        "/api/v1/repositories/analyze",
        json={"repository_url": "https://github.com/example/service"},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["repository"]["owner"] == "example"
    assert body["analysis_metadata"]["files_inspected"] == 4
    assert "FastAPI" in body["report"]["technology_stack"]
    assert body["report"]["entry_points"] == ["app/main.py"]
    assert body["report"]["code_intelligence"]["metadata"]["symbols_found"] >= 2
    assert any("CheckoutService" in item for item in body["report"]["code_intelligence"]["top_symbols"])


def test_onboarding_guide_endpoint_uses_github_service_and_returns_guide(monkeypatch):
    import app.api.routes as routes

    monkeypatch.setattr(routes, "GitHubService", FakeGitHubService)
    client = TestClient(app)

    response = client.post(
        "/api/v1/repositories/guides/onboarding",
        json={"repository_url": "https://github.com/example/service"},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["repository"]["owner"] == "example"
    assert body["analysis_metadata"]["analysis_mode"] == "heuristic"
    assert body["guide"]["title"] == "Onboarding Guide for example/service"
    assert [section["title"] for section in body["guide"]["sections"]] == [
        "Project Overview",
        "Technology Stack",
        "How To Run",
        "Architecture Summary",
        "Key Components",
        "Code Navigation",
        "Common Workflows",
        "Useful Files",
        "Assumptions",
    ]
    how_to_run = next(section for section in body["guide"]["sections"] if section["title"] == "How To Run")
    assert any(item["evidence"] == ["pyproject.toml"] for item in how_to_run["items"])


def test_pull_request_review_endpoint_uses_github_service_and_returns_review(monkeypatch):
    import app.api.routes as routes

    monkeypatch.setattr(routes, "GitHubService", FakeGitHubService)
    client = TestClient(app)

    response = client.post(
        "/api/v1/repositories/pull-requests/review",
        json={
            "repository_url": "https://github.com/example/service",
            "pull_request_number": 8,
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert body["repository"]["owner"] == "example"
    assert body["pull_request"]["number"] == 8
    assert body["analysis_metadata"]["changed_files"] == 3
    assert body["analysis_metadata"]["analysis_mode"] == "heuristic"
    assert body["review"]["confidence"] == "High"
    assert body["review"]["findings"]
    assert all(finding["evidence"] for finding in body["review"]["findings"])
    assert {finding["category"] for finding in body["review"]["findings"]} >= {
        "potential_risk",
        "testing_concern",
    }


def test_incident_investigation_endpoint_returns_traceable_rca(monkeypatch):
    import app.api.routes as routes

    monkeypatch.setattr(routes, "GitHubService", FakeGitHubService)
    client = TestClient(app)

    response = client.post(
        "/api/v1/incidents/investigate",
        json={
            "scenario_id": "checkout-latency",
            "repository_url": "https://github.com/example/service",
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert body["scenario_id"] == "checkout-latency"
    assert body["analysis_metadata"]["fixture_version"] == "v1"
    assert body["analysis_metadata"]["repository_analyzed"] is True
    assert body["rca"]["confidence"] == "High"
    assert body["rca"]["suspected_root_cause"]["category"] == "CONNECTION_POOL_REGRESSION"
    assert body["rca"]["summary"]["evidence_ids"]
    assert body["rca"]["mitigation"]["evidence_ids"]
    assert body["rca"]["repository_context"]


def test_incident_investigation_endpoint_allows_missing_repository_url():
    client = TestClient(app)

    response = client.post(
        "/api/v1/incidents/investigate",
        json={"scenario_id": "checkout-latency"},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["analysis_metadata"]["repository_analyzed"] is False
    assert any("No repository URL" in assumption for assumption in body["rca"]["assumptions"])


def test_incident_investigation_repository_failure_still_returns_rca(monkeypatch):
    import app.api.routes as routes

    class FailingGitHubService:
        def load_repository(self, repository_url: str):
            raise GitHubError("rate limited", status_code=502)

    monkeypatch.setattr(routes, "GitHubService", FailingGitHubService)
    client = TestClient(app)

    response = client.post(
        "/api/v1/incidents/investigate",
        json={
            "scenario_id": "checkout-latency",
            "repository_url": "https://github.com/example/service",
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert body["analysis_metadata"]["repository_analyzed"] is False
    assert any("Repository analysis was unavailable" in assumption for assumption in body["rca"]["assumptions"])


def test_incident_investigation_unknown_scenario_returns_structured_error():
    client = TestClient(app)

    response = client.post(
        "/api/v1/incidents/investigate",
        json={"scenario_id": "checkout-latency-v2"},
    )

    assert response.status_code == 404
    assert response.json() == {
        "detail": {
            "code": "SCENARIO_NOT_FOUND",
            "message": "Unknown scenario: checkout-latency-v2",
        }
    }


def test_incident_investigation_empty_scenario_fails_validation():
    client = TestClient(app)

    response = client.post(
        "/api/v1/incidents/investigate",
        json={"scenario_id": ""},
    )

    assert response.status_code == 422


def test_incident_investigation_malformed_fixture_returns_structured_error(monkeypatch):
    import app.api.routes as routes

    class BrokenIncidentInvestigationService:
        def __init__(self, github_service=None):
            pass

        def investigate(self, scenario_id: str, repository_url: str | None = None):
            raise FixtureValidationError("checkout-latency@v1")

    monkeypatch.setattr(routes, "IncidentInvestigationService", BrokenIncidentInvestigationService)
    client = TestClient(app)

    response = client.post(
        "/api/v1/incidents/investigate",
        json={"scenario_id": "checkout-latency"},
    )

    assert response.status_code == 500
    assert response.json() == {
        "detail": {
            "code": "FIXTURE_VALIDATION_ERROR",
            "message": "Scenario fixture is invalid: checkout-latency@v1",
        }
    }


def test_evaluation_mutation_endpoints_require_explicit_opt_in(monkeypatch):
    monkeypatch.delenv("AGENTOPS_ENABLE_EVALUATION_MUTATIONS", raising=False)
    client = TestClient(app)

    response = client.post(
        "/api/v1/evaluations/run",
        json={"suite_id": "mvp-demo-suite@v2", "version_label": "api-test"},
    )

    assert response.status_code == 403
    assert response.json()["detail"]["code"] == "EVALUATION_MUTATIONS_DISABLED"


def test_read_only_evaluation_endpoint_rejects_invalid_identifiers():
    client = TestClient(app)

    response = client.get(
        "/api/v1/evaluations/runs/run-000001",
        params={"suite_id": "mvp-demo-suite", "suite_version": "v2/../../../outside"},
    )

    assert response.status_code == 400
    assert response.json()["detail"]["code"] == "EVALUATION_IDENTIFIER_INVALID"
