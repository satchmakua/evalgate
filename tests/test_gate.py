from gatecheck.gate import gate, save_baseline
from gatecheck.types import GradeResult, TaskResult


def _result(passed):
    return TaskResult(suite="s", task_id="t", model="ollama:m",
                      grades=[GradeResult("contains", passed=passed)])


def test_gate_passes_when_equal_to_baseline(tmp_path):
    base = tmp_path / "b.json"
    save_baseline([_result(True)], base)
    ok, _ = gate([_result(True)], base)
    assert ok is True


def test_gate_fails_on_regression(tmp_path):
    base = tmp_path / "b.json"
    save_baseline([_result(True), _result(True)], base)   # baseline pass_rate 1.0
    ok, lines = gate([_result(True), _result(False)], base)  # now 0.5
    assert ok is False
    assert any("FAIL" in ln for ln in lines)


def test_gate_tolerance_allows_small_drop(tmp_path):
    base = tmp_path / "b.json"
    save_baseline([_result(True), _result(True), _result(True), _result(True)], base)  # 1.0
    ok, _ = gate([_result(True), _result(True), _result(True), _result(False)], base,
                 tolerance=0.3)  # 0.75 >= 1.0 - 0.3
    assert ok is True


def test_min_pass_rate_floor(tmp_path):
    base = tmp_path / "missing.json"  # no baseline yet
    ok, _ = gate([_result(False)], base, min_pass_rate=0.8)
    assert ok is False


def test_save_baseline_roundtrip(tmp_path):
    base = tmp_path / "b.json"
    snap = save_baseline([_result(True)], base)
    assert snap["s::ollama:m"]["pass_rate"] == 1.0
    assert base.exists()
