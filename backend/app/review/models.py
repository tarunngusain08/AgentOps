from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class Finding:
    category: str
    severity: str
    description: str
    evidence: list[str]


@dataclass(frozen=True)
class Review:
    summary: str
    findings: list[Finding]
    assumptions: list[str]
    confidence: str
    metadata: dict[str, int | str | bool]


@dataclass(frozen=True)
class ChangedFileSignal:
    path: str
    status: str
    category: str
    additions: int
    deletions: int
    changes: int
    patch: str | None
    patch_inspected: bool
    high_signal: bool


@dataclass(frozen=True)
class DiffAnalysis:
    files: list[ChangedFileSignal]
    changed_files: int
    files_inspected: int
    patch_bytes: int
    high_signal_files: int
    truncated: bool
    assumptions: list[str] = field(default_factory=list)
