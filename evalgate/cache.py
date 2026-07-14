"""On-disk completion cache: skip re-calling a model for an unchanged
(model, messages, options) across runs.

One JSON file per key, named by a SHA-256 of the key, in a directory you choose
(`--cache-dir`). Writes are atomic (write a unique temp file, then `os.replace`)
so an interrupted run can't leave a half-written entry, and an unreadable or
corrupt entry is treated as a miss rather than raising. A small in-process layer
avoids re-reading/re-writing the same key within a run.

Like the in-memory cache, dedup is best-effort under concurrency (the get/set is
a check-then-act) and never affects correctness -- only whether a duplicate call
is avoided.
"""

import hashlib
import json
import os
import tempfile

from .types import Completion

# The Completion fields we persist and restore. `cost` is not stored -- it is
# recomputed from tokens at read time, so a pricing change takes effect without
# invalidating the cache.
_FIELDS = ("text", "model", "provider", "prompt_tokens", "completion_tokens", "latency_s")


class DiskCache:
    def __init__(self, directory):
        self.dir = directory
        os.makedirs(directory, exist_ok=True)
        self._mem = {}  # within-run layer: key -> Completion

    def _path(self, key):
        digest = hashlib.sha256("\x00".join(key).encode("utf-8")).hexdigest()
        return os.path.join(self.dir, digest + ".json")

    def get(self, key):
        if key in self._mem:
            return self._mem[key]
        try:
            with open(self._path(key), encoding="utf-8") as f:
                data = json.load(f)
            comp = Completion(**{k: data[k] for k in _FIELDS})
        except (OSError, ValueError, KeyError, TypeError):
            return None  # missing or corrupt -> treat as a miss
        self._mem[key] = comp
        return comp

    def __setitem__(self, key, comp):
        self._mem[key] = comp
        record = {k: getattr(comp, k) for k in _FIELDS}
        # keep the key components in the file for debuggability / grep
        record["_key"] = {"model": key[0], "messages": key[1], "options": key[2]}
        # Best-effort: any write failure (dir vanished/read-only/full) must not
        # break the run -- so mkstemp is inside the try too, not just the write.
        tmp = None
        try:
            fd, tmp = tempfile.mkstemp(dir=self.dir, suffix=".tmp")
            with os.fdopen(fd, "w", encoding="utf-8") as f:
                json.dump(record, f)
            os.replace(tmp, self._path(key))  # atomic on the same filesystem
        except OSError:
            if tmp is not None:
                try:
                    os.remove(tmp)
                except OSError:
                    pass
