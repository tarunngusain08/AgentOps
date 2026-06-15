import pytest

from app.incident.fixtures import FixtureValidationError, IncidentFixtureLoader, ScenarioNotFoundError


def test_fixture_loader_returns_checkout_latency_v1():
    fixture = IncidentFixtureLoader().load("checkout-latency")

    assert fixture.id == "checkout-latency"
    assert fixture.version == "v1"
    assert [item["id"] for item in fixture.data["metrics"]] == ["metric-1", "metric-2"]
    assert [item["id"] for item in fixture.data["logs"]] == ["log-1", "log-2"]


def test_fixture_loader_unknown_scenario():
    with pytest.raises(ScenarioNotFoundError) as exc:
        IncidentFixtureLoader().load("checkout-latency-v2")

    assert exc.value.scenario_id == "checkout-latency-v2"


def test_fixture_loader_malformed_fixture():
    loader = IncidentFixtureLoader(
        fixtures={
            "checkout-latency": {
                "id": "checkout-latency",
                "version": "v1",
                "data": {"metrics": []},
            }
        }
    )

    with pytest.raises(FixtureValidationError) as exc:
        loader.load("checkout-latency")

    assert exc.value.fixture_name == "checkout-latency@v1"

