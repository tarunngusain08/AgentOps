from __future__ import annotations

import re
from pathlib import Path

from app.evaluation.errors import EvaluationIdentifierInvalidError

SAFE_IDENTIFIER_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_-]{0,127}$")


def validate_evaluation_identifier(value: str, field_name: str) -> str:
    if not SAFE_IDENTIFIER_RE.fullmatch(value):
        raise EvaluationIdentifierInvalidError(f"Invalid evaluation identifier: {field_name}")
    return value


def validate_contained_path(base: Path, path: Path) -> Path:
    resolved_base = base.resolve(strict=False)
    resolved_path = path.resolve(strict=False)
    if not resolved_path.is_relative_to(resolved_base):
        raise EvaluationIdentifierInvalidError("Evaluation artifact path escaped its storage root.")
    return path
