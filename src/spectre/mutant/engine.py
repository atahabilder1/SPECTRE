"""Mutation testing engine for EVM specifications."""

from __future__ import annotations

import shutil
import subprocess
import sys
import tempfile
from collections.abc import Iterator
from dataclasses import dataclass, field
from enum import Enum, auto
from pathlib import Path

from spectre.mutant.operators import (
    Mutation,
    MutationOperator,
    get_all_operators,
)


class MutantStatus(Enum):
    """Status of a mutant after testing."""

    PENDING = auto()
    KILLED = auto()  # Tests detected the mutation
    SURVIVED = auto()  # Tests did not detect the mutation
    TIMEOUT = auto()  # Tests timed out
    ERROR = auto()  # Error running tests


@dataclass
class MutantResult:
    """Result of testing a single mutant."""

    mutation: Mutation
    status: MutantStatus
    test_output: str = ""
    duration: float = 0.0


@dataclass
class MutationTestResult:
    """Overall result of mutation testing."""

    total_mutants: int = 0
    killed: int = 0
    survived: int = 0
    timeout: int = 0
    errors: int = 0
    results: list[MutantResult] = field(default_factory=list)

    @property
    def mutation_score(self) -> float:
        """Calculate mutation score (killed / total)."""
        if self.total_mutants == 0:
            return 0.0
        return self.killed / self.total_mutants * 100

    @property
    def survivors(self) -> list[MutantResult]:
        """Get list of surviving mutants."""
        return [r for r in self.results if r.status == MutantStatus.SURVIVED]


class MutationEngine:
    """
    Mutation testing engine for EVM specifications.

    Generates mutants from source files and runs tests to detect them.
    """

    def __init__(
        self,
        source_dir: Path,
        test_dir: Path,
        operators: list[MutationOperator] | None = None,
        timeout: int = 60,
        parallel: int = 1,
    ) -> None:
        """
        Initialize mutation engine.

        Args:
            source_dir: Directory containing source files to mutate
            test_dir: Directory containing test files
            operators: Mutation operators to use (default: all)
            timeout: Timeout for running tests in seconds
            parallel: Number of parallel test runs (not yet implemented)
        """
        self.source_dir = Path(source_dir)
        self.test_dir = Path(test_dir)
        self.operators = operators or get_all_operators()
        self.timeout = timeout
        self.parallel = parallel

    def find_source_files(self, pattern: str = "*.py") -> list[Path]:
        """Find all source files to mutate."""
        return list(self.source_dir.rglob(pattern))

    def generate_mutations(self, file_path: Path) -> Iterator[Mutation]:
        """Generate all mutations for a single file."""
        source = file_path.read_text()
        rel_path = str(file_path.relative_to(self.source_dir))

        for operator in self.operators:
            yield from operator.generate_mutations(source, rel_path)

    def generate_all_mutations(self) -> Iterator[Mutation]:
        """Generate mutations for all source files."""
        for file_path in self.find_source_files():
            yield from self.generate_mutations(file_path)

    def apply_mutation(self, mutation: Mutation, target_dir: Path) -> Path:
        """
        Apply a mutation to a copy of the source.

        Args:
            mutation: The mutation to apply
            target_dir: Directory to copy sources to

        Returns:
            Path to the mutated file
        """
        # Copy source directory to target
        if target_dir.exists():
            shutil.rmtree(target_dir)
        shutil.copytree(self.source_dir, target_dir)

        # Apply the mutation
        file_path = target_dir / mutation.file_path
        source = file_path.read_text()
        lines = source.split("\n")

        # Replace the mutated line
        line_idx = mutation.line_number - 1
        if 0 <= line_idx < len(lines):
            # Find the original content and replace
            original_line = lines[line_idx]
            # Calculate indentation
            indent = len(original_line) - len(original_line.lstrip())
            lines[line_idx] = " " * indent + mutation.mutated

        file_path.write_text("\n".join(lines))
        return file_path

    def run_tests(self, source_dir: Path) -> tuple[bool, str]:
        """
        Run tests against mutated source.

        Args:
            source_dir: Directory containing mutated source

        Returns:
            Tuple of (tests_passed, output)
        """
        try:
            result = subprocess.run(
                [
                    sys.executable,
                    "-m",
                    "pytest",
                    str(self.test_dir),
                    "-x",  # Stop on first failure
                    "--tb=no",  # No traceback
                    "-q",  # Quiet output
                ],
                capture_output=True,
                text=True,
                timeout=self.timeout,
                cwd=source_dir.parent,
                env={
                    **dict(__import__("os").environ),
                    "PYTHONPATH": str(source_dir),
                },
            )
            passed = result.returncode == 0
            output = result.stdout + result.stderr
            return passed, output

        except subprocess.TimeoutExpired:
            return False, "TIMEOUT"
        except Exception as e:
            return False, f"ERROR: {e}"

    def test_mutant(self, mutation: Mutation) -> MutantResult:
        """Test a single mutant."""
        import time

        start_time = time.time()

        with tempfile.TemporaryDirectory() as tmp_dir:
            target_dir = Path(tmp_dir) / "src"

            try:
                self.apply_mutation(mutation, target_dir)
                passed, output = self.run_tests(target_dir)

                duration = time.time() - start_time

                if "TIMEOUT" in output:
                    status = MutantStatus.TIMEOUT
                elif "ERROR" in output:
                    status = MutantStatus.ERROR
                elif passed:
                    status = MutantStatus.SURVIVED
                else:
                    status = MutantStatus.KILLED

                return MutantResult(
                    mutation=mutation,
                    status=status,
                    test_output=output[:500],  # Truncate output
                    duration=duration,
                )

            except Exception as e:
                return MutantResult(
                    mutation=mutation,
                    status=MutantStatus.ERROR,
                    test_output=str(e),
                    duration=time.time() - start_time,
                )

    def run(
        self,
        max_mutants: int | None = None,
        file_filter: str | None = None,
    ) -> MutationTestResult:
        """
        Run mutation testing.

        Args:
            max_mutants: Maximum number of mutants to test
            file_filter: Only mutate files matching this pattern

        Returns:
            MutationTestResult with all results
        """
        result = MutationTestResult()
        mutations = list(self.generate_all_mutations())

        # Apply file filter
        if file_filter:
            mutations = [m for m in mutations if file_filter in m.file_path]

        # Limit number of mutants
        if max_mutants:
            mutations = mutations[:max_mutants]

        result.total_mutants = len(mutations)

        for mutation in mutations:
            mutant_result = self.test_mutant(mutation)
            result.results.append(mutant_result)

            if mutant_result.status == MutantStatus.KILLED:
                result.killed += 1
            elif mutant_result.status == MutantStatus.SURVIVED:
                result.survived += 1
            elif mutant_result.status == MutantStatus.TIMEOUT:
                result.timeout += 1
            else:
                result.errors += 1

        return result

    def run_quick(
        self,
        sample_size: int = 10,
    ) -> MutationTestResult:
        """
        Run a quick mutation test with sampling.

        Args:
            sample_size: Number of mutations to sample

        Returns:
            MutationTestResult with sampled results
        """
        import random

        mutations = list(self.generate_all_mutations())
        if len(mutations) > sample_size:
            mutations = random.sample(mutations, sample_size)

        return self.run(max_mutants=len(mutations))
