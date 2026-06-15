from __future__ import annotations

from typing import Any

from app.evaluation.models import ExpectedFact

SUPPORTED_MATCH_TYPES = {"contains", "equals", "list_contains", "exists"}


class FactMatcher:
    def match(self, fact: ExpectedFact, actual: Any) -> bool:
        if fact.match_type == "contains":
            return _normalize(fact.value) in _normalize(str(actual))
        if fact.match_type == "equals":
            return _normalize(str(actual)) == _normalize(fact.value)
        if fact.match_type == "list_contains":
            if not isinstance(actual, list):
                return False
            normalized = {_normalize(str(item)) for item in actual}
            return _normalize(fact.value) in normalized
        if fact.match_type == "exists":
            return actual is not None and str(actual).strip() != ""
        return False


def _normalize(value: str) -> str:
    return " ".join(value.strip().casefold().split())

