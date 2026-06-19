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
    group: str = "workflow",
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
        group=group,
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


MVP_DEMO_SUITE_V2 = EvaluationSuite(
    schema_version=EVALUATION_SUITE_SCHEMA_VERSION,
    id="mvp-demo-suite",
    version="v2",
    tasks=[
        EvaluationTask(
            id="repository-architecture",
            priority="P0",
            workflow="architecture_report",
            fixture_id="python_app@v1",
            pass_threshold=80,
            checks=[
                _check("arch-no-exception", "Architecture workflow completes.", 15, True, "contains", "workflow_status=success", "workflow"),
                _check("arch-fastapi", "Architecture report detects FastAPI.", 15, True, "contains", "FastAPI", "retrieval"),
                _check("arch-code-intelligence", "Architecture report includes code intelligence.", 20, True, "contains", "code_intelligence", "static_intelligence"),
                _check("arch-python-symbol", "Python service symbol is extracted.", 25, True, "contains", "CheckoutService.process_checkout", "static_intelligence"),
                _check("arch-test-link", "Python source is linked to nearby test.", 25, False, "contains", "tests/test_checkout.py -> app/services/checkout.py", "static_intelligence"),
            ],
        ),
        EvaluationTask(
            id="onboarding-guide",
            priority="P0",
            workflow="onboarding_guide",
            fixture_id="go_service@v1",
            pass_threshold=80,
            checks=[
                _check("guide-no-exception", "Onboarding workflow completes.", 15, True, "contains", "workflow_status=success", "workflow"),
                _check("guide-code-navigation", "Guide contains Code Navigation section.", 20, True, "contains", "Code Navigation", "static_intelligence"),
                _check("guide-go-method", "Guide references Go method navigation.", 25, True, "contains", "BillingService.CreateInvoice", "static_intelligence"),
                _check("guide-go-test-link", "Guide references nearby Go tests.", 20, False, "contains", "billing/service_test.go", "static_intelligence"),
                _check("guide-how-to-run", "Guide still includes How To Run.", 20, True, "contains", "How To Run", "workflow"),
            ],
        ),
        EvaluationTask(
            id="pr-review",
            priority="P0",
            workflow="pr_review",
            fixture_id="go_pr_static@v1",
            pass_threshold=80,
            checks=[
                _check("review-no-exception", "PR review workflow completes.", 15, True, "contains", "workflow_status=success", "workflow"),
                _check("review-architecture-impact", "PR review includes architecture impact.", 20, True, "contains", "architecture_impact", "workflow"),
                _check("review-indexed-symbol", "PR review cites indexed changed symbols.", 30, True, "contains", "BillingService.CreateInvoice", "static_intelligence"),
                _check("review-test-signal", "PR review cites nearby indexed tests.", 20, False, "contains", "billing/service_test.go", "static_intelligence"),
                _check("review-testing-concern", "PR review keeps testing concern signal.", 15, True, "contains", "testing_concern", "regression"),
            ],
        ),
        EvaluationTask(
            id="incident-rca",
            priority="P0",
            workflow="incident_rca",
            fixture_id="checkout-latency@v1",
            pass_threshold=80,
            checks=[
                _check("incident-no-exception", "Incident workflow completes.", 20, True, "contains", "workflow_status=success", "workflow"),
                _check("incident-root-cause", "RCA identifies connection pool regression.", 30, True, "contains", "CONNECTION_POOL_REGRESSION", "workflow"),
                _check("incident-evidence", "RCA includes evidence ids.", 25, True, "contains", "metric-1", "retrieval"),
                _check("incident-confidence", "RCA reports high confidence.", 25, False, "contains", "High", "regression"),
            ],
        ),
        EvaluationTask(
            id="static-ts-index",
            priority="P0",
            workflow="static_index",
            fixture_id="ts_frontend@v1",
            pass_threshold=80,
            checks=[
                _check("ts-no-exception", "TypeScript index workflow completes.", 15, True, "contains", "workflow_status=success", "workflow"),
                _check("ts-symbol", "TypeScript component symbol is extracted.", 30, True, "contains", "CheckoutButton", "static_intelligence"),
                _check("ts-import", "TypeScript import is extracted.", 25, True, "contains", "react", "static_intelligence"),
                _check("ts-test-link", "TypeScript test is linked to source.", 30, False, "contains", "src/components/CheckoutButton.test.tsx", "static_intelligence"),
            ],
        ),
        EvaluationTask(
            id="repository-evolution",
            priority="P0",
            workflow="static_index",
            fixture_id="go_service_moved@v1",
            pass_threshold=80,
            checks=[
                _check("evolution-no-exception", "Repository evolution fixture indexes successfully.", 15, True, "contains", "workflow_status=success", "workflow"),
                _check("evolution-symbol", "Moved Go symbol remains detected.", 35, True, "contains", "CreateInvoice", "static_intelligence"),
                _check("evolution-source-path", "Moved source path is indexed.", 25, True, "contains", "billing/invoice_service.go", "regression"),
                _check("evolution-test-link", "Moved test still links to source.", 25, True, "contains", "billing/invoice_service_test.go", "regression"),
            ],
        ),
    ],
)


class EvaluationSuiteLoader:
    def __init__(self, suites: list[EvaluationSuite] | None = None):
        self.suites = suites or [MVP_DEMO_SUITE, MVP_DEMO_SUITE_V2]

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
