"""Tests for PHANTOM differential fuzzer."""

from ethereum.common.types import Opcode
from spectre.phantom.executor import (
    DifferentialExecutor,
    DivergenceType,
    Fork,
)
from spectre.phantom.generator import (
    BoundaryBytecodeGenerator,
    BytecodeGenerator,
    GeneratorStrategy,
    GrammarBytecodeGenerator,
    RandomBytecodeGenerator,
)
from spectre.phantom.minimizer import CustomMinimizer


class TestRandomBytecodeGenerator:
    """Tests for random bytecode generation."""

    def test_generates_bytecode(self):
        """Test that generator produces bytecode."""
        gen = RandomBytecodeGenerator(min_length=10, max_length=20)
        result = gen.generate()

        assert result.code is not None
        assert 10 <= len(result.code) <= 20
        assert result.strategy == GeneratorStrategy.RANDOM

    def test_deterministic_with_seed(self):
        """Test that same seed produces same output."""
        gen = RandomBytecodeGenerator()
        result1 = gen.generate(seed=42)
        result2 = gen.generate(seed=42)

        assert result1.code == result2.code

    def test_different_seeds_different_output(self):
        """Test that different seeds produce different output."""
        gen = RandomBytecodeGenerator()
        result1 = gen.generate(seed=1)
        result2 = gen.generate(seed=2)

        # Very unlikely to be the same
        assert result1.code != result2.code


class TestGrammarBytecodeGenerator:
    """Tests for grammar-based bytecode generation."""

    def test_generates_valid_structure(self):
        """Test that generated code has valid structure."""
        gen = GrammarBytecodeGenerator(max_depth=10)
        result = gen.generate(seed=42)

        # Should end with STOP
        assert result.code[-1] == Opcode.STOP

    def test_contains_push_operations(self):
        """Test that generated code contains PUSH operations."""
        gen = GrammarBytecodeGenerator(max_depth=15)
        result = gen.generate(seed=42)

        # Should contain at least one PUSH
        has_push = any(Opcode.PUSH1 <= b <= Opcode.PUSH32 for b in result.code)
        assert has_push

    def test_respects_max_depth(self):
        """Test that depth limit is respected."""
        gen = GrammarBytecodeGenerator(max_depth=5)
        result = gen.generate(seed=42)

        # With max_depth=5, code should be relatively short
        assert len(result.code) < 200


class TestBoundaryBytecodeGenerator:
    """Tests for boundary value bytecode generation."""

    def test_uses_boundary_values(self):
        """Test that boundary values are included."""
        gen = BoundaryBytecodeGenerator()
        result = gen.generate(seed=42)

        # Code should contain push instructions
        assert len(result.code) > 2
        assert result.strategy == GeneratorStrategy.BOUNDARY


class TestBytecodeGenerator:
    """Tests for the main BytecodeGenerator class."""

    def test_generates_mixed_strategies(self):
        """Test that generator uses multiple strategies."""
        gen = BytecodeGenerator()
        results = list(gen.generate(count=20, seed=42))

        strategies_used = {r.strategy for r in results}
        # Should use multiple strategies
        assert len(strategies_used) > 1

    def test_respects_strategy_filter(self):
        """Test that strategy filter works."""
        gen = BytecodeGenerator(strategies=[GeneratorStrategy.RANDOM])
        results = list(gen.generate(count=10, seed=42))

        for result in results:
            assert result.strategy == GeneratorStrategy.RANDOM

    def test_generate_for_eip(self):
        """Test EIP-focused generation."""
        gen = BytecodeGenerator()
        results = list(gen.generate_for_eip(3855, count=10))

        assert len(results) == 10


class TestDifferentialExecutor:
    """Tests for differential execution."""

    def test_execute_single_fork(self):
        """Test execution on a single fork."""
        executor = DifferentialExecutor()

        # Simple code: PUSH1 1, STOP
        code = bytes([Opcode.PUSH1, 0x01, Opcode.STOP])
        trace = executor.execute_single(code, Fork.FRONTIER)

        assert trace.fork == Fork.FRONTIER
        assert trace.result.success

    def test_detects_push0_divergence(self):
        """Test that PUSH0 divergence is detected between forks."""
        executor = DifferentialExecutor(
            fork_a=Fork.FRONTIER,
            fork_b=Fork.SHANGHAI,
        )

        # PUSH0 (only valid in Shanghai)
        code = bytes([Opcode.PUSH0, Opcode.STOP])

        trace_a = executor.execute_single(code, Fork.FRONTIER)
        trace_b = executor.execute_single(code, Fork.SHANGHAI)

        # Frontier should fail, Shanghai should succeed
        assert not trace_a.result.success
        assert trace_b.result.success

    def test_compare_identical_execution(self):
        """Test that identical executions show no divergence."""
        executor = DifferentialExecutor(
            fork_a=Fork.HOMESTEAD,
            fork_b=Fork.SHANGHAI,
        )

        # Code that works the same in both forks
        code = bytes([Opcode.PUSH1, 0x01, Opcode.PUSH1, 0x02, Opcode.ADD, Opcode.STOP])

        from spectre.phantom.generator import GeneratedBytecode

        bytecode = GeneratedBytecode(
            code=code,
            strategy=GeneratorStrategy.RANDOM,
            description="Test",
        )

        divergences = executor.execute_differential(bytecode)

        # Filter out expected divergences (gas differences might occur)
        unexpected = [d for d in divergences if not d.is_expected()]

        # Gas differences are expected between forks
        # Only check for major divergences
        major = [
            d
            for d in unexpected
            if d.divergence_type
            in (DivergenceType.SUCCESS_MISMATCH, DivergenceType.RETURN_DATA_MISMATCH)
        ]
        assert len(major) == 0


class TestDeltaDebugger:
    """Tests for delta debugging minimizer."""

    def test_minimize_simple(self):
        """Test minimization of simple case."""

        # Test predicate: bytecode contains 0x5F (PUSH0)
        def has_push0(code: bytes) -> bool:
            return 0x5F in code

        minimizer = CustomMinimizer(has_push0)

        original = bytes([0x60, 0x01, 0x5F, 0x00, 0x60, 0x02])
        result = minimizer.minimize(original)

        assert 0x5F in result.minimized
        assert len(result.minimized) <= len(result.original)

    def test_minimize_empty_input(self):
        """Test minimization with empty input."""
        minimizer = CustomMinimizer(lambda x: False)
        result = minimizer.minimize(b"")

        assert result.minimized == b""
        assert result.iterations == 0

    def test_minimize_single_byte(self):
        """Test minimization of single byte."""
        minimizer = CustomMinimizer(lambda x: len(x) >= 1)
        result = minimizer.minimize(bytes([0x00]))

        assert len(result.minimized) == 1

    def test_reduction_percent(self):
        """Test reduction percentage calculation."""
        from spectre.phantom.minimizer import MinimizationResult

        result = MinimizationResult.from_bytecodes(
            original=bytes(100),
            minimized=bytes(25),
            iterations=10,
        )

        assert result.reduction_percent == 75.0
