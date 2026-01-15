"""Tests for state transition function in Frontier fork."""

import pytest

from ethereum.common.types import Account, Environment, State, Transaction, ZERO_ADDRESS
from ethereum.frontier.fork import state_transition, validate_transaction


@pytest.fixture
def funded_state():
    """Create state with a funded sender."""
    state = State()
    sender = b"\x00" * 19 + b"\x01"
    state.set_account(
        sender,
        Account(
            nonce=0,
            balance=10**18,  # 1 ETH
            code=b"",
            storage={},
        ),
    )
    return state


@pytest.fixture
def env():
    """Create default environment."""
    return Environment(
        coinbase=b"\x00" * 19 + b"\xff",
        number=1000,
        gas_limit=10_000_000,
        gas_price=1,
        timestamp=1000000,
        difficulty=1,
    )


class TestValidateTransaction:
    """Tests for transaction validation."""

    def test_valid_transaction(self, funded_state):
        """Test valid transaction passes validation."""
        tx = Transaction(
            sender=b"\x00" * 19 + b"\x01",
            to=b"\x00" * 19 + b"\x02",
            value=1000,
            data=b"",
            gas=21000,
            gas_price=1,
            nonce=0,
        )
        assert validate_transaction(tx, funded_state) is None

    def test_invalid_nonce(self, funded_state):
        """Test wrong nonce fails validation."""
        tx = Transaction(
            sender=b"\x00" * 19 + b"\x01",
            to=b"\x00" * 19 + b"\x02",
            value=0,
            data=b"",
            gas=21000,
            gas_price=1,
            nonce=1,  # Should be 0
        )
        error = validate_transaction(tx, funded_state)
        assert error is not None
        assert "nonce" in error.lower()

    def test_insufficient_gas(self, funded_state):
        """Test insufficient gas fails validation."""
        tx = Transaction(
            sender=b"\x00" * 19 + b"\x01",
            to=b"\x00" * 19 + b"\x02",
            value=0,
            data=b"",
            gas=100,  # Less than intrinsic gas
            gas_price=1,
            nonce=0,
        )
        error = validate_transaction(tx, funded_state)
        assert error is not None
        assert "gas" in error.lower()

    def test_insufficient_balance(self, funded_state):
        """Test insufficient balance fails validation."""
        tx = Transaction(
            sender=b"\x00" * 19 + b"\x01",
            to=b"\x00" * 19 + b"\x02",
            value=10**19,  # More than balance
            data=b"",
            gas=21000,
            gas_price=1,
            nonce=0,
        )
        error = validate_transaction(tx, funded_state)
        assert error is not None
        assert "balance" in error.lower()


class TestStateTransition:
    """Tests for state transition function."""

    def test_simple_transfer(self, funded_state, env):
        """Test simple value transfer."""
        sender = b"\x00" * 19 + b"\x01"
        recipient = b"\x00" * 19 + b"\x02"

        tx = Transaction(
            sender=sender,
            to=recipient,
            value=1000,
            data=b"",
            gas=21000,
            gas_price=1,
            nonce=0,
        )

        new_state, result = state_transition(funded_state, tx, env)

        assert result.success
        assert result.gas_used == 21000
        assert new_state.get_balance(recipient) == 1000
        assert new_state.get_account(sender).nonce == 1

    def test_contract_creation(self, funded_state, env):
        """Test contract creation."""
        sender = b"\x00" * 19 + b"\x01"

        # Simple contract: PUSH1 0x42, PUSH1 0, MSTORE, PUSH1 32, PUSH1 0, RETURN
        init_code = bytes([
            0x60, 0x42,  # PUSH1 0x42
            0x60, 0x00,  # PUSH1 0
            0x52,        # MSTORE
            0x60, 0x20,  # PUSH1 32
            0x60, 0x00,  # PUSH1 0
            0xF3,        # RETURN
        ])

        tx = Transaction(
            sender=sender,
            to=None,  # Contract creation
            value=0,
            data=init_code,
            gas=100000,
            gas_price=1,
            nonce=0,
        )

        new_state, result = state_transition(funded_state, tx, env)

        assert result.success
        assert result.created_address is not None

    def test_gas_refund(self, funded_state, env):
        """Test unused gas is refunded."""
        sender = b"\x00" * 19 + b"\x01"
        initial_balance = funded_state.get_balance(sender)

        tx = Transaction(
            sender=sender,
            to=b"\x00" * 19 + b"\x02",
            value=0,
            data=b"",
            gas=50000,  # More than needed
            gas_price=1,
            nonce=0,
        )

        new_state, result = state_transition(funded_state, tx, env)

        assert result.success
        # Should only charge for gas actually used
        expected_balance = initial_balance - result.gas_used
        assert new_state.get_balance(sender) == expected_balance

    def test_coinbase_reward(self, funded_state, env):
        """Test coinbase receives gas payment."""
        tx = Transaction(
            sender=b"\x00" * 19 + b"\x01",
            to=b"\x00" * 19 + b"\x02",
            value=0,
            data=b"",
            gas=21000,
            gas_price=10,
            nonce=0,
        )

        new_state, result = state_transition(funded_state, tx, env)

        assert result.success
        coinbase_balance = new_state.get_balance(env.coinbase)
        assert coinbase_balance == result.gas_used * 10

    def test_failed_transaction(self, funded_state, env):
        """Test failed transaction still charges gas."""
        sender = b"\x00" * 19 + b"\x01"

        # Code that reverts
        code = bytes([0xFD])  # REVERT with no args will fail

        tx = Transaction(
            sender=sender,
            to=None,
            value=0,
            data=code,
            gas=100000,
            gas_price=1,
            nonce=0,
        )

        new_state, result = state_transition(funded_state, tx, env)

        # Transaction should fail but gas should be charged
        assert not result.success
        assert result.gas_used > 0


class TestContractCall:
    """Tests for calling contracts."""

    def test_call_empty_account(self, funded_state, env):
        """Test calling empty account succeeds with no code execution."""
        tx = Transaction(
            sender=b"\x00" * 19 + b"\x01",
            to=b"\x00" * 19 + b"\x02",  # Empty account
            value=100,
            data=b"hello",
            gas=30000,
            gas_price=1,
            nonce=0,
        )

        new_state, result = state_transition(funded_state, tx, env)

        assert result.success
        assert new_state.get_balance(b"\x00" * 19 + b"\x02") == 100

    def test_call_contract_with_code(self, funded_state, env):
        """Test calling contract executes its code."""
        contract = b"\x00" * 19 + b"\x02"

        # Contract that stores calldata length in storage slot 0
        # CALLDATASIZE, PUSH1 0, SSTORE, STOP
        code = bytes([0x36, 0x60, 0x00, 0x55, 0x00])
        funded_state.set_code(contract, code)

        tx = Transaction(
            sender=b"\x00" * 19 + b"\x01",
            to=contract,
            value=0,
            data=b"hello world",
            gas=100000,
            gas_price=1,
            nonce=0,
        )

        new_state, result = state_transition(funded_state, tx, env)

        assert result.success
        # Storage slot 0 should contain calldata length (11)
        assert new_state.get_storage(contract, 0) == 11
