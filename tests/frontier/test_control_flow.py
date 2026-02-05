"""Tests for control flow operations in Frontier EVM."""

import pytest

from ethereum.common.types import Environment, Opcode, State
from ethereum.frontier.vm.interpreter import Interpreter
from tests.conftest import assemble, create_message, push


@pytest.fixture
def interpreter():
    return Interpreter(State(), Environment())


class TestJump:
    """Tests for JUMP opcode."""

    def test_jump_valid(self, interpreter):
        """Test jumping to valid JUMPDEST."""
        # PUSH1 4, JUMP, INVALID, JUMPDEST, STOP
        code = assemble(
            push(4),
            Opcode.JUMP,
            Opcode.INVALID,
            Opcode.JUMPDEST,
            Opcode.STOP,
        )
        result = interpreter.execute(create_message(code))
        assert result.success

    def test_jump_invalid_dest(self, interpreter):
        """Test jumping to invalid destination fails."""
        # Try to jump to non-JUMPDEST
        code = assemble(
            push(3),  # Jump to STOP (not JUMPDEST)
            Opcode.JUMP,
            Opcode.INVALID,
            Opcode.STOP,
        )
        result = interpreter.execute(create_message(code))
        assert not result.success
        assert "invalid jump" in result.error.lower()

    def test_jump_to_push_data(self, interpreter):
        """Test jumping into PUSH data fails."""
        # PUSH2 0x5B5B (contains JUMPDEST bytes), jump to middle
        code = bytes(
            [
                0x61,
                0x5B,
                0x5B,  # PUSH2 0x5B5B
                0x60,
                0x01,  # PUSH1 1 (try to jump here)
                0x56,  # JUMP
                0x00,  # STOP
            ]
        )
        result = interpreter.execute(create_message(code))
        assert not result.success

    def test_jump_out_of_bounds(self, interpreter):
        """Test jumping beyond code length fails."""
        code = assemble(
            push(100),  # Way beyond code
            Opcode.JUMP,
        )
        result = interpreter.execute(create_message(code))
        assert not result.success


class TestJumpi:
    """Tests for JUMPI (conditional jump) opcode."""

    def test_jumpi_condition_true(self, interpreter):
        """Test JUMPI jumps when condition is non-zero."""
        code = assemble(
            push(1),  # condition (true)
            push(6),  # destination
            Opcode.JUMPI,
            Opcode.INVALID,
            Opcode.JUMPDEST,
            Opcode.STOP,
        )
        result = interpreter.execute(create_message(code))
        assert result.success

    def test_jumpi_condition_false(self, interpreter):
        """Test JUMPI falls through when condition is zero."""
        code = assemble(
            push(0),  # condition (false)
            push(7),  # destination (won't jump)
            Opcode.JUMPI,
            Opcode.STOP,  # Should reach here
            Opcode.INVALID,
            Opcode.JUMPDEST,
        )
        result = interpreter.execute(create_message(code))
        assert result.success

    def test_jumpi_large_condition(self, interpreter):
        """Test JUMPI with large non-zero condition."""
        # PUSH32 (33 bytes) + PUSH1 (2 bytes) + JUMPI (1 byte) + INVALID (1 byte) = 37
        # JUMPDEST is at position 37
        code = assemble(
            push(2**255, 32),  # Large non-zero (true) - 33 bytes
            push(37),  # destination - 2 bytes
            Opcode.JUMPI,  # 1 byte
            Opcode.INVALID,  # 1 byte (skipped by jump)
            Opcode.JUMPDEST,  # at position 37
            Opcode.STOP,
        )
        result = interpreter.execute(create_message(code))
        assert result.success


class TestJumpdest:
    """Tests for JUMPDEST opcode."""

    def test_jumpdest_as_noop(self, interpreter):
        """Test JUMPDEST acts as no-op when executed normally."""
        code = assemble(
            Opcode.JUMPDEST,
            Opcode.JUMPDEST,
            Opcode.JUMPDEST,
            Opcode.STOP,
        )
        result = interpreter.execute(create_message(code))
        assert result.success

    def test_jumpdest_gas(self, interpreter):
        """Test JUMPDEST costs 1 gas."""
        code = assemble(Opcode.JUMPDEST, Opcode.STOP)
        result = interpreter.execute(create_message(code, gas=1))
        assert result.success


class TestPc:
    """Tests for PC (program counter) opcode."""

    def test_pc_start(self, interpreter):
        """Test PC at start of code."""
        code = assemble(Opcode.PC, Opcode.STOP)
        result = interpreter.execute(create_message(code))
        assert result.success

    def test_pc_after_push(self, interpreter):
        """Test PC after PUSH instruction."""
        # PUSH1 0, PC (should be 2)
        code = assemble(push(0), Opcode.PC, Opcode.STOP)
        result = interpreter.execute(create_message(code))
        assert result.success


class TestStop:
    """Tests for STOP opcode."""

    def test_stop_ends_execution(self, interpreter):
        """Test STOP terminates execution successfully."""
        code = assemble(Opcode.STOP, Opcode.INVALID)
        result = interpreter.execute(create_message(code))
        assert result.success
        assert result.return_data == b""


class TestReturn:
    """Tests for RETURN opcode."""

    def test_return_empty(self, interpreter):
        """Test RETURN with no data."""
        code = assemble(
            push(0),  # size
            push(0),  # offset
            Opcode.RETURN,
        )
        result = interpreter.execute(create_message(code))
        assert result.success
        assert result.return_data == b""

    def test_return_with_data(self, interpreter):
        """Test RETURN with data in memory."""
        code = assemble(
            push(0x42),
            push(0),
            Opcode.MSTORE,  # Store 0x42 at memory[0]
            push(32),  # size
            push(0),  # offset
            Opcode.RETURN,
        )
        result = interpreter.execute(create_message(code))
        assert result.success
        assert len(result.return_data) == 32
        assert result.return_data[-1] == 0x42


class TestRevert:
    """Tests for REVERT opcode."""

    def test_revert(self, interpreter):
        """Test REVERT ends execution unsuccessfully."""
        code = assemble(
            push(0),  # size
            push(0),  # offset
            Opcode.REVERT,
        )
        result = interpreter.execute(create_message(code))
        assert not result.success

    def test_revert_with_data(self, interpreter):
        """Test REVERT returns data."""
        code = assemble(
            push(0xFF),
            push(0),
            Opcode.MSTORE,
            push(32),
            push(0),
            Opcode.REVERT,
        )
        result = interpreter.execute(create_message(code))
        assert not result.success
        assert len(result.return_data) == 32


class TestInvalid:
    """Tests for INVALID opcode."""

    def test_invalid_fails(self, interpreter):
        """Test INVALID opcode causes failure."""
        code = assemble(Opcode.INVALID)
        result = interpreter.execute(create_message(code))
        assert not result.success
        assert "invalid" in result.error.lower()


class TestGas:
    """Tests for GAS opcode."""

    def test_gas_returns_remaining(self, interpreter):
        """Test GAS returns remaining gas."""
        code = assemble(Opcode.GAS, Opcode.STOP)
        result = interpreter.execute(create_message(code, gas=10000))
        assert result.success
        # GAS costs 2, so remaining should be less than initial
        assert result.gas_remaining < 10000
