"""Tests for ADVERSARY test generator."""

from spectre.adversary.analyzer import (
    EIPAnalyzer,
    EIPCategory,
    OpcodeChange,
)
from spectre.adversary.generator import TestGenerator, TestSuite
from spectre.adversary.strategies import (
    BoundaryValueStrategy,
    ForkBoundaryStrategy,
    GasExhaustionStrategy,
    OpcodeInteractionStrategy,
    StrategyType,
    get_all_strategies,
)


class TestEIPAnalyzer:
    """Tests for EIP analyzer."""

    def test_get_known_eip(self):
        """Test getting a known EIP."""
        analyzer = EIPAnalyzer()
        eip = analyzer.get_eip(3855)

        assert eip is not None
        assert eip.number == 3855
        assert eip.title == "PUSH0 instruction"
        assert eip.category == EIPCategory.CORE

    def test_get_unknown_eip(self):
        """Test getting an unknown EIP returns None."""
        analyzer = EIPAnalyzer()
        eip = analyzer.get_eip(99999)

        assert eip is None

    def test_get_opcodes_for_eip(self):
        """Test getting opcodes for an EIP."""
        analyzer = EIPAnalyzer()
        opcodes = analyzer.get_opcodes_for_eip(3855)

        assert len(opcodes) == 1
        assert opcodes[0].name == "PUSH0"
        assert opcodes[0].opcode == 0x5F
        assert opcodes[0].gas_cost == 2

    def test_get_boundary_values(self):
        """Test getting boundary values for EIP."""
        analyzer = EIPAnalyzer()
        boundaries = analyzer.get_boundary_values(3855)

        # Should include standard EVM boundaries plus EIP-specific
        assert 0 in boundaries
        assert 2**256 - 1 in boundaries

    def test_list_all_eips(self):
        """Test listing all known EIPs."""
        analyzer = EIPAnalyzer()
        eips = analyzer.list_all_eips()

        assert len(eips) > 0
        assert 3855 in eips
        assert 145 in eips

    def test_get_gas_changes(self):
        """Test getting gas changes from EIP."""
        analyzer = EIPAnalyzer()
        gas = analyzer.get_gas_changes(3855)

        assert "PUSH0" in gas
        assert gas["PUSH0"] == 2

    def test_get_new_opcodes(self):
        """Test getting only new opcodes."""
        analyzer = EIPAnalyzer()
        new_ops = analyzer.get_new_opcodes(145)

        assert len(new_ops) == 3  # SHL, SHR, SAR
        for op in new_ops:
            assert op.change_type == OpcodeChange.NEW_OPCODE


class TestBoundaryValueStrategy:
    """Tests for boundary value test generation."""

    def test_generates_tests(self):
        """Test that strategy generates tests."""
        strategy = BoundaryValueStrategy()
        analyzer = EIPAnalyzer()
        eip = analyzer.get_eip(3855)

        tests = list(strategy.generate(eip, analyzer))

        assert len(tests) > 0
        for test in tests:
            assert test.strategy == StrategyType.BOUNDARY
            assert len(test.bytecode) > 0

    def test_test_names_unique(self):
        """Test that generated test names are unique."""
        strategy = BoundaryValueStrategy()
        analyzer = EIPAnalyzer()
        eip = analyzer.get_eip(3855)

        tests = list(strategy.generate(eip, analyzer))
        names = [t.name for t in tests]

        # All names should be unique
        assert len(names) == len(set(names))


class TestOpcodeInteractionStrategy:
    """Tests for opcode interaction test generation."""

    def test_generates_stack_tests(self):
        """Test generation of stack interaction tests."""
        strategy = OpcodeInteractionStrategy()
        analyzer = EIPAnalyzer()
        eip = analyzer.get_eip(3855)

        tests = list(strategy.generate(eip, analyzer))

        # Should have DUP tests
        dup_tests = [t for t in tests if "dup" in t.name]
        assert len(dup_tests) > 0

    def test_generates_swap_tests(self):
        """Test generation of swap interaction tests."""
        strategy = OpcodeInteractionStrategy()
        analyzer = EIPAnalyzer()
        eip = analyzer.get_eip(145)  # SHL/SHR/SAR

        tests = list(strategy.generate(eip, analyzer))

        # Should have SWAP tests
        swap_tests = [t for t in tests if "swap" in t.name]
        assert len(swap_tests) > 0


