"""Tests for stack operations in Frontier EVM."""

import pytest

from ethereum.common.types import Opcode, State, Environment
from ethereum.frontier.vm.interpreter import Interpreter
from ethereum.frontier.vm.stack import Stack, StackOverflowError, StackUnderflowError
from tests.conftest import assemble, push, create_message


class TestStack:
    """Tests for the Stack class directly."""

    def test_push_pop(self):
        """Test basic push and pop."""
        stack = Stack()
        stack.push(42)
        assert stack.pop() == 42

    def test_stack_underflow(self):
        """Test popping from empty stack raises error."""
        stack = Stack()
        with pytest.raises(StackUnderflowError):
            stack.pop()

    def test_stack_overflow(self):
        """Test exceeding stack depth limit."""
        stack = Stack()
        for i in range(1024):
            stack.push(i)
        with pytest.raises(StackOverflowError):
            stack.push(1024)

    def test_peek(self):
        """Test peeking at stack values."""
        stack = Stack()
        stack.push(1)
        stack.push(2)
        stack.push(3)
        assert stack.peek(0) == 3
        assert stack.peek(1) == 2
        assert stack.peek(2) == 1

    def test_dup(self):
        """Test DUP operation."""
        stack = Stack()
        stack.push(10)
        stack.push(20)
        stack.push(30)
        stack.dup(1)  # DUP1 duplicates top
        assert stack.pop() == 30
        assert stack.pop() == 30

    def test_swap(self):
        """Test SWAP operation."""
        stack = Stack()
        stack.push(1)
        stack.push(2)
        stack.swap(1)  # SWAP1 swaps top two
        assert stack.pop() == 1
        assert stack.pop() == 2

    def test_u256_overflow_wraps(self):
        """Test that values exceeding U256 wrap around."""
        stack = Stack()
        stack.push(2**256)  # Should wrap to 0
        assert stack.pop() == 0

        stack.push(2**256 + 5)  # Should wrap to 5
        assert stack.pop() == 5


class TestPushOpcodes:
    """Tests for PUSH1-PUSH32 opcodes."""

    @pytest.fixture
    def interpreter(self):
        return Interpreter(State(), Environment())

    def test_push1(self, interpreter):
        """Test PUSH1 opcode."""
        code = assemble(push(0xFF), Opcode.STOP)
        result = interpreter.execute(create_message(code))
        assert result.success

    def test_push32(self, interpreter):
        """Test PUSH32 with max value."""
        max_val = 2**256 - 1
        code = assemble(push(max_val, 32), Opcode.STOP)
        result = interpreter.execute(create_message(code))
        assert result.success

    def test_push_truncated(self, interpreter):
        """Test PUSH at end of code is zero-padded."""
        # PUSH2 but only 1 byte available
        code = bytes([0x61, 0xFF])  # PUSH2 0xFF (missing second byte)
        result = interpreter.execute(create_message(code))
        assert result.success


class TestDupOpcodes:
    """Tests for DUP1-DUP16 opcodes."""

    @pytest.fixture
    def interpreter(self):
        return Interpreter(State(), Environment())

    def test_dup1(self, interpreter):
        """Test DUP1 duplicates top of stack."""
        code = assemble(
            push(42),
            Opcode.DUP1,
            Opcode.STOP,
        )
        result = interpreter.execute(create_message(code))
        assert result.success

    def test_dup16(self, interpreter):
        """Test DUP16 duplicates 16th item."""
        # Push 16 values, then DUP16
        code = bytearray()
        for i in range(16):
            code.extend(push(i))
        code.append(Opcode.DUP16)
        code.append(Opcode.STOP)
        result = interpreter.execute(create_message(bytes(code)))
        assert result.success

    def test_dup_underflow(self, interpreter):
        """Test DUP with insufficient stack depth fails."""
        code = assemble(
            push(1),
            Opcode.DUP2,  # Only 1 item on stack
            Opcode.STOP,
        )
        result = interpreter.execute(create_message(code))
        assert not result.success
        assert "underflow" in result.error.lower()


class TestSwapOpcodes:
    """Tests for SWAP1-SWAP16 opcodes."""

    @pytest.fixture
    def interpreter(self):
        return Interpreter(State(), Environment())

    def test_swap1(self, interpreter):
        """Test SWAP1 swaps top two items."""
        code = assemble(
            push(1),
            push(2),
            Opcode.SWAP1,
            Opcode.STOP,
        )
        result = interpreter.execute(create_message(code))
        assert result.success

    def test_swap16(self, interpreter):
        """Test SWAP16 swaps top with 17th item."""
        code = bytearray()
        for i in range(17):
            code.extend(push(i))
        code.append(Opcode.SWAP16)
        code.append(Opcode.STOP)
        result = interpreter.execute(create_message(bytes(code)))
        assert result.success

    def test_swap_underflow(self, interpreter):
        """Test SWAP with insufficient stack depth fails."""
        code = assemble(
            push(1),
            Opcode.SWAP1,  # Only 1 item on stack
            Opcode.STOP,
        )
        result = interpreter.execute(create_message(code))
        assert not result.success


class TestPopOpcode:
    """Tests for POP opcode."""

    @pytest.fixture
    def interpreter(self):
        return Interpreter(State(), Environment())

    def test_pop(self, interpreter):
        """Test POP removes top item."""
        code = assemble(
            push(1),
            push(2),
            Opcode.POP,
            Opcode.STOP,
        )
        result = interpreter.execute(create_message(code))
        assert result.success

    def test_pop_underflow(self, interpreter):
        """Test POP on empty stack fails."""
        code = assemble(Opcode.POP, Opcode.STOP)
        result = interpreter.execute(create_message(code))
        assert not result.success
