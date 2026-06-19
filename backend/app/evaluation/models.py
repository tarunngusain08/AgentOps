from __future__ import annotations

from dataclasses import dataclass
from typing import Any

EVALUATION_RUN_SCHEMA_VERSION = "evaluation-run/v1"
EVALUATION_SUITE_SCHEMA_VERSION = "evaluation-suite/v1"
EXECUTION_TRACE_SCHEMA_VERSION = "execution-trace/v1"
REGRESSION_REPORT_SCHEMA_VERSION = "regression-report/v1"
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
    group: str = "workflow"


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
    group: str = "workflow"


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


@dataclass(frozen=True)
class TraceSpan:
    id: str
    name: str
    start_ms: int
    duration_ms: int
    status: str
    metadata: dict[str, str | int | float | bool | None]


@dataclass(frozen=True)
class ExecutionTrace:
    schema_version: str
    trace_id: str
    run_id: str
    task_id: str
    started_at: str
    duration_ms: int
    spans: list[TraceSpan]


@dataclass(frozen=True)
class CheckComparison:
    id: str
    required: bool
    baseline_passed: bool
    candidate_passed: bool
    status: str


@dataclass(frozen=True)
class TaskComparison:
    id: str
    priority: str
    baseline_score: int
    candidate_score: int
    score_delta: int
    baseline_passed: bool
    candidate_passed: bool
    status: str
    regression_reasons: list[str]
    check_comparisons: list[CheckComparison]


@dataclass(frozen=True)
class RegressionSummary:
    total_tasks: int
    regressed_tasks: int
    improved_tasks: int
    unchanged_tasks: int
    p0_regressions: int


@dataclass(frozen=True)
class RegressionReport:
    schema_version: str
    report_id: str
    baseline_run_id: str
    candidate_run_id: str
    suite_id: str
    suite_version: str
    status: str
    comparison_passed: bool
    task_comparisons: list[TaskComparison]
    summary: RegressionSummary
