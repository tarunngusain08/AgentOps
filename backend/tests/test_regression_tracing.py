from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from app.evaluation.errors import ComparisonCheckSetMismatchError, EvaluationIdentifierInvalidError, EvaluationRunReadError
from app.evaluation.models import EXECUTION_TRACE_SCHEMA_VERSION, ExecutionTrace, TraceSpan
from app.evaluation.regression import IMPROVEMENT, NO_CHANGE, REGRESSION, RegressionComparator
from app.evaluation.storage import EvaluationStorage
from app.evaluation.tracing import validate_trace_metadata
from app.main import app


def test_regression_comparison_works_without_trace_files():
    baseline = _run("run-000001", score=100, passed=True)
    candidate = _run("run-000002", score=100, passed=True)

    report = RegressionComparator().compare(baseline, candidate)

    assert report.status == NO_CHANGE
    assert report.comparison_passed is True
    assert report.summary.p0_regressions == 0


def test_regression_comparison_rejects_check_set_mismatch():
    baseline = _run("run-000001")
    candidate = _run("run-000002")
    candidate["tasks"][0]["checks"].append(
        {
            "id": "extra-check",
            "description": "extra",
            "weight": 1,
            "required": False,
            "passed": True,
            "expected": "extra",
            "actual": "extra",
            "evidence": [],
        }
    )

    with pytest.raises(ComparisonCheckSetMismatchError):
        RegressionComparator().compare(baseline, candidate)


@pytest.mark.parametrize(
    ("baseline_score", "candidate_score", "expected_status"),
    [
        (100, 96, NO_CHANGE),
        (100, 95, REGRESSION),
        (90, 94, NO_CHANGE),
        (90, 95, IMPROVEMENT),
    ],
)
def test_regression_threshold_boundaries(baseline_score, candidate_score, expected_status):
    baseline = _run("run-000001", score=baseline_score, passed=True)
    candidate = _run("run-000002", score=candidate_score, passed=True)

    report = RegressionComparator().compare(baseline, candidate)

    assert report.task_comparisons[0].status == expected_status


def test_required_check_pass_to_fail_is_a_p0_regression():
    baseline = _run("run-000001", score=100, passed=True, check_passed=True)
    candidate = _run("run-000002", score=100, passed=True, check_passed=False)

    report = RegressionComparator().compare(baseline, candidate)

    assert report.status == REGRESSION
    assert report.comparison_passed is False
    assert report.summary.p0_regressions == 1
    assert report.task_comparisons[0].regression_reasons == ["required_check_failed"]


def test_trace_metadata_rejects_large_values():
    with pytest.raises(ValueError):
        validate_trace_metadata({"raw_output": "x" * 4097})


def test_trace_storage_validates_schema_before_write(tmp_path):
    storage = EvaluationStorage(root=tmp_path)
    trace = ExecutionTrace(
        schema_version=EXECUTION_TRACE_SCHEMA_VERSION,
        trace_id="trace-run-000001-task",
        run_id="run-000001",
        task_id="task",
        started_at="2026-06-15T00:00:00+00:00",
        duration_ms=0,
        spans=[
            TraceSpan(
                id="span-001",
                name="task_start",
                start_ms=0,
                duration_ms=0,
                status="ok",
                metadata={"raw_output": "x" * 4097},
            )
        ],
    )

    with pytest.raises(ValueError):
        storage.save_trace(trace)


def test_corrupt_trace_artifact_is_reported(tmp_path):
    trace_path = tmp_path / "traces" / "run-000001" / "trace-run-000001-task.json"
    trace_path.parent.mkdir(parents=True)
    trace_path.write_text("{not json", encoding="utf-8")

    with pytest.raises(EvaluationRunReadError):
        EvaluationStorage(root=tmp_path).load_trace("trace-run-000001-task")


def test_trace_lookup_rejects_glob_metacharacters(tmp_path):
    trace_path = tmp_path / "traces" / "run-000001" / "trace-run-000001-task.json"
    trace_path.parent.mkdir(parents=True)
    trace_path.write_text(
        '{"schema_version":"execution-trace/v1","trace_id":"trace-run-000001-task","run_id":"run-000001","task_id":"task","started_at":"2026-06-15T00:00:00+00:00","duration_ms":0,"spans":[]}',
        encoding="utf-8",
    )

    with pytest.raises(EvaluationIdentifierInvalidError):
        EvaluationStorage(root=tmp_path).load_trace("*")


def test_run_lookup_rejects_path_traversal(tmp_path):
    with pytest.raises(EvaluationIdentifierInvalidError):
        EvaluationStorage(root=tmp_path).load_run("mvp-demo-suite", "v2", "../../../outside")


def test_evaluation_api_emits_traces_and_compares_runs(tmp_path, monkeypatch):
    monkeypatch.setenv("AGENTOPS_HOME", str(tmp_path))
    monkeypatch.setenv("GITHUB_SHA", "m06-api-sha")
    monkeypatch.setenv("AGENTOPS_ENABLE_EVALUATION_MUTATIONS", "true")
    client = TestClient(app)

    first = client.post(
        "/api/v1/evaluations/run",
        json={"suite_id": "mvp-demo-suite@v1", "version_label": "api-test"},
    ).json()
    second = client.post(
        "/api/v1/evaluations/run",
        json={"suite_id": "mvp-demo-suite@v1", "version_label": "api-test"},
    ).json()

    traces = client.get(f"/api/v1/evaluations/runs/{first['run_id']}/traces")
    comparison = client.post(
        "/api/v1/evaluations/compare",
        json={
            "suite_id": "mvp-demo-suite",
            "suite_version": "v1",
            "baseline_run_id": first["run_id"],
            "candidate_run_id": second["run_id"],
        },
    )

    assert traces.status_code == 200
    assert len(traces.json()["traces"]) == 4
    assert comparison.status_code == 200
    assert comparison.json()["status"] == NO_CHANGE
    assert comparison.json()["comparison_passed"] is True
    assert (tmp_path / "regression-reports" / f"regression-{first['run_id']}-vs-{second['run_id']}.json").exists()


def _run(run_id: str, score: int = 100, passed: bool = True, check_passed: bool = True) -> dict:
    return {
        "schema_version": "evaluation-run/v1",
        "run_id": run_id,
        "result_hash": f"hash-{run_id}",
        "suite_id": "mvp-demo-suite",
        "suite_version": "v1",
        "implementation_version": "sha",
        "version_label": "test",
        "fixture_versions": {"task": "fixture@v1"},
        "tasks": [
            {
                "id": "task",
                "priority": "P0",
                "workflow": "architecture_report",
                "fixture_id": "fixture@v1",
                "score": score,
                "passed": passed,
                "checks": [
                    {
                        "id": "required-check",
                        "description": "required",
                        "weight": 100,
                        "required": True,
                        "passed": check_passed,
                        "expected": "expected",
                        "actual": "expected" if check_passed else None,
                        "evidence": [],
                    }
                ],
            }
        ],
        "summary": {
            "total_tasks": 1,
            "passed_tasks": 1 if passed else 0,
            "failed_tasks": 0 if passed else 1,
            "pass_rate": 1.0 if passed else 0.0,
        },
        "metadata": {"duration_ms": 0, "analysis_mode": "heuristic"},
    }
