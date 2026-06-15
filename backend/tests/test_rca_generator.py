from app.incident.analyzer import IncidentAnalyzer
from app.incident.evidence_collector import EvidenceCollector
from app.incident.fixtures import IncidentFixtureLoader
from app.incident.rca_generator import RCAGenerator


def test_rca_generator_references_valid_evidence_ids_everywhere():
    fixture = IncidentFixtureLoader().load("checkout-latency")
    bundle = EvidenceCollector().collect(fixture, None)
    findings = IncidentAnalyzer().analyze(bundle)

    rca = RCAGenerator().generate(
        fixture=fixture,
        bundle=bundle,
        findings=findings,
        analysis_duration_ms=12,
        repository_analyzed=False,
    )

    valid_ids = {item.id for item in rca.evidence}
    traceable_sections = [
        rca.summary,
        rca.impact,
        rca.suspected_root_cause.explanation,
        rca.mitigation,
        rca.prevention,
    ]

    for section in traceable_sections:
        assert section.evidence_ids
        assert set(section.evidence_ids) <= valid_ids
    assert all(set(event.evidence_ids) <= valid_ids for event in rca.timeline)
    assert [event.timestamp for event in rca.timeline] == sorted(event.timestamp for event in rca.timeline)
    assert rca.confidence == "High"
    assert rca.metadata["analysis_duration_ms"] == 12


def test_mitigation_and_prevention_derive_from_root_cause_category():
    fixture = IncidentFixtureLoader().load("checkout-latency")
    bundle = EvidenceCollector().collect(fixture, None)
    findings = IncidentAnalyzer().analyze(bundle)

    rca = RCAGenerator().generate(
        fixture=fixture,
        bundle=bundle,
        findings=findings,
        analysis_duration_ms=1,
        repository_analyzed=False,
    )

    assert rca.suspected_root_cause.category == "CONNECTION_POOL_REGRESSION"
    assert "connection pool" in rca.mitigation.text.lower()
    assert "connection-pool" in rca.prevention.text.lower()