class TestGasExhaustionStrategy:
    """Tests for gas exhaustion test generation."""

    def test_generates_exact_gas_tests(self):
        """Test generation of exact gas tests."""
        strategy = GasExhaustionStrategy()
        analyzer = EIPAnalyzer()
        eip = analyzer.get_eip(3855)

        tests = list(strategy.generate(eip, analyzer))

        exact_tests = [t for t in tests if "exact" in t.name]
        assert len(exact_tests) > 0

    def test_generates_insufficient_gas_tests(self):
        """Test generation of insufficient gas tests."""
        strategy = GasExhaustionStrategy()
        analyzer = EIPAnalyzer()
        eip = analyzer.get_eip(3855)

        tests = list(strategy.generate(eip, analyzer))

        insufficient_tests = [t for t in tests if "insufficient" in t.name]
        assert len(insufficient_tests) > 0
        for test in insufficient_tests:
            assert not test.expected_success


class TestForkBoundaryStrategy:
    """Tests for fork boundary test generation."""

    def test_generates_pre_fork_tests(self):
        """Test generation of pre-fork tests."""
        strategy = ForkBoundaryStrategy()
        analyzer = EIPAnalyzer()
        eip = analyzer.get_eip(3855)

        tests = list(strategy.generate(eip, analyzer))

        pre_tests = [t for t in tests if "pre" in t.name]
        assert len(pre_tests) > 0

    def test_generates_post_fork_tests(self):
        """Test generation of post-fork tests."""
        strategy = ForkBoundaryStrategy()
        analyzer = EIPAnalyzer()
        eip = analyzer.get_eip(3855)

        tests = list(strategy.generate(eip, analyzer))

        post_tests = [t for t in tests if "post" in t.name]
        assert len(post_tests) > 0


class TestTestGenerator:
    """Tests for main test generator."""

    def test_generate_for_known_eip(self):
        """Test generating tests for known EIP."""
        generator = TestGenerator()
        suite = generator.generate_for_eip(3855)

        assert suite.eip_number == 3855
        assert len(suite.test_cases) > 0

    def test_generate_for_unknown_eip(self):
        """Test generating tests for unknown EIP."""
        generator = TestGenerator()
        suite = generator.generate_for_eip(99999)

        assert suite.eip_number == 99999
        assert len(suite.test_cases) == 0

    def test_generate_with_strategy_filter(self):
        """Test generating with specific strategies."""
        generator = TestGenerator()
        suite = generator.generate_for_eip(
            3855,
            strategy_types=[StrategyType.BOUNDARY],
        )

        for test in suite.test_cases:
            assert test.strategy == StrategyType.BOUNDARY

    def test_generate_all(self):
        """Test generating tests for all known EIPs."""
        generator = TestGenerator()
        all_suites = generator.generate_all()

        assert len(all_suites) > 0
        assert 3855 in all_suites


class TestTestSuite:
    """Tests for TestSuite class."""

    def test_to_dict(self):
        """Test conversion to dictionary."""
        suite = TestSuite(
            eip_number=3855,
            eip_title="PUSH0 instruction",
            test_cases=[],
        )

        data = suite.to_dict()

        assert data["eip_number"] == 3855
        assert data["eip_title"] == "PUSH0 instruction"
        assert "generated_at" in data

    def test_to_json(self):
        """Test conversion to JSON."""
        suite = TestSuite(
            eip_number=3855,
            eip_title="PUSH0",
            test_cases=[],
        )

        json_str = suite.to_json()

        import json

        data = json.loads(json_str)
        assert data["eip_number"] == 3855

    def test_to_eest_format(self):
        """Test conversion to EEST format."""
        from spectre.adversary.strategies import TestCase

        suite = TestSuite(
            eip_number=3855,
            eip_title="PUSH0",
            test_cases=[
                TestCase(
                    name="test_push0",
                    strategy=StrategyType.BOUNDARY,
                    bytecode=bytes([0x5F, 0x00]),
                    description="Test PUSH0",
                ),
            ],
        )

        eest = suite.to_eest_format()

        assert "_info" in eest
        assert eest["_info"]["eip"] == 3855
        assert "EIP3855_test_push0" in eest


class TestStrategyCollection:
    """Tests for strategy collection functions."""

    def test_get_all_strategies(self):
        """Test getting all strategies."""
        strategies = get_all_strategies()

        assert len(strategies) >= 4
        types = {s.strategy_type for s in strategies}
        assert StrategyType.BOUNDARY in types
        assert StrategyType.GAS_EXHAUSTION in types
