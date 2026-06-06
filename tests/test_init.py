import pytest
from pathlib import Path
import jupytertracker
from conftest import _IP as _global_ip


def test_export_before_start_raises():
    with pytest.raises(RuntimeError, match="not been started"):
        jupytertracker.export_script("/tmp/out.py")


def test_unknown_mode_raises(tmp_path):
    jupytertracker.start(ip=_global_ip)
    with pytest.raises(ValueError, match="Unknown mode"):
        jupytertracker.export_script(str(tmp_path / "out.py"), mode="unknown")


def test_dedup_mode_raises_not_implemented(tmp_path):
    jupytertracker.start(ip=_global_ip)
    with pytest.raises(NotImplementedError):
        jupytertracker.export_script(str(tmp_path / "out.py"), mode="dedup")


def test_start_stop_start_clears_log(tmp_path):
    ip = _global_ip
    jupytertracker.start(ip=ip)
    ip.run_cell("a = 1")
    jupytertracker.stop()
    ip.run_cell("b = 2")  # not tracked
    jupytertracker.start(ip=ip)  # fresh session — old log discarded
    ip.run_cell("c = 3")
    log = jupytertracker.get_log()
    sources = [r.source for r in log]
    assert not any("a = 1" in s for s in sources)  # pre-stop entries gone
    assert not any("b = 2" in s for s in sources)  # untracked — still absent
    assert any("c = 3" in s for s in sources)       # post-restart entry present


def test_full_pipeline(tmp_path):
    ip = _global_ip
    jupytertracker.start(ip=ip)
    ip.run_cell("x = 10")
    ip.run_cell("y = 20")
    ip.run_cell("x = 99")  # re-run with new value
    ip.run_cell("y = 20")  # re-run unchanged
    out = tmp_path / "output.py"
    jupytertracker.export_script(str(out))
    content = out.read_text()
    assert content.count("# execution") == 4
    assert "x = 10" in content
    assert "x = 99" in content
    assert content.index("x = 10") < content.index("x = 99")


def test_clear_resets_log():
    ip = _global_ip
    jupytertracker.start(ip=ip)
    ip.run_cell("a = 1")
    assert len(jupytertracker.get_log()) == 1
    jupytertracker.clear()
    assert jupytertracker.get_log() == []


def test_stop_before_start_does_not_raise():
    jupytertracker.stop()  # _tracker is None — should not raise


def test_get_log_before_start_returns_empty():
    assert jupytertracker.get_log() == []
