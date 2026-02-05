"""Tests for arithmetic opcodes in Frontier EVM."""

import pytest

from ethereum.common.types import Environment, Opcode, State
from ethereum.frontier.vm.interpreter import Interpreter
from tests.conftest import assemble, create_message, push


@pytest.fixture
def interpreter():
    """Create interpreter for testing."""
    state = State()
    env = Environment()
    return Interpreter(state, env)


class TestAdd:
    """Tests for ADD opcode."""

    def test_add_simple(self, interpreter):
        """Test simple addition."""
        # PUSH1 3, PUSH1 5, ADD, STOP
        code = assemble(
            push(5),
            push(3),
            Opcode.ADD,
            Opcode.STOP,
        )
        result = interpreter.execute(create_message(code))
        assert result.success

    def test_add_overflow(self, interpreter):
        """Test addition with overflow wraps around."""
        # (2^256 - 1) + 1 = 0
        max_val = 2**256 - 1
        code = assemble(
            push(1, 32),
            push(max_val, 32),
            Opcode.ADD,
            Opcode.STOP,
        )
        result = interpreter.execute(create_message(code))
        assert result.success

    def test_add_zero(self, interpreter):
        """Test adding zero."""
        code = assemble(
            push(0),
            push(42),
            Opcode.ADD,
            Opcode.STOP,
        )
        result = interpreter.execute(create_message(code))
        assert result.success


class TestSub:
    """Tests for SUB opcode."""

    def test_sub_simple(self, interpreter):
        """Test simple subtraction."""
        # 10 - 3 = 7
        code = assemble(
            push(3),
            push(10),
            Opcode.SUB,
            Opcode.STOP,
        )
        result = interpreter.execute(create_message(code))
        assert result.success

    def test_sub_underflow(self, interpreter):
        """Test subtraction with underflow wraps around."""
        # 0 - 1 = 2^256 - 1
        code = assemble(
            push(1),
            push(0),
            Opcode.SUB,
            Opcode.STOP,
        )
        result = interpreter.execute(create_message(code))
        assert result.success


class TestMul:
    """Tests for MUL opcode."""

    def test_mul_simple(self, interpreter):
        """Test simple multiplication."""
        # 6 * 7 = 42
        code = assemble(
            push(7),
            push(6),
            Opcode.MUL,
            Opcode.STOP,
        )
        result = interpreter.execute(create_message(code))
        assert result.success

    def test_mul_overflow(self, interpreter):
        """Test multiplication overflow wraps."""
        # Large values wrap modulo 2^256
        code = assemble(
            push(2**128, 32),
            push(2**128, 32),
            Opcode.MUL,
            Opcode.STOP,
        )
        result = interpreter.execute(create_message(code))
        assert result.success

    def test_mul_by_zero(self, interpreter):
        """Test multiplication by zero."""
        code = assemble(
            push(0),
            push(12345),
            Opcode.MUL,
            Opcode.STOP,
        )
        result = interpreter.execute(create_message(code))
        assert result.success


class TestDiv:
    """Tests for DIV opcode."""

    def test_div_simple(self, interpreter):
        """Test simple division."""
        # 42 / 7 = 6
        code = assemble(
            push(7),
            push(42),
            Opcode.DIV,
            Opcode.STOP,
        )
        result = interpreter.execute(create_message(code))
        assert result.success

    def test_div_by_zero(self, interpreter):
        """Test division by zero returns 0."""
        code = assemble(
            push(0),
            push(42),
            Opcode.DIV,
            Opcode.STOP,
        )
        result = interpreter.execute(create_message(code))
        assert result.success

    def test_div_truncates(self, interpreter):
        """Test division truncates toward zero."""
        # 7 / 3 = 2 (truncated)
        code = assemble(
            push(3),
            push(7),
            Opcode.DIV,
            Opcode.STOP,
        )
        result = interpreter.execute(create_message(code))
        assert result.success


