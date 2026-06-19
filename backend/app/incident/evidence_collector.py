from __future__ import annotations

from app.analyzer.repository_analyzer import RepositoryAnalysis
from app.incident.models import EvidenceItem, IncidentEvidenceBundle, RepositorySignal, ScenarioFixture


class EvidenceCollector:
    def collect(self, fixture: ScenarioFixture, repository_analysis: RepositoryAnalysis | None) -> IncidentEvidenceBundle:
        repository_signals = self._repository_signals(repository_analysis)
        return IncidentEvidenceBundle(
            metrics=self._items(fixture, "metrics"),
            logs=self._items(fixture, "logs"),
            deployment_events=self._items(fixture, "deployment_events"),
            change_evidence=self._items(fixture, "change_evidence"),
            repository_signals=repository_signals,
        )

    def _items(self, fixture: ScenarioFixture, group: str) -> list[EvidenceItem]:
        items = [
            EvidenceItem(
                id=str(raw["id"]),
                type=str(raw["type"]),
                source=str(raw["source"]),
                timestamp=str(raw["timestamp"]),
                description=str(raw["description"]),
            )
            for raw in fixture.data[group]
        ]
        return sorted(items, key=lambda item: (item.timestamp, item.id))

    def _repository_signals(self, repository_analysis: RepositoryAnalysis | None) -> list[RepositorySignal]:
        if repository_analysis is None:
            return []

        signals: list[RepositorySignal] = []
        for component in repository_analysis.components:
            confidence = self._component_confidence(component.name)
            for path in component.evidence[:3]:
                signals.append(
                    RepositorySignal(
                        component=component.name,
                        path=path,
                        reason=self._component_reason(component.name),
                        confidence=confidence,
                    )
                )

        for symbol in repository_analysis.repository_index.symbols[:6]:
            if symbol.kind == "test_function":
                continue
            signals.append(
                RepositorySignal(
                    component="Static Code Intelligence",
                    path=symbol.path,
                    reason=f"Indexed {symbol.kind.replace('_', ' ')} {self._symbol_name(symbol)} may help localize repository context.",
                    confidence=0.62,
                )
            )

        return sorted(signals, key=lambda signal: (-signal.confidence, signal.path))

    @staticmethod
    def _component_confidence(component_name: str) -> float:
        if component_name == "API/Application Layer":
            return 0.9
        if component_name in {"Service Layer", "Database", "Persistence Layer"}:
            return 0.82
        if component_name == "Source Modules":
            return 0.74
        return 0.55

    @staticmethod
    def _component_reason(component_name: str) -> str:
        if component_name == "API/Application Layer":
            return "Backend API or application code is the most likely place to inspect checkout request handling."
        if component_name == "Service Layer":
            return "Service code commonly coordinates checkout workflows and downstream calls."
        if component_name in {"Database", "Persistence Layer"}:
            return "Database-facing code is relevant to connection pool and query latency investigations."
        if component_name == "Source Modules":
            return "Primary source modules provide code context for the incident workflow."
        return "Repository component may provide useful investigation context."

    @staticmethod
    def _symbol_name(symbol) -> str:
        return f"{symbol.container}.{symbol.name}" if symbol.container else symbol.name
