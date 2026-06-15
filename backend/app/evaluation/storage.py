from __future__ import annotations

import os
from dataclasses import asdict
from pathlib import Path
from typing import Any

from app.evaluation.errors import EvaluationRunNotFoundError, EvaluationRunReadError, StateFileInvalidError
from app.evaluation.json_utils import read_json, write_canonical_json
from app.evaluation.models import EVALUATION_RUN_SCHEMA_VERSION, STATE_SCHEMA_VERSION, EvaluationRun


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

    @staticmethod
    def _validate_run_dict(data: dict[str, Any]) -> None:
        if data.get("schema_version") != EVALUATION_RUN_SCHEMA_VERSION:
            raise ValueError("Unsupported evaluation run schema.")
        required = ["run_id", "result_hash", "suite_id", "suite_version", "implementation_version", "tasks", "summary"]
        for key in required:
            if key not in data:
                raise ValueError(f"Evaluation run missing field: {key}")

