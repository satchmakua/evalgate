from gatecheck.cache import DiskCache
from gatecheck.types import Completion


def _comp(text="hi"):
    return Completion(text=text, model="m", provider="p",
                      prompt_tokens=3, completion_tokens=1, latency_s=0.5)


def test_roundtrip_across_instances(tmp_path):
    key = ("openai:gpt-4o", "[]", "{}")
    DiskCache(str(tmp_path))[key] = _comp("hi")
    # a fresh instance (new run) reads the entry from disk, not from memory
    got = DiskCache(str(tmp_path)).get(key)
    assert got is not None
    assert got.text == "hi" and got.prompt_tokens == 3 and got.latency_s == 0.5


def test_miss_returns_none(tmp_path):
    assert DiskCache(str(tmp_path)).get(("m", "[]", "{}")) is None


def test_corrupt_entry_is_a_miss(tmp_path):
    c = DiskCache(str(tmp_path))
    key = ("m", "[]", "{}")
    with open(c._path(key), "w", encoding="utf-8") as f:
        f.write("{ this is not valid json")
    assert c.get(key) is None          # corrupt -> miss, no exception


def test_distinct_keys_do_not_collide(tmp_path):
    c = DiskCache(str(tmp_path))
    c[("m", "[]", "{}")] = _comp("A")
    c[("m", "[]", '{"temperature": 0}')] = _comp("B")   # different options
    fresh = DiskCache(str(tmp_path))
    assert fresh.get(("m", "[]", "{}")).text == "A"
    assert fresh.get(("m", "[]", '{"temperature": 0}')).text == "B"


def test_no_temp_files_left_behind(tmp_path):
    c = DiskCache(str(tmp_path))
    c[("m", "[]", "{}")] = _comp("hi")
    leftover = [p for p in tmp_path.iterdir() if p.suffix == ".tmp"]
    assert leftover == []              # atomic write cleans up its temp file


def test_write_failure_does_not_raise(tmp_path):
    import shutil
    d = tmp_path / "c"
    c = DiskCache(str(d))
    shutil.rmtree(d)                   # cache dir vanishes mid-run (removable/network volume)
    c[("m", "[]", "{}")] = _comp("hi")  # best-effort: a write failure must not raise
    assert c.get(("m", "[]", "{}")).text == "hi"  # in-memory layer still serves it this run
