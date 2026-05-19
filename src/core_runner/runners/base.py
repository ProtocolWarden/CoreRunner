# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2026 ProtocolWarden
from typing import Protocol

from core_runner.contracts.invocation import RuntimeInvocation
from core_runner.contracts.result import RuntimeResult


class RuntimeRunner(Protocol):
    def run(self, invocation: RuntimeInvocation) -> RuntimeResult: ...
