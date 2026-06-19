from __future__ import annotations

import argparse
from pathlib import Path
from typing import Sequence

from app.evaluation.baseline import BaselineValidationError, validate_baseline, validate_evaluation_run_integrity
from app.evaluation.errors import (
    CandidateRunNotFoundError,
    ComparisonCheckSetMismatchError,
    EvaluationIdentifierInvalidError,
    EvaluationError,
    EvaluationSuiteNotFoundError,
    SuiteVersionMismatchError,
)
from app.evaluation.identifiers import validate_evaluation_identifier
from app.evaluation.json_utils import read_json, write_canonical_json
from app.evaluation.regression import RegressionComparator
from app.evaluation.service import EvaluationService
from app.evaluation.suites import EvaluationSuiteLoader

PASS = 0
QUALITY_FAILURE = 1
MISSING_INPUT = 2
INVALID_INPUT = 3


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="python -m app.evaluation.cli")
    subparsers = parser.add_subparsers(dest="command", required=True)

    run_parser = subparsers.add_parser("run")
    run_parser.add_argument("--suite", default="mvp-demo-suite@v2")
    run_parser.add_argument("--version", default="local")
    run_parser.add_argument("--output", required=True)

    compare_parser = subparsers.add_parser("compare")
    compare_parser.add_argument("--baseline", required=True)
    compare_parser.add_argument("--candidate", required=True)
    compare_parser.add_argument("--fail-on-p0-regression", action="store_true")

    args = parser.parse_args(argv)
    if args.command == "run":
        return _run_suite(args.suite, args.version, Path(args.output))
    if args.command == "compare":
        return _compare(Path(args.baseline), Path(args.candidate), args.fail_on_p0_regression)
    return INVALID_INPUT


def _run_suite(suite_id: str, version_label: str, output: Path) -> int:
    try:
        run = EvaluationService().run_suite(suite_id=suite_id, version_label=version_label)
    except EvaluationSuiteNotFoundError as exc:
        print(exc.message)
        return MISSING_INPUT
    except EvaluationError as exc:
        print(exc.message)
        return INVALID_INPUT

    write_canonical_json(output, run)
    if _has_p0_failure(run):
        return QUALITY_FAILURE
    return PASS


def _compare(baseline_path: Path, candidate_path: Path, fail_on_p0_regression: bool) -> int:
    if not baseline_path.exists() or not candidate_path.exists():
        print("Baseline or candidate evaluation run is missing.")
        return MISSING_INPUT

    try:
        baseline = read_json(baseline_path)
        candidate = read_json(candidate_path)
        suite = EvaluationSuiteLoader().load(f"{baseline['suite_id']}@{baseline['suite_version']}")
        validate_baseline(baseline, suite)
        validate_evaluation_run_integrity(candidate)
        report = RegressionComparator().compare(baseline, candidate)
        report_id = validate_evaluation_identifier(report.report_id, "report_id")
    except (
        BaselineValidationError,
        ComparisonCheckSetMismatchError,
        EvaluationIdentifierInvalidError,
        SuiteVersionMismatchError,
        KeyError,
        ValueError,
    ) as exc:
        print(str(exc))
        return INVALID_INPUT
    except (EvaluationSuiteNotFoundError, CandidateRunNotFoundError) as exc:
        print(exc.message)
        return MISSING_INPUT

    report_path = Path(".agentops") / "regression-reports" / f"{report_id}.json"
    from dataclasses import asdict

    write_canonical_json(report_path, asdict(report))
    print(f"Regression report: {report_path}")

    if _has_p0_failure(candidate):
        return QUALITY_FAILURE
    if fail_on_p0_regression and report.summary.p0_regressions > 0:
        return QUALITY_FAILURE
    return PASS


def _has_p0_failure(run: dict) -> bool:
    return any(task["priority"] == "P0" and not task["passed"] for task in run["tasks"])


if __name__ == "__main__":
    raise SystemExit(main())
