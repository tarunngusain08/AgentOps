from __future__ import annotations

import os
from dataclasses import asdict
from pathlib import Path
from typing import Any

from app.evaluation.errors import (
    EvaluationRunNotFoundError,
    EvaluationRunReadError,
    RegressionReportWriteError,
    StateFileInvalidError,
    TraceNotFoundError,
)
from app.evaluation.json_utils import read_json, write_canonical_json
from app.evaluation.models import (
    EVALUATION_RUN_SCHEMA_VERSION,
    EXECUTION_TRACE_SCHEMA_VERSION,
    REGRESSION_REPORT_SCHEMA_VERSION,
    STATE_SCHEMA_VERSION,
    EvaluationRun,
    ExecutionTrace,
    RegressionReport,
)
from app.evaluation.tracing import ALLOWED_SPAN_NAMES, validate_trace_metadata


class EvaluationStorage:
    def __init__(self, root: Path | None = None):
        self.root = root or Path(os.getenv("AGENTOPS_HOME", ".agentops"))

    def next_run_id(self) -> str:
        state = self._read_state()
        counter = state["run_counter"] + 1
        self._write_state(counter)
        return f"run-{counter:06d}"

    def save_run(self, run: EvaluationRun) -> None:
        run_dict = asdict(run)
        self._validate_run_dict(run_dict)
        write_canonical_json(self._run_path(run.suite_id, run.suite_version, run.run_id), run_dict)

    def save_trace(self, trace: ExecutionTrace) -> None:
        trace_dict = asdict(trace)
        self._validate_trace_dict(trace_dict)
        write_canonical_json(self._trace_path(trace.run_id, trace.trace_id), trace_dict)

    def list_traces(self, run_id: str) -> list[dict[str, Any]]:
        trace_dir = self.root / "traces" / run_id
        if not trace_dir.exists():
            return []
        traces = [self._load_trace_path(path) for path in sorted(trace_dir.glob("*.json"))]
        return sorted(traces, key=lambda trace: trace["task_id"])

    def load_trace(self, trace_id: str) -> dict[str, Any]:
        matches = sorted((self.root / "traces").glob(f"*/{trace_id}.json"))
        if not matches:
            raise TraceNotFoundError(f"Execution trace not found: {trace_id}")
        return self._load_trace_path(matches[0])

    def save_regression_report(self, report: RegressionReport) -> None:
        report_dict = asdict(report)
        self._validate_regression_report_dict(report_dict)
        try:
            write_canonical_json(self._regression_report_path(report.report_id), report_dict)
        except Exception as exc:
            raise RegressionReportWriteError(f"Regression report could not be written: {report.report_id}") from exc

    def load_run(self, suite_id: str, suite_version: str, run_id: str) -> dict[str, Any]:
        path = self._run_path(suite_id, suite_version, run_id)
        if not path.exists():
            raise EvaluationRunNotFoundError(f"Evaluation run not found: {run_id}")
        try:
            data = read_json(path)
            self._validate_run_dict(data)
        except EvaluationRunNotFoundError:
            raise
        except Exception as exc:
            raise EvaluationRunReadError(f"Evaluation run is unreadable: {run_id}") from exc
        return data

    def _read_state(self) -> dict[str, int | str]:
        path = self.root / "state.json"
        if not path.exists():
            return {"schema_version": STATE_SCHEMA_VERSION, "run_counter": 0}
        try:
            state = read_json(path)
        except Exception as exc:
            raise StateFileInvalidError("Evaluation state file is invalid.") from exc
        if state.get("schema_version") != STATE_SCHEMA_VERSION or not isinstance(state.get("run_counter"), int):
            raise StateFileInvalidError("Evaluation state file is invalid.")
        return state

    def _write_state(self, counter: int) -> None:
        write_canonical_json(
            self.root / "state.json",
            {"schema_version": STATE_SCHEMA_VERSION, "run_counter": counter},
        )

    def _run_path(self, suite_id: str, suite_version: str, run_id: str) -> Path:
        return self.root / "eval-runs" / f"{suite_id}@{suite_version}" / f"{run_id}.json"

    def _trace_path(self, run_id: str, trace_id: str) -> Path:
        return self.root / "traces" / run_id / f"{trace_id}.json"

    def _regression_report_path(self, report_id: str) -> Path:
        return self.root / "regression-reports" / f"{report_id}.json"

    def _load_trace_path(self, path: Path) -> dict[str, Any]:
        try:
            data = read_json(path)
            self._validate_trace_dict(data)
        except Exception as exc:
            raise EvaluationRunReadError(f"Execution trace is unreadable: {path.name}") from exc
        return data

    @staticmethod
    def _validate_run_dict(data: dict[str, Any]) -> None:
        if data.get("schema_version") != EVALUATION_RUN_SCHEMA_VERSION:
            raise ValueError("Unsupported evaluation run schema.")
        required = ["run_id", "result_hash", "suite_id", "suite_version", "implementation_version", "tasks", "summary"]
        for key in required:
            if key not in data:
                raise ValueError(f"Evaluation run missing field: {key}")

    @staticmethod
    def _validate_trace_dict(data: dict[str, Any]) -> None:
        if data.get("schema_version") != EXECUTION_TRACE_SCHEMA_VERSION:
            raise ValueError("Unsupported execution trace schema.")
        required = ["trace_id", "run_id", "task_id", "started_at", "duration_ms", "spans"]
        for key in required:
            if key not in data:
                raise ValueError(f"Execution trace missing field: {key}")
        previous = (-1, "")
        for span in data["spans"]:
            if span.get("name") not in ALLOWED_SPAN_NAMES:
                raise ValueError(f"Unsupported trace span: {span.get('name')}")
            current = (span.get("start_ms"), span.get("id"))
            if current < previous:
                raise ValueError("Trace spans must be sorted.")
            previous = current
            validate_trace_metadata(span.get("metadata", {}))

    @staticmethod
    def _validate_regression_report_dict(data: dict[str, Any]) -> None:
        if data.get("schema_version") != REGRESSION_REPORT_SCHEMA_VERSION:
            raise ValueError("Unsupported regression report schema.")
        required = [
            "report_id",
            "baseline_run_id",
            "candidate_run_id",
            "suite_id",
            "suite_version",
            "status",
            "comparison_passed",
            "task_comparisons",
            "summary",
        ]
        for key in required:
            if key not in data:
                raise ValueError(f"Regression report missing field: {key}")
