"""Deterministic graders: no model in the loop, so verdicts are reproducible."""

import json
import re

from jsonschema import ValidationError, validate

from ..types import GradeResult


def grade_exact(output, spec, **kwargs):
    target = spec["value"]
    out = output.strip()
    ok = (out.lower() == target.lower()) if spec.get("ignorecase") else (out == target)
    return GradeResult("exact", passed=ok, detail=f"== {target!r}")


def grade_contains(output, spec, **kwargs):
    """Pass if expected text appears. `any_of` (default) or `all_of`."""
    needles = spec.get("any_of") or spec.get("all_of") or spec.get("value") or []
    if isinstance(needles, str):
        needles = [needles]
    ic = spec.get("ignorecase", False)
    hay = output.lower() if ic else output
    found = [n for n in needles if (n.lower() if ic else n) in hay]
    require_all = "all_of" in spec
    ok = (len(found) == len(needles)) if require_all else (len(found) > 0)
    return GradeResult("contains", passed=ok, detail=f"matched {found} of {needles}")


def grade_regex(output, spec, **kwargs):
    flags = re.IGNORECASE if spec.get("ignorecase") else 0
    match = re.search(spec["pattern"], output, flags)
    return GradeResult("regex", passed=bool(match),
                       detail=f"/{spec['pattern']}/ -> {bool(match)}")


def grade_json_schema(output, spec, **kwargs):
    """Pass if output is valid JSON (optionally conforming to a JSON schema)."""
    text = _extract_json(output)
    try:
        obj = json.loads(text)
    except Exception as exc:
        return GradeResult("json_schema", passed=False, detail=f"invalid JSON: {exc}")
    schema = spec.get("schema")
    if schema:
        try:
            validate(obj, schema)
        except ValidationError as exc:
            return GradeResult("json_schema", passed=False, detail=f"schema: {exc.message}")
    return GradeResult("json_schema", passed=True, detail="valid")


def _extract_json(text):
    fenced = re.search(r"```(?:json)?\s*(.*?)```", text, re.DOTALL)
    if fenced:
        return fenced.group(1).strip()
    start, end = text.find("{"), text.rfind("}")
    if start != -1 and end != -1 and end > start:
        return text[start:end + 1]
    return text.strip()


DETERMINISTIC = {
    "exact": grade_exact,
    "contains": grade_contains,
    "regex": grade_regex,
    "json_schema": grade_json_schema,
}
