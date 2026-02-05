"""Tests for gas calculations in Frontier EVM."""

import pytest

from ethereum.common.types import Environment, Opcode, State
from ethereum.frontier.vm.gas import GasSchedule
from ethereum.frontier.vm.interpreter import Interpreter
from ethereum.frontier.vm.memory import Memory
from tests.conftest import assemble, create_message, push


class TestGasSchedule:
    """Tests for gas schedule calculations."""

    def test_memory_expansion_cost_small(self):
        """Test memory expansion cost for small memory."""
        # First 32 bytes: 3 * 1 + 1^2/512 = 3
        cost = GasSchedule.memory_expansion_cost(0, 1)
        assert cost == 3

    def test_memory_expansion_cost_medium(self):
        """Test memory expansion cost for medium memory."""
        # 10 words: 3 * 10 + 100/512 = 30
        cost = GasSchedule.memory_expansion_cost(0, 10)
        assert cost == 30

    def test_memory_expansion_cost_large(self):
        """Test memory expansion cost for large memory."""
        # The quadratic term becomes significant
        cost = GasSchedule.memory_expansion_cost(0, 100)
        assert cost > 300  # Linear would be 300

    def test_memory_expansion_cost_delta(self):
        """Test memory expansion cost is delta."""
        # Expanding from 10 to 20 words
        full_cost = GasSchedule.memory_expansion_cost(0, 20)
        initial_cost = GasSchedule.memory_expansion_cost(0, 10)
        delta = GasSchedule.memory_expansion_cost(10, 20)
        assert delta == full_cost - initial_cost

    def test_copy_cost(self):
        """Test copy operation gas cost."""
        # 64 bytes = 2 words
        cost = GasSchedule.copy_cost(64)
        assert cost == 6  # 3 * 2

        # Partial word still counts as full word
        cost = GasSchedule.copy_cost(33)
        assert cost == 6  # 3 * 2 (rounds up)

    def test_sha3_cost(self):
        """Test SHA3 gas cost."""
        # 32 bytes = 1 word
        cost = GasSchedule.sha3_cost(32)
        assert cost == 30 + 6  # G_SHA3 + 1 * G_SHA3WORD

        # 64 bytes = 2 words
        cost = GasSchedule.sha3_cost(64)
        assert cost == 30 + 12

    def test_exp_cost_zero(self):
        """Test EXP cost with zero exponent."""
        cost = GasSchedule.exp_cost(0)
        assert cost == 10  # Just G_EXP

    def test_exp_cost_small(self):
        """Test EXP cost with small exponent."""
        cost = GasSchedule.exp_cost(255)
        assert cost == 10 + 10  # G_EXP + 1 byte

    def test_exp_cost_large(self):
        """Test EXP cost with large exponent."""
        cost = GasSchedule.exp_cost(2**64)
        assert cost == 10 + 90  # G_EXP + 9 bytes

    def test_log_cost(self):
        """Test LOG gas cost."""
        # LOG0 with 100 bytes
        cost = GasSchedule.log_cost(100, 0)
        assert cost == 375 + 800  # G_LOG + 100 * G_LOGDATA

        # LOG2 with 50 bytes
        cost = GasSchedule.log_cost(50, 2)
        assert cost == 375 + 400 + 750  # G_LOG + data + 2 topics

    def test_sstore_cost_new(self):
        """Test SSTORE cost for new value."""
        cost = GasSchedule.sstore_cost(0, 100)
        assert cost == 20000  # G_SSET

    def test_sstore_cost_update(self):
        """Test SSTORE cost for updating value."""
        cost = GasSchedule.sstore_cost(50, 100)
        assert cost == 5000  # G_SRESET

    def test_sstore_cost_clear(self):
        """Test SSTORE cost for clearing value."""
        cost = GasSchedule.sstore_cost(100, 0)
        assert cost == 5000  # G_SRESET (refund handled separately)

    def test_transaction_intrinsic_gas(self):
        """Test transaction intrinsic gas calculation."""
        # Empty data, not create
        gas = GasSchedule.transaction_intrinsic_gas(b"", False)
        assert gas == 21000

        # Empty data, create
        gas = GasSchedule.transaction_intrinsic_gas(b"", True)
        assert gas == 53000

        # With data
        data = bytes([0, 0, 1, 1, 1])  # 2 zeros, 3 non-zeros
        gas = GasSchedule.transaction_intrinsic_gas(data, False)
        assert gas == 21000 + 2 * 4 + 3 * 68


