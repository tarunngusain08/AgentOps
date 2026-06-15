from dataclasses import replace

from app.incident.analyzer import CorrelationLevel, IncidentAnalyzer, confidence_label
from app.incident.evidence_collector import EvidenceCollector
from app.incident.fixtures import IncidentFixtureLoader
from app.incident.models import IncidentEvidenceBundle, InvestigationOutcome, RootCauseCategory


def _bundle() -> IncidentEvidenceBundle:
    fixture = IncidentFixtureLoader().load("checkout-latency")
    return EvidenceCollector().collect(fixture, None)


def test_incident_analyzer_identifies_connection_pool_regression():
    findings = IncidentAnalyzer().analyze(_bundle())

    assert findings.root_cause_category == RootCauseCategory.CONNECTION_POOL_REGRESSION
    assert findings.outcome == InvestigationOutcome.ROOT_CAUSE_IDENTIFIED
    assert findings.confidence_score == 100


def test_correlation_scoring_full_matches():
    analyzer = IncidentAnalyzer()
    bundle = _bundle()

    assert analyzer.metric_correlation(bundle) == CorrelationLevel.FULL
    assert analyzer.log_correlation(bundle) == CorrelationLevel.FULL
    assert analyzer.deployment_correlation(bundle) == CorrelationLevel.FULL
    assert analyzer.change_correlation(bundle) == CorrelationLevel.FULL


def test_correlation_scoring_none_matches():
    empty_bundle = IncidentEvidenceBundle(metrics=[], logs=[], deployment_events=[], change_evidence=[])
    analyzer = IncidentAnalyzer()

    assert analyzer.metric_correlation(empty_bundle) == CorrelationLevel.NONE
    assert analyzer.log_correlation(empty_bundle) == CorrelationLevel.NONE
    assert analyzer.deployment_correlation(empty_bundle) == CorrelationLevel.NONE
    assert analyzer.change_correlation(empty_bundle) == CorrelationLevel.NONE


def test_correlation_scoring_partial_matches():
    bundle = _bundle()
    late_metric = replace(bundle.metrics[0], timestamp="2026-06-10T10:30:00+00:00")
    partial_bundle = replace(
        bundle,
        metrics=[late_metric],
        logs=[replace(bundle.logs[0], description="Checkout API emitted timeout errors.")],
        change_evidence=[replace(bundle.change_evidence[0], description="Related change touched checkout backend routing.")],
    )
    analyzer = IncidentAnalyzer()

    assert analyzer.metric_correlation(partial_bundle) == CorrelationLevel.PARTIAL
    assert analyzer.log_correlation(partial_bundle) == CorrelationLevel.PARTIAL
    assert analyzer.change_correlation(partial_bundle) == CorrelationLevel.PARTIAL


def test_confidence_label_boundaries():
    assert confidence_label(49) == "Low"
    assert confidence_label(50) == "Medium"
    assert confidence_label(79) == "Medium"
    assert confidence_label(80) == "High"
    assert confidence_label(100) == "High"


def test_outcome_selection_insufficient_evidence():
    findings = IncidentAnalyzer().analyze(IncidentEvidenceBundle(metrics=[], logs=[], deployment_events=[], change_evidence=[]))

    assert findings.outcome == InvestigationOutcome.INSUFFICIENT_EVIDENCE
    assert findings.root_cause_category == RootCauseCategory.UNKNOWN


def test_outcome_selection_conflicting_evidence():
    bundle = _bundle()
    conflicting_change = replace(
        bundle.change_evidence[0],
        description="Related change reduced checkout DB connection pool size and changed checkout query timeout configuration.",
    )
    findings = IncidentAnalyzer().analyze(replace(bundle, change_evidence=[conflicting_change]))

    assert findings.outcome == InvestigationOutcome.CONFLICTING_EVIDENCE
    assert findings.root_cause_category == RootCauseCategory.UNKNOWN

