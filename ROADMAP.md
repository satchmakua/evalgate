# Roadmap

Planned work for evalgate, roughly in priority order, with the known
limitations that motivate it.

## Known limitations

- **Partial `seed` support.** Only the OpenAI adapter forwards `seed`, so
  cross-provider reproducibility is best-effort.
- **Judge token counts aren't broken out.** Judge calls are priced into
  `judge_cost_usd`, but their tokens aren't added to the token columns (those
  stay the task model's).
- **Bedrock signing isn't exercised against live AWS.** The SigV4 signer is
  verified against two official AWS test vectors (get-vanilla + get-utf8) and
  the request shape is stub-tested, but there are no AWS credentials available
  here to run a real call end to end.
- **In-run cache dedup is best-effort under concurrency.** With `--cache` and
  `--concurrency > 1`, two identical calls launched at the same instant can both
  run; results stay correct but the cost dedup isn't exact. Exact when
  sequential. A per-key lock/future would make it exact.

## Near term

- _(done 2026-07-14)_ Persist the completion cache to disk (`--cache-dir`) so
  unchanged tasks are skipped across runs.

## Medium term

- Weighted scoring (per-suite or per-tag weights) in the gate.
- A scheduled (non-gating) CI job that runs the judge suites on a stronger judge.

---

## Review-driven hardening — positioning, taste, and proof (added 2026-06-28)

> Added after an external code review (captured in `../ai-docs/project_eval/`). This is
> the most *finished and runnable* project of the family — its gap is **category** (a
> well-built instance of a known tool), not completeness. The landscape moved (promptfoo
> is now part of OpenAI; Inspect AI is the open Python standard; Braintrust owns SaaS
> tracing), and the name collides with EleutherAI's `lm-evaluation-harness`. These items
> raise it from "a solid harness" to "this person understands evaluation."
>
> **Definition of Done — the "Sparkle Bar":** a real captured artifact at the top of the
> README · a flagship demo in one screen · stress-tested core · honest numbers with CIs ·
> cold-clone reproducible (`make demo` + CI) · polished surface · one positioning paragraph.

**Hardening items:**
- [x] **H1 — Position + rename.** Done 2026-07-13: README opens with a "why this
  and not promptfoo / Inspect AI / Braintrust" section plus an EleutherAI
  disambiguation note; package, CLI, and config renamed **lmeval → evalgate**
  (105 tests green under the new name). *Remaining:* rename the GitHub repo
  itself (`llm-eval-harness` → `evalgate`) — owner action.
- [x] **H2 — Show eval *taste*: ship hard suites.** Done 2026-07-13. Shipped
  `faithfulness` (abstention + counterfactual grounding), `tool-use` (selection
  + arg-grounding via `json_schema`, decline/clarify by judge), and `red-team`
  (refuse-harmful **and** don't-over-refuse, both axes tagged). All three ran
  against 3 models and **discriminated** them (e.g. tool-use: Claude 0.75 vs
  local 0.5). The run also surfaced a real methodology finding — the local 8B
  judge mis-graded several nuanced cases — which motivated a swappable
  **`--judge-model`** override (added + tested) and a Claude-judged reference
  run. *Accept met:* suites ship and run.
- [x] **H3 — Upgrade the judge.** Done 2026-07-14. Added a `pairwise` grader:
  compares the output against a fixed `reference` and runs BOTH orderings, so a
  position-biased judge collapses to a tie instead of a spurious win (`require:
  win|tie`). Ships with a `preference` demo suite (ran live) and 5 unit tests
  (incl. the position-bias→tie case). CI still gates only on deterministic
  graders because pairwise, like `llm_judge`, is non-reproducible — documented in
  the grader reference and the grader docstring. *Accept met.*
- [x] **H4 — The real comparison artifact.** Done 2026-07-13: all 3 suites ×
  3 models (llama3.1:8b, qwen2.5:7b-instruct, claude-haiku-4-5 live), ~$0.001
  hosted spend. README now leads with the real table + what the run caught (an
  under-specified task all three models failed identically — since fixed);
  artifacts committed in `docs/example-run/`, post-fix snapshot in
  `baselines/default.json`. *(Screenshot swapped for the committed HTML
  dashboard + inline table — greppable and diffable beat a PNG.)*
- [x] **H5 — Per-tag / category breakdown** — shipped: `tags` on tasks (task- and
  suite-level, merged), pass rate + Wilson CI per (tag, model) in the Markdown
  report and HTML dashboard.

*(The "Known limitations" above — partial `seed` forwarding, judge token columns, no live-Bedrock run — remain valid and tracked; folding a live-AWS Bedrock smoke test into CI would close the last one.)*
