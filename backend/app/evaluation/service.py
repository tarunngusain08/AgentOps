from __future__ import annotations

from app.evaluation.runner import EvaluationRunner
from app.evaluation.storage import EvaluationStorage
from app.evaluation.suites import EvaluationSuiteLoader
from app.evaluation.versioning import ImplementationVersionResolver


class EvaluationService:
    def __init__(
        self,
        suite_loader: EvaluationSuiteLoader | None = None,
        storage: EvaluationStorage | None = None,
        runner: EvaluationRunner | None = None,
        version_resolver: ImplementationVersionResolver | None = None,
    ):
        self.suite_loader = suite_loader or EvaluationSuiteLoader()
        self.storage = storage or EvaluationStorage()
        self.runner = runner or EvaluationRunner()
        self.version_resolver = version_resolver or ImplementationVersionResolver()

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
        from dataclasses import asdict

        return asdict(run)

    def load_run(self, suite_id: str, suite_version: str, run_id: str) -> dict:
        return self.storage.load_run(suite_id, suite_version, run_id)

