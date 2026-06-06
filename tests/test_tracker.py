import pytest
from IPython.testing.globalipapp import get_ipython
from jupytertracker.tracker import Tracker


def _run_cell(ip, source: str):
    """Simulate a cell execution through the real IPython kernel."""
    ip.run_cell(source)


def test_records_single_cell(ip):
    tracker = Tracker()
    tracker.start(ip=ip)
    _run_cell(ip, "x = 1")
    log = tracker.log
    assert len(log) == 1
    assert "x = 1" in log[0].source
    tracker.stop()


def test_records_multiple_cells_in_order(ip):
    tracker = Tracker()
    tracker.start(ip=ip)
    _run_cell(ip, "a = 1")
    _run_cell(ip, "b = 2")
    _run_cell(ip, "c = 3")
    log = tracker.log
    assert len(log) == 3
    assert log[0].exec_count < log[1].exec_count < log[2].exec_count
    tracker.stop()


def test_records_rerun_with_modified_source(ip):
    tracker = Tracker()
    tracker.start(ip=ip)
    _run_cell(ip, "x = 1")
    _run_cell(ip, "x = 99")  # same "cell", modified source
    log = tracker.log
    assert len(log) == 2
    assert "x = 1" in log[0].source
    assert "x = 99" in log[1].source
    tracker.stop()


def test_start_is_idempotent(ip):
    tracker = Tracker()
    tracker.start(ip=ip)
    hook_count_before = len([h for h in ip.events.callbacks.get("pre_run_cell", [])])
    tracker.start(ip=ip)  # second call — must not double-register
    hook_count_after = len([h for h in ip.events.callbacks.get("pre_run_cell", [])])
    assert hook_count_before == hook_count_after
    tracker.stop()


def test_stop_unregisters_hooks(ip):
    tracker = Tracker()
    tracker.start(ip=ip)
    tracker.stop()
    _run_cell(ip, "y = 42")
    assert tracker.log == []


def test_stop_before_start_does_not_raise(ip):
    tracker = Tracker()
    tracker.stop()  # should not raise


def test_hook_exception_does_not_disrupt_execution(ip, capsys):
    tracker = Tracker()
    tracker.start(ip=ip)

    # Corrupt the hook to raise intentionally
    original = tracker._on_pre_run_cell
    def bad_hook(info):
        raise RuntimeError("intentional test error")
    ip.events.unregister("pre_run_cell", original)
    ip.events.register("pre_run_cell", bad_hook)

    # Cell execution must still succeed despite bad hook
    result = ip.run_cell("z = 7")
    assert result.success

    ip.events.unregister("pre_run_cell", bad_hook)
    tracker.stop()


def test_start_without_ipython_raises(monkeypatch):
    import IPython.core.interactiveshell as _shell
    # Temporarily clear the global singleton so get_ipython() returns None
    orig = _shell.InteractiveShell._instance
    _shell.InteractiveShell._instance = None
    try:
        tracker = Tracker()
        with pytest.raises(RuntimeError, match="No active IPython kernel"):
            tracker.start(ip=None)
    finally:
        _shell.InteractiveShell._instance = orig


def test_failed_cell_not_recorded(ip):
    tracker = Tracker()
    tracker.start(ip=ip)
    _run_cell(ip, "x = 1")                  # succeeds
    _run_cell(ip, "raise ValueError('boom')")  # fails
    _run_cell(ip, "y = 2")                  # succeeds
    log = tracker.log
    assert len(log) == 2
    assert "x = 1" in log[0].source
    assert "y = 2" in log[1].source
    assert log[0].exec_count == 1
    assert log[1].exec_count == 2
    tracker.stop()


def test_syntax_error_cell_not_recorded(ip):
    tracker = Tracker()
    tracker.start(ip=ip)
    _run_cell(ip, "x = 1")
    _run_cell(ip, "def bad syntax(:")   # syntax error — never executes
    _run_cell(ip, "y = 2")
    log = tracker.log
    sources = [r.source for r in log]
    assert len(log) == 2
    assert any("x = 1" in s for s in sources)
    assert any("y = 2" in s for s in sources)
    tracker.stop()


def test_exec_count_stays_contiguous_after_failure(ip):
    tracker = Tracker()
    tracker.start(ip=ip)
    _run_cell(ip, "a = 1")
    _run_cell(ip, "raise RuntimeError()")
    _run_cell(ip, "b = 2")
    log = tracker.log
    assert len(log) == 2
    assert log[0].exec_count == 1
    assert log[1].exec_count == 2  # counter rolled back on failure, so next success is 2
    tracker.stop()


def test_clear_empties_log(ip):
    tracker = Tracker()
    tracker.start(ip=ip)
    _run_cell(ip, "a = 1")
    assert len(tracker.log) == 1
    tracker.clear()
    assert tracker.log == []
    tracker.stop()
