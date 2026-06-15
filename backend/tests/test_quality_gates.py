from __future__ import annotations

from pathlib import Path

import pytest

from app.evaluation import cli
from app.evaluation.baseline import BaselineValidationError, validate_baseline
from app.evaluation.hashing import evaluation_result_hash
from app.evaluation.json_utils import read_json, write_canonical_json
from app.evaluation.suites import EvaluationSuiteLoader

ROOT = Path(__file__).resolve().parents[2]
BASELINE_PATH = ROOT / "backend" / "app" / "evaluation" / "baselines" / "mvp-demo-suite@v1.json"
WORKFLOW_PATH = ROOT / ".github" / "workflows" / "agentops-quality.yml"


def test_tracked_baseline_has_valid_hash_and_p0_tasks():
    baseline = read_json(BASELINE_PATH)
    suite = EvaluationSuiteLoader().load("mvp-demo-suite@v1")

    validate_baseline(baseline, suite)


def test_baseline_hash_integrity_detects_manual_edits():
    baseline = read_json(BASELINE_PATH)
    suite = EvaluationSuiteLoader().load("mvp-demo-suite@v1")
    baseline["tasks"][0]["score"] = 99

    with pytest.raises(BaselineValidationError):
        validate_baseline(baseline, suite)


def test_baseline_p0_task_list_must_match_suite():
    baseline = read_json(BASELINE_PATH)
    suite = EvaluationSuiteLoader().load("mvp-demo-suite@v1")
    baseline["tasks"] = baseline["tasks"][1:]
    baseline["result_hash"] = evaluation_result_hash(baseline)

    with pytest.raises(BaselineValidationError):
        validate_baseline(baseline, suite)


def test_cli_run_and_compare_pass(tmp_path, monkeypatch):
    candidate_path = tmp_path / "candidate.json"
    monkeypatch.setenv("AGENTOPS_HOME", str(tmp_path / "runtime"))
    monkeypatch.setenv("GITHUB_SHA", "quality-gate-sha")

    run_code = cli.main([
        "run",
        "--suite",
        "mvp-demo-suite@v1",
        "--version",
        "test",
        "--output",
        str(candidate_path),
    ])
    compare_code = cli.main([
        "compare",
        "--baseline",
        str(BASELINE_PATH),
        "--candidate",
        str(candidate_path),
        "--fail-on-p0-regression",
    ])

    assert run_code == 0
    assert compare_code == 0
    assert candidate_path.exists()
    assert (Path(".agentops") / "regression-reports").exists()


def test_cli_compare_fails_for_candidate_p0_failure(tmp_path):
    candidate = read_json(BASELINE_PATH)
    candidate["run_id"] = "run-failing"
    candidate["tasks"][0]["passed"] = False
    candidate["tasks"][0]["checks"][0]["passed"] = False
    candidate["tasks"][0]["checks"][0]["actual"] = None
    candidate["summary"]["passed_tasks"] = 3
    candidate["summary"]["failed_tasks"] = 1
    candidate["summary"]["pass_rate"] = 0.75
    candidate["result_hash"] = evaluation_result_hash(candidate)
    candidate_path = tmp_path / "candidate-failing.json"
    write_canonical_json(candidate_path, candidate)

    code = cli.main([
        "compare",
        "--baseline",
        str(BASELINE_PATH),
        "--candidate",
        str(candidate_path),
        "--fail-on-p0-regression",
    ])

    assert code == 1


def test_cli_compare_missing_input_exit_code(tmp_path):
    code = cli.main([
        "compare",
        "--baseline",
        str(BASELINE_PATH),
        "--candidate",
        str(tmp_path / "missing.json"),
    ])

    assert code == 2


def test_cli_compare_invalid_input_exit_code(tmp_path):
    candidate_path = tmp_path / "candidate.json"
    candidate_path.write_text("{not json", encoding="utf-8")

    code = cli.main([
        "compare",
        "--baseline",
        str(BASELINE_PATH),
        "--candidate",
        str(candidate_path),
    ])

    assert code == 3


def test_ci_workflow_pins_runtimes_and_uploads_artifacts():
    workflow = WORKFLOW_PATH.read_text(encoding="utf-8")

    assert 'python-version: "3.13"' in workflow
    assert 'node-version: "22"' in workflow
    assert "backend/requirements-lock.txt" in workflow
    assert "frontend/package-lock.json" in workflow
    assert "retention-days: 30" in workflow
    assert "actions/upload-artifact@v4" in workflow


def test_dependency_lockfiles_exist():
    assert (ROOT / "backend" / "requirements-lock.txt").exists()
    assert (ROOT / "frontend" / "package-lock.json").exists()
