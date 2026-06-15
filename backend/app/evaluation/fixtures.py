from __future__ import annotations

from app.github.pull_request_loader import PullRequestFile, PullRequestSnapshot
from app.github.service import GitHubFile, RepositorySnapshot


def repository_fixture() -> RepositorySnapshot:
    return RepositorySnapshot(
        owner="example",
        name="service",
        default_branch="main",
        html_url="https://github.com/example/service",
        description="Fixture service for deterministic evaluation",
        primary_language="Python",
        topics=[],
        tree_paths=[
            "pyproject.toml",
            "app/main.py",
            "app/services/checkout.py",
            "tests/test_checkout.py",
        ],
        top_level_directories=["app", "tests"],
        selected_paths=["pyproject.toml", "app/main.py"],
        files=[
            GitHubFile("pyproject.toml", 'dependencies = ["fastapi", "pydantic"]', 40, "manifest"),
            GitHubFile("app/main.py", "from fastapi import FastAPI\napp = FastAPI()", 42, "entry_point"),
        ],
        truncated=False,
    )


def pull_request_fixture() -> PullRequestSnapshot:
    return PullRequestSnapshot(
        owner="example",
        repo="service",
        number=8,
        title="Update FastAPI dependency and app entry point",
        state="open",
        html_url="https://github.com/example/service/pull/8",
        base_branch="main",
        head_branch="feature/update-fastapi",
        author="developer",
        changed_files=2,
        files=[
            PullRequestFile(
                filename="pyproject.toml",
                status="modified",
                additions=2,
                deletions=1,
                changes=3,
                patch="@@ fastapi dependency",
            ),
            PullRequestFile(
                filename="app/main.py",
                status="modified",
                additions=8,
                deletions=2,
                changes=10,
                patch="@@ app entry point",
            ),
        ],
        truncated=False,
    )

