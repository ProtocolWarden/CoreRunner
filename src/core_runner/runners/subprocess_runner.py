# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2026 ProtocolWarden
"""SubprocessRunner — RxP invocation runner backed by core_runner.safe_run().

Provides stdout/stderr capture to files and ArtifactDescriptor production
on top of the process-group-safe safe_run() primitive.
"""
from __future__ import annotations

import os
from datetime import UTC, datetime
from pathlib import Path

from core_runner.contracts.invocation import RuntimeInvocation
from core_runner.contracts.result import ArtifactDescriptor, RuntimeResult
from core_runner.io.paths import capture_directory
from core_runner.process import safe_run


class SubprocessRunner:
    def run(self, invocation: RuntimeInvocation) -> RuntimeResult:
        started_at = _utc_now_iso()
        working_dir = Path(invocation.working_directory)
        if not working_dir.exists() or not working_dir.is_dir():
            return RuntimeResult(
                invocation_id=invocation.invocation_id,
                runtime_name=invocation.runtime_name,
                runtime_kind=invocation.runtime_kind,
                status="rejected",
                exit_code=None,
                started_at=started_at,
                finished_at=_utc_now_iso(),
                stdout_path=None,
                stderr_path=None,
                artifacts=[],
                error_summary=f"working directory does not exist: {working_dir}",
            )

        out_dir = capture_directory(invocation)
        out_dir.mkdir(parents=True, exist_ok=True)
        stdout_path = out_dir / "stdout.txt"
        stderr_path = out_dir / "stderr.txt"

        env_overlay: dict[str, str] = dict(invocation.environment)

        result = safe_run(
            list(invocation.command),
            cwd=str(working_dir),
            env=env_overlay if env_overlay else None,
            timeout_seconds=invocation.timeout_seconds,
        )

        stdout_path.write_text(result.stdout, encoding="utf-8")
        stderr_path.write_text(result.stderr, encoding="utf-8")

        finished_at = _utc_now_iso()
        artifacts = [
            ArtifactDescriptor(
                artifact_id="stdout",
                path=str(stdout_path),
                kind="log_excerpt",
                description="captured stdout",
            ),
            ArtifactDescriptor(
                artifact_id="stderr",
                path=str(stderr_path),
                kind="log_excerpt",
                description="captured stderr",
            ),
        ]

        if result.timed_out:
            timeout_val = invocation.timeout_seconds
            error_summary = (
                f"process exceeded timeout of {timeout_val} seconds"
                if timeout_val
                else "process timed out"
            )
            return RuntimeResult(
                invocation_id=invocation.invocation_id,
                runtime_name=invocation.runtime_name,
                runtime_kind=invocation.runtime_kind,
                status="timed_out",
                exit_code=result.returncode,
                started_at=started_at,
                finished_at=finished_at,
                stdout_path=str(stdout_path),
                stderr_path=str(stderr_path),
                artifacts=artifacts,
                error_summary=error_summary,
            )

        status = "succeeded" if result.returncode == 0 else "failed"
        return RuntimeResult(
            invocation_id=invocation.invocation_id,
            runtime_name=invocation.runtime_name,
            runtime_kind=invocation.runtime_kind,
            status=status,
            exit_code=result.returncode,
            started_at=started_at,
            finished_at=finished_at,
            stdout_path=str(stdout_path),
            stderr_path=str(stderr_path),
            artifacts=artifacts,
            error_summary=None,
        )


def _utc_now_iso() -> str:
    return datetime.now(UTC).isoformat()
