from app.analyzer.repository_analyzer import ComponentFinding, RepositoryAnalysis
from app.incident.evidence_collector import EvidenceCollector
from app.incident.fixtures import IncidentFixtureLoader


def test_evidence_collector_separates_evidence_from_repository_context():
    fixture = IncidentFixtureLoader().load("checkout-latency")
    analysis = RepositoryAnalysis(
        technology_stack=["Python", "FastAPI"],
        components=[
            ComponentFinding("Source Modules", "Implementation modules.", ["app/"]),
            ComponentFinding("API/Application Layer", "API layer.", ["backend/"]),
        ],
        entry_points=["backend/app/main.py"],
        important_files=["pyproject.toml"],
        relationships=[],
        assumptions=[],
        overview="Example",
    )

    bundle = EvidenceCollector().collect(fixture, analysis)

    assert [item.id for item in bundle.metrics] == ["metric-1", "metric-2"]
    assert [item.id for item in bundle.logs] == ["log-1", "log-2"]
    assert [item.id for item in bundle.deployment_events] == ["deploy-1", "deploy-2"]
    assert [item.id for item in bundle.change_evidence] == ["change-1", "change-2"]
    assert [(signal.component, signal.path) for signal in bundle.repository_signals] == [
        ("API/Application Layer", "backend/"),
        ("Source Modules", "app/"),
    ]


def test_evidence_collector_omits_repository_context_without_analysis():
    fixture = IncidentFixtureLoader().load("checkout-latency")

    bundle = EvidenceCollector().collect(fixture, None)

    assert bundle.repository_signals == []

