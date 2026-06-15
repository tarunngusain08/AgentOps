from __future__ import annotations

from typing import Protocol

from app.analyzer.repository_analyzer import RepositoryAnalysis
from app.incident.evidence_collector import EvidenceCollector
from app.incident.models import IncidentEvidenceBundle, ScenarioFixture


class InvestigationProvider(Protocol):
    def collect(self, fixture: ScenarioFixture, repository_analysis: RepositoryAnalysis | None) -> IncidentEvidenceBundle:
        ...


class FixtureInvestigationProvider:
    def __init__(self, evidence_collector: EvidenceCollector | None = None):
        self.evidence_collector = evidence_collector or EvidenceCollector()

    def collect(self, fixture: ScenarioFixture, repository_analysis: RepositoryAnalysis | None) -> IncidentEvidenceBundle:
        return self.evidence_collector.collect(fixture, repository_analysis)

