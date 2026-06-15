from __future__ import annotations

from dataclasses import asdict
from types import SimpleNamespace

import pytest
from fastapi.testclient import TestClient

from app.evaluation.errors import StateFileInvalidError
from app.evaluation.matcher import FactMatcher
from app.evaluation.models import (
    EVALUATION_SUITE_SCHEMA_VERSION,
    EvaluationCheck,
    EvaluationSuite,
    EvaluationTask,
    ExpectedFact,
)
from app.evaluation.runner import EvaluationRunner
from app.evaluation.service import EvaluationService
from app.evaluation.storage import EvaluationStorage
from app.evaluation.suites import EvaluationSuiteLoader, MVP_DEMO_SUITE
from app.evaluation.versioning import ImplementationVersionResolver
from app.main import app


class StaticVersionResolver:
    def resolve(self) -> str:
        return "test-implementation-sha"


class StaticWorkflowExecutor:
    def __init__(self, output: str | None = None):
        self.output = output or (
            "workflow_status=success API/Application Layer FastAPI app/main.py "
            "How To Run pyproject.toml Useful Files potential_risk testing_concern "
            "CONNECTION_POOL_REGRESSION metric-1 High"
        )

    def execute(self, workflow: str) -> tuple[str, list[str]]:
        return f"{self.output} workflow={workflow}", [f"{workflow}-evidence"]


def test_implementation_version_prefers_github_sha(monkeypatch):
    monkeypatch.setenv("GITHUB_SHA", "github-sha")
    monkeypatch.setenv("APP_VERSION", "app-version")

    assert ImplementationVersionResolver().resolve() == "github-sha"


def test_implementation_version_uses_git_before_app_version(monkeypatch):
    import app.evaluation.versioning as versioning

    monkeypatch.delenv("GITHUB_SHA", raising=False)
    monkeypatch.setenv("APP_VERSION", "app-version")
    monkeypatch.setattr(
        versioning.subprocess,
        "run",
        lambda *args, **kwargs: SimpleNamespace(stdout="git-sha\n"),
    )

    assert ImplementationVersionResolver().resolve() == "git-sha"


def test_state_counter_persists_run_ids(tmp_path):
    storage = EvaluationStorage(root=tmp_path)

    assert storage.next_run_id() == "run-000001"
    assert storage.next_run_id() == "run-000002"
    assert EvaluationStorage(root=tmp_path).next_run_id() == "run-000003"


def test_invalid_state_file_fails_loudly(tmp_path):
    (tmp_path / "state.json").write_text(
        '{"schema_version":"agentops-state/v1","run_counter":"oops"}',
        encoding="utf-8",
    )

    with pytest.raises(StateFileInvalidError):
        EvaluationStorage(root=tmp_path).next_run_id()


def test_result_hash_is_stable_but_run_id_is_execution_specific(tmp_path):
    service = EvaluationService(
        storage=EvaluationStorage(root=tmp_path),
        runner=EvaluationRunner(workflow_executor=StaticWorkflowExecutor()),
        version_resolver=StaticVersionResolver(),
    )

    first = service.run_suite("mvp-demo-suite@v1", "local-test")
    second = service.run_suite("mvp-demo-suite@v1", "local-test")

    assert first["run_id"] == "run-000001"
    assert second["run_id"] == "run-000002"
    assert first["result_hash"] == second["result_hash"]


def test_persisted_json_is_stable_except_execution_fields(tmp_path):
    service = EvaluationService(
        storage=EvaluationStorage(root=tmp_path),
        runner=EvaluationRunner(workflow_executor=StaticWorkflowExecutor()),
        version_resolver=StaticVersionResolver(),
    )

    first = service.run_suite("mvp-demo-suite@v1", "local-test")
    second = service.run_suite("mvp-demo-suite@v1", "local-test")

    assert _without_execution_fields(first) == _without_execution_fields(second)


