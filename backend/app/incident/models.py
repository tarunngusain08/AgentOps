from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


class RootCauseCategory:
    CONNECTION_POOL_REGRESSION = "CONNECTION_POOL_REGRESSION"
    QUERY_PERFORMANCE = "QUERY_PERFORMANCE"
    TIMEOUT_CONFIGURATION = "TIMEOUT_CONFIGURATION"
    UNKNOWN = "UNKNOWN"


class InvestigationOutcome:
    ROOT_CAUSE_IDENTIFIED = "ROOT_CAUSE_IDENTIFIED"
    INSUFFICIENT_EVIDENCE = "INSUFFICIENT_EVIDENCE"
    CONFLICTING_EVIDENCE = "CONFLICTING_EVIDENCE"


@dataclass(frozen=True)
class ScenarioFixture:
    id: str
    version: str
    data: dict[str, Any]


@dataclass(frozen=True)
class EvidenceItem:
    id: str
    type: str
    source: str
    timestamp: str
    description: str


@dataclass(frozen=True)
class RepositorySignal:
    component: str
    path: str
    reason: str
    confidence: float


@dataclass(frozen=True)
class IncidentEvidenceBundle:
    metrics: list[EvidenceItem]
    logs: list[EvidenceItem]
    deployment_events: list[EvidenceItem]
    change_evidence: list[EvidenceItem]
    repository_signals: list[RepositorySignal] = field(default_factory=list)


@dataclass(frozen=True)
class TraceableText:
    text: str
    evidence_ids: list[str]


@dataclass(frozen=True)
class TimelineEvent:
    timestamp: str
    type: str
    description: str
    evidence_ids: list[str]


@dataclass(frozen=True)
class IncidentFindings:
    matched_metrics: list[str]
    matched_logs: list[str]
    matched_changes: list[str]
    matched_deployments: list[str]
    root_cause_category: str
    outcome: str
    confidence_score: int


@dataclass(frozen=True)
class RootCause:
    category: str
    title: str
    explanation: TraceableText
    evidence_ids: list[str]


@dataclass(frozen=True)
class IncidentRCA:
    summary: TraceableText
    impact: TraceableText
    timeline: list[TimelineEvent]
    evidence: list[EvidenceItem]
    repository_context: list[RepositorySignal]
    suspected_root_cause: RootCause
    mitigation: TraceableText
    prevention: TraceableText
    assumptions: list[str]
    confidence: str
    metadata: dict[str, int | str | bool | list[str]]

