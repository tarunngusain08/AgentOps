from __future__ import annotations

from pathlib import PurePosixPath

from app.analyzer.file_selection import classify_file
from app.github.pull_request_loader import PullRequestFile
from app.review.models import ChangedFileSignal, DiffAnalysis

MAX_PATCH_BYTES = 1 * 1024 * 1024
MAX_CHANGED_FILES = 200

CODE_EXTENSIONS = {
    ".py",
    ".ts",
    ".tsx",
    ".js",
    ".jsx",
    ".java",
    ".go",
    ".rs",
    ".kt",
    ".rb",
    ".php",
}
TEST_MARKERS = ("/test/", "/tests/", "/__tests__/", ".test.", ".spec.", "_test.")
DOC_EXTENSIONS = {".md", ".mdx", ".rst", ".txt"}
HIGH_SIGNAL_CATEGORIES = {"manifest", "config", "infrastructure", "entry_point", "source"}
CATEGORY_PRIORITY = {
    "manifest": 0,
    "infrastructure": 1,
    "config": 2,
    "entry_point": 3,
    "source": 4,
    "test": 5,
    "docs": 6,
    "other": 7,
}


class DiffAnalyzer:
    def __init__(
        self,
        max_changed_files: int = MAX_CHANGED_FILES,
        max_patch_bytes: int = MAX_PATCH_BYTES,
    ):
        self.max_changed_files = max_changed_files
        self.max_patch_bytes = max_patch_bytes

    def analyze(self, files: list[PullRequestFile], upstream_truncated: bool = False) -> DiffAnalysis:
        classified = [
            self._classify(file)
            for file in files[: self.max_changed_files]
            if file.filename
        ]
        selected = sorted(
            classified,
            key=lambda item: (
                CATEGORY_PRIORITY.get(item.category, 99),
                -item.changes,
                item.path.lower(),
            ),
        )

        patch_bytes = 0
        inspected_paths = set()
        truncated = upstream_truncated or len(files) > self.max_changed_files
        assumptions = [
            "PR review is heuristic and based on changed-file metadata and available patch snippets.",
        ]

        for signal in selected:
            patch_size = len(signal.patch.encode("utf-8")) if signal.patch else 0
            if patch_size and patch_bytes + patch_size > self.max_patch_bytes:
                truncated = True
                continue
            if signal.patch:
                patch_bytes += patch_size
            inspected_paths.add(signal.path)

        if truncated:
            assumptions.append("Diff analysis was truncated, so lower-signal files or patch content may be omitted.")

        final_files = [
            ChangedFileSignal(
                path=signal.path,
                status=signal.status,
                category=signal.category,
                additions=signal.additions,
                deletions=signal.deletions,
                changes=signal.changes,
                patch=signal.patch if signal.path in inspected_paths else None,
                patch_inspected=signal.path in inspected_paths,
                high_signal=signal.high_signal,
            )
            for signal in selected
        ]

        return DiffAnalysis(
            files=final_files,
            changed_files=len(files),
            files_inspected=len(inspected_paths),
            patch_bytes=patch_bytes,
            high_signal_files=sum(1 for signal in final_files if signal.high_signal),
            truncated=truncated,
            assumptions=assumptions,
        )

    def _classify(self, file: PullRequestFile) -> ChangedFileSignal:
        category = self._category(file.filename)
        return ChangedFileSignal(
            path=file.filename,
            status=file.status,
            category=category,
            additions=file.additions,
            deletions=file.deletions,
            changes=file.changes,
            patch=file.patch,
            patch_inspected=False,
            high_signal=category in HIGH_SIGNAL_CATEGORIES,
        )

    def _category(self, path: str) -> str:
        classified = classify_file(path)
        if classified in {"manifest", "config", "infrastructure", "entry_point"}:
            return classified

        normalized = f"/{path.lower()}"
        suffix = PurePosixPath(path).suffix.lower()
        name = PurePosixPath(path).name.lower()
        if any(marker in normalized for marker in TEST_MARKERS) or name.startswith("test_"):
            return "test"
        if normalized.startswith("/docs/") or normalized.startswith("/doc/") or suffix in DOC_EXTENSIONS:
            return "docs"
        if suffix in CODE_EXTENSIONS:
            return "source"
        return "other"
