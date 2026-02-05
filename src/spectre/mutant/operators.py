"""Mutation operators for EVM specification testing.

These operators create small changes (mutations) in the EVM implementation
to test whether the test suite can detect these changes.
"""

from __future__ import annotations

import re
from abc import ABC, abstractmethod
from collections.abc import Iterator
from dataclasses import dataclass
from enum import Enum, auto


class MutationType(Enum):
    """Types of mutations that can be applied."""

    ARITHMETIC_SWAP = auto()  # Swap arithmetic operators
    COMPARISON_SWAP = auto()  # Swap comparison operators
    CONSTANT_CHANGE = auto()  # Change constant values
    OFF_BY_ONE = auto()  # Off-by-one errors
    BOUNDARY_CHANGE = auto()  # Change boundary conditions
    LOGIC_NEGATE = auto()  # Negate boolean conditions
    RETURN_VALUE = auto()  # Change return values
    GAS_COST = auto()  # Modify gas costs


@dataclass(frozen=True)
class Mutation:
    """Represents a single mutation."""

    mutation_type: MutationType
    file_path: str
    line_number: int
    original: str
    mutated: str
    description: str

    def __str__(self) -> str:
        return (
            f"{self.mutation_type.name} at {self.file_path}:{self.line_number}: {self.description}"
        )


class MutationOperator(ABC):
    """Base class for mutation operators."""

    name: str = "base"
    description: str = "Base mutation operator"

    @abstractmethod
    def generate_mutations(self, source: str, file_path: str) -> Iterator[Mutation]:
        """Generate mutations for the given source code."""
        pass


class ArithmeticSwapOperator(MutationOperator):
    """Swap arithmetic operators (+, -, *, /, %)."""

    name = "arithmetic_swap"
    description = "Swaps arithmetic operators"

    SWAPS = {
        "+": "-",
        "-": "+",
        "*": "/",
        "/": "*",
        "%": "/",
        "//": "*",
    }

    def generate_mutations(self, source: str, file_path: str) -> Iterator[Mutation]:
        lines = source.split("\n")
        for line_num, line in enumerate(lines, 1):
            # Skip comments and strings
            if line.strip().startswith("#"):
                continue

            for original, replacement in self.SWAPS.items():
                # Find operator in arithmetic context
                pattern = rf"(\w+)\s*{re.escape(original)}\s*(\w+)"
                for match in re.finditer(pattern, line):
                    mutated_line = (
                        line[: match.start()]
                        + match.group(1)
                        + f" {replacement} "
                        + match.group(2)
                        + line[match.end() :]
                    )
                    yield Mutation(
                        mutation_type=MutationType.ARITHMETIC_SWAP,
                        file_path=file_path,
                        line_number=line_num,
                        original=line.strip(),
                        mutated=mutated_line.strip(),
                        description=f"Swap '{original}' with '{replacement}'",
                    )


class ComparisonSwapOperator(MutationOperator):
    """Swap comparison operators (<, >, <=, >=, ==, !=)."""

    name = "comparison_swap"
    description = "Swaps comparison operators"

    SWAPS = {
        "<=": ">",
        ">=": "<",
        "<": ">=",
        ">": "<=",
        "==": "!=",
        "!=": "==",
    }

    def generate_mutations(self, source: str, file_path: str) -> Iterator[Mutation]:
        lines = source.split("\n")
        for line_num, line in enumerate(lines, 1):
            if line.strip().startswith("#"):
                continue

            for original, replacement in self.SWAPS.items():
                pattern = rf"(\w+)\s*{re.escape(original)}\s*(\w+)"
                for match in re.finditer(pattern, line):
                    mutated_line = (
                        line[: match.start()]
                        + match.group(1)
                        + f" {replacement} "
                        + match.group(2)
                        + line[match.end() :]
                    )
                    yield Mutation(
                        mutation_type=MutationType.COMPARISON_SWAP,
                        file_path=file_path,
                        line_number=line_num,
                        original=line.strip(),
                        mutated=mutated_line.strip(),
                        description=f"Swap '{original}' with '{replacement}'",
                    )


