"""Regression gating: compare a run against a committed baseline and fail on drops."""

import json
from pathlib import Path

from .report import summarize


def save_baseline(results, path):
    """Persist per-(suite, model) pass_rate and mean_judge as the baseline."""
    rows = summarize(results)
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    snap = {
        f"{r['suite']}::{r['model']}": {
            "pass_rate": r["pass_rate"],
            "mean_judge": r["mean_judge"],
        }
        for r in rows
    }
    path.write_text(json.dumps(snap, indent=2))
    return snap


def gate(results, baseline_path, tolerance=0.0, min_pass_rate=None):
    """Return (ok, lines).

    Fails if any (suite, model) drops below an absolute `min_pass_rate`, or if
    its pass_rate falls more than `tolerance` below the baseline. Unknown keys
    (no baseline entry) are reported but never fail the gate.
    """
    rows = summarize(results)
    path = Path(baseline_path)
    baseline = json.loads(path.read_text()) if path.exists() else {}

    ok = True
    lines = []
    for r in rows:
        key = f"{r['suite']}::{r['model']}"
        pr = r["pass_rate"]
        if pr is None:
            lines.append(f"SKIP {key}: no auto-graded tasks")
            continue
        if min_pass_rate is not None and pr < min_pass_rate:
            ok = False
            lines.append(f"FAIL {key}: pass_rate {pr:.3f} < min {min_pass_rate}")
            continue
        base_pr = baseline.get(key, {}).get("pass_rate")
        if base_pr is None:
            lines.append(f"NEW  {key}: pass_rate {pr:.3f} (no baseline)")
        elif pr < base_pr - tolerance:
            ok = False
            lines.append(f"FAIL {key}: pass_rate {pr:.3f} < baseline {base_pr:.3f} "
                         f"(tolerance {tolerance})")
        else:
            lines.append(f"OK   {key}: pass_rate {pr:.3f} (baseline {base_pr:.3f})")
    return ok, lines