def test_suite_validation_rejects_duplicate_checks_and_nonpositive_weights():
    good_task = MVP_DEMO_SUITE.tasks[0]
    duplicate_check_suite = EvaluationSuite(
        schema_version=EVALUATION_SUITE_SCHEMA_VERSION,
        id="invalid-suite",
        version="v1",
        tasks=[
            EvaluationTask(
                id="task",
                priority="P0",
                workflow="architecture_report",
                fixture_id="fixture@v1",
                pass_threshold=80,
                checks=[good_task.checks[0], good_task.checks[0]],
            )
        ],
    )
    zero_weight_suite = EvaluationSuite(
        schema_version=EVALUATION_SUITE_SCHEMA_VERSION,
        id="invalid-suite",
        version="v1",
        tasks=[
            EvaluationTask(
                id="task",
                priority="P0",
                workflow="architecture_report",
                fixture_id="fixture@v1",
                pass_threshold=80,
                checks=[
                    EvaluationCheck(
                        id="zero",
                        description="zero weight",
                        weight=0,
                        required=True,
                        expected_fact=ExpectedFact("zero", "contains", "anything"),
                    )
                ],
            )
        ],
    )

    with pytest.raises(Exception):
        EvaluationSuiteLoader([duplicate_check_suite]).list_suites()
    with pytest.raises(Exception):
        EvaluationSuiteLoader([zero_weight_suite]).list_suites()


def test_scoring_requires_threshold_and_required_checks():
    suite = EvaluationSuite(
        schema_version=EVALUATION_SUITE_SCHEMA_VERSION,
        id="scoring-suite",
        version="v1",
        tasks=[
            EvaluationTask(
                id="scoring-task",
                priority="P0",
                workflow="architecture_report",
                fixture_id="fixture@v1",
                pass_threshold=50,
                checks=[
                    EvaluationCheck(
                        id="optional-pass",
                        description="optional pass",
                        weight=50,
                        required=False,
                        expected_fact=ExpectedFact("optional-pass", "contains", "present"),
                    ),
                    EvaluationCheck(
                        id="required-fail",
                        description="required fail",
                        weight=50,
                        required=True,
                        expected_fact=ExpectedFact("required-fail", "contains", "missing"),
                    ),
                ],
            )
        ],
    )

    run = EvaluationRunner(workflow_executor=StaticWorkflowExecutor("present")).run(
        suite=suite,
        run_id="run-000001",
        implementation_version="sha",
        version_label="test",
    )

    task = run.tasks[0]
    assert task.score == 50
    assert task.passed is False
    assert task.checks[1].actual is None


def test_expected_fact_matching_normalizes_text():
    matcher = FactMatcher()
    fact = ExpectedFact("fact", "contains", "API Application Layer")

    assert matcher.match(fact, "api    application   layer")


def test_evaluation_run_api_persists_under_agentops_home(tmp_path, monkeypatch):
    monkeypatch.setenv("AGENTOPS_HOME", str(tmp_path))
    monkeypatch.setenv("GITHUB_SHA", "api-test-sha")
    client = TestClient(app)

    response = client.post(
        "/api/v1/evaluations/run",
        json={"suite_id": "mvp-demo-suite@v1", "version_label": "api-test"},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["schema_version"] == "evaluation-run/v1"
    assert body["run_id"] == "run-000001"
    assert body["summary"]["total_tasks"] == 4
    assert body["implementation_version"] == "api-test-sha"
    assert (tmp_path / "eval-runs" / "mvp-demo-suite@v1" / "run-000001.json").exists()


def test_evaluation_suites_api_lists_p0_suite():
    client = TestClient(app)

    response = client.get("/api/v1/evaluations/suites")

    assert response.status_code == 200
    body = response.json()
    suite = body["suites"][0]
    assert suite["qualified_id"] == "mvp-demo-suite@v1"
    assert suite["p0_tasks"] == [
        "repository-architecture",
        "onboarding-guide",
        "pr-review",
        "incident-rca",
    ]


def _without_execution_fields(run: dict) -> dict:
    normalized = asdict(run) if not isinstance(run, dict) else dict(run)
    normalized.pop("run_id", None)
    normalized["metadata"] = dict(normalized["metadata"])
    normalized["metadata"].pop("duration_ms", None)
    return normalized
