"""Pairwise / preference judging with a position-swap to control order bias.

Instead of scoring one answer 1-5, this asks a judge which of two answers is
better: the model's `output` vs. a fixed `reference` answer from the spec. LLM
judges have a well-known position bias -- they favour whichever answer they see
first -- so every comparison is run BOTH ways (output as A, then output as B),
and a preference only counts if it survives the swap. A judge that flips when
the answers swap positions collapses to a tie, not a spurious win.

Non-deterministic (a model is in the loop), so -- like `llm_judge` -- it is
excluded from CI gating by default (`--deterministic-only`). It compares against
a fixed reference answer; head-to-head model-vs-model (arena-style) comparison
would need a cross-model pass and isn't supported here.
"""

from collections import Counter

from ..types import GradeResult
from .llm_judge import _safe_json


def grade_pairwise(output, spec, judge_fn=None, judge_fns=None, task_input=None, **kwargs):
    """Pass if `output` is judged at least as good as `spec['reference']`.

    `require`: "tie" (default) passes unless the output is judged *worse* than the
    reference; "win" requires the output to be strictly preferred. With multiple
    `judge_models`, each judge does the swap and their verdicts are majority-voted.
    """
    fns = list(judge_fns) if judge_fns else ([judge_fn] if judge_fn else [])
    if not fns:
        return GradeResult("pairwise", passed=None, detail="no judge provider configured")
    reference = spec.get("reference", "")
    criteria = spec.get("criteria", "which answer is more correct, complete, and helpful")
    context = f"TASK:\n{task_input}\n\n" if task_input else ""

    def prompt_for(a, b):
        return (
            "Compare two answers to the same task. Judge which one better meets this "
            f"criterion: {criteria}.\n\n{context}"
            f"ANSWER A:\n{a}\n\nANSWER B:\n{b}\n\n"
            'Reply with ONLY JSON: {"winner": "A" | "B" | "tie", "rationale": "<one sentence>"}.'
        )

    def verdict_from(fn):
        # round 1: output in position A; round 2: swap -> output in position B
        r1 = _winner(fn(prompt_for(output, reference)))
        r2 = _winner(fn(prompt_for(reference, output)))
        chose1 = {"A": "output", "B": "reference", "tie": "tie", None: None}[r1]
        chose2 = {"A": "reference", "B": "output", "tie": "tie", None: None}[r2]
        if chose1 == "output" and chose2 == "output":
            return "output"
        if chose1 == "reference" and chose2 == "reference":
            return "reference"
        return "tie"  # a flip across the swap (position bias) or genuine parity

    verdicts = [verdict_from(fn) for fn in fns]
    agg = _majority(verdicts)
    require = spec.get("require", "tie")  # "win" = strictly preferred; "tie" = not worse
    passed = (agg == "output") if require == "win" else (agg != "reference")
    detail = f"{agg} vs reference (per-judge {verdicts}, require={require})"
    return GradeResult("pairwise", passed=passed, detail=detail)


def _winner(text):
    """Parse a judge reply into "A" / "B" / "tie" / None (unparseable)."""
    parsed = _safe_json(text)
    if not parsed:
        return None
    w = str(parsed.get("winner", "")).strip().lower()
    if w.startswith("a"):
        return "A"
    if w.startswith("b"):
        return "B"
    if "tie" in w or "equal" in w:
        return "tie"
    return None


def _majority(verdicts):
    votes = [v for v in verdicts if v]
    if not votes:
        return "tie"
    counts = Counter(votes)
    top, n = counts.most_common(1)[0]
    if list(counts.values()).count(n) > 1:  # no strict plurality -> tie
        return "tie"
    return top
