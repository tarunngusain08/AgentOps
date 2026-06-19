from __future__ import annotations

from dataclasses import asdict

from app.analyzer.repository_analyzer import RepositoryAnalyzer
from app.documentation.documentation_generator import DocumentationGenerator
from app.evaluation.fixtures import pull_request_fixture, repository_fixture
from app.incident.service import IncidentInvestigationService
from app.reporting.report_generator import ReportGenerator
from app.review.diff_analyzer import DiffAnalyzer
from app.review.pr_review_generator import PRReviewGenerator


class WorkflowExecutor:
    def __init__(self):
        self.repository_analyzer = RepositoryAnalyzer()
        self.report_generator = ReportGenerator()
        self.documentation_generator = DocumentationGenerator()
        self.diff_analyzer = DiffAnalyzer()
        self.pr_review_generator = PRReviewGenerator()

    def execute(self, workflow: str, fixture_id: str = "repository-basic@v1") -> tuple[str, list[str]]:
        if workflow == "architecture_report":
            return self._architecture_report(fixture_id)
        if workflow == "onboarding_guide":
            return self._onboarding_guide(fixture_id)
        if workflow == "pr_review":
            return self._pr_review(fixture_id)
        if workflow == "incident_rca":
            return self._incident_rca()
        if workflow == "static_index":
            return self._static_index(fixture_id)
        raise ValueError(f"Unsupported workflow: {workflow}")

    def _architecture_report(self, fixture_id: str) -> tuple[str, list[str]]:
        snapshot = repository_fixture(fixture_id)
        analysis = self.repository_analyzer.analyze(snapshot)
        response = self.report_generator.generate(snapshot, analysis)
        evidence = [
            *response.report.important_files,
            *[file.path for file in analysis.repository_index.files],
            *[link.test_path for link in analysis.repository_index.tests],
        ]
        return _flatten({"workflow_status": "success", "report": _model_to_dict(response.report)}), evidence

    def _onboarding_guide(self, fixture_id: str) -> tuple[str, list[str]]:
        snapshot = repository_fixture(fixture_id)
        analysis = self.repository_analyzer.analyze(snapshot)
        report = self.report_generator.generate(snapshot, analysis).report
        guide = self.documentation_generator.generate_onboarding_guide(snapshot, analysis, report)
        return _flatten({"workflow_status": "success", "guide": asdict(guide)}), guide.evidence

    def _pr_review(self, fixture_id: str) -> tuple[str, list[str]]:
        repository_fixture_id = "go_service@v1" if fixture_id == "go_pr_static@v1" else "repository-basic@v1"
        snapshot = repository_fixture(repository_fixture_id)
        pull_request = pull_request_fixture(fixture_id)
        analysis = self.repository_analyzer.analyze(snapshot)
        report = self.report_generator.generate(snapshot, analysis).report
        diff = self.diff_analyzer.analyze(pull_request.files, upstream_truncated=pull_request.truncated)
        review = self.pr_review_generator.generate(snapshot, analysis, report, pull_request, diff)
        evidence = [item for finding in review.findings for item in finding.evidence]
        return _flatten({"workflow_status": "success", "review": asdict(review)}), evidence

    def _incident_rca(self) -> tuple[str, list[str]]:
        rca = IncidentInvestigationService().investigate("checkout-latency")
        evidence = [item.id for item in rca.evidence]
        return _flatten({"workflow_status": "success", "rca": asdict(rca)}), evidence

    def _static_index(self, fixture_id: str) -> tuple[str, list[str]]:
        snapshot = repository_fixture(fixture_id)
        analysis = self.repository_analyzer.analyze(snapshot)
        index = analysis.repository_index
        payload = {
            "workflow_status": "success",
            "repository_index": {
                "files": [asdict(file) for file in index.files],
                "symbols": [asdict(symbol) for symbol in index.symbols],
                "imports": [asdict(item) for item in index.imports],
                "tests": [asdict(link) for link in index.tests],
                "metadata": asdict(index.metadata),
            },
        }
        evidence = [file.path for file in index.files]
        evidence.extend(link.test_path for link in index.tests)
        return _flatten(payload), evidence


def _flatten(value: object) -> str:
    if isinstance(value, dict):
        return " ".join(f"{key}={_flatten(item)}" for key, item in value.items())
    if isinstance(value, list):
        return " ".join(_flatten(item) for item in value)
    return str(value)


def _model_to_dict(value: object) -> dict:
    if hasattr(value, "model_dump"):
        return value.model_dump()
    if hasattr(value, "dict"):
        return value.dict()
    raise TypeError(f"Unsupported model type: {type(value).__name__}")
