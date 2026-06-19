from __future__ import annotations

import base64
import json
import os
from dataclasses import dataclass, field
from urllib.error import HTTPError, URLError
from urllib.parse import quote, urlparse
from urllib.request import Request, urlopen

from app.analyzer.file_selection import FileSelectionResult, select_architecture_files

MAX_FILES = 100
MAX_TOTAL_BYTES = 2 * 1024 * 1024
MAX_FILE_BYTES = 512 * 1024
GITHUB_API_BASE = "https://api.github.com"
PUBLIC_REPOSITORY_ERROR = "Repository must be public or could not be found."


@dataclass(frozen=True)
class ParsedRepository:
    owner: str
    name: str


@dataclass(frozen=True)
class GitHubFile:
    path: str
    content: str
    size: int
    source_type: str


@dataclass(frozen=True)
class RepositorySnapshot:
    owner: str
    name: str
    default_branch: str
    html_url: str | None
    description: str | None
    primary_language: str | None
    topics: list[str]
    tree_paths: list[str]
    top_level_directories: list[str]
    selected_paths: list[str]
    files: list[GitHubFile] = field(default_factory=list)
    truncated: bool = False
    truncation_reason: str = "none"


class GitHubError(Exception):
    def __init__(self, message: str, status_code: int = 502):
        super().__init__(message)
        self.message = message
        self.status_code = status_code


def parse_github_url(repository_url: str) -> ParsedRepository:
    parsed = urlparse(repository_url.strip())
    if parsed.scheme not in {"http", "https"} or parsed.netloc.lower() != "github.com":
        raise ValueError("Repository URL must use https://github.com/{owner}/{repo}.")

    parts = [part for part in parsed.path.strip("/").split("/") if part]
    if len(parts) < 2:
        raise ValueError("Repository URL must include both owner and repository name.")

    repo_name = parts[1]
    if repo_name.endswith(".git"):
        repo_name = repo_name[:-4]

    if not parts[0] or not repo_name:
        raise ValueError("Repository URL must include both owner and repository name.")

    return ParsedRepository(owner=parts[0], name=repo_name)


