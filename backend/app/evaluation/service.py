from __future__ import annotations

from dataclasses import asdict

from app.evaluation.errors import (
    BaselineRunNotFoundError,
    CandidateRunNotFoundError,
    EvaluationRunNotFoundError,
)
from app.evaluation.regression import RegressionComparator
from app.evaluation.runner import EvaluationRunner
from app.evaluation.storage import EvaluationStorage
from app.evaluation.suites import EvaluationSuiteLoader
from app.evaluation.tracing import ExecutionTraceBuilder
from app.evaluation.versioning import ImplementationVersionResolver


class EvaluationService:
    def __init__(
        self,
        suite_loader: EvaluationSuiteLoader | None = None,
        storage: EvaluationStorage | None = None,
        runner: EvaluationRunner | None = None,
        version_resolver: ImplementationVersionResolver | None = None,
        trace_builder: ExecutionTraceBuilder | None = None,
        comparator: RegressionComparator | None = None,
    ):
        self.suite_loader = suite_loader or EvaluationSuiteLoader()
        self.storage = storage or EvaluationStorage()
        self.runner = runner or EvaluationRunner()
        self.version_resolver = version_resolver or ImplementationVersionResolver()
        self.trace_builder = trace_builder or ExecutionTraceBuilder()
        self.comparator = comparator or RegressionComparator()

    def list_suites(self) -> dict:
        return {
            "suites": [
                {
                    "schema_version": suite.schema_version,
                    "id": suite.id,
                    "version": suite.version,
                    "qualified_id": suite.qualified_id,
                    "task_count": len(suite.tasks),
                    "p0_tasks": [task.id for task in suite.tasks if task.priority == "P0"],
                }
                for suite in self.suite_loader.list_suites()
            ]
        }

    def run_suite(self, suite_id: str, version_label: str) -> dict:
        suite = self.suite_loader.load(suite_id)
        run_id = self.storage.next_run_id()
        implementation_version = self.version_resolver.resolve()
        run = self.runner.run(
            suite=suite,
            run_id=run_id,
            implementation_version=implementation_version,
            version_label=version_label,
        )
        self.storage.save_run(run)
        for task in run.tasks:
            self.storage.save_trace(self.trace_builder.build(run.run_id, task))

        return asdict(run)

    def load_run(self, suite_id: str, suite_version: str, run_id: str) -> dict:
        return self.storage.load_run(suite_id, suite_version, run_id)

    def list_traces(self, run_id: str) -> list[dict]:
        return self.storage.list_traces(run_id)

    def load_trace(self, trace_id: str) -> dict:
        return self.storage.load_trace(trace_id)

    def compare_runs(self, suite_id: str, suite_version: str, baseline_run_id: str, candidate_run_id: str) -> dict:
        try:
            baseline = self.storage.load_run(suite_id, suite_version, baseline_run_id)
        except EvaluationRunNotFoundError as exc:
            raise BaselineRunNotFoundError(f"Baseline evaluation run not found: {baseline_run_id}") from exc
        try:
            candidate = self.storage.load_run(suite_id, suite_version, candidate_run_id)
        except EvaluationRunNotFoundError as exc:
            raise CandidateRunNotFoundError(f"Candidate evaluation run not found: {candidate_run_id}") from exc

        report = self.comparator.compare(baseline, candidate)
        self.storage.save_regression_report(report)
        return asdict(report)
