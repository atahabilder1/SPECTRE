"""Test generation strategies for EIP validation."""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Iterator
from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Any

from ethereum.common.types import Opcode
from spectre.adversary.analyzer import EIPAnalyzer, EIPSpec, OpcodeSpec


class StrategyType(Enum):
    """Types of test generation strategies."""

    BOUNDARY = auto()
    OPCODE_INTERACTION = auto()
    CALL_CONTEXT = auto()
    GAS_EXHAUSTION = auto()
    FORK_BOUNDARY = auto()
    STACK_DEPTH = auto()
    MEMORY_EXPANSION = auto()


@dataclass
class TestCase:
    """A generated test case."""

    name: str
    strategy: StrategyType
    bytecode: bytes
    calldata: bytes = b""
    value: int = 0
    gas_limit: int = 1_000_000
    expected_success: bool = True
    expected_return: bytes | None = None
    expected_gas_used: int | None = None
    description: str = ""
    pre_state: dict[str, Any] = field(default_factory=dict)
    post_state: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "name": self.name,
            "strategy": self.strategy.name,
            "bytecode": self.bytecode.hex(),
            "calldata": self.calldata.hex(),
            "value": self.value,
            "gas_limit": self.gas_limit,
            "expected_success": self.expected_success,
            "expected_return": self.expected_return.hex() if self.expected_return else None,
            "expected_gas_used": self.expected_gas_used,
            "description": self.description,
            "pre_state": self.pre_state,
            "post_state": self.post_state,
        }


class TestStrategy(ABC):
    """Base class for test generation strategies."""

    strategy_type: StrategyType

    @abstractmethod
    def generate(self, eip: EIPSpec, analyzer: EIPAnalyzer) -> Iterator[TestCase]:
        """Generate test cases for an EIP."""
        pass

    def _push_value(self, value: int) -> bytes:
        """Generate PUSH instruction for value."""
        if value == 0:
            return bytes([Opcode.PUSH1, 0])
        byte_length = (value.bit_length() + 7) // 8
        byte_length = min(max(byte_length, 1), 32)
        opcode = Opcode.PUSH1 + byte_length - 1
        value_bytes = value.to_bytes(byte_length, "big")
        return bytes([opcode]) + value_bytes


class BoundaryValueStrategy(TestStrategy):
    """Generate tests for boundary values."""

    strategy_type = StrategyType.BOUNDARY

    def generate(self, eip: EIPSpec, analyzer: EIPAnalyzer) -> Iterator[TestCase]:
        boundaries = analyzer.get_boundary_values(eip.number)

        for opcode_spec in eip.opcodes:
            for boundary in boundaries:
                # Test opcode with boundary value
                code = bytearray()

                # Push boundary value(s) as needed
                for _ in range(opcode_spec.stack_input):
                    code.extend(self._push_value(boundary % (2**256)))

                # Execute opcode
                code.append(opcode_spec.opcode)

                # Terminate
                code.append(Opcode.STOP)

                yield TestCase(
                    name=f"boundary_{opcode_spec.name}_{boundary}",
                    strategy=self.strategy_type,
                    bytecode=bytes(code),
                    description=f"Test {opcode_spec.name} with boundary value {boundary}",
                    expected_gas_used=opcode_spec.gas_cost,
                )

    def generate_overflow_tests(self, opcode_spec: OpcodeSpec) -> Iterator[TestCase]:
        """Generate overflow boundary tests."""
        max_u256 = 2**256 - 1

        # Test max value + 1 (overflow)
        code = bytearray()
        code.extend(self._push_value(1))
        code.extend(self._push_value(max_u256))
        code.append(Opcode.ADD)
        code.append(Opcode.STOP)

        yield TestCase(
            name=f"overflow_{opcode_spec.name}",
            strategy=self.strategy_type,
            bytecode=bytes(code),
            description="Test arithmetic overflow",
        )


