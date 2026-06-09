"""Aggregate results into per-(suite, model) summaries and write reports."""

import csv
import json
import statistics
from dataclasses import asdict
from datetime import datetime
from pathlib import Path

SUMMARY_COLS = ["suite", "model", "tasks", "passed", "pass_rate", "mean_judge",
                "prompt_tokens", "completion_tokens", "cost_usd",
                "p50_latency_s", "p95_latency_s"]


def summarize(results):
    groups = {}
    for r in results:
        groups.setdefault((r.suite, r.model), []).append(r)

    rows = []
    for (suite, model), rs in sorted(groups.items()):
        verdicts = [x.verdict for x in rs if x.verdict is not None]
        passed = sum(1 for v in verdicts if v)
        judge_scores = [g.score for x in rs for g in x.grades
                        if g.grader == "llm_judge" and g.score is not None]
        latencies = [x.latency_s for x in rs if x.latency_s]
        rows.append({
            "suite": suite,
            "model": model,
            "tasks": len(rs),
            "passed": passed,
            "pass_rate": round(passed / len(verdicts), 4) if verdicts else None,
            "mean_judge": round(statistics.mean(judge_scores), 2) if judge_scores else None,
            "prompt_tokens": sum(x.prompt_tokens for x in rs),
            "completion_tokens": sum(x.completion_tokens for x in rs),
            "cost_usd": round(sum(x.cost_usd for x in rs), 6),
            "p50_latency_s": round(statistics.median(latencies), 3) if latencies else None,
            "p95_latency_s": round(_percentile(latencies, 95), 3) if latencies else None,
        })
    return rows


def _percentile(xs, p):
    if not xs:
        return 0.0
    s = sorted(xs)
    k = (len(s) - 1) * p / 100.0
    lo = int(k)
    if lo + 1 < len(s):
        return s[lo] + (s[lo + 1] - s[lo]) * (k - lo)
    return s[lo]


def _md_table(rows):
    if not rows:
        return "_no results_"
    header = "| " + " | ".join(SUMMARY_COLS) + " |"
    sep = "| " + " | ".join("---" for _ in SUMMARY_COLS) + " |"
    body = ["| " + " | ".join(str(r.get(c, "")) for c in SUMMARY_COLS) + " |" for r in rows]
    return "\n".join([header, sep, *body])


def write_reports(results, out_dir):
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    rows = summarize(results)

    json_path = out / f"run-{stamp}.json"
    json_path.write_text(json.dumps(
        {"summary": rows, "results": [asdict(r) for r in results]}, indent=2))

    csv_path = out / f"summary-{stamp}.csv"
    with open(csv_path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=SUMMARY_COLS)
        writer.writeheader()
        writer.writerows(rows)

    md_path = out / f"summary-{stamp}.md"
    md_path.write_text(f"# Eval run -- {stamp}\n\n{_md_table(rows)}\n")

    return {"json": str(json_path), "csv": str(csv_path), "md": str(md_path), "rows": rows}
