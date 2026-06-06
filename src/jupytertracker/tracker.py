from __future__ import annotations

import sys
import time
from dataclasses import dataclass, field
from typing import List


@dataclass
class ExecutionRecord:
    exec_count: int
    source: str
    timestamp: float
    duration: float = 0.0  # seconds; set by post_run_cell


class Tracker:
    def __init__(self) -> None:
        self._log: List[ExecutionRecord] = []
        self._ip = None
        self._registered = False
        self._counter = 0        # own counter — ip.execution_count isn't reliable pre-run
        self._pending = None     # staged record; committed only on successful post_run_cell

    def start(self, ip=None) -> None:
        if self._registered:
            return  # idempotent — already tracking, do nothing
        if ip is None:
            try:
                from IPython import get_ipython
                ip = get_ipython()
            except ImportError:
                pass
        if ip is None:
            raise RuntimeError(
                "No active IPython kernel found. "
                "Call jupytertracker.start() from inside a Jupyter notebook, "
                "or pass an IPython instance: jupytertracker.start(ip=get_ipython())"
            )
        self._ip = ip
        self._log.clear()   # fresh session — discard any log from a previous run
        self._counter = 0
        self._pending = None
        ip.events.register("pre_run_cell", self._on_pre_run_cell)
        ip.events.register("post_run_cell", self._on_post_run_cell)
        self._registered = True

    def stop(self) -> None:
        if not self._registered or self._ip is None:
            return
        for event, handler in [
            ("pre_run_cell", self._on_pre_run_cell),
            ("post_run_cell", self._on_post_run_cell),
        ]:
            try:
                self._ip.events.unregister(event, handler)
            except ValueError:
                pass
        self._pending = None
        self._registered = False

    def _on_pre_run_cell(self, info) -> None:
        try:
            self._counter += 1
            self._pending = ExecutionRecord(
                exec_count=self._counter,
                source=info.raw_cell,
                timestamp=time.time(),
            )
        except Exception as exc:
            print(f"[jupytertracker] hook error (ignored): {exc}", file=sys.stderr)

    def _on_post_run_cell(self, result) -> None:
        try:
            if self._pending is None:
                return
            if result.success:
                self._pending.duration = time.time() - self._pending.timestamp
                self._log.append(self._pending)
            else:
                # Discard: error, exception, or user interruption
                self._counter -= 1
            self._pending = None
        except Exception as exc:
            print(f"[jupytertracker] hook error (ignored): {exc}", file=sys.stderr)

    @property
    def log(self) -> List[ExecutionRecord]:
        return list(self._log)

    def clear(self) -> None:
        self._log.clear()
