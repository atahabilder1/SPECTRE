"""Tests for MUTANT mutation testing engine."""

import pytest

from spectre.mutant.operators import (
    ArithmeticSwapOperator,
    ComparisonSwapOperator,
    OffByOneOperator,
    GasCostOperator,
    LogicNegateOperator,
    MutationType,
    get_all_operators,
)


class TestArithmeticSwapOperator:
    """Tests for arithmetic swap mutations."""

    def test_swap_add_to_sub(self):
        """Test swapping + to -."""
        op = ArithmeticSwapOperator()
        source = "result = a + b"
        mutations = list(op.generate_mutations(source, "test.py"))

        assert len(mutations) > 0
        swap_mutation = next(
            (m for m in mutations if "+" in m.original and "-" in m.mutated),
            None,
        )
        assert swap_mutation is not None
        assert swap_mutation.mutation_type == MutationType.ARITHMETIC_SWAP

    def test_swap_mul_to_div(self):
        """Test swapping * to /."""
        op = ArithmeticSwapOperator()
        source = "result = x * y"
        mutations = list(op.generate_mutations(source, "test.py"))

        swap_mutation = next(
            (m for m in mutations if "*" in m.description and "/" in m.description),
            None,
        )
        assert swap_mutation is not None

    def test_ignores_comments(self):
        """Test that comments are not mutated."""
        op = ArithmeticSwapOperator()
        source = "# result = a + b"
        mutations = list(op.generate_mutations(source, "test.py"))
        assert len(mutations) == 0


class TestComparisonSwapOperator:
    """Tests for comparison swap mutations."""

    def test_swap_lt_to_gte(self):
        """Test swapping < to >=."""
        op = ComparisonSwapOperator()
        source = "if x < y:"
        mutations = list(op.generate_mutations(source, "test.py"))

        swap_mutation = next(
            (m for m in mutations if "<" in m.description and ">=" in m.description),
            None,
        )
        assert swap_mutation is not None
        assert swap_mutation.mutation_type == MutationType.COMPARISON_SWAP

    def test_swap_eq_to_neq(self):
        """Test swapping == to !=."""
        op = ComparisonSwapOperator()
        source = "if a == b:"
        mutations = list(op.generate_mutations(source, "test.py"))

        swap_mutation = next(
            (m for m in mutations if "==" in m.description and "!=" in m.description),
            None,
        )
        assert swap_mutation is not None


class TestOffByOneOperator:
    """Tests for off-by-one mutations."""

    def test_increment_constant(self):
        """Test incrementing numeric constant."""
        op = OffByOneOperator()
        source = "limit = 1024"
        mutations = list(op.generate_mutations(source, "test.py"))

        plus_one = next(
            (m for m in mutations if "1025" in m.mutated),
            None,
        )
        assert plus_one is not None
        assert plus_one.mutation_type == MutationType.OFF_BY_ONE

    def test_decrement_constant(self):
        """Test decrementing numeric constant."""
        op = OffByOneOperator()
        source = "depth = 10"
        mutations = list(op.generate_mutations(source, "test.py"))

        minus_one = next(
            (m for m in mutations if "9" in m.mutated and "10" in m.original),
            None,
        )
        assert minus_one is not None

    def test_no_decrement_zero(self):
        """Test that 0 is not decremented to -1."""
        op = OffByOneOperator()
        source = "start = 0"
        mutations = list(op.generate_mutations(source, "test.py"))

        # Should have +1 mutation but not -1
        minus_one = next(
            (m for m in mutations if "-1" in m.mutated),
            None,
        )
        assert minus_one is None


class TestGasCostOperator:
    """Tests for gas cost mutations."""

    def test_double_gas_cost(self):
        """Test doubling gas cost constants."""
        op = GasCostOperator()
        source = "G_SLOAD = 50"
        mutations = list(op.generate_mutations(source, "test.py"))

        double = next(
            (m for m in mutations if "100" in m.mutated),
            None,
        )
        assert double is not None
        assert double.mutation_type == MutationType.GAS_COST

    def test_halve_gas_cost(self):
        """Test halving gas cost constants."""
        op = GasCostOperator()
        source = "G_CREATE = 32000"
        mutations = list(op.generate_mutations(source, "test.py"))

        half = next(
            (m for m in mutations if "16000" in m.mutated),
            None,
        )
        assert half is not None


class TestLogicNegateOperator:
    """Tests for logic negation mutations."""

    def test_negate_condition(self):
        """Test negating if condition."""
        op = LogicNegateOperator()
        source = "if x > 0:"
        mutations = list(op.generate_mutations(source, "test.py"))

        negate = next(
            (m for m in mutations if "not" in m.mutated),
            None,
        )
        assert negate is not None
        assert negate.mutation_type == MutationType.LOGIC_NEGATE


class TestOperatorCollection:
    """Tests for operator collection functions."""

    def test_get_all_operators(self):
        """Test getting all operators."""
        operators = get_all_operators()
        assert len(operators) >= 5  # We have at least 5 operators

    def test_all_operators_have_names(self):
        """Test all operators have names."""
        operators = get_all_operators()
        for op in operators:
            assert hasattr(op, "name")
            assert op.name is not None

    def test_all_operators_generate(self):
        """Test all operators can generate mutations."""
        operators = get_all_operators()
        source = """
        G_SLOAD = 50
        if x < 10:
            result = a + b
            return True
        """

        for op in operators:
            # Should not raise
            list(op.generate_mutations(source, "test.py"))
