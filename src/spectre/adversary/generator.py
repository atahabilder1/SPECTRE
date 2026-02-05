"""Test case generator for EIP validation."""

from __future__ import annotations

import json
from collections.abc import Iterator
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any

from spectre.adversary.analyzer import EIPAnalyzer
from spectre.adversary.strategies import (
    StrategyType,
    TestCase,
    TestStrategy,
    get_all_strategies,
)


@dataclass
class TestSuite:
    """A collection of test cases for an EIP."""

    eip_number: int
    eip_title: str
    test_cases: list[TestCase] = field(default_factory=list)
    generated_at: str = field(default_factory=lambda: datetime.now().isoformat())

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "eip_number": self.eip_number,
            "eip_title": self.eip_title,
            "generated_at": self.generated_at,
            "test_count": len(self.test_cases),
            "tests": [tc.to_dict() for tc in self.test_cases],
        }

    def to_json(self, indent: int = 2) -> str:
        """Convert to JSON string."""
        return json.dumps(self.to_dict(), indent=indent)

    def to_eest_format(self) -> dict[str, Any]:
        """
        Convert to Ethereum Execution Spec Tests (EEST) format.

        This format is compatible with the official Ethereum test suite.
        """
        tests: dict[str, Any] = {}

        for tc in self.test_cases:
            test_name = f"EIP{self.eip_number}_{tc.name}"

            tests[test_name] = {
                "env": {
                    "currentNumber": "0x1",
                    "currentGasLimit": hex(tc.gas_limit),
                    "currentDifficulty": "0x1",
                    "currentTimestamp": "0x1",
                    "currentCoinbase": "0x" + "00" * 20,
                },
                "pre": self._generate_pre_state(tc),
                "transaction": {
                    "data": ["0x" + tc.calldata.hex()],
                    "gasLimit": [hex(tc.gas_limit)],
                    "gasPrice": "0x1",
                    "nonce": "0x0",
                    "to": "0x" + "00" * 19 + "02",
                    "value": [hex(tc.value)],
                    "sender": "0x" + "00" * 19 + "01",
                },
                "expect": [
                    {
                        "result": {
                            "0x" + "00" * 19 + "01": {
                                "shouldExist": True,
                            }
                        }
                    }
                ],
            }

        return {
            "_info": {
                "filling-tool": "SPECTRE/adversary",
                "generatedAt": self.generated_at,
                "eip": self.eip_number,
            },
            **tests,
        }

    def _generate_pre_state(self, tc: TestCase) -> dict[str, Any]:
        """Generate pre-state for a test case."""
        contract_addr = "0x" + "00" * 19 + "02"
        sender_addr = "0x" + "00" * 19 + "01"

        pre: dict[str, Any] = {
            sender_addr: {
                "balance": "0xffffffffff",
                "nonce": "0x0",
                "code": "0x",
                "storage": {},
            },
            contract_addr: {
                "balance": "0x0",
                "nonce": "0x0",
                "code": "0x" + tc.bytecode.hex(),
                "storage": {},
            },
        }

        # Add any custom pre-state
        for addr, state in tc.pre_state.items():
            pre[addr] = state

        return pre


class TestGenerator:
    """
    Generate test cases for EIP validation.

    Uses multiple strategies to create comprehensive test coverage.
    """

    def __init__(
        self,
        strategies: list[TestStrategy] | None = None,
        analyzer: EIPAnalyzer | None = None,
    ) -> None:
        self.strategies = strategies or get_all_strategies()
        self.analyzer = analyzer or EIPAnalyzer()

    def generate_for_eip(
        self,
        eip_number: int,
        strategy_types: list[StrategyType] | None = None,
    ) -> TestSuite:
        """
        Generate test cases for an EIP.

        Args:
            eip_number: The EIP number to generate tests for
            strategy_types: Specific strategies to use (default: all)

        Returns:
            TestSuite with generated test cases
        """
        eip = self.analyzer.get_eip(eip_number)
        if not eip:
            return TestSuite(
                eip_number=eip_number,
                eip_title=f"Unknown EIP {eip_number}",
            )

        test_cases: list[TestCase] = []

        for strategy in self.strategies:
            if strategy_types and strategy.strategy_type not in strategy_types:
                continue

            for test_case in strategy.generate(eip, self.analyzer):
                test_cases.append(test_case)

        return TestSuite(
            eip_number=eip.number,
            eip_title=eip.title,
            test_cases=test_cases,
        )

    def generate_for_opcodes(
        self,
        opcodes: list[int],
    ) -> Iterator[TestCase]:
        """Generate test cases focused on specific opcodes."""
        from spectre.adversary.strategies import BoundaryValueStrategy

        strategy = BoundaryValueStrategy()

        for opcode in opcodes:
            # Generate boundary tests
            code = bytearray()
            code.extend(strategy._push_value(2**255 - 1))
            code.extend(strategy._push_value(1))
            code.append(opcode)
            code.append(0x00)  # STOP

            yield TestCase(
                name=f"opcode_0x{opcode:02X}_boundary",
                strategy=StrategyType.BOUNDARY,
                bytecode=bytes(code),
                description=f"Boundary test for opcode 0x{opcode:02X}",
            )

    def save_test_suite(
        self,
        suite: TestSuite,
        output_dir: Path,
        format: str = "json",
    ) -> Path:
        """
        Save test suite to file.

        Args:
            suite: The test suite to save
            output_dir: Directory to save to
            format: Output format ("json" or "eest")

        Returns:
            Path to the saved file
        """
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

        if format == "json":
            filename = f"eip{suite.eip_number}_tests.json"
            content = suite.to_json()
        elif format == "eest":
            filename = f"eip{suite.eip_number}_tests_eest.json"
            content = json.dumps(suite.to_eest_format(), indent=2)
        else:
            raise ValueError(f"Unknown format: {format}")

        output_path = output_dir / filename
        output_path.write_text(content)
        return output_path

    def generate_all(self) -> dict[int, TestSuite]:
        """Generate test suites for all known EIPs."""
        results: dict[int, TestSuite] = {}

        for eip_number in self.analyzer.list_all_eips():
            results[eip_number] = self.generate_for_eip(eip_number)

        return results


def generate_eip_tests(
    eip_number: int,
    output_dir: Path | None = None,
) -> TestSuite:
    """
    Convenience function to generate tests for an EIP.

    Args:
        eip_number: The EIP to generate tests for
        output_dir: Optional directory to save tests

    Returns:
        Generated test suite
    """
    generator = TestGenerator()
    suite = generator.generate_for_eip(eip_number)

    if output_dir:
        generator.save_test_suite(suite, output_dir)
        generator.save_test_suite(suite, output_dir, format="eest")

    return suite
