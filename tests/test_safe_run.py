# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2026 ProtocolWarden
import os
import signal
import sys
import textwrap

import pytest

from core_runner.process import SafeRunResult, safe_run


def test_zero_exit_success():
    result = safe_run([sys.executable, "-c", "import sys; sys.exit(0)"])
    assert result.returncode == 0
    assert not result.timed_out


def test_nonzero_exit_failure():
    result = safe_run([sys.executable, "-c", "import sys; sys.exit(42)"])
    assert result.returncode == 42
    assert not result.timed_out


def test_stdout_capture():
    result = safe_run([sys.executable, "-c", "print('hello')"])
    assert result.stdout.strip() == "hello"
    assert result.returncode == 0


def test_stderr_capture():
    result = safe_run([sys.executable, "-c", "import sys; sys.stderr.write('err\\n')"])
    assert result.stderr.strip() == "err"


def test_stdout_stderr_separate():
    result = safe_run(
        [sys.executable, "-c", "import sys; print('out'); sys.stderr.write('err\\n')"]
    )
    assert "out" in result.stdout
    assert "err" in result.stderr


def test_env_overlay(tmp_path):
    result = safe_run(
        [sys.executable, "-c", "import os; print(os.environ['TEST_VAR'])"],
        env={"TEST_VAR": "injected"},
    )
    assert result.stdout.strip() == "injected"


def test_cwd(tmp_path):
    result = safe_run(
        [sys.executable, "-c", "import os; print(os.getcwd())"],
        cwd=str(tmp_path),
    )
    assert result.stdout.strip() == str(tmp_path)


def test_timeout_kills_process():
    result = safe_run(
        [sys.executable, "-c", "import time; time.sleep(60)"],
        timeout_seconds=1,
    )
    assert result.timed_out
    assert result.returncode is not None


def test_process_group_kill_on_timeout():
    """Child that spawns a grandchild — both must die on timeout."""
    script = textwrap.dedent("""\
        import subprocess, sys, time
        p = subprocess.Popen([sys.executable, "-c", "import time; time.sleep(60)"])
        time.sleep(60)
    """)
    result = safe_run([sys.executable, "-c", script], timeout_seconds=2)
    assert result.timed_out


def test_capture_output_false():
    result = safe_run(
        [sys.executable, "-c", "print('ignored')"],
        capture_output=False,
    )
    assert result.stdout == ""
    assert result.stderr == ""
    assert result.returncode == 0


def test_safe_run_result_dataclass():
    r = SafeRunResult(returncode=0, stdout="a", stderr="b", timed_out=False)
    assert r.returncode == 0
    assert r.stdout == "a"
    assert r.stderr == "b"
    assert not r.timed_out
