from gatecheck.graders import is_deterministic, run_grader


def test_contains_any_ignorecase():
    r = run_grader({"type": "contains", "any_of": ["positive"], "ignorecase": True}, "Positive.")
    assert r.passed is True


def test_contains_all_of_fails_when_missing():
    r = run_grader({"type": "contains", "all_of": ["alpha", "omega"]}, "only alpha here")
    assert r.passed is False


def test_regex_match():
    r = run_grader({"type": "regex", "pattern": r"\d{3}-\d{4}"}, "call 555-0100 today")
    assert r.passed is True


def test_exact_mismatch():
    r = run_grader({"type": "exact", "value": "yes"}, "no")
    assert r.passed is False


def test_json_schema_valid():
    spec = {"type": "json_schema",
            "schema": {"type": "object", "required": ["x"],
                       "properties": {"x": {"type": "number"}}}}
    assert run_grader(spec, '{"x": 5}').passed is True


def test_json_schema_invalid_json():
    spec = {"type": "json_schema", "schema": {"type": "object", "required": ["x"]}}
    assert run_grader(spec, "not json at all").passed is False


def test_json_extracted_from_fence():
    spec = {"type": "json_schema",
            "schema": {"type": "object", "required": ["a"]}}
    assert run_grader(spec, "```json\n{\"a\": 1}\n```").passed is True


def test_llm_judge_parses_and_passes():
    r = run_grader(
        {"type": "llm_judge", "rubric": "x", "pass_threshold": 4},
        "anything",
        judge_fn=lambda p: '{"score": 5, "rationale": "good"}',
    )
    assert r.passed is True and r.score == 5.0


def test_llm_judge_unparseable_is_none():
    r = run_grader({"type": "llm_judge", "rubric": "x"}, "out",
                   judge_fn=lambda p: "I think it's pretty good!")
    assert r.passed is None


def test_llm_judge_ensemble_averages_scores():
    r = run_grader(
        {"type": "llm_judge", "rubric": "x", "pass_threshold": 4}, "out",
        judge_fns=[lambda p: '{"score": 5, "rationale": "a"}',
                   lambda p: '{"score": 3, "rationale": "b"}'],
    )
    assert r.score == 4.0      # mean of 5 and 3
    assert r.passed is True    # 4.0 >= 4


def test_llm_judge_ensemble_below_threshold_fails():
    r = run_grader(
        {"type": "llm_judge", "rubric": "x", "pass_threshold": 4}, "out",
        judge_fns=[lambda p: '{"score": 5}', lambda p: '{"score": 2}'],
    )
    assert r.score == 3.5
    assert r.passed is False


def test_llm_judge_ensemble_skips_unparseable_members():
    r = run_grader(
        {"type": "llm_judge", "rubric": "x", "pass_threshold": 4}, "out",
        judge_fns=[lambda p: "garbage", lambda p: '{"score": 5}'],
    )
    assert r.score == 5.0      # only the parseable judge counts
    assert r.passed is True


def test_llm_judge_skips_non_numeric_score():
    # a judge returning valid JSON but a non-numeric score must be skipped, not crash
    r = run_grader(
        {"type": "llm_judge", "rubric": "x", "pass_threshold": 4}, "out",
        judge_fn=lambda p: '{"score": "N/A", "rationale": "bad"}',
    )
    assert r.passed is None


def test_llm_judge_tolerates_trailing_braces():
    # a valid JSON object followed by prose containing braces still parses
    r = run_grader(
        {"type": "llm_judge", "rubric": "x", "pass_threshold": 4}, "out",
        judge_fn=lambda p: '{"score": 5, "rationale": "ok"}. Note: use {curly} braces.',
    )
    assert r.score == 5.0 and r.passed is True


def _always_prefers(winner, loser):
    """A judge that prefers `winner` over `loser` regardless of A/B position."""
    def judge(prompt):
        return '{"winner": "A"}' if prompt.index(winner) < prompt.index(loser) else '{"winner": "B"}'
    return judge


def test_pairwise_prefers_output_across_swap():
    r = run_grader({"type": "pairwise", "reference": "REF", "require": "win"},
                   "OUT", judge_fn=_always_prefers("OUT", "REF"))
    assert r.passed is True
    assert "output" in r.detail


def test_pairwise_position_bias_collapses_to_tie():
    # a judge that ALWAYS picks position A (pure position bias) must not yield a win
    r = run_grader({"type": "pairwise", "reference": "REF", "require": "win"},
                   "OUT", judge_fn=lambda p: '{"winner": "A"}')
    assert r.passed is False        # the swap caught the bias -> tie, not a spurious win
    assert "tie" in r.detail


def test_pairwise_reference_preferred_fails_default_bar():
    r = run_grader({"type": "pairwise", "reference": "REF"},  # default require=tie
                   "OUT", judge_fn=_always_prefers("REF", "OUT"))
    assert r.passed is False        # output judged worse than the reference


def test_pairwise_tie_passes_default_bar():
    r = run_grader({"type": "pairwise", "reference": "REF"}, "OUT",
                   judge_fn=lambda p: '{"winner": "tie"}')
    assert r.passed is True         # not worse than the reference -> meets the default bar
    assert "tie" in r.detail


def test_pairwise_no_judge_is_none():
    assert run_grader({"type": "pairwise", "reference": "x"}, "y").passed is None


def test_is_deterministic():
    assert is_deterministic({"type": "contains"}) is True
    assert is_deterministic({"type": "llm_judge"}) is False