class TestGasConsumption:
    """Tests for gas consumption during execution."""

    @pytest.fixture
    def interpreter(self):
        return Interpreter(State(), Environment())

    def test_add_gas(self, interpreter):
        """Test ADD consumes correct gas."""
        code = assemble(push(1), push(2), Opcode.ADD, Opcode.STOP)
        result = interpreter.execute(create_message(code, gas=100))
        # PUSH1 (3) + PUSH1 (3) + ADD (3) = 9
        assert result.gas_used == 9

    def test_mul_gas(self, interpreter):
        """Test MUL consumes correct gas."""
        code = assemble(push(2), push(3), Opcode.MUL, Opcode.STOP)
        result = interpreter.execute(create_message(code, gas=100))
        # PUSH1 (3) + PUSH1 (3) + MUL (5) = 11
        assert result.gas_used == 11

    def test_exp_gas_zero_exponent(self, interpreter):
        """Test EXP with zero exponent."""
        code = assemble(push(0), push(2), Opcode.EXP, Opcode.STOP)
        result = interpreter.execute(create_message(code, gas=100))
        # PUSH1 (3) + PUSH1 (3) + EXP(0) (10) = 16
        assert result.gas_used == 16

    def test_exp_gas_large_exponent(self, interpreter):
        """Test EXP with larger exponent."""
        code = assemble(push(256, 2), push(2), Opcode.EXP, Opcode.STOP)
        result = interpreter.execute(create_message(code, gas=1000))
        # PUSH2 (3) + PUSH1 (3) + EXP(256=2 bytes) (10 + 20) = 36
        assert result.gas_used == 36

    def test_mstore_gas_no_expansion(self, interpreter):
        """Test MSTORE gas without memory expansion."""
        # Memory already expanded
        code = assemble(
            push(0),
            push(0),
            Opcode.MSTORE,  # First store expands
            push(0),
            push(0),
            Opcode.MSTORE,  # Second store doesn't
            Opcode.STOP,
        )
        result = interpreter.execute(create_message(code, gas=1000))
        # First MSTORE: 3 + 3 + 3 + 3 (expansion) = 12
        # Second MSTORE: 3 + 3 + 3 = 9 (no expansion)
        # Total: 12 + 9 = 21
        assert result.gas_used == 21

    def test_sload_gas(self, interpreter):
        """Test SLOAD gas cost."""
        code = assemble(push(0), Opcode.SLOAD, Opcode.POP, Opcode.STOP)
        result = interpreter.execute(create_message(code, gas=1000))
        # PUSH1 (3) + SLOAD (50) + POP (2) = 55
        assert result.gas_used == 55

    def test_out_of_gas(self, interpreter):
        """Test execution fails when out of gas."""
        code = assemble(push(1), push(2), Opcode.ADD, Opcode.STOP)
        result = interpreter.execute(create_message(code, gas=5))
        assert not result.success
        assert "gas" in result.error.lower()

    def test_memory_expansion_gas(self, interpreter):
        """Test memory expansion adds gas cost."""
        # Store at offset 0 (expands to 32 bytes)
        code1 = assemble(push(1), push(0), Opcode.MSTORE, Opcode.STOP)
        result1 = interpreter.execute(create_message(code1, gas=1000))

        # Store at offset 1000 (expands to more memory)
        code2 = assemble(push(1), push(1000), Opcode.MSTORE, Opcode.STOP)
        result2 = interpreter.execute(create_message(code2, gas=10000))

        # Second should use more gas due to memory expansion
        assert result2.gas_used > result1.gas_used


class TestMemoryGas:
    """Tests for memory-related gas calculations."""

    def test_memory_word_size(self):
        """Test memory word size calculation."""
        mem = Memory()
        assert mem.word_size(0) == 0
        assert mem.word_size(1) == 1
        assert mem.word_size(32) == 1
        assert mem.word_size(33) == 2
        assert mem.word_size(64) == 2
        assert mem.word_size(65) == 3

    def test_memory_expansion_cost_calculation(self):
        """Test memory expansion cost calculation."""
        mem = Memory()

        # First word expansion
        cost = mem.expansion_cost(0, 32)
        assert cost == 3  # 3 * 1 + 1/512

        # No expansion for existing memory
        mem.load(0, 32)  # Expand memory
        cost = mem.expansion_cost(0, 32)
        assert cost == 0

        # Additional expansion
        cost = mem.expansion_cost(32, 32)
        assert cost == 3  # One more word
