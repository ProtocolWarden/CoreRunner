# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2026 ProtocolWarden
"""core_runner.process — process-group-safe subprocess primitive.

A lightweight alternative to the full RxP invocation path. Suitable for
callers that do not need artifact file capture or RxP contract types
(TeamExecutor, DAGExecutor, CritiqueExecutor).

Key safety guarantees:
- start_new_session=True — child is its own process-group leader
- os.killpg(SIGKILL) on timeout — reaps all descendants, not just direct child
- Transient SIGTERM handler — child group is killed if the Python supervisor
  is itself killed (OOM killer, supervisor stop)
"""
from __future__ import annotations

import os
import signal
import subprocess
import threading
from dataclasses import dataclass
from typing import NoReturn


@dataclass
class SafeRunResult:
    returncode: int | None
    stdout: str
    stderr: str
    timed_out: bool


def safe_run(
    cmd: list[str],
    *,
    cwd: str = ".",
    env: dict[str, str] | None = None,
    timeout_seconds: int | None = None,
    capture_output: bool = True,
) -> SafeRunResult:
    """Run cmd in a new process group with full descendant cleanup on timeout.

    When capture_output=False, stdout and stderr are not captured (suitable
    for interactive or fire-and-forget use). SafeRunResult.stdout/stderr will
    be empty strings in that case.
    """
    run_env = os.environ.copy()
    if env:
        run_env.update(env)

    kwargs: dict = {
        "cwd": cwd,
        "env": run_env,
        "start_new_session": True,
    }
    if capture_output:
        kwargs["stdout"] = subprocess.PIPE
        kwargs["stderr"] = subprocess.PIPE

    proc = subprocess.Popen(cmd, **kwargs)

    try:
        pgid: int | None = os.getpgid(proc.pid) if proc.pid else None
    except OSError:
        pgid = None

    def _kill_group() -> None:
        if pgid is not None:
            try:
                os.killpg(pgid, signal.SIGKILL)
            except (ProcessLookupError, OSError):
                pass

    # signal.signal() only works from the main thread. When safe_run is called
    # from a ThreadPoolExecutor (e.g. TeamExecutor parallel stages), skip the
    # handler — _kill_group() is still called on timeout for cleanup.
    in_main_thread = threading.current_thread() is threading.main_thread()
    prev_sigterm: object = None
    if in_main_thread:
        prev_sigterm = signal.getsignal(signal.SIGTERM)

        def _sigterm_handler(signum: int, _frame: object) -> NoReturn:
            _kill_group()
            signal.signal(signal.SIGTERM, prev_sigterm)  # type: ignore[arg-type]
            raise SystemExit(128 + signum)

        signal.signal(signal.SIGTERM, _sigterm_handler)
    try:
        try:
            stdout_bytes, stderr_bytes = proc.communicate(timeout=timeout_seconds)
        except subprocess.TimeoutExpired:
            _kill_group()
            try:
                stdout_bytes, stderr_bytes = proc.communicate(timeout=5)
            except subprocess.TimeoutExpired:
                proc.kill()
                stdout_bytes, stderr_bytes = proc.communicate()
            return SafeRunResult(
                returncode=proc.returncode,
                stdout=stdout_bytes.decode(errors="replace") if stdout_bytes else "",
                stderr=stderr_bytes.decode(errors="replace") if stderr_bytes else "",
                timed_out=True,
            )
    finally:
        if in_main_thread:
            signal.signal(signal.SIGTERM, prev_sigterm)  # type: ignore[arg-type]

    return SafeRunResult(
        returncode=proc.returncode,
        stdout=stdout_bytes.decode(errors="replace") if stdout_bytes else "",
        stderr=stderr_bytes.decode(errors="replace") if stderr_bytes else "",
        timed_out=False,
    )
