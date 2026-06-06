import pytest
from pathlib import Path
from jupytertracker.tracker import ExecutionRecord
from jupytertracker.exporter import export_sequential


def _records(*sources):
    return [
        ExecutionRecord(exec_count=i + 1, source=src, timestamp=float(i))
        for i, src in enumerate(sources)
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
    assert lines == [
        "# execution 1",
        "# execution 2",
        "# execution 3",
        "# execution 4",
        "# execution 5",
    ]


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