class OffByOneOperator(MutationOperator):
    """Introduce off-by-one errors in numeric literals."""

    name = "off_by_one"
    description = "Introduces off-by-one errors"

    def generate_mutations(self, source: str, file_path: str) -> Iterator[Mutation]:
        lines = source.split("\n")
        for line_num, line in enumerate(lines, 1):
            if line.strip().startswith("#"):
                continue

            # Find numeric literals
            for match in re.finditer(r"\b(\d+)\b", line):
                value = int(match.group(1))

                # Generate +1 mutation
                mutated_plus = line[: match.start()] + str(value + 1) + line[match.end() :]
                yield Mutation(
                    mutation_type=MutationType.OFF_BY_ONE,
                    file_path=file_path,
                    line_number=line_num,
                    original=line.strip(),
                    mutated=mutated_plus.strip(),
                    description=f"Change {value} to {value + 1}",
                )

                # Generate -1 mutation (only if > 0)
                if value > 0:
                    mutated_minus = line[: match.start()] + str(value - 1) + line[match.end() :]
                    yield Mutation(
                        mutation_type=MutationType.OFF_BY_ONE,
                        file_path=file_path,
                        line_number=line_num,
                        original=line.strip(),
                        mutated=mutated_minus.strip(),
                        description=f"Change {value} to {value - 1}",
                    )