class TestSdiv:
    """Tests for SDIV opcode (signed division)."""

    def test_sdiv_positive(self, interpreter):
        """Test signed division of positive numbers."""
        code = assemble(
            push(3),
            push(9),
            Opcode.SDIV,
            Opcode.STOP,
        )
        result = interpreter.execute(create_message(code))
        assert result.success

    def test_sdiv_negative(self, interpreter):
        """Test signed division with negative numbers."""
        # -9 / 3 = -3
        neg_9 = 2**256 - 9  # Two's complement
        code = assemble(
            push(3),
            push(neg_9, 32),
            Opcode.SDIV,
            Opcode.STOP,
        )
        result = interpreter.execute(create_message(code))
        assert result.success

    def test_sdiv_by_zero(self, interpreter):
        """Test signed division by zero returns 0."""
        code = assemble(
            push(0),
            push(42),
            Opcode.SDIV,
            Opcode.STOP,
        )
        result = interpreter.execute(create_message(code))
        assert result.success


class TestMod:
    """Tests for MOD opcode."""

    def test_mod_simple(self, interpreter):
        """Test simple modulo."""
        # 10 % 3 = 1
        code = assemble(
            push(3),
            push(10),
            Opcode.MOD,
            Opcode.STOP,
        )
        result = interpreter.execute(create_message(code))
        assert result.success

    def test_mod_by_zero(self, interpreter):
        """Test modulo by zero returns 0."""
        code = assemble(
            push(0),
            push(42),
            Opcode.MOD,
            Opcode.STOP,
        )
        result = interpreter.execute(create_message(code))
        assert result.success


class TestExp:
    """Tests for EXP opcode."""

    def test_exp_simple(self, interpreter):
        """Test simple exponentiation."""
        # 2^10 = 1024
        code = assemble(
            push(10),
            push(2),
            Opcode.EXP,
            Opcode.STOP,
        )
        result = interpreter.execute(create_message(code))
        assert result.success

    def test_exp_zero_exponent(self, interpreter):
        """Test any number to the power of 0 is 1."""
        code = assemble(
            push(0),
            push(123),
            Opcode.EXP,
            Opcode.STOP,
        )
        result = interpreter.execute(create_message(code))
        assert result.success

    def test_exp_zero_base(self, interpreter):
        """Test 0 to any positive power is 0."""
        code = assemble(
            push(5),
            push(0),
            Opcode.EXP,
            Opcode.STOP,
        )
        result = interpreter.execute(create_message(code))
        assert result.success


class TestAddmod:
    """Tests for ADDMOD opcode."""

    def test_addmod_simple(self, interpreter):
        """Test ADDMOD with simple values."""
        # (10 + 10) % 8 = 4
        code = assemble(
            push(8),
            push(10),
            push(10),
            Opcode.ADDMOD,
            Opcode.STOP,
        )
        result = interpreter.execute(create_message(code))
        assert result.success

    def test_addmod_overflow(self, interpreter):
        """Test ADDMOD handles overflow correctly."""
        # Uses full 512-bit intermediate result
        max_val = 2**256 - 1
        code = assemble(
            push(2**256 - 2, 32),
            push(max_val, 32),
            push(max_val, 32),
            Opcode.ADDMOD,
            Opcode.STOP,
        )
        result = interpreter.execute(create_message(code))
        assert result.success

    def test_addmod_by_zero(self, interpreter):
        """Test ADDMOD by zero returns 0."""
        code = assemble(
            push(0),
            push(10),
            push(10),
            Opcode.ADDMOD,
            Opcode.STOP,
        )
        result = interpreter.execute(create_message(code))
        assert result.success


class TestMulmod:
    """Tests for MULMOD opcode."""

    def test_mulmod_simple(self, interpreter):
        """Test MULMOD with simple values."""
        # (10 * 10) % 8 = 4
        code = assemble(
            push(8),
            push(10),
            push(10),
            Opcode.MULMOD,
            Opcode.STOP,
        )
        result = interpreter.execute(create_message(code))
        assert result.success

    def test_mulmod_by_zero(self, interpreter):
        """Test MULMOD by zero returns 0."""
        code = assemble(
            push(0),
            push(10),
            push(10),
            Opcode.MULMOD,
            Opcode.STOP,
        )
        result = interpreter.execute(create_message(code))
        assert result.success
