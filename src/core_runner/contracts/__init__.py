# SPDX-License-Identifier: AGPL-3.0-or-later
"""CoreRunner contract surface — canonical RxP types.

CoreRunner delegates contract semantics to RxP:
- ``RuntimeInvocation`` — what to run
- ``RuntimeResult`` — what came back
- ``ArtifactDescriptor`` — file artifacts produced by a run

Status values are RxP's runtime_status vocabulary (string literals):
``pending | running | succeeded | failed | timed_out | cancelled |
rejected``.
"""
from core_runner.contracts.invocation import RuntimeInvocation
from core_runner.contracts.result import ArtifactDescriptor, RuntimeResult

__all__ = ["RuntimeInvocation", "RuntimeResult", "ArtifactDescriptor"]
