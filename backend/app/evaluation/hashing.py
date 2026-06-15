from __future__ import annotations

from typing import Any

from app.evaluation.json_utils import sha256_hex


def evaluation_result_hash(run: dict[str, Any]) -> str:
    return sha256_hex(evaluation_result_hash_payload(run))


def evaluation_result_hash_payload(run: dict[str, Any]) -> dict[str, Any]:
    return {
        "suite_id": run["suite_id"],
        "suite_version": run["suite_version"],
        "fixture_versions": run["fixture_versions"],
        "tasks": run["tasks"],
        "summary": run["summary"],
    }
