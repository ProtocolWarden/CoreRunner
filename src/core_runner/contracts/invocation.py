# SPDX-License-Identifier: AGPL-3.0-or-later
"""CoreRunner consumes the canonical RxP RuntimeInvocation contract.

Re-exported here so callers can ``from core_runner.contracts
import RuntimeInvocation`` without depending on the RxP package
directly.
"""
from rxp.contracts import RuntimeInvocation

__all__ = ["RuntimeInvocation"]
