"""Tests for EIP-3855 PUSH0 opcode in Shanghai fork.

EIP-3855: PUSH0 Instruction
- New opcode 0x5F that pushes the value 0 onto the stack
- Gas cost: 2 (G_BASE)
- More efficient than PUSH1 0x00 which costs 3 gas
"""

import pytest

from ethereum.common.types import Account, Environment, Opcode, State, Transaction
from ethereum.shanghai.fork import state_transition
from ethereum.shanghai.vm.interpreter import ShanghaiInterpreter, ShanghaiGasSchedule
from tests.conftest import assemble, push, create_message


@pytest.fixture
def state():
    """Create empty state."""
    return State()


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
        number=17000000,  # Shanghai block
        gas_limit=10_000_000,
        gas_price=1,
        timestamp=1000000,
        difficulty=0,  # Post-merge
    )


class TestPush0Opcode:
    """Tests for PUSH0 opcode behavior."""

    def test_push0_pushes_zero(self, state, env):
        """Test PUSH0 pushes 0 onto the stack."""
        interpreter = ShanghaiInterpreter(state, env)

        # PUSH0, PUSH1 1, ADD, STOP
        # Result should be 0 + 1 = 1
        code = assemble(
            Opcode.PUSH0,
            push(1),
            Opcode.ADD,
            Opcode.STOP,
        )

        result = interpreter.execute(create_message(code))
        assert result.success

    def test_push0_gas_cost(self, state, env):
        """Test PUSH0 costs 2 gas (G_BASE)."""
        interpreter = ShanghaiInterpreter(state, env)

        # Just PUSH0 and STOP
        code = bytes([Opcode.PUSH0, Opcode.STOP])

        result = interpreter.execute(create_message(code, gas=100))
        assert result.success
        # PUSH0 costs 2
        assert result.gas_used == 2

    def test_push0_cheaper_than_push1(self, state, env):
        """Test PUSH0 is cheaper than PUSH1 0."""
        interpreter = ShanghaiInterpreter(state, env)

        # Using PUSH0
        code_push0 = bytes([Opcode.PUSH0, Opcode.STOP])
        result_push0 = interpreter.execute(create_message(code_push0, gas=100))

        # Using PUSH1 0
        code_push1 = bytes([0x60, 0x00, Opcode.STOP])  # PUSH1 0x00
        result_push1 = interpreter.execute(create_message(code_push1, gas=100))

        assert result_push0.success
        assert result_push1.success
        # PUSH0 (2) < PUSH1 (3)
        assert result_push0.gas_used < result_push1.gas_used
        assert result_push0.gas_used == 2
        assert result_push1.gas_used == 3

    def test_push0_multiple(self, state, env):
        """Test multiple PUSH0 operations."""
        interpreter = ShanghaiInterpreter(state, env)

        # Push three zeros
        code = bytes([
            Opcode.PUSH0,
            Opcode.PUSH0,
            Opcode.PUSH0,
            Opcode.STOP,
        ])

        result = interpreter.execute(create_message(code, gas=100))
        assert result.success
        # 3 * PUSH0 (2) = 6
        assert result.gas_used == 6

    def test_push0_in_arithmetic(self, state, env):
        """Test PUSH0 works correctly in arithmetic operations."""
        interpreter = ShanghaiInterpreter(state, env)

        # 5 + 0 = 5, then 5 * 0 = 0
        code = assemble(
            Opcode.PUSH0,     # Push 0
            push(5),          # Push 5
            Opcode.ADD,       # 5 + 0 = 5
            Opcode.PUSH0,     # Push 0
            Opcode.MUL,       # 5 * 0 = 0
            Opcode.STOP,
        )

        result = interpreter.execute(create_message(code))
        assert result.success

    def test_push0_as_memory_offset(self, state, env):
        """Test PUSH0 can be used as memory offset."""
        interpreter = ShanghaiInterpreter(state, env)

        # Store 0x42 at memory[0] using PUSH0 for offset
        code = assemble(
            push(0x42),       # value
            Opcode.PUSH0,     # offset (0)
            Opcode.MSTORE,    # Store at memory[0]
            push(32),         # size
            Opcode.PUSH0,     # offset (0)
            Opcode.RETURN,    # Return memory[0:32]
        )

        result = interpreter.execute(create_message(code))
        assert result.success
        assert len(result.return_data) == 32
        assert result.return_data[-1] == 0x42

    def test_push0_as_storage_key(self, state, env):
        """Test PUSH0 can be used as storage key."""
        interpreter = ShanghaiInterpreter(state, env)
        target = b"\x00" * 19 + b"\x02"

        # Store value 123 at storage[0] using PUSH0
        code = assemble(
            push(123),        # value
            Opcode.PUSH0,     # key (0)
            Opcode.SSTORE,
            Opcode.STOP,
        )

        result = interpreter.execute(create_message(code, target=target))
        assert result.success
        assert interpreter.state.get_storage(target, 0) == 123