class GasCostOperator(MutationOperator):
    """Modify gas cost constants."""

    name = "gas_cost"
    description = "Modifies gas cost values"

    GAS_PATTERN = re.compile(r"G_\w+\s*[=:]\s*(\d+)")

    def generate_mutations(self, source: str, file_path: str) -> Iterator[Mutation]:
        lines = source.split("\n")
        for line_num, line in enumerate(lines, 1):
            if line.strip().startswith("#"):
                continue

            for match in self.GAS_PATTERN.finditer(line):
                value = int(match.group(1))

                # Double the gas cost
                mutated_double = line[: match.start(1)] + str(value * 2) + line[match.end(1) :]
                yield Mutation(
                    mutation_type=MutationType.GAS_COST,
                    file_path=file_path,
                    line_number=line_num,
                    original=line.strip(),
                    mutated=mutated_double.strip(),
                    description=f"Double gas cost from {value} to {value * 2}",
                )

                # Halve the gas cost
                if value > 1:
                    mutated_half = line[: match.start(1)] + str(value // 2) + line[match.end(1) :]
                    yield Mutation(
                        mutation_type=MutationType.GAS_COST,
                        file_path=file_path,
                        line_number=line_num,
                        original=line.strip(),
                        mutated=mutated_half.strip(),
                        description=f"Halve gas cost from {value} to {value // 2}",
                    )


class LogicNegateOperator(MutationOperator):
    """Negate boolean conditions."""

    name = "logic_negate"
    description = "Negates boolean conditions"

    def generate_mutations(self, source: str, file_path: str) -> Iterator[Mutation]:
        lines = source.split("\n")
        for line_num, line in enumerate(lines, 1):
            if line.strip().startswith("#"):
                continue

            # Find 'if condition:' patterns
            if_match = re.match(r"(\s*if\s+)(.+)(:)", line)
            if if_match:
                prefix = if_match.group(1)
                condition = if_match.group(2)
                suffix = if_match.group(3)

                mutated_line = f"{prefix}not ({condition}){suffix}"
                yield Mutation(
                    mutation_type=MutationType.LOGIC_NEGATE,
                    file_path=file_path,
                    line_number=line_num,
                    original=line.strip(),
                    mutated=mutated_line.strip(),
                    description="Negate condition",
                )


class ReturnValueOperator(MutationOperator):
    """Modify return values."""

    name = "return_value"
    description = "Modifies return values"

    def generate_mutations(self, source: str, file_path: str) -> Iterator[Mutation]:
        lines = source.split("\n")
        for line_num, line in enumerate(lines, 1):
            if line.strip().startswith("#"):
                continue

            # Find 'return value' patterns
            return_match = re.match(r"(\s*return\s+)(.+)", line)
            if return_match:
                prefix = return_match.group(1)
                value = return_match.group(2).strip()

                # For True/False returns
                if value == "True":
                    yield Mutation(
                        mutation_type=MutationType.RETURN_VALUE,
                        file_path=file_path,
                        line_number=line_num,
                        original=line.strip(),
                        mutated=f"{prefix}False",
                        description="Change return True to False",
                    )
                elif value == "False":
                    yield Mutation(
                        mutation_type=MutationType.RETURN_VALUE,
                        file_path=file_path,
                        line_number=line_num,
                        original=line.strip(),
                        mutated=f"{prefix}True",
                        description="Change return False to True",
                    )
                elif value == "0":
                    yield Mutation(
                        mutation_type=MutationType.RETURN_VALUE,
                        file_path=file_path,
                        line_number=line_num,
                        original=line.strip(),
                        mutated=f"{prefix}1",
                        description="Change return 0 to 1",
                    )
                elif value == "None":
                    yield Mutation(
                        mutation_type=MutationType.RETURN_VALUE,
                        file_path=file_path,
                        line_number=line_num,
                        original=line.strip(),
                        mutated=f'{prefix}""',
                        description="Change return None to empty string",
                    )


class BoundaryChangeOperator(MutationOperator):
    """Change boundary conditions."""

    name = "boundary_change"
    description = "Modifies boundary conditions"

    BOUNDARIES = {
        "1024": ["1023", "1025"],  # Stack limit
        "256": ["255", "257"],  # Byte range
        "32": ["31", "33"],  # Word size
        "2**256": ["2**256 - 1", "2**256 + 1"],
        "2**255": ["2**255 - 1", "2**255 + 1"],
    }

    def generate_mutations(self, source: str, file_path: str) -> Iterator[Mutation]:
        lines = source.split("\n")
        for line_num, line in enumerate(lines, 1):
            if line.strip().startswith("#"):
                continue

            for boundary, replacements in self.BOUNDARIES.items():
                if boundary in line:
                    for replacement in replacements:
                        mutated_line = line.replace(boundary, replacement, 1)
                        yield Mutation(
                            mutation_type=MutationType.BOUNDARY_CHANGE,
                            file_path=file_path,
                            line_number=line_num,
                            original=line.strip(),
                            mutated=mutated_line.strip(),
                            description=f"Change boundary {boundary} to {replacement}",
                        )


class ConstantChangeOperator(MutationOperator):
    """Change specific EVM constants."""

    name = "constant_change"
    description = "Modifies EVM constants"

    CONSTANTS = {
        "MAX_U256": "MAX_U256 - 1",
        "ZERO_ADDRESS": 'b"\\x00" * 19 + b"\\x01"',
    }

    def generate_mutations(self, source: str, file_path: str) -> Iterator[Mutation]:
        lines = source.split("\n")
        for line_num, line in enumerate(lines, 1):
            if line.strip().startswith("#"):
                continue

            for constant, replacement in self.CONSTANTS.items():
                if constant in line and "=" not in line[: line.index(constant)]:
                    mutated_line = line.replace(constant, replacement, 1)
                    yield Mutation(
                        mutation_type=MutationType.CONSTANT_CHANGE,
                        file_path=file_path,
                        line_number=line_num,
                        original=line.strip(),
                        mutated=mutated_line.strip(),
                        description=f"Change constant {constant}",
                    )


# All available operators
ALL_OPERATORS: list[type[MutationOperator]] = [
    ArithmeticSwapOperator,
    ComparisonSwapOperator,
    OffByOneOperator,
    GasCostOperator,
    LogicNegateOperator,
    ReturnValueOperator,
    BoundaryChangeOperator,
    ConstantChangeOperator,
]


def get_operator(name: str) -> type[MutationOperator] | None:
    """Get operator class by name."""
    for op in ALL_OPERATORS:
        if op.name == name:
            return op
    return None


def get_all_operators() -> list[MutationOperator]:
    """Get instances of all operators."""
    return [op() for op in ALL_OPERATORS]
