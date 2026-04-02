"""Legacy compatibility shim for the migrated runtime flow-state contract tests.

Keep this thin wrapper only while external runners or old references still point to:
tests/test_flow_state_contract.py

The canonical contract now lives in:
tests/runtime/test_flow_state_contract.py
"""

from tests.runtime.test_flow_state_contract import *  # noqa: F401,F403
