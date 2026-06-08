from fastapi.testclient import TestClient

from app.github.service import GitHubFile, RepositorySnapshot
from app.main import app


class FakeGitHubService:
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
            tree_paths=["pyproject.toml", "app/main.py"],
            top_level_directories=["app"],
            selected_paths=["pyproject.toml", "app/main.py"],
            files=[
                GitHubFile("pyproject.toml", 'dependencies = ["fastapi"]', 25, "manifest"),
                GitHubFile("app/main.py", "from fastapi import FastAPI", 27, "entry_point"),
            ],
            truncated=False,
        )


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
    assert body["analysis_metadata"]["files_inspected"] == 2
    assert "FastAPI" in body["report"]["technology_stack"]
    assert body["report"]["entry_points"] == ["app/main.py"]


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
        "Common Workflows",
        "Useful Files",
        "Assumptions",
    ]
    how_to_run = next(section for section in body["guide"]["sections"] if section["title"] == "How To Run")
    assert any(item["evidence"] == ["pyproject.toml"] for item in how_to_run["items"])
