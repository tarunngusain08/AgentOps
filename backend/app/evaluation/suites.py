from __future__ import annotations

from app.evaluation.errors import EvaluationSuiteNotFoundError, EvaluationSuiteValidationError
from app.evaluation.matcher import SUPPORTED_MATCH_TYPES
from app.evaluation.models import (
    EVALUATION_SUITE_SCHEMA_VERSION,
    EvaluationCheck,
    EvaluationSuite,
    EvaluationTask,
    ExpectedFact,
)


def _check(
    check_id: str,
    description: str,
    weight: int,
    required: bool,
    match_type: str,
    value: str,
) -> EvaluationCheck:
    return EvaluationCheck(
        id=check_id,
        description=description,
        weight=weight,
        required=required,
        expected_fact=ExpectedFact(
            id=check_id,
            match_type=match_type,
            value=value,
        ),
    )


MVP_DEMO_SUITE = EvaluationSuite(
    schema_version=EVALUATION_SUITE_SCHEMA_VERSION,
    id="mvp-demo-suite",
    version="v1",
    tasks=[
        EvaluationTask(
            id="repository-architecture",
            priority="P0",
            workflow="architecture_report",
            fixture_id="repository-basic@v1",
            pass_threshold=80,
            checks=[
                _check("arch-no-exception", "Architecture workflow completes.", 20, True, "contains", "workflow_status=success"),
                _check("arch-api-layer", "Architecture report identifies API layer.", 30, True, "contains", "API/Application Layer"),
                _check("arch-fastapi", "Architecture report detects FastAPI.", 25, False, "contains", "FastAPI"),
                _check("arch-entrypoint", "Architecture report cites app entry point.", 25, True, "contains", "app/main.py"),
            ],
        ),
        EvaluationTask(
            id="onboarding-guide",
            priority="P0",
            workflow="onboarding_guide",
            fixture_id="repository-basic@v1",
            pass_threshold=80,
            checks=[
                _check("guide-no-exception", "Onboarding workflow completes.", 20, True, "contains", "workflow_status=success"),
                _check("guide-how-to-run", "Guide contains How To Run section.", 25, True, "contains", "How To Run"),
                _check("guide-evidence", "Guide cites pyproject evidence.", 25, True, "contains", "pyproject.toml"),
                _check("guide-useful-files", "Guide contains useful files.", 30, False, "contains", "Useful Files"),
            ],
        ),
        EvaluationTask(
            id="pr-review",
            priority="P0",
            workflow="pr_review",
            fixture_id="pull-request-basic@v1",
            pass_threshold=80,
            checks=[
                _check("review-no-exception", "PR review workflow completes.", 20, True, "contains", "workflow_status=success"),
                _check("review-risk", "PR review identifies potential risk.", 30, True, "contains", "potential_risk"),
                _check("review-testing", "PR review identifies testing concern.", 25, True, "contains", "testing_concern"),
                _check("review-evidence", "PR review includes file evidence.", 25, True, "contains", "pyproject.toml"),
            ],
        ),
        EvaluationTask(
            id="incident-rca",
            priority="P0",
            workflow="incident_rca",
            fixture_id="checkout-latency@v1",
            pass_threshold=80,
            checks=[
                _check("incident-no-exception", "Incident workflow completes.", 20, True, "contains", "workflow_status=success"),
                _check("incident-root-cause", "RCA identifies connection pool regression.", 30, True, "contains", "CONNECTION_POOL_REGRESSION"),
                _check("incident-evidence", "RCA includes evidence ids.", 25, True, "contains", "metric-1"),
                _check("incident-confidence", "RCA reports high confidence.", 25, False, "contains", "High"),
            ],
        ),
    ],
)


class EvaluationSuiteLoader:
    def __init__(self, suites: list[EvaluationSuite] | None = None):
        self.suites = suites or [MVP_DEMO_SUITE]

    def list_suites(self) -> list[EvaluationSuite]:
        for suite in self.suites:
            self.validate(suite)
        return self.suites

    def load(self, qualified_id: str) -> EvaluationSuite:
        for suite in self.suites:
            if qualified_id in {suite.id, suite.qualified_id}:
                self.validate(suite)
                return suite
        raise EvaluationSuiteNotFoundError(f"Unknown evaluation suite: {qualified_id}")

    def validate(self, suite: EvaluationSuite) -> None:
        try:
            self._validate(suite)
        except EvaluationSuiteValidationError:
            raise
        except Exception as exc:
            raise EvaluationSuiteValidationError(f"Evaluation suite is invalid: {suite.qualified_id}") from exc

    def _validate(self, suite: EvaluationSuite) -> None:
        if suite.schema_version != EVALUATION_SUITE_SCHEMA_VERSION:
            raise EvaluationSuiteValidationError(f"Unsupported suite schema: {suite.schema_version}")
        if not suite.tasks:
            raise EvaluationSuiteValidationError("Evaluation suite must contain at least one task.")

        task_ids = set()
        for task in suite.tasks:
            if task.id in task_ids:
                raise EvaluationSuiteValidationError(f"Duplicate task id: {task.id}")
            task_ids.add(task.id)
            if not task.fixture_id or "@" not in task.fixture_id:
                raise EvaluationSuiteValidationError(f"Task must pin fixture version: {task.id}")
            if task.pass_threshold < 0 or task.pass_threshold > 100:
                raise EvaluationSuiteValidationError(f"Invalid pass threshold for task: {task.id}")
            if not task.checks:
                raise EvaluationSuiteValidationError(f"Task must contain checks: {task.id}")

            check_ids = set()
            total_weight = 0
            for check in task.checks:
                if check.id in check_ids:
                    raise EvaluationSuiteValidationError(f"Duplicate check id: {check.id}")
                check_ids.add(check.id)
                if check.weight <= 0:
                    raise EvaluationSuiteValidationError(f"Check weight must be positive: {check.id}")
                total_weight += check.weight
                if check.expected_fact.match_type not in SUPPORTED_MATCH_TYPES:
                    raise EvaluationSuiteValidationError(f"Unsupported match type: {check.expected_fact.match_type}")
                if not check.expected_fact.id or not check.expected_fact.value:
                    raise EvaluationSuiteValidationError(f"Expected fact is incomplete: {check.id}")
            if total_weight <= 0:
                raise EvaluationSuiteValidationError(f"Task total weight must be positive: {task.id}")

