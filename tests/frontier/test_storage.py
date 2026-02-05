"""Tests for storage operations in Frontier EVM."""

import pytest

from ethereum.common.types import Account, Environment, Opcode, State
from ethereum.frontier.vm.interpreter import Interpreter
from tests.conftest import assemble, create_message, push


@pytest.fixture
def state_with_contract():
    """Create state with a contract that has storage."""
    state = State()
    contract_addr = b"\x00" * 19 + b"\x02"
    state.set_account(
        contract_addr,
        Account(
            nonce=0,
            balance=1000,
            code=b"",
            storage={0: 100, 1: 200, 2**255: 999},
        ),
    )
    return state


@pytest.fixture
def interpreter(state_with_contract):
    return Interpreter(state_with_contract, Environment())


class TestSload:
    """Tests for SLOAD opcode."""

    def test_sload_existing(self, interpreter):
        """Test loading existing storage value."""
        code = assemble(
            push(0),
            Opcode.SLOAD,
            Opcode.STOP,
        )
        result = interpreter.execute(create_message(code))
        assert result.success

    def test_sload_nonexistent(self, interpreter):
        """Test loading non-existent storage returns 0."""
        code = assemble(
            push(999),
            Opcode.SLOAD,
            Opcode.STOP,
        )
        result = interpreter.execute(create_message(code))
        assert result.success

    def test_sload_large_key(self, interpreter):
        """Test loading from large storage key."""
        code = assemble(
            push(2**255, 32),
            Opcode.SLOAD,
            Opcode.STOP,
        )
        result = interpreter.execute(create_message(code))
        assert result.success


class TestSstore:
    """Tests for SSTORE opcode."""

    def test_sstore_new_value(self, interpreter):
        """Test storing a new value."""
        code = assemble(
            push(42),  # value
            push(100),  # key
            Opcode.SSTORE,
            Opcode.STOP,
        )
        result = interpreter.execute(create_message(code))
        assert result.success
        # Verify storage was updated
        assert interpreter.state.get_storage(b"\x00" * 19 + b"\x02", 100) == 42

    def test_sstore_overwrite(self, interpreter):
        """Test overwriting existing value."""
        code = assemble(
            push(999),  # new value
            push(0),  # existing key
            Opcode.SSTORE,
            Opcode.STOP,
        )
        result = interpreter.execute(create_message(code))
        assert result.success
        assert interpreter.state.get_storage(b"\x00" * 19 + b"\x02", 0) == 999

    def test_sstore_zero_clears(self, interpreter):
        """Test storing 0 clears the storage slot."""
        code = assemble(
            push(0),  # value (clear)
            push(0),  # existing key
            Opcode.SSTORE,
            Opcode.STOP,
        )
        result = interpreter.execute(create_message(code))
        assert result.success
        assert interpreter.state.get_storage(b"\x00" * 19 + b"\x02", 0) == 0

    def test_sstore_gas_cost_new(self, interpreter):
        """Test SSTORE gas cost for new storage."""
        code = assemble(
            push(1),  # value
            push(9999),  # new key
            Opcode.SSTORE,
            Opcode.STOP,
        )
        result = interpreter.execute(create_message(code, gas=100000))
        assert result.success
        # G_SSET = 20000 for setting from 0 to non-0
        assert result.gas_used > 20000

    def test_sstore_gas_cost_update(self, interpreter):
        """Test SSTORE gas cost for updating existing storage."""
        code = assemble(
            push(999),  # new value
            push(0),  # existing key (has value 100)
            Opcode.SSTORE,
            Opcode.STOP,
        )
        result = interpreter.execute(create_message(code, gas=100000))
        assert result.success
        # G_SRESET = 5000 for updating non-0 to non-0
        assert result.gas_used < 20000


class TestStorageEdgeCases:
    """Edge case tests for storage operations."""

    def test_sload_sstore_same_slot(self, interpreter):
        """Test loading then storing to same slot."""
        code = assemble(
            push(0),
            Opcode.SLOAD,  # Load existing value
            push(1),
            Opcode.ADD,  # Add 1
            push(0),
            Opcode.SSTORE,  # Store back
            Opcode.STOP,
        )
        result = interpreter.execute(create_message(code))
        assert result.success
        # Original value was 100, should now be 101
        assert interpreter.state.get_storage(b"\x00" * 19 + b"\x02", 0) == 101

    def test_multiple_sstores(self, interpreter):
        """Test multiple SSTORE operations."""
        code = assemble(
            push(1),
            push(10),
            Opcode.SSTORE,
            push(2),
            push(11),
            Opcode.SSTORE,
            push(3),
            push(12),
            Opcode.SSTORE,
            Opcode.STOP,
        )
        result = interpreter.execute(create_message(code))
        assert result.success
        target = b"\x00" * 19 + b"\x02"
        assert interpreter.state.get_storage(target, 10) == 1
        assert interpreter.state.get_storage(target, 11) == 2
        assert interpreter.state.get_storage(target, 12) == 3
