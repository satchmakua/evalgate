"""Load eval suites from YAML files."""

from pathlib import Path

import yaml

from .types import Suite, Task


def load_suites(path, only=None):
    """Load one suite file or every *.yaml in a directory.

    `only` optionally restricts to suites whose name is in the given list.
    """
    p = Path(path)
    files = [p] if p.is_file() else sorted(p.glob("*.yaml"))
    suites = []
    for f in files:
        raw = yaml.safe_load(f.read_text()) or {}
        name = raw.get("name", f.stem)
        if only and name not in only:
            continue
        tasks = [
            Task(
                id=t["id"],
                prompt=t["prompt"],
                system=t.get("system"),
                graders=t.get("graders", []),
                expected=t.get("expected"),
            )
            for t in raw.get("tasks", [])
        ]
        suites.append(Suite(
            name=name,
            description=raw.get("description", ""),
            tasks=tasks,
            models=raw.get("models"),
        ))
    return suites
