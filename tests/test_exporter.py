import pytest
from pathlib import Path
from jupytertracker.tracker import ExecutionRecord
from jupytertracker.exporter import export_sequential


def _records(*sources, durations=None):
    if durations is None:
        durations = [0.1 * (i + 1) for i in range(len(sources))]
    return [
        ExecutionRecord(exec_count=i + 1, source=src, timestamp=float(i), duration=dur)
        for i, (src, dur) in enumerate(zip(sources, durations))
    ]


def test_sequential_preserves_all_executions(tmp_path):
    log = _records("x = 1", "y = 2", "x = 99", "y = 2")
    out = tmp_path / "out.py"
    export_sequential(log, out)
    content = out.read_text()
    assert content.count("# execution") == 4
    assert "x = 1" in content
    assert "x = 99" in content


def test_sequential_preserves_modified_source_at_each_run(tmp_path):
    log = _records("model = train(lr=0.01)", "model = train(lr=0.1)")
    out = tmp_path / "out.py"
    export_sequential(log, out)
    content = out.read_text()
    assert "lr=0.01" in content
    assert "lr=0.1" in content
    # Both versions present — neither deduplicated
    assert content.index("lr=0.01") < content.index("lr=0.1")


def test_sequential_execution_order(tmp_path):
    log = _records("a = 1", "b = 2", "c = 3", "b = 99", "c = 3")
    out = tmp_path / "out.py"
    export_sequential(log, out)
    content = out.read_text()
    lines = [l for l in content.splitlines() if l.startswith("# execution")]
    assert len(lines) == 5
    for i, line in enumerate(lines, start=1):
        assert line.startswith(f"# execution {i}  [")


def test_empty_log_produces_header_only(tmp_path):
    out = tmp_path / "out.py"
    export_sequential([], out)
    content = out.read_text()
    assert "No cells were recorded" in content


def test_magic_command_gets_comment(tmp_path):
    log = _records("%matplotlib inline", "x = 1")
    out = tmp_path / "out.py"
    export_sequential(log, out)
    content = out.read_text()
    assert "magic/shell command" in content


def test_shell_command_gets_comment(tmp_path):
    log = _records("!pip install pandas", "import pandas")
    out = tmp_path / "out.py"
    export_sequential(log, out)
    content = out.read_text()
    assert "magic/shell command" in content


def test_normal_cell_no_magic_comment(tmp_path):
    log = _records("x = 1 + 1")
    out = tmp_path / "out.py"
    export_sequential(log, out)
    content = out.read_text()
    assert "magic/shell" not in content


def test_output_file_has_header_warning(tmp_path):
    log = _records("x = 1")
    out = tmp_path / "out.py"
    export_sequential(log, out)
    content = out.read_text()
    assert "jupytertracker" in content
    assert "sequential mode" in content


def test_execution_time_shown_per_cell(tmp_path):
    log = _records("x = 1", "y = 2", durations=[0.5, 1.25])
    out = tmp_path / "out.py"
    export_sequential(log, out)
    content = out.read_text()
    assert "500ms" in content
    assert "1.25s" in content


def test_total_execution_time_in_header(tmp_path):
    log = _records("x = 1", "y = 2", durations=[30.0, 45.0])
    out = tmp_path / "out.py"
    export_sequential(log, out)
    content = out.read_text()
    # 75 seconds total = 1m 15.0s
    assert "1m 15.0s" in content


def test_cell_count_in_header(tmp_path):
    log = _records("a = 1", "b = 2", "c = 3")
    out = tmp_path / "out.py"
    export_sequential(log, out)
    content = out.read_text()
    assert "Cells recorded: 3" in content


def test_fmt_duration_ms(tmp_path):
    log = _records("x = 1", durations=[0.034])
    out = tmp_path / "out.py"
    export_sequential(log, out)
    assert "34ms" in out.read_text()


def test_duration_recorded_in_tracker(ip):
    import jupytertracker
    jupytertracker.start(ip=ip)
    ip.run_cell("import time; time.sleep(0.05)")
    log = jupytertracker.get_log()
    assert len(log) == 1
    assert log[0].duration >= 0.05
