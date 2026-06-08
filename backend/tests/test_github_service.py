import pytest

from app.github.service import parse_github_url


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
