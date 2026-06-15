from __future__ import annotations

from dataclasses import dataclass
from typing import Any

EVALUATION_RUN_SCHEMA_VERSION = "evaluation-run/v1"
EVALUATION_SUITE_SCHEMA_VERSION = "evaluation-suite/v1"
STATE_SCHEMA_VERSION = "agentops-state/v1"


@dataclass(frozen=True)
class ExpectedFact:
    id: str
    match_type: str
    value: str


@dataclass(frozen=True)
class EvaluationCheck:
    id: str
    description: str
    weight: int
    required: bool
    expected_fact: ExpectedFact


@dataclass(frozen=True)
class EvaluationTask:
    id: str
    priority: str
    workflow: str
    fixture_id: str
    pass_threshold: int
    checks: list[EvaluationCheck]


@dataclass(frozen=True)
class EvaluationSuite:
    schema_version: str
    id: str
    version: str
    tasks: list[EvaluationTask]

    @property
    def qualified_id(self) -> str:
        return f"{self.id}@{self.version}"


@dataclass(frozen=True)
class CheckResult:
    id: str
    description: str
    weight: int
    required: bool
    passed: bool
    expected: str
    actual: Any
    evidence: list[str]


@dataclass(frozen=True)
class TaskResult:
    id: str
    priority: str
    workflow: str
    fixture_id: str
    score: int
    passed: bool
    checks: list[CheckResult]


@dataclass(frozen=True)
class EvaluationSummary:
    total_tasks: int
    passed_tasks: int
    failed_tasks: int
    pass_rate: float


@dataclass(frozen=True)
class EvaluationRun:
    schema_version: str
    run_id: str
    result_hash: str
    suite_id: str
    suite_version: str
    implementation_version: str
    version_label: str
    fixture_versions: dict[str, str]
    tasks: list[TaskResult]
    summary: EvaluationSummary
    metadata: dict[str, int | str]

