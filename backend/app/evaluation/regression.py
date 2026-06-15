from __future__ import annotations

from app.evaluation.errors import ComparisonCheckSetMismatchError, SuiteVersionMismatchError
from app.evaluation.models import (
    REGRESSION_REPORT_SCHEMA_VERSION,
    CheckComparison,
    RegressionReport,
    RegressionSummary,
    TaskComparison,
)

SCORE_DELTA_THRESHOLD = 5
NO_CHANGE = "NO_CHANGE"
IMPROVEMENT = "IMPROVEMENT"
REGRESSION = "REGRESSION"
MIXED = "MIXED"


class RegressionComparator:
    def compare(self, baseline: dict, candidate: dict) -> RegressionReport:
        self._validate_compatibility(baseline, candidate)

        task_comparisons = [
            self._compare_task(baseline_task, candidate_task)
            for baseline_task, candidate_task in zip(baseline["tasks"], candidate["tasks"], strict=True)
        ]
        status = self._overall_status(task_comparisons)
        p0_regressions = sum(
            1
            for task in task_comparisons
            if task.priority == "P0" and task.status in {REGRESSION, MIXED}
        )
        comparison_passed = self._comparison_passed(status, p0_regressions)
        summary = RegressionSummary(
            total_tasks=len(task_comparisons),
            regressed_tasks=sum(1 for task in task_comparisons if task.status == REGRESSION),
            improved_tasks=sum(1 for task in task_comparisons if task.status == IMPROVEMENT),
            unchanged_tasks=sum(1 for task in task_comparisons if task.status == NO_CHANGE),
            p0_regressions=p0_regressions,
        )

        return RegressionReport(
            schema_version=REGRESSION_REPORT_SCHEMA_VERSION,
            report_id=f"regression-{baseline['run_id']}-vs-{candidate['run_id']}",
            baseline_run_id=baseline["run_id"],
            candidate_run_id=candidate["run_id"],
            suite_id=baseline["suite_id"],
            suite_version=baseline["suite_version"],
            status=status,
            comparison_passed=comparison_passed,
            task_comparisons=task_comparisons,
            summary=summary,
        )

    def _validate_compatibility(self, baseline: dict, candidate: dict) -> None:
        if baseline["suite_id"] != candidate["suite_id"] or baseline["suite_version"] != candidate["suite_version"]:
            raise SuiteVersionMismatchError("Evaluation runs must use the same suite id and version.")

        baseline_tasks = [task["id"] for task in baseline["tasks"]]
        candidate_tasks = [task["id"] for task in candidate["tasks"]]
        if baseline_tasks != candidate_tasks:
            raise ComparisonCheckSetMismatchError("Evaluation task ids differ between runs.")

        for baseline_task, candidate_task in zip(baseline["tasks"], candidate["tasks"], strict=True):
            baseline_checks = [check["id"] for check in baseline_task["checks"]]
            candidate_checks = [check["id"] for check in candidate_task["checks"]]
            if baseline_checks != candidate_checks:
                raise ComparisonCheckSetMismatchError(
                    f"Evaluation check ids differ for task: {baseline_task['id']}"
                )

    def _compare_task(self, baseline: dict, candidate: dict) -> TaskComparison:
        score_delta = int(candidate["score"]) - int(baseline["score"])
        check_comparisons = [
            self._compare_check(baseline_check, candidate_check)
            for baseline_check, candidate_check in zip(baseline["checks"], candidate["checks"], strict=True)
        ]
        regression_reasons = self._regression_reasons(baseline, candidate, score_delta, check_comparisons)
        regressed = bool(regression_reasons)
        improved = self._improved(baseline, candidate, score_delta)
        if regressed and improved:
            status = MIXED
        elif regressed:
            status = REGRESSION
        elif improved:
            status = IMPROVEMENT
        else:
            status = NO_CHANGE

        return TaskComparison(
            id=baseline["id"],
            priority=baseline["priority"],
            baseline_score=int(baseline["score"]),
            candidate_score=int(candidate["score"]),
            score_delta=score_delta,
            baseline_passed=bool(baseline["passed"]),
            candidate_passed=bool(candidate["passed"]),
            status=status,
            regression_reasons=regression_reasons,
            check_comparisons=check_comparisons,
        )

    @staticmethod
    def _compare_check(baseline: dict, candidate: dict) -> CheckComparison:
        if baseline["passed"] == candidate["passed"]:
            status = NO_CHANGE
        elif candidate["passed"]:
            status = IMPROVEMENT
        else:
            status = REGRESSION
        return CheckComparison(
            id=baseline["id"],
            required=bool(baseline["required"]),
            baseline_passed=bool(baseline["passed"]),
            candidate_passed=bool(candidate["passed"]),
            status=status,
        )

    @staticmethod
    def _regression_reasons(
        baseline: dict,
        candidate: dict,
        score_delta: int,
        checks: list[CheckComparison],
    ) -> list[str]:
        reasons = []
        if baseline["passed"] and not candidate["passed"]:
            reasons.append("task_passed_to_failed")
        if score_delta <= -SCORE_DELTA_THRESHOLD:
            reasons.append("score_delta_threshold")
        if any(check.required and check.baseline_passed and not check.candidate_passed for check in checks):
            reasons.append("required_check_failed")
        return reasons

    @staticmethod
    def _improved(baseline: dict, candidate: dict, score_delta: int) -> bool:
        return (not baseline["passed"] and candidate["passed"]) or score_delta >= SCORE_DELTA_THRESHOLD

    @staticmethod
    def _overall_status(tasks: list[TaskComparison]) -> str:
        has_regression = any(task.status in {REGRESSION, MIXED} for task in tasks)
        has_improvement = any(task.status in {IMPROVEMENT, MIXED} for task in tasks)
        if has_regression and has_improvement:
            return MIXED
        if has_regression:
            return REGRESSION
        if has_improvement:
            return IMPROVEMENT
        return NO_CHANGE

    @staticmethod
    def _comparison_passed(status: str, p0_regressions: int) -> bool:
        if status == REGRESSION:
            return False
        if status == MIXED:
            return p0_regressions == 0
        return True
