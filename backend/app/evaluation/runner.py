from __future__ import annotations

from dataclasses import asdict
from time import perf_counter

from app.evaluation.hashing import evaluation_result_hash
from app.evaluation.matcher import FactMatcher
from app.evaluation.models import (
    EVALUATION_RUN_SCHEMA_VERSION,
    CheckResult,
    EvaluationRun,
    EvaluationSummary,
    EvaluationSuite,
    TaskResult,
)
from app.evaluation.workflows import WorkflowExecutor


class EvaluationRunner:
    def __init__(self, workflow_executor: WorkflowExecutor | None = None, matcher: FactMatcher | None = None):
        self.workflow_executor = workflow_executor or WorkflowExecutor()
        self.matcher = matcher or FactMatcher()

    def run(
        self,
        suite: EvaluationSuite,
        run_id: str,
        implementation_version: str,
        version_label: str,
    ) -> EvaluationRun:
        started = perf_counter()
        task_results = [self._run_task(task) for task in suite.tasks]
        passed_tasks = sum(1 for task in task_results if task.passed)
        summary = EvaluationSummary(
            total_tasks=len(task_results),
            passed_tasks=passed_tasks,
            failed_tasks=len(task_results) - passed_tasks,
            pass_rate=round(passed_tasks / len(task_results), 4) if task_results else 0.0,
        )
        fixture_versions = {task.id: task.fixture_id for task in suite.tasks}
        result_hash = self._result_hash(suite, fixture_versions, task_results, summary)
        duration_ms = int((perf_counter() - started) * 1000)

        return EvaluationRun(
            schema_version=EVALUATION_RUN_SCHEMA_VERSION,
            run_id=run_id,
            result_hash=result_hash,
            suite_id=suite.id,
            suite_version=suite.version,
            implementation_version=implementation_version,
            version_label=version_label,
            fixture_versions=fixture_versions,
            tasks=task_results,
            summary=summary,
            metadata={
                "duration_ms": duration_ms,
                "analysis_mode": "heuristic",
            },
        )

    def _run_task(self, task) -> TaskResult:
        try:
            actual_text, evidence = self.workflow_executor.execute(task.workflow)
        except Exception as exc:
            actual_text = f"workflow_status=exception exception={exc.__class__.__name__}"
            evidence = []

        check_results = [
            self._run_check(check, actual_text, evidence)
            for check in task.checks
        ]
        total_weight = sum(check.weight for check in check_results)
        passed_weight = sum(check.weight for check in check_results if check.passed)
        score = round((passed_weight / total_weight) * 100)
        required_passed = all(check.passed for check in check_results if check.required)
        passed = score >= task.pass_threshold and required_passed

        return TaskResult(
            id=task.id,
            priority=task.priority,
            workflow=task.workflow,
            fixture_id=task.fixture_id,
            score=score,
            passed=passed,
            checks=check_results,
        )

    def _run_check(self, check, actual_text: str, evidence: list[str]) -> CheckResult:
        passed = self.matcher.match(check.expected_fact, actual_text)
        return CheckResult(
            id=check.id,
            description=check.description,
            weight=check.weight,
            required=check.required,
            passed=passed,
            expected=check.expected_fact.value,
            actual=check.expected_fact.value if passed else None,
            evidence=evidence if passed else [],
        )

    def _result_hash(
        self,
        suite: EvaluationSuite,
        fixture_versions: dict[str, str],
        tasks: list[TaskResult],
        summary: EvaluationSummary,
    ) -> str:
        return evaluation_result_hash(
            {
                "suite_id": suite.id,
                "suite_version": suite.version,
                "fixture_versions": fixture_versions,
                "tasks": [asdict(task) for task in tasks],
                "summary": asdict(summary),
            }
        )
