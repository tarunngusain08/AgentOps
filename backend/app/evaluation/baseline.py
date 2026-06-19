from __future__ import annotations

from typing import Any

from app.evaluation.errors import EvaluationError
from app.evaluation.hashing import evaluation_result_hash
from app.evaluation.identifiers import validate_evaluation_identifier
from app.evaluation.models import EVALUATION_RUN_SCHEMA_VERSION, EvaluationSuite


class BaselineValidationError(EvaluationError):
    code = "BASELINE_VALIDATION_ERROR"
    status_code = 500


def validate_evaluation_run_integrity(run: dict[str, Any]) -> None:
    if run.get("schema_version") != EVALUATION_RUN_SCHEMA_VERSION:
        raise BaselineValidationError("Evaluation run schema version is invalid.")
    for field_name in ("run_id", "suite_id", "suite_version"):
        try:
            validate_evaluation_identifier(str(run.get(field_name) or ""), field_name)
        except EvaluationError as exc:
            raise BaselineValidationError(exc.message) from exc
    if evaluation_result_hash(run) != run.get("result_hash"):
        raise BaselineValidationError("Evaluation run result_hash does not match content.")


def validate_baseline(run: dict[str, Any], suite: EvaluationSuite) -> None:
    validate_evaluation_run_integrity(run)
    if run.get("suite_id") != suite.id or run.get("suite_version") != suite.version:
        raise BaselineValidationError("Baseline suite id/version does not match requested suite.")

    baseline_p0_tasks = [task["id"] for task in run.get("tasks", []) if task.get("priority") == "P0"]
    suite_p0_tasks = [task.id for task in suite.tasks if task.priority == "P0"]
    if baseline_p0_tasks != suite_p0_tasks:
        raise BaselineValidationError("Baseline P0 task list does not match suite P0 task list.")