class TestPush0InContractCreation:
    """Tests for PUSH0 in contract creation."""

    def test_push0_in_init_code(self, funded_state, env):
        """Test PUSH0 works in contract init code."""
        sender = b"\x00" * 19 + b"\x01"

        # Init code using PUSH0
        # PUSH0, PUSH0, MSTORE, PUSH1 32, PUSH0, RETURN
        init_code = bytes([
            Opcode.PUSH0,     # Push 0 (value)
            Opcode.PUSH0,     # Push 0 (offset)
            0x52,             # MSTORE
            0x60, 0x20,       # PUSH1 32
            Opcode.PUSH0,     # Push 0 (offset)
            0xF3,             # RETURN
        ])

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
        # Deployed code should be 32 zero bytes
        deployed = new_state.get_code(result.created_address)
        assert deployed == b"\x00" * 32

    def test_push0_in_deployed_code(self, funded_state, env):
        """Test calling contract with PUSH0 in deployed code."""
        contract = b"\x00" * 19 + b"\x02"

        # Contract code using PUSH0: returns 0
        # PUSH0, PUSH0, MSTORE, PUSH1 32, PUSH0, RETURN
        code = bytes([
            Opcode.PUSH0,
            Opcode.PUSH0,
            0x52,        # MSTORE
            0x60, 0x20,  # PUSH1 32
            Opcode.PUSH0,
            0xF3,        # RETURN
        ])
        funded_state.set_code(contract, code)

        tx = Transaction(
            sender=b"\x00" * 19 + b"\x01",
            to=contract,
            value=0,
            data=b"",
            gas=100000,
            gas_price=1,
            nonce=0,
        )

        new_state, result = state_transition(funded_state, tx, env)

        assert result.success
        assert result.return_data == b"\x00" * 32


class TestShanghaiGasSchedule:
    """Tests for Shanghai gas schedule."""

    def test_push0_gas_constant(self):
        """Test PUSH0 gas constant is defined."""
        assert ShanghaiGasSchedule.G_PUSH0 == 2
        assert ShanghaiGasSchedule.G_PUSH0 == ShanghaiGasSchedule.G_BASE


class TestShanghaiStateTransition:
    """Tests for Shanghai state transition."""

    def test_eip3860_initcode_limit(self, funded_state, env):
        """Test EIP-3860 initcode size limit."""
        sender = b"\x00" * 19 + b"\x01"

        # Initcode larger than 49152 bytes (2 * MAX_CODE_SIZE)
        large_initcode = b"\x00" * 50000

        tx = Transaction(
            sender=sender,
            to=None,
            value=0,
            data=large_initcode,
            gas=10_000_000,
            gas_price=1,
            nonce=0,
        )

        new_state, result = state_transition(funded_state, tx, env)

        assert not result.success
        assert "initcode" in result.error.lower() or "large" in result.error.lower()

    def test_eip3860_initcode_gas(self, funded_state, env):
        """Test EIP-3860 initcode gas metering."""
        sender = b"\x00" * 19 + b"\x01"

        # Small initcode that just returns
        init_code = bytes([0x00])  # STOP

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
        # Gas should include initcode word cost
        # Intrinsic + initcode gas + execution
        assert result.gas_used > 53000  # Base create cost

    def test_code_size_limit(self, funded_state, env):
        """Test EIP-170 code size limit is enforced."""
        sender = b"\x00" * 19 + b"\x01"

        # Init code that returns code larger than 24576 bytes
        # PUSH2 size, PUSH1 0, RETURN
        large_size = 25000
        init_code = bytes([
            0x61,                          # PUSH2
            (large_size >> 8) & 0xFF,      # size high byte
            large_size & 0xFF,             # size low byte
            0x60, 0x00,                    # PUSH1 0
            0xF3,                          # RETURN
        ])

        tx = Transaction(
            sender=sender,
            to=None,
            value=0,
            data=init_code,
            gas=10_000_000,
            gas_price=1,
            nonce=0,
        )

        new_state, result = state_transition(funded_state, tx, env)

        assert not result.success
        assert "code size" in result.error.lower() or "limit" in result.error.lower()
