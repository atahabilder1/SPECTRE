"""Tests for EIP-2 changes in Homestead fork.

EIP-2: Homestead Hard-fork Changes
- Increased gas cost for CREATE
- Contract creation failure behavior changes
"""

import pytest

from ethereum.common.types import Account, Environment, Opcode, State, Transaction
from ethereum.homestead.fork import state_transition
from ethereum.homestead.vm.interpreter import HomesteadGasSchedule, HomesteadInterpreter
from tests.conftest import create_message


@pytest.fixture
def funded_state():
    """Create state with funded sender."""
    state = State()
    sender = b"\x00" * 19 + b"\x01"
    state.set_account(
        sender,
        Account(nonce=0, balance=10**18, code=b"", storage={}),
    )
    return state


@pytest.fixture
def env():
    """Create default environment."""
    return Environment(
        coinbase=b"\x00" * 19 + b"\xff",
        number=1150000,  # Homestead block
        gas_limit=10_000_000,
        gas_price=1,
        timestamp=1000000,
        difficulty=1,
    )


class TestHomesteadGasSchedule:
    """Tests for Homestead gas schedule."""

    def test_create_gas_unchanged(self):
        """Test CREATE gas cost in Homestead."""
        assert HomesteadGasSchedule.G_CREATE == 32000


class TestHomesteadInterpreter:
    """Tests for Homestead interpreter."""

    def test_push0_not_supported(self, funded_state, env):
        """Test PUSH0 is not supported in Homestead."""
        interpreter = HomesteadInterpreter(funded_state, env)

        # PUSH0 opcode
        code = bytes([Opcode.PUSH0, Opcode.STOP])
        result = interpreter.execute(create_message(code))

        assert not result.success
        assert "push0" in result.error.lower() or "not supported" in result.error.lower()


class TestEIP2ContractCreation:
    """Tests for EIP-2 contract creation behavior."""

    def test_successful_create(self, funded_state, env):
        """Test successful contract creation."""
        sender = b"\x00" * 19 + b"\x01"

        # Simple contract that returns 0x42
        init_code = bytes(
            [
                0x60,
                0x42,  # PUSH1 0x42
                0x60,
                0x00,  # PUSH1 0
                0x53,  # MSTORE8
                0x60,
                0x01,  # PUSH1 1
                0x60,
                0x00,  # PUSH1 0
                0xF3,  # RETURN
            ]
        )

        tx = Transaction(
            sender=sender,
            to=None,
            value=0,
            data=init_code,
            gas=100000,
            gas_price=1,
            nonce=0,
        )

        new_state, result = state_transition(funded_state, tx, env)

        assert result.success
        assert result.created_address is not None
        # Contract should have deployed code
        deployed_code = new_state.get_code(result.created_address)
        assert deployed_code == bytes([0x42])

    def test_create_with_value(self, funded_state, env):
        """Test contract creation with value transfer."""
        sender = b"\x00" * 19 + b"\x01"

        # Empty contract
        init_code = bytes([0x00])  # STOP

        tx = Transaction(
            sender=sender,
            to=None,
            value=1000,
            data=init_code,
            gas=100000,
            gas_price=1,
            nonce=0,
        )

        new_state, result = state_transition(funded_state, tx, env)

        assert result.success
        assert result.created_address is not None
        # New contract should have received value
        assert new_state.get_balance(result.created_address) == 1000

    def test_create_out_of_gas_deployment(self, funded_state, env):
        """Test CREATE fails when out of gas for code deployment."""
        sender = b"\x00" * 19 + b"\x01"

        # Contract that returns large code
        init_code = bytes(
            [
                0x60,
                0xFF,  # PUSH1 255
                0x60,
                0x00,  # PUSH1 0
                0xF3,  # RETURN (returns 255 zero bytes)
            ]
        )

        tx = Transaction(
            sender=sender,
            to=None,
            value=0,
            data=init_code,
            gas=53000 + 100,  # Just enough for intrinsic + init, not deployment
            gas_price=1,
            nonce=0,
        )

        new_state, result = state_transition(funded_state, tx, env)

        # In Homestead, insufficient gas for deployment should fail
        # (behavior differs from Frontier in edge cases)
        assert not result.success or result.created_address is None

    def test_create_revert_in_constructor(self, funded_state, env):
        """Test CREATE with reverting constructor."""
        sender = b"\x00" * 19 + b"\x01"

        # Constructor that reverts
        init_code = bytes(
            [
                0x60,
                0x00,  # PUSH1 0
                0x60,
                0x00,  # PUSH1 0
                0xFD,  # REVERT
            ]
        )

        tx = Transaction(
            sender=sender,
            to=None,
            value=0,
            data=init_code,
            gas=100000,
            gas_price=1,
            nonce=0,
        )

        new_state, result = state_transition(funded_state, tx, env)

        assert not result.success
        assert result.created_address is None


class TestHomesteadStateTransition:
    """Tests for Homestead state transition."""

    def test_simple_transfer(self, funded_state, env):
        """Test simple value transfer works."""
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
        assert new_state.get_balance(recipient) == 1000

    def test_nonce_increment(self, funded_state, env):
        """Test sender nonce is incremented."""
        sender = b"\x00" * 19 + b"\x01"

        tx = Transaction(
            sender=sender,
            to=b"\x00" * 19 + b"\x02",
            value=0,
            data=b"",
            gas=21000,
            gas_price=1,
            nonce=0,
        )

        new_state, result = state_transition(funded_state, tx, env)

        assert result.success
        assert new_state.get_account(sender).nonce == 1

    def test_contract_call(self, funded_state, env):
        """Test calling a contract."""
        sender = b"\x00" * 19 + b"\x01"
        contract = b"\x00" * 19 + b"\x02"

        # Contract that returns caller
        # CALLER, PUSH1 0, MSTORE, PUSH1 32, PUSH1 0, RETURN
        code = bytes([0x33, 0x60, 0x00, 0x52, 0x60, 0x20, 0x60, 0x00, 0xF3])
        funded_state.set_code(contract, code)

        tx = Transaction(
            sender=sender,
            to=contract,
            value=0,
            data=b"",
            gas=100000,
            gas_price=1,
            nonce=0,
        )

        new_state, result = state_transition(funded_state, tx, env)

        assert result.success
        assert len(result.return_data) == 32
        # Caller should be sender address (padded to 32 bytes)
        expected = b"\x00" * 12 + sender
        assert result.return_data == expected
