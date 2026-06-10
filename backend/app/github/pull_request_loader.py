from __future__ import annotations

from dataclasses import dataclass
from urllib.parse import quote

from app.github.service import GitHubService, parse_github_url

MAX_CHANGED_FILES = 200
PER_PAGE = 100


@dataclass(frozen=True)
class PullRequestFile:
    filename: str
    status: str
    additions: int
    deletions: int
    changes: int
    patch: str | None


@dataclass(frozen=True)
class PullRequestSnapshot:
    owner: str
    repo: str
    number: int
    title: str
    state: str
    html_url: str | None
    base_branch: str
    head_branch: str
    author: str | None
    changed_files: int
    files: list[PullRequestFile]
    truncated: bool


class PullRequestLoader:
    def __init__(
        self,
        service: GitHubService | None = None,
        max_changed_files: int = MAX_CHANGED_FILES,
    ):
        self.service = service or GitHubService()
        self.max_changed_files = max_changed_files

    def load(self, repository_url: str, pull_request_number: int) -> PullRequestSnapshot:
        parsed = parse_github_url(repository_url)
        owner = quote(parsed.owner, safe="")
        repo = quote(parsed.name, safe="")
        pr = self.service.request_json(f"/repos/{owner}/{repo}/pulls/{pull_request_number}")
        if not isinstance(pr, dict):
            raise ValueError("GitHub returned an invalid pull request response.")

        files = self._load_files(parsed.owner, parsed.name, pull_request_number)
        changed_files = int(pr.get("changed_files") or len(files))
        truncated = changed_files > len(files) or changed_files > self.max_changed_files

        return PullRequestSnapshot(
            owner=parsed.owner,
            repo=parsed.name,
            number=pull_request_number,
            title=str(pr.get("title") or f"PR #{pull_request_number}"),
            state=str(pr.get("state") or "unknown"),
            html_url=pr.get("html_url"),
            base_branch=str((pr.get("base") or {}).get("ref") or ""),
            head_branch=str((pr.get("head") or {}).get("ref") or ""),
            author=(pr.get("user") or {}).get("login"),
            changed_files=changed_files,
            files=files,
            truncated=truncated,
        )

    def _load_files(self, owner: str, repo: str, pull_request_number: int) -> list[PullRequestFile]:
        files: list[PullRequestFile] = []
        safe_owner = quote(owner, safe="")
        safe_repo = quote(repo, safe="")
        max_pages = (self.max_changed_files + PER_PAGE - 1) // PER_PAGE

        for page in range(1, max_pages + 1):
            response = self.service.request_json(
                f"/repos/{safe_owner}/{safe_repo}/pulls/{pull_request_number}/files?per_page={PER_PAGE}&page={page}"
            )
            if not isinstance(response, list):
                raise ValueError("GitHub returned an invalid pull request files response.")
            for file_json in response:
                if len(files) >= self.max_changed_files:
                    return files
                if not isinstance(file_json, dict):
                    continue
                files.append(
                    PullRequestFile(
                        filename=str(file_json.get("filename") or ""),
                        status=str(file_json.get("status") or "modified"),
                        additions=int(file_json.get("additions") or 0),
                        deletions=int(file_json.get("deletions") or 0),
                        changes=int(file_json.get("changes") or 0),
                        patch=file_json.get("patch") if isinstance(file_json.get("patch"), str) else None,
                    )
                )
            if len(response) < PER_PAGE:
                break

        return files