class GitHubService:
    def __init__(
        self,
        token: str | None = None,
        max_files: int = MAX_FILES,
        max_total_bytes: int = MAX_TOTAL_BYTES,
        timeout_seconds: int = 20,
    ):
        self.token = token or os.getenv("GITHUB_TOKEN")
        self.max_files = max_files
        self.max_total_bytes = max_total_bytes
        self.timeout_seconds = timeout_seconds
        self._public_repository_cache: dict[tuple[str, str], dict] = {}

    def load_repository(self, repository_url: str) -> RepositorySnapshot:
        parsed = parse_github_url(repository_url)
        repo = self._get_public_repository_metadata(parsed)
        default_branch = repo.get("default_branch") or "main"

        tree = self._get_tree(parsed.owner, parsed.name, default_branch)
        tree_paths = [
            item["path"]
            for item in tree.get("tree", [])
            if item.get("type") in {"blob", "tree"} and isinstance(item.get("path"), str)
        ]
        top_level_directories = self._top_level_directories(tree_paths)
        selection = select_architecture_files(tree_paths, self.max_files)
        files, byte_limited = self._load_selected_files(parsed.owner, parsed.name, default_branch, selection)
        truncated = bool(tree.get("truncated")) or selection.truncated or byte_limited
        truncation_reason = "none"
        if selection.truncated or bool(tree.get("truncated")):
            truncation_reason = "file_limit"
        elif byte_limited:
            truncation_reason = "byte_limit"

        return RepositorySnapshot(
            owner=parsed.owner,
            name=parsed.name,
            default_branch=default_branch,
            html_url=repo.get("html_url"),
            description=repo.get("description"),
            primary_language=repo.get("language"),
            topics=repo.get("topics") or [],
            tree_paths=tree_paths,
            top_level_directories=top_level_directories,
            selected_paths=selection.paths,
            files=files,
            truncated=truncated,
            truncation_reason=truncation_reason,
        )

    def _load_selected_files(
        self,
        owner: str,
        repo: str,
        ref: str,
        selection: FileSelectionResult,
    ) -> tuple[list[GitHubFile], bool]:
        files: list[GitHubFile] = []
        total_bytes = 0
        byte_limited = False

        for path in selection.paths:
            if total_bytes >= self.max_total_bytes:
                byte_limited = True
                break
            file_json = self._get_content(owner, repo, path, ref)
            if not isinstance(file_json, dict):
                continue
            if file_json.get("type") != "file":
                continue
            size = int(file_json.get("size") or 0)
            if size > MAX_FILE_BYTES or total_bytes + size > self.max_total_bytes:
                byte_limited = True
                continue
            encoded = file_json.get("content")
            if not isinstance(encoded, str):
                continue
            try:
                raw = base64.b64decode(encoded, validate=False)
                if b"\x00" in raw:
                    continue
                content = raw.decode("utf-8", errors="replace")
            except Exception:
                continue

            files.append(
                GitHubFile(
                    path=path,
                    content=content,
                    size=size,
                    source_type=selection.path_types.get(path, "selected"),
                )
            )
            total_bytes += size

        return files, byte_limited

    def _get_tree(self, owner: str, repo: str, ref: str) -> dict:
        safe_ref = quote(ref, safe="")
        return self._get_json(f"/repos/{owner}/{repo}/git/trees/{safe_ref}?recursive=1")

    def _get_content(self, owner: str, repo: str, path: str, ref: str) -> dict | list | None:
        safe_path = quote(path, safe="/")
        safe_ref = quote(ref, safe="")
        try:
            return self._get_json(f"/repos/{owner}/{repo}/contents/{safe_path}?ref={safe_ref}")
        except GitHubError as exc:
            if exc.status_code == 404:
                return None
            raise

    def request_json(self, path: str) -> dict | list:
        return self._get_json(path)

    def ensure_public_repository(self, repository_url: str) -> ParsedRepository:
        parsed = parse_github_url(repository_url)
        self._get_public_repository_metadata(parsed)
        return parsed

    def _get_public_repository_metadata(self, parsed: ParsedRepository) -> dict:
        key = (parsed.owner, parsed.name)
        if key in self._public_repository_cache:
            return self._public_repository_cache[key]

        safe_owner = quote(parsed.owner, safe="")
        safe_repo = quote(parsed.name, safe="")
        try:
            repo = self._get_json(f"/repos/{safe_owner}/{safe_repo}", use_token=False)
        except GitHubError as exc:
            if exc.status_code == 404:
                raise GitHubError(PUBLIC_REPOSITORY_ERROR, status_code=404) from exc
            raise
        if not isinstance(repo, dict) or repo.get("private") is not False:
            raise GitHubError(PUBLIC_REPOSITORY_ERROR, status_code=404)

        self._public_repository_cache[key] = repo
        return repo

    def _get_json(self, path: str, use_token: bool = True) -> dict | list:
        url = f"{GITHUB_API_BASE}{path}"
        headers = {
            "Accept": "application/vnd.github+json",
            "User-Agent": "agentops-m01-repository-understanding",
            "X-GitHub-Api-Version": "2022-11-28",
        }
        if use_token and self.token:
            headers["Authorization"] = f"Bearer {self.token}"

        request = Request(url, headers=headers)
        try:
            with urlopen(request, timeout=self.timeout_seconds) as response:
                return json.loads(response.read().decode("utf-8"))
        except HTTPError as exc:
            message = exc.reason
            try:
                body = json.loads(exc.read().decode("utf-8"))
                message = body.get("message") or message
            except Exception:
                pass
            status = 404 if exc.code == 404 else 502
            raise GitHubError(f"GitHub API error: {message}", status_code=status) from exc
        except URLError as exc:
            raise GitHubError(f"Unable to reach GitHub: {exc.reason}", status_code=502) from exc
        except json.JSONDecodeError as exc:
            raise GitHubError("GitHub returned an invalid response.", status_code=502) from exc

    @staticmethod
    def _top_level_directories(paths: list[str]) -> list[str]:
        directories = set()
        for path in paths:
            if "/" in path:
                directories.add(path.split("/", 1)[0])
        return sorted(directories)
