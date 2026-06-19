import io
import json
from urllib.error import HTTPError

import pytest

from app.github.service import GitHubError, GitHubService, parse_github_url


def test_parse_github_url_accepts_standard_repo_url():
    parsed = parse_github_url("https://github.com/fastapi/fastapi")

    assert parsed.owner == "fastapi"
    assert parsed.name == "fastapi"


def test_parse_github_url_strips_git_suffix():
    parsed = parse_github_url("https://github.com/owner/repo.git")

    assert parsed.owner == "owner"
    assert parsed.name == "repo"


def test_parse_github_url_rejects_non_github_urls():
    with pytest.raises(ValueError):
        parse_github_url("https://gitlab.com/owner/repo")


def test_load_repository_checks_public_visibility_without_token(monkeypatch):
    import app.github.service as service_module

    calls = []

    def fake_urlopen(request, timeout):
        calls.append((request.full_url, request.headers.get("Authorization")))
        if request.full_url == "https://api.github.com/repos/owner/repo":
            return FakeResponse(
                {
                    "default_branch": "main",
                    "html_url": "https://github.com/owner/repo",
                    "description": "public repo",
                    "language": "Python",
                    "topics": [],
                    "private": False,
                }
            )
        if request.full_url == "https://api.github.com/repos/owner/repo/git/trees/main?recursive=1":
            return FakeResponse({"tree": []})
        raise AssertionError(f"Unexpected request: {request.full_url}")

    monkeypatch.setattr(service_module, "urlopen", fake_urlopen)

    snapshot = GitHubService(token="secret-token").load_repository("https://github.com/owner/repo")

    assert snapshot.owner == "owner"
    assert calls == [
        ("https://api.github.com/repos/owner/repo", None),
        ("https://api.github.com/repos/owner/repo/git/trees/main?recursive=1", "Bearer secret-token"),
    ]


def test_private_or_inaccessible_repo_never_uses_token_backed_fetch(monkeypatch):
    import app.github.service as service_module

    calls = []

    def fake_urlopen(request, timeout):
        calls.append((request.full_url, request.headers.get("Authorization")))
        raise HTTPError(
            request.full_url,
            404,
            "Not Found",
            None,
            io.BytesIO(json.dumps({"message": "Not Found"}).encode("utf-8")),
        )

    monkeypatch.setattr(service_module, "urlopen", fake_urlopen)

    with pytest.raises(GitHubError) as exc:
        GitHubService(token="secret-token").load_repository("https://github.com/owner/private")

    assert exc.value.status_code == 404
    assert exc.value.message == "Repository must be public or could not be found."
    assert calls == [("https://api.github.com/repos/owner/private", None)]


class FakeResponse:
    def __init__(self, payload):
        self.payload = payload

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, traceback):
        return False

    def read(self):
        return json.dumps(self.payload).encode("utf-8")