class OpcodeInteractionStrategy(TestStrategy):
    """Generate tests for opcode interactions."""

    strategy_type = StrategyType.OPCODE_INTERACTION

    def generate(self, eip: EIPSpec, analyzer: EIPAnalyzer) -> Iterator[TestCase]:
        for opcode_spec in eip.opcodes:
            # Test with stack operations
            yield from self._generate_stack_interactions(opcode_spec)

            # Test with memory operations
            yield from self._generate_memory_interactions(opcode_spec)

            # Test with control flow
            yield from self._generate_control_flow_interactions(opcode_spec)

    def _generate_stack_interactions(self, opcode_spec: OpcodeSpec) -> Iterator[TestCase]:
        """Generate stack operation interactions."""
        # DUP after opcode
        code = bytearray()
        for _ in range(opcode_spec.stack_input):
            code.extend(self._push_value(42))
        code.append(opcode_spec.opcode)
        if opcode_spec.stack_output > 0:
            code.append(Opcode.DUP1)
        code.append(Opcode.STOP)

        yield TestCase(
            name=f"stack_dup_{opcode_spec.name}",
            strategy=self.strategy_type,
            bytecode=bytes(code),
            description=f"Test {opcode_spec.name} followed by DUP1",
        )

        # SWAP with opcode result
        if opcode_spec.stack_output > 0:
            code = bytearray()
            code.extend(self._push_value(1))  # Extra value for swap
            for _ in range(opcode_spec.stack_input):
                code.extend(self._push_value(42))
            code.append(opcode_spec.opcode)
            code.append(Opcode.SWAP1)
            code.append(Opcode.STOP)

            yield TestCase(
                name=f"stack_swap_{opcode_spec.name}",
                strategy=self.strategy_type,
                bytecode=bytes(code),
                description=f"Test {opcode_spec.name} followed by SWAP1",
            )

    def _generate_memory_interactions(self, opcode_spec: OpcodeSpec) -> Iterator[TestCase]:
        """Generate memory operation interactions."""
        if opcode_spec.stack_output > 0:
            # Store result in memory
            code = bytearray()
            for _ in range(opcode_spec.stack_input):
                code.extend(self._push_value(42))
            code.append(opcode_spec.opcode)
            code.extend(self._push_value(0))  # offset
            code.append(Opcode.MSTORE)
            code.append(Opcode.STOP)

            yield TestCase(
                name=f"memory_store_{opcode_spec.name}",
                strategy=self.strategy_type,
                bytecode=bytes(code),
                description=f"Test storing {opcode_spec.name} result in memory",
            )

    def _generate_control_flow_interactions(self, opcode_spec: OpcodeSpec) -> Iterator[TestCase]:
        """Generate control flow interactions."""
        if opcode_spec.stack_output > 0:
            # Use result in conditional jump
            code = bytearray()
            for _ in range(opcode_spec.stack_input):
                code.extend(self._push_value(1))
            code.append(opcode_spec.opcode)
            # JUMPI target
            jump_target = len(code) + 4
            code.extend(self._push_value(jump_target))
            code.append(Opcode.JUMPI)
            code.append(Opcode.STOP)
            code.append(Opcode.JUMPDEST)
            code.append(Opcode.STOP)

            yield TestCase(
                name=f"control_jumpi_{opcode_spec.name}",
                strategy=self.strategy_type,
                bytecode=bytes(code),
                description=f"Test using {opcode_spec.name} result in JUMPI",
            )


class CallContextStrategy(TestStrategy):
    """Generate tests for different call contexts."""

    strategy_type = StrategyType.CALL_CONTEXT

    CONTEXTS = [
        ("direct", 0),
        ("delegatecall", Opcode.DELEGATECALL),
        ("staticcall", Opcode.STATICCALL),
        ("callcode", Opcode.CALLCODE),
    ]

    def generate(self, eip: EIPSpec, analyzer: EIPAnalyzer) -> Iterator[TestCase]:
        for opcode_spec in eip.opcodes:
            for context_name, _ in self.CONTEXTS:
                yield TestCase(
                    name=f"context_{context_name}_{opcode_spec.name}",
                    strategy=self.strategy_type,
                    bytecode=self._generate_context_code(opcode_spec),
                    description=f"Test {opcode_spec.name} in {context_name} context",
                )

    def _generate_context_code(self, opcode_spec: OpcodeSpec) -> bytes:
        """Generate code for context testing."""
        code = bytearray()
        for _ in range(opcode_spec.stack_input):
            code.extend(self._push_value(0))
        code.append(opcode_spec.opcode)
        code.append(Opcode.STOP)
        return bytes(code)


