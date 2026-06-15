from __future__ import annotations

from datetime import datetime, timedelta
from enum import Enum

from app.incident.models import (
    EvidenceItem,
    IncidentEvidenceBundle,
    IncidentFindings,
    InvestigationOutcome,
    RootCauseCategory,
)

DEPLOYMENT_WINDOW = timedelta(minutes=10)


class CorrelationLevel(str, Enum):
    NONE = "none"
    PARTIAL = "partial"
    FULL = "full"


class IncidentAnalyzer:
    def analyze(self, bundle: IncidentEvidenceBundle) -> IncidentFindings:
        metric_level = self.metric_correlation(bundle)
        log_level = self.log_correlation(bundle)
        deployment_level = self.deployment_correlation(bundle)
        change_level = self.change_correlation(bundle)

        matched_categories = self._matched_root_cause_categories(
            metric_level=metric_level,
            log_level=log_level,
            deployment_level=deployment_level,
            change_level=change_level,
            changes=bundle.change_evidence,
        )
        outcome = self._outcome(matched_categories)
        root_cause_category = matched_categories[0] if outcome == InvestigationOutcome.ROOT_CAUSE_IDENTIFIED else RootCauseCategory.UNKNOWN
        confidence_score = (
            self._metric_score(metric_level)
            + self._log_score(log_level)
            + self._deployment_score(deployment_level)
            + self._change_score(change_level)
        )

        return IncidentFindings(
            matched_metrics=[item.id for item in bundle.metrics if self._contains_any(item.description, ["latency", "p95", "spike", "increased"])],
            matched_logs=[item.id for item in bundle.logs if self._contains_any(item.description, ["timeout", "checkout", "database", "db", "connection pool", "pool wait"])],
            matched_changes=[item.id for item in bundle.change_evidence if self._is_relevant_change(item)],
            matched_deployments=[item.id for item in bundle.deployment_events if "deployment" in item.description.lower() or "rollback" in item.description.lower()],
            root_cause_category=root_cause_category,
            outcome=outcome,
            confidence_score=confidence_score,
        )

    def metric_correlation(self, bundle: IncidentEvidenceBundle) -> CorrelationLevel:
        spike_times = [
            self._parse_time(item.timestamp)
            for item in bundle.metrics
            if self._contains_any(item.description, ["latency", "p95", "spike", "increased"])
        ]
        if not spike_times:
            return CorrelationLevel.NONE

        deployment_times = [self._parse_time(item.timestamp) for item in bundle.deployment_events if "deployment" in item.description.lower()]
        if any(self._inside_deployment_window(spike_time, deployment_times) for spike_time in spike_times):
            return CorrelationLevel.FULL
        return CorrelationLevel.PARTIAL

    def log_correlation(self, bundle: IncidentEvidenceBundle) -> CorrelationLevel:
        has_timeout_or_checkout = any(self._contains_any(item.description, ["timeout", "checkout"]) for item in bundle.logs)
        has_pool_or_db_wait = any(self._contains_any(item.description, ["connection pool", "pool wait", "database", "db wait"]) for item in bundle.logs)

        if has_timeout_or_checkout and has_pool_or_db_wait:
            return CorrelationLevel.FULL
        if has_timeout_or_checkout:
            return CorrelationLevel.PARTIAL
        return CorrelationLevel.NONE

    def deployment_correlation(self, bundle: IncidentEvidenceBundle) -> CorrelationLevel:
        deployment_times = [self._parse_time(item.timestamp) for item in bundle.deployment_events if "deployment" in item.description.lower()]
        if not deployment_times:
            return CorrelationLevel.NONE

        spike_times = [
            self._parse_time(item.timestamp)
            for item in bundle.metrics
            if self._contains_any(item.description, ["latency", "p95", "spike", "increased"])
        ]
        if any(self._inside_deployment_window(spike_time, deployment_times) for spike_time in spike_times):
            return CorrelationLevel.FULL
        return CorrelationLevel.PARTIAL

    def change_correlation(self, bundle: IncidentEvidenceBundle) -> CorrelationLevel:
        relevant_changes = [item for item in bundle.change_evidence if self._is_relevant_change(item)]
        if not relevant_changes:
            return CorrelationLevel.NONE
        if any(self._has_root_cause_keyword(item) for item in relevant_changes):
            return CorrelationLevel.FULL
        return CorrelationLevel.PARTIAL

    def _matched_root_cause_categories(
        self,
        metric_level: CorrelationLevel,
        log_level: CorrelationLevel,
        deployment_level: CorrelationLevel,
        change_level: CorrelationLevel,
        changes: list[EvidenceItem],
    ) -> list[str]:
        matches: list[str] = []
        if (
            metric_level == CorrelationLevel.FULL
            and log_level == CorrelationLevel.FULL
            and deployment_level == CorrelationLevel.FULL
            and change_level == CorrelationLevel.FULL
            and any(self._contains_any(item.description, ["connection pool", "pool size"]) for item in changes)
        ):
            matches.append(RootCauseCategory.CONNECTION_POOL_REGRESSION)

        if (
            metric_level == CorrelationLevel.FULL
            and log_level in {CorrelationLevel.PARTIAL, CorrelationLevel.FULL}
            and any(self._contains_any(item.description, ["query"]) for item in changes)
        ):
            matches.append(RootCauseCategory.QUERY_PERFORMANCE)

        if (
            log_level in {CorrelationLevel.PARTIAL, CorrelationLevel.FULL}
            and any("timeout" in item.description.lower() for item in changes)
        ):
            matches.append(RootCauseCategory.TIMEOUT_CONFIGURATION)

        return matches

    @staticmethod
    def _outcome(matched_categories: list[str]) -> str:
        if len(matched_categories) == 1:
            return InvestigationOutcome.ROOT_CAUSE_IDENTIFIED
        if len(matched_categories) > 1:
            return InvestigationOutcome.CONFLICTING_EVIDENCE
        return InvestigationOutcome.INSUFFICIENT_EVIDENCE

    @staticmethod
    def _metric_score(level: CorrelationLevel) -> int:
        return {CorrelationLevel.NONE: 0, CorrelationLevel.PARTIAL: 15, CorrelationLevel.FULL: 30}[level]

    @staticmethod
    def _log_score(level: CorrelationLevel) -> int:
        return {CorrelationLevel.NONE: 0, CorrelationLevel.PARTIAL: 15, CorrelationLevel.FULL: 30}[level]

    @staticmethod
    def _deployment_score(level: CorrelationLevel) -> int:
        return {CorrelationLevel.NONE: 0, CorrelationLevel.PARTIAL: 10, CorrelationLevel.FULL: 20}[level]

    @staticmethod
    def _change_score(level: CorrelationLevel) -> int:
        return {CorrelationLevel.NONE: 0, CorrelationLevel.PARTIAL: 10, CorrelationLevel.FULL: 20}[level]

    @staticmethod
    def _contains_any(text: str, needles: list[str]) -> bool:
        lowered = text.lower()
        return any(needle in lowered for needle in needles)

    def _is_relevant_change(self, item: EvidenceItem) -> bool:
        return self._contains_any(item.description, ["checkout", "backend", "config", "configuration"])

    def _has_root_cause_keyword(self, item: EvidenceItem) -> bool:
        return self._contains_any(item.description, ["connection pool", "timeout", "query", "db", "pool size"])

    @staticmethod
    def _parse_time(value: str) -> datetime:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))

    @staticmethod
    def _inside_deployment_window(event_time: datetime, deployment_times: list[datetime]) -> bool:
        return any(deployment_time <= event_time <= deployment_time + DEPLOYMENT_WINDOW for deployment_time in deployment_times)


def confidence_label(confidence_score: int) -> str:
    if confidence_score >= 80:
        return "High"
    if confidence_score >= 50:
        return "Medium"
    return "Low"
