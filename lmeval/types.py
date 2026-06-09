"""Core data structures shared across the harness."""

from dataclasses import dataclass, field
from typing import Any, Optional


@dataclass
class Completion:
    """One model response plus the bookkeeping needed for cost/latency tracking."""
    text: str
    model: str
    provider: str
    prompt_tokens: int = 0
    completion_tokens: int = 0
    latency_s: float = 0.0


@dataclass
class GradeResult:
    """The verdict from a single grader.

    passed: True/False for graders that decide; None for ones that can't
            (e.g. an unparseable judge response).
    score:  raw grader score where applicable (e.g. an LLM judge's 1-5).
    """
    grader: str
    passed: Optional[bool] = None
    score: Optional[float] = None
    detail: str = ""


@dataclass
class Task:
    """A single eval item: a prompt and the graders that judge its output."""
    id: str
    prompt: str
    system: Optional[str] = None
    graders: list = field(default_factory=list)
    expected: Any = None


@dataclass
class Suite:
    """A named group of related tasks."""
    name: str
    description: str = ""
    tasks: list = field(default_factory=list)
    models: Optional[list] = None


@dataclass
class TaskResult:
    """The outcome of running one task against one model."""
    suite: str
    task_id: str
    model: str
    output: str = ""
    prompt_tokens: int = 0
    completion_tokens: int = 0
    cost_usd: float = 0.0
    latency_s: float = 0.0
    grades: list = field(default_factory=list)
    error: Optional[str] = None

    @property
    def verdict(self) -> Optional[bool]:
        """Overall pass/fail: True if every deciding grader passed.

        Returns None when no grader produced a definite verdict (e.g. a task
        graded only by manual review), and False on a hard error.
        """
        if self.error:
            return False
        decided = [g.passed for g in self.grades if g.passed is not None]
        if not decided:
            return None
        return all(decided)
