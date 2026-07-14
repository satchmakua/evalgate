# Example run — 3 models, 3 suites (2026-07-13)

Artifacts from a real run of every bundled suite against two local models and
one hosted model:

```
evalgate run --models ollama:llama3.1:8b ollama:qwen2.5:7b-instruct anthropic:claude-haiku-4-5
```

*(The captured artifacts predate the project's rename and carry the old `lmeval`
name internally; they are kept byte-for-byte as produced.)*

- [`summary.md`](summary.md) — the per-(suite, model) table with Wilson CIs,
  the per-tag breakdown, and the Failures section.
- [`dashboard.html`](dashboard.html) — the self-contained HTML dashboard
  (open it in a browser).
- [`transcripts.jsonl`](transcripts.jsonl) — one self-contained record per
  task: the exact input sent, the model output, and every grader verdict.

**What this run caught.** All three models failed `structured-output ::
action-object` the *same way*: each returned valid JSON but invented its own
container key (`details`, `details`, `parameters`) because the task's prompt
demanded schema-conformant JSON without ever stating the required shape
(`params`). A three-way identical failure is the signature of an
under-specified task, not a bad model — the suite was fixed to name the
expected keys, and all three models pass the corrected task (see
`baselines/default.json` for the post-fix snapshot). These artifacts are kept
as-is, failures included, because catching exactly this is what the harness is
for.

Total hosted spend for the run: about **$0.001** (six Claude Haiku calls; the
local models and the local LLM judge are free).
