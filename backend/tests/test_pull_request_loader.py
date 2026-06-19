from app.github.pull_request_loader import PullRequestLoader
from app.github.service import ParsedRepository


class FakeGitHubService:
    def ensure_public_repository(self, repository_url: str) -> ParsedRepository:
        assert repository_url == "https://github.com/example/service"
        return ParsedRepository(owner="example", name="service")

    def request_json(self, path: str):
        if path == "/repos/example/service/pulls/12":
            return {
                "number": 12,
                "title": "Update API dependencies",
                "state": "open",
                "html_url": "https://github.com/example/service/pull/12",
                "base": {"ref": "main"},
                "head": {"ref": "feature/dependencies"},
                "user": {"login": "developer"},
                "changed_files": 2,
            }
        if path == "/repos/example/service/pulls/12/files?per_page=100&page=1":
            return [
                {
                    "filename": "pyproject.toml",
                    "status": "modified",
                    "additions": 3,
                    "deletions": 1,
                    "changes": 4,
                    "patch": "@@ dependency update",
                },
                {
                    "filename": "app/main.py",
                    "status": "modified",
                    "additions": 8,
                    "deletions": 2,
                    "changes": 10,
                    "patch": "@@ app change",
                },
            ]
        raise AssertionError(f"Unexpected path: {path}")


def test_pull_request_loader_loads_pr_metadata_and_files():
    loader = PullRequestLoader(service=FakeGitHubService())

    snapshot = loader.load("https://github.com/example/service", 12)

    assert snapshot.owner == "example"
    assert snapshot.repo == "service"
    assert snapshot.number == 12
    assert snapshot.title == "Update API dependencies"
    assert snapshot.base_branch == "main"
    assert snapshot.head_branch == "feature/dependencies"
    assert snapshot.author == "developer"
    assert snapshot.changed_files == 2
    assert [file.filename for file in snapshot.files] == ["pyproject.toml", "app/main.py"]
    assert snapshot.truncated is False
