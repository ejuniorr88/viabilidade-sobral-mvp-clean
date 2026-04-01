"""Compat shim for migrated runtime flow-state contract tests.

This file preserves the old path while delegating to the new canonical test module:
tests/runtime/test_flow_state_contract.py
"""

from tests.runtime.test_flow_state_contract import *  # noqa: F401,F403