class GasExhaustionStrategy(TestStrategy):
    """Generate tests for gas exhaustion scenarios."""

    strategy_type = StrategyType.GAS_EXHAUSTION

    def generate(self, eip: EIPSpec, analyzer: EIPAnalyzer) -> Iterator[TestCase]:
        for opcode_spec in eip.opcodes:
            if opcode_spec.gas_cost:
                # Test with exact gas
                yield TestCase(
                    name=f"gas_exact_{opcode_spec.name}",
                    strategy=self.strategy_type,
                    bytecode=self._generate_opcode_code(opcode_spec),
                    gas_limit=opcode_spec.gas_cost + 50,  # Small buffer for setup
                    description=f"Test {opcode_spec.name} with near-exact gas",
                )

                # Test with insufficient gas
                yield TestCase(
                    name=f"gas_insufficient_{opcode_spec.name}",
                    strategy=self.strategy_type,
                    bytecode=self._generate_opcode_code(opcode_spec),
                    gas_limit=opcode_spec.gas_cost - 1,
                    expected_success=False,
                    description=f"Test {opcode_spec.name} with insufficient gas",
                )

                # Test repeated execution until gas exhaustion
                yield TestCase(
                    name=f"gas_loop_{opcode_spec.name}",
                    strategy=self.strategy_type,
                    bytecode=self._generate_loop_code(opcode_spec),
                    gas_limit=opcode_spec.gas_cost * 10,
                    description=f"Test {opcode_spec.name} in loop until gas exhaustion",
                )

    def _generate_opcode_code(self, opcode_spec: OpcodeSpec) -> bytes:
        """Generate minimal code for single opcode execution."""
        code = bytearray()
        for _ in range(opcode_spec.stack_input):
            code.extend(self._push_value(1))
        code.append(opcode_spec.opcode)
        code.append(Opcode.STOP)
        return bytes(code)

    def _generate_loop_code(self, opcode_spec: OpcodeSpec) -> bytes:
        """Generate code that loops an opcode."""
        code = bytearray()

        # Setup: push counter
        code.extend(self._push_value(100))  # Loop 100 times

        # Loop start (JUMPDEST)
        loop_start = len(code)
        code.append(Opcode.JUMPDEST)

        # Execute opcode
        for _ in range(opcode_spec.stack_input):
            code.extend(self._push_value(1))
        code.append(opcode_spec.opcode)
        if opcode_spec.stack_output > 0:
            code.append(Opcode.POP)

        # Decrement counter
        code.extend(self._push_value(1))
        code.append(Opcode.SWAP1)
        code.append(Opcode.SUB)
        code.append(Opcode.DUP1)

        # Jump if not zero
        code.extend(self._push_value(loop_start))
        code.append(Opcode.JUMPI)

        code.append(Opcode.STOP)
        return bytes(code)


class ForkBoundaryStrategy(TestStrategy):
    """Generate tests for fork boundary conditions."""

    strategy_type = StrategyType.FORK_BOUNDARY

    def generate(self, eip: EIPSpec, analyzer: EIPAnalyzer) -> Iterator[TestCase]:
        # Test new opcodes that shouldn't work in earlier forks
        for opcode_spec in eip.opcodes:
            yield TestCase(
                name=f"fork_pre_{opcode_spec.name}",
                strategy=self.strategy_type,
                bytecode=self._generate_opcode_code(opcode_spec),
                description=f"Test {opcode_spec.name} should fail in pre-fork",
                expected_success=False,  # Should fail in older fork
            )

            yield TestCase(
                name=f"fork_post_{opcode_spec.name}",
                strategy=self.strategy_type,
                bytecode=self._generate_opcode_code(opcode_spec),
                description=f"Test {opcode_spec.name} should succeed in post-fork",
                expected_success=True,  # Should work in new fork
            )

    def _generate_opcode_code(self, opcode_spec: OpcodeSpec) -> bytes:
        """Generate code for opcode testing."""
        code = bytearray()
        for _ in range(opcode_spec.stack_input):
            code.extend(self._push_value(0))
        code.append(opcode_spec.opcode)
        code.append(Opcode.STOP)
        return bytes(code)


class StackDepthStrategy(TestStrategy):
    """Generate tests for stack depth limits."""

    strategy_type = StrategyType.STACK_DEPTH

    def generate(self, eip: EIPSpec, analyzer: EIPAnalyzer) -> Iterator[TestCase]:
        for opcode_spec in eip.opcodes:
            # Test at stack limit
            yield TestCase(
                name=f"stack_limit_{opcode_spec.name}",
                strategy=self.strategy_type,
                bytecode=self._generate_stack_limit_code(opcode_spec),
                description=f"Test {opcode_spec.name} near stack limit",
            )

    def _generate_stack_limit_code(self, opcode_spec: OpcodeSpec) -> bytes:
        """Generate code that pushes to near stack limit."""
        code = bytearray()

        # Push many values (but stay under 1024 limit)
        for _ in range(1020):
            code.extend(self._push_value(0))

        # Execute target opcode
        for _ in range(opcode_spec.stack_input):
            pass  # Already have values on stack
        code.append(opcode_spec.opcode)

        code.append(Opcode.STOP)
        return bytes(code)


# All strategies
ALL_STRATEGIES: list[type[TestStrategy]] = [
    BoundaryValueStrategy,
    OpcodeInteractionStrategy,
    CallContextStrategy,
    GasExhaustionStrategy,
    ForkBoundaryStrategy,
    StackDepthStrategy,
]


def get_all_strategies() -> list[TestStrategy]:
    """Get instances of all strategies."""
    return [s() for s in ALL_STRATEGIES]


def get_strategy(strategy_type: StrategyType) -> TestStrategy | None:
    """Get a strategy by type."""
    for s in ALL_STRATEGIES:
        if s.strategy_type == strategy_type:
            return s()
    return None
