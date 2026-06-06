"""
jupytertracker — record Jupyter notebook cell executions and export an ordered script.

Basic usage:
    import jupytertracker
    jupytertracker.start()
    # ... run cells in your notebook ...
    jupytertracker.export_script("output.py")
"""

from __future__ import annotations

from pathlib import Path
from typing import Optional

from .tracker import Tracker
from .exporter import export_sequential

_tracker: Optional[Tracker] = None


def start(ip=None) -> None:
    """Start tracking cell executions. Safe to call multiple times (idempotent)."""
    global _tracker
    if _tracker is None:
        _tracker = Tracker()
    _tracker.start(ip=ip)


def stop() -> None:
    """Stop tracking. Does nothing if tracking was not started."""
    if _tracker is not None:
        _tracker.stop()


def export_script(path: str, mode: str = "sequential") -> None:
    """Export the recorded execution log to a Python script.

    Args:
        path: Output file path (e.g. 'output.py').
        mode: 'sequential' (default) — every execution in order, no deduplication.
              'dedup' — last version of each cell only (deferred to v2).
    """
    if _tracker is None:
        raise RuntimeError(
            "Tracking has not been started. Call jupytertracker.start() first."
        )
    if mode == "sequential":
        export_sequential(_tracker.log, path)
    elif mode == "dedup":
        raise NotImplementedError(
            "mode='dedup' is planned for v2. Use mode='sequential' (the default)."
        )
    else:
        raise ValueError(f"Unknown mode '{mode}'. Use 'sequential'.")


def clear() -> None:
    """Clear the recorded execution log without stopping tracking."""
    if _tracker is not None:
        _tracker.clear()


def get_log():
    """Return a copy of the current execution log (list of ExecutionRecord)."""
    if _tracker is None:
        return []
    return _tracker.log
