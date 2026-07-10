from __future__ import annotations

import json
import re
from typing import Any

from pydantic import BaseModel


class JSONRepairResult(BaseModel):
    raw_response: str
    repair_attempted: bool
    repair_success: bool
    validated_json: Any = None
    validation_errors: list[str] = []


def _extract_json_like(text: str) -> str | None:
    fenced = re.search(r"```(?:json)?\s*(.*?)```", text, flags=re.DOTALL | re.IGNORECASE)
    if fenced:
        return fenced.group(1).strip()
    start_candidates = [i for i in [text.find("{"), text.find("[")] if i >= 0]
    if not start_candidates:
        return None
    start = min(start_candidates)
    end = max(text.rfind("}"), text.rfind("]"))
    if end <= start:
        return None
    return text[start : end + 1]


def repair_json(text: str, empty_structure: Any | None = None) -> JSONRepairResult:
    errors: list[str] = []
    try:
        return JSONRepairResult(
            raw_response=text,
            repair_attempted=False,
            repair_success=True,
            validated_json=json.loads(text),
        )
    except Exception as exc:
        errors.append(str(exc))

    candidate = _extract_json_like(text or "")
    if candidate:
        repaired = re.sub(r",(\s*[}\]])", r"\1", candidate)
        repaired = repaired.replace("\u201c", '"').replace("\u201d", '"')
        try:
            return JSONRepairResult(
                raw_response=text,
                repair_attempted=True,
                repair_success=True,
                validated_json=json.loads(repaired),
                validation_errors=errors,
            )
        except Exception as exc:
            errors.append(str(exc))

    return JSONRepairResult(
        raw_response=text,
        repair_attempted=True,
        repair_success=False,
        validated_json=empty_structure if empty_structure is not None else {},
        validation_errors=errors,
    )
