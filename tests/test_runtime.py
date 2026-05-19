# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2026 ProtocolWarden
import sys
from pathlib import Path

from core_runner.contracts.invocation import RuntimeInvocation
from core_runner.contracts.result import RuntimeResult
from core_runner.runners.subprocess_runner import SubprocessRunner
from core_runner.runtime import CoreRunner


def test_default_facade_uses_subprocess_runner() -> None:
    runtime = CoreRunner()
    assert isinstance(runtime.runner, SubprocessRunner)


def test_is_registered_reports_registered_kinds() -> None:
    runtime = CoreRunner()
    assert runtime.is_registered("subprocess") is True
    assert runtime.is_registered("manual") is False


def test_facade_returns_runtime_result(tmp_path: Path) -> None:
    runtime = CoreRunner()
    invocation = RuntimeInvocation(
        invocation_id="inv-facade",
        runtime_name="local",
        runtime_kind="subprocess",
        working_directory=str(tmp_path),
        command=[sys.executable, "-c", "print('facade')"],
        environment={},
        timeout_seconds=5,
        input_payload_path=None,
        output_result_path=str(tmp_path / "result.json"),
        artifact_directory=None,
    )

    result = runtime.run(invocation)
    assert isinstance(result, RuntimeResult)
    assert (tmp_path / "result.json").exists()
