from __future__ import annotations

from app.incident.models import ScenarioFixture


class ScenarioNotFoundError(Exception):
    def __init__(self, scenario_id: str):
        super().__init__(scenario_id)
        self.scenario_id = scenario_id


class FixtureValidationError(Exception):
    def __init__(self, fixture_name: str):
        super().__init__(fixture_name)
        self.fixture_name = fixture_name


CHECKOUT_LATENCY_FIXTURE = {
    "id": "checkout-latency",
    "version": "v1",
    "data": {
        "metrics": [
            {
                "id": "metric-1",
                "type": "metric",
                "source": "checkout-latency-fixture",
                "timestamp": "2026-06-10T10:03:00+00:00",
                "description": "Checkout p95 latency increased from 350ms to 2400ms within five minutes of deployment.",
            },
            {
                "id": "metric-2",
                "type": "metric",
                "source": "checkout-latency-fixture",
                "timestamp": "2026-06-10T10:04:00+00:00",
                "description": "Checkout request throughput stayed stable while latency increased.",
            },
        ],
        "logs": [
            {
                "id": "log-1",
                "type": "log",
                "source": "checkout-latency-fixture",
                "timestamp": "2026-06-10T10:05:00+00:00",
                "description": "Checkout API emitted timeout errors waiting for database responses.",
            },
            {
                "id": "log-2",
                "type": "log",
                "source": "checkout-latency-fixture",
                "timestamp": "2026-06-10T10:07:00+00:00",
                "description": "Checkout service reported database connection pool wait time above threshold.",
            },
        ],
        "deployment_events": [
            {
                "id": "deploy-1",
                "type": "deployment",
                "source": "checkout-latency-fixture",
                "timestamp": "2026-06-10T09:58:00+00:00",
                "description": "checkout-service deployment completed for release 2026.06.10.1.",
            },
            {
                "id": "deploy-2",
                "type": "deployment",
                "source": "checkout-latency-fixture",
                "timestamp": "2026-06-10T10:10:00+00:00",
                "description": "Rollback began after latency and timeout errors were confirmed.",
            },
        ],
        "change_evidence": [
            {
                "id": "change-1",
                "type": "change",
                "source": "checkout-latency-fixture",
                "timestamp": "2026-06-10T09:52:00+00:00",
                "description": "Related change reduced checkout DB connection pool size in backend configuration.",
            },
            {
                "id": "change-2",
                "type": "change",
                "source": "checkout-latency-fixture",
                "timestamp": "2026-06-10T09:54:00+00:00",
                "description": "Change touched checkout backend request handling around database pool acquisition.",
            },
        ],
    },
}


class IncidentFixtureLoader:
    def __init__(self, fixtures: dict[str, dict] | None = None):
        self.fixtures = fixtures or {"checkout-latency": CHECKOUT_LATENCY_FIXTURE}

    def load(self, scenario_id: str) -> ScenarioFixture:
        if scenario_id not in self.fixtures:
            raise ScenarioNotFoundError(scenario_id)

        raw_fixture = self.fixtures[scenario_id]
        fixture_name = f"{raw_fixture.get('id', scenario_id)}@{raw_fixture.get('version', 'unknown')}"
        if not self._is_valid(raw_fixture):
            raise FixtureValidationError(fixture_name)

        return ScenarioFixture(
            id=str(raw_fixture["id"]),
            version=str(raw_fixture["version"]),
            data=raw_fixture["data"],
        )

    def _is_valid(self, fixture: dict) -> bool:
        if not fixture.get("id") or not fixture.get("version") or not isinstance(fixture.get("data"), dict):
            return False

        data = fixture["data"]
        required_groups = ["metrics", "logs", "deployment_events", "change_evidence"]
        evidence_ids: set[str] = set()

        for group in required_groups:
            items = data.get(group)
            if not isinstance(items, list):
                return False
            for item in items:
                if not self._is_valid_evidence_item(item):
                    return False
                item_id = str(item["id"])
                if item_id in evidence_ids:
                    return False
                evidence_ids.add(item_id)

        return bool(evidence_ids)

    @staticmethod
    def _is_valid_evidence_item(item: object) -> bool:
        if not isinstance(item, dict):
            return False
        return all(isinstance(item.get(key), str) and item.get(key) for key in ["id", "type", "source", "timestamp", "description"])
