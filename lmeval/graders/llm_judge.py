"""LLM-as-judge grader: a second model scores the output against a rubric.

This captures subjective qualities (faithfulness, tone, in-character-ness)
that exact-match graders cannot. It is non-deterministic, so it is excluded
from CI gating by default (see --deterministic-only).
"""

import json
import re

from ..types import GradeResult


def grade_llm_judge(output, spec, judge_fn=None, **kwargs):
    if judge_fn is None:
        return GradeResult("llm_judge", passed=None, detail="no judge provider configured")
    prompt = (
        "You are grading an AI response. Grade strictly and fairly.\n"
        f"RUBRIC:\n{spec['rubric']}\n\n"
        f"RESPONSE TO GRADE:\n{output}\n\n"
        'Reply with ONLY JSON: {"score": <integer 1-5>, "rationale": "<one sentence>"}.'
    )
    raw = judge_fn(prompt)
    parsed = _safe_json(raw)
    if not parsed or "score" not in parsed:
        return GradeResult("llm_judge", passed=None, score=None,
                           detail=f"unparseable judge output: {raw[:160]!r}")
    score = float(parsed["score"])
    threshold = spec.get("pass_threshold", 4)
    return GradeResult("llm_judge", passed=score >= threshold, score=score,
                       detail=parsed.get("rationale", ""))


def _safe_json(text):
    match = re.search(r"\{.*\}", text, re.DOTALL)
    if not match:
        return None
    try:
        return json.loads(match.group(0))
    except Exception:
        return None
