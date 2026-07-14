"""Grader registry and dispatch."""

from ..types import GradeResult
from .deterministic import DETERMINISTIC
from .llm_judge import grade_llm_judge
from .pairwise import grade_pairwise

_GRADERS = dict(DETERMINISTIC)
_GRADERS["llm_judge"] = grade_llm_judge
_GRADERS["pairwise"] = grade_pairwise

# judge-backed graders are NOT in DETERMINISTIC -> skipped under --deterministic-only
DETERMINISTIC_TYPES = set(DETERMINISTIC)
JUDGE_TYPES = {"llm_judge", "pairwise"}


def run_grader(spec, output, judge_fn=None, judge_fns=None, task_input=None):
    fn = _GRADERS.get(spec.get("type"))
    if fn is None:
        return GradeResult(spec.get("type", "?"), passed=None, detail="unknown grader")
    return fn(output, spec, judge_fn=judge_fn, judge_fns=judge_fns, task_input=task_input)


def is_deterministic(spec):
    return spec.get("type") in DETERMINISTIC_TYPES
