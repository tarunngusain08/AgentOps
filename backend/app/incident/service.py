from __future__ import annotations

from time import perf_counter

from app.analyzer.repository_analyzer import RepositoryAnalyzer
from app.github.service import GitHubService
from app.incident.analyzer import IncidentAnalyzer
from app.incident.fixtures import IncidentFixtureLoader
from app.incident.models import IncidentRCA
from app.incident.provider import FixtureInvestigationProvider
from app.incident.rca_generator import RCAGenerator
from app.reporting.report_generator import ReportGenerator


class IncidentInvestigationService:
    def __init__(
        self,
        github_service: GitHubService | None = None,
        fixture_loader: IncidentFixtureLoader | None = None,
        repository_analyzer: RepositoryAnalyzer | None = None,
        report_generator: ReportGenerator | None = None,
        provider: FixtureInvestigationProvider | None = None,
        incident_analyzer: IncidentAnalyzer | None = None,
        rca_generator: RCAGenerator | None = None,
    ):
        self.github_service = github_service or GitHubService()
        self.fixture_loader = fixture_loader or IncidentFixtureLoader()
        self.repository_analyzer = repository_analyzer or RepositoryAnalyzer()
        self.report_generator = report_generator or ReportGenerator()
        self.provider = provider or FixtureInvestigationProvider()
        self.incident_analyzer = incident_analyzer or IncidentAnalyzer()
        self.rca_generator = rca_generator or RCAGenerator()

    def investigate(self, scenario_id: str, repository_url: str | None = None) -> IncidentRCA:
        started = perf_counter()
        fixture = self.fixture_loader.load(scenario_id)
        repository_analysis = None
        repository_analyzed = False
        repository_unavailable = False

        if repository_url:
            try:
                snapshot = self.github_service.load_repository(repository_url)
                repository_analysis = self.repository_analyzer.analyze(snapshot)
                self.report_generator.generate(snapshot, repository_analysis)
                repository_analyzed = True
            except Exception:
                repository_unavailable = True

        bundle = self.provider.collect(fixture, repository_analysis)
        findings = self.incident_analyzer.analyze(bundle)
        duration_ms = int((perf_counter() - started) * 1000)
        return self.rca_generator.generate(
            fixture=fixture,
            bundle=bundle,
            findings=findings,
            analysis_duration_ms=duration_ms,
            repository_analyzed=repository_analyzed,
            repository_unavailable=repository_unavailable,
        )

