from __future__ import annotations

from app.incident.analyzer import confidence_label
from app.incident.models import (
    EvidenceItem,
    IncidentEvidenceBundle,
    IncidentFindings,
    IncidentRCA,
    InvestigationOutcome,
    RootCause,
    RootCauseCategory,
    ScenarioFixture,
    TimelineEvent,
    TraceableText,
)


class RCAGenerator:
    def generate(
        self,
        fixture: ScenarioFixture,
        bundle: IncidentEvidenceBundle,
        findings: IncidentFindings,
        analysis_duration_ms: int,
        repository_analyzed: bool,
        repository_unavailable: bool = False,
    ) -> IncidentRCA:
        evidence = self._ordered_evidence(bundle)
        evidence_ids = {item.id for item in evidence}
        root_evidence_ids = self._root_evidence_ids(findings, evidence_ids)
        category = findings.root_cause_category

        summary = TraceableText(
            text=self._summary_text(category, findings.outcome),
            evidence_ids=root_evidence_ids[:3],
        )
        impact = TraceableText(
            text="Checkout p95 latency and timeout errors increased after the correlated deployment.",
            evidence_ids=self._valid_ids(["metric-1", "log-1", "deploy-1"], evidence_ids),
        )
        root_cause = RootCause(
            category=category,
            title=self._root_cause_title(category, findings.outcome),
            explanation=TraceableText(
                text=self._root_cause_explanation(category, findings.outcome),
                evidence_ids=root_evidence_ids,
            ),
            evidence_ids=root_evidence_ids,
        )
        mitigation = TraceableText(
            text=self._mitigation(category, findings.outcome),
            evidence_ids=self._valid_ids(["change-1", "log-2", "deploy-2"], evidence_ids) or root_evidence_ids[:1],
        )
        prevention = TraceableText(
            text=self._prevention(category, findings.outcome),
            evidence_ids=self._valid_ids(["change-1", "metric-1", "log-2"], evidence_ids) or root_evidence_ids[:1],
        )

        self._validate_traceable_sections(
            sections=[summary, impact, root_cause.explanation, mitigation, prevention],
            evidence_ids=evidence_ids,
        )

        assumptions = [
            "Incident analysis is deterministic and based on the versioned synthetic checkout-latency@v1 fixture.",
            "Repository context is best-effort enrichment and is not treated as incident evidence.",
            "No LLM reasoning, real observability integration, or live production telemetry is used in M04.",
        ]
        if repository_unavailable:
            assumptions.append("Repository analysis was unavailable, so the RCA was generated without repository context.")
        elif not repository_analyzed:
            assumptions.append("No repository URL was provided, so repository context was omitted.")
        if findings.outcome == InvestigationOutcome.CONFLICTING_EVIDENCE:
            assumptions.append("Multiple root cause categories matched, so the RCA reports conflicting evidence.")
        if findings.outcome == InvestigationOutcome.INSUFFICIENT_EVIDENCE:
            assumptions.append("No root cause category met the minimum scenario-specific threshold.")

        components = self._repository_components(bundle)
        metadata: dict[str, int | str | bool | list[str]] = {
            "fixture_id": fixture.id,
            "fixture_version": fixture.version,
            "repository_analyzed": repository_analyzed,
            "repository_components_matched": components,
            "evidence_count": len(evidence),
            "analysis_duration_ms": analysis_duration_ms,
            "confidence_score": findings.confidence_score,
            "analysis_mode": "heuristic",
            "truncated": False,
        }

        return IncidentRCA(
            summary=summary,
            impact=impact,
            timeline=self._timeline(evidence),
            evidence=evidence,
            repository_context=bundle.repository_signals,
            suspected_root_cause=root_cause,
            mitigation=mitigation,
            prevention=prevention,
            assumptions=assumptions,
            confidence=confidence_label(findings.confidence_score),
            metadata=metadata,
        )

    def _ordered_evidence(self, bundle: IncidentEvidenceBundle) -> list[EvidenceItem]:
        return [
            *bundle.metrics,
            *bundle.logs,
            *bundle.deployment_events,
            *bundle.change_evidence,
        ]

    def _timeline(self, evidence: list[EvidenceItem]) -> list[TimelineEvent]:
        return [
            TimelineEvent(
                timestamp=item.timestamp,
                type=item.type,
                description=item.description,
                evidence_ids=[item.id],
            )
            for item in sorted(evidence, key=lambda item: (item.timestamp, item.id))
        ]

    def _root_evidence_ids(self, findings: IncidentFindings, evidence_ids: set[str]) -> list[str]:
        ordered = [
            *findings.matched_metrics,
            *findings.matched_logs,
            *findings.matched_deployments,
            *findings.matched_changes,
        ]
        return self._valid_ids(ordered, evidence_ids)

    @staticmethod
    def _valid_ids(ids: list[str], evidence_ids: set[str]) -> list[str]:
        result: list[str] = []
        for evidence_id in ids:
            if evidence_id in evidence_ids and evidence_id not in result:
                result.append(evidence_id)
        return result

    @staticmethod
    def _summary_text(category: str, outcome: str) -> str:
        if outcome == InvestigationOutcome.ROOT_CAUSE_IDENTIFIED and category == RootCauseCategory.CONNECTION_POOL_REGRESSION:
            return "Checkout latency spike is most consistent with a database connection pool regression introduced shortly before deployment."
        if outcome == InvestigationOutcome.CONFLICTING_EVIDENCE:
            return "The fixture contains evidence for multiple plausible root cause categories."
        return "The fixture does not contain enough aligned evidence to identify a single root cause."

    @staticmethod
    def _root_cause_title(category: str, outcome: str) -> str:
        if outcome != InvestigationOutcome.ROOT_CAUSE_IDENTIFIED:
            return "Root cause not uniquely identified"
        titles = {
            RootCauseCategory.CONNECTION_POOL_REGRESSION: "Checkout DB connection pool regression",
            RootCauseCategory.QUERY_PERFORMANCE: "Checkout query performance regression",
            RootCauseCategory.TIMEOUT_CONFIGURATION: "Checkout timeout configuration regression",
        }
        return titles.get(category, "Unknown root cause")

    @staticmethod
    def _root_cause_explanation(category: str, outcome: str) -> str:
        if outcome != InvestigationOutcome.ROOT_CAUSE_IDENTIFIED:
            return "The analyzer could not select exactly one root cause category from the available evidence."
        if category == RootCauseCategory.CONNECTION_POOL_REGRESSION:
            return (
                "Latency increased inside the deployment correlation window, checkout timeout logs appeared, "
                "connection pool wait logs were present, and related change evidence points to DB pool sizing."
            )
        if category == RootCauseCategory.QUERY_PERFORMANCE:
            return "Latency and log evidence align with a query-related backend change."
        if category == RootCauseCategory.TIMEOUT_CONFIGURATION:
            return "Timeout logs align with a timeout or configuration change."
        return "The evidence did not match a known deterministic root cause category."

    @staticmethod
    def _mitigation(category: str, outcome: str) -> str:
        if outcome != InvestigationOutcome.ROOT_CAUSE_IDENTIFIED:
            return "Pause rollout and collect more targeted evidence before applying a category-specific mitigation."
        if category == RootCauseCategory.CONNECTION_POOL_REGRESSION:
            return "Rollback or raise the checkout DB connection pool settings changed before deployment, then verify pool wait time and latency recover."
        if category == RootCauseCategory.QUERY_PERFORMANCE:
            return "Rollback the query-related change or disable the affected path, then compare query latency against baseline."
        if category == RootCauseCategory.TIMEOUT_CONFIGURATION:
            return "Rollback the timeout/configuration change and confirm checkout timeout errors stop increasing."
        return "Apply mitigation only after a root cause category is identified."

    @staticmethod
    def _prevention(category: str, outcome: str) -> str:
        if outcome != InvestigationOutcome.ROOT_CAUSE_IDENTIFIED:
            return "Add scenario-specific checks once more evidence identifies a single root cause category."
        if category == RootCauseCategory.CONNECTION_POOL_REGRESSION:
            return "Add connection-pool regression checks for checkout deployments, including pool wait time alerts and pre-release configuration review."
        if category == RootCauseCategory.QUERY_PERFORMANCE:
            return "Add query latency regression checks for checkout workflows before deployment."
        if category == RootCauseCategory.TIMEOUT_CONFIGURATION:
            return "Add timeout configuration review and deployment checks for checkout services."
        return "Add regression tests when a known root cause category is available."

    @staticmethod
    def _repository_components(bundle: IncidentEvidenceBundle) -> list[str]:
        components: list[str] = []
        for signal in bundle.repository_signals:
            if signal.component not in components:
                components.append(signal.component)
        return components

    @staticmethod
    def _validate_traceable_sections(sections: list[TraceableText], evidence_ids: set[str]) -> None:
        for section in sections:
            if not section.evidence_ids:
                raise ValueError("Traceable RCA sections must include at least one evidence ID.")
            if any(evidence_id not in evidence_ids for evidence_id in section.evidence_ids):
                raise ValueError("Traceable RCA sections must reference valid evidence IDs.")

