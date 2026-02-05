"""Delta debugging for minimizing failing test cases."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass

from spectre.phantom.executor import (
    DifferentialExecutor,
    Divergence,
    Fork,
)
from spectre.phantom.generator import GeneratedBytecode, GeneratorStrategy


@dataclass
class MinimizationResult:
    """Result of minimizing a test case."""

    original: bytes
    minimized: bytes
    original_size: int
    minimized_size: int
    iterations: int
    reduction_percent: float

    @classmethod
    def from_bytecodes(
        cls,
        original: bytes,
        minimized: bytes,
        iterations: int,
    ) -> MinimizationResult:
        original_size = len(original)
        minimized_size = len(minimized)
        reduction = (1 - minimized_size / original_size) * 100 if original_size > 0 else 0

        return cls(
            original=original,
            minimized=minimized,
            original_size=original_size,
            minimized_size=minimized_size,
            iterations=iterations,
            reduction_percent=reduction,
        )


class DeltaDebugger:
    """
    Delta debugging algorithm for minimizing failing test cases.

    Given a failing bytecode, finds the minimal bytecode that still fails.
    """

    def __init__(
        self,
        executor: DifferentialExecutor | None = None,
        fork_a: Fork = Fork.FRONTIER,
        fork_b: Fork = Fork.SHANGHAI,
    ) -> None:
        self.executor = executor or DifferentialExecutor(fork_a, fork_b)
        self.fork_a = fork_a
        self.fork_b = fork_b

    def _test_bytecode(self, bytecode: bytes) -> bool:
        """Test if bytecode produces a divergence."""
        generated = GeneratedBytecode(
            code=bytecode,
            strategy=GeneratorStrategy.RANDOM,
            description="Minimization candidate",
        )
        divergences = self.executor.execute_differential(generated)
        # Return True if we find unexpected divergences
        return any(not d.is_expected() for d in divergences)

    def _split(self, bytecode: bytes, n: int) -> list[bytes]:
        """Split bytecode into n roughly equal parts."""
        if n <= 0:
            return [bytecode]

        chunk_size = max(1, len(bytecode) // n)
        chunks = []

        for i in range(0, len(bytecode), chunk_size):
            chunks.append(bytecode[i:i + chunk_size])

        return chunks

    def _complement(self, bytecode: bytes, chunk: bytes, start: int) -> bytes:
        """Return bytecode with chunk removed."""
        end = start + len(chunk)
        return bytecode[:start] + bytecode[end:]

    def minimize_ddmin(
        self,
        bytecode: bytes,
        max_iterations: int = 1000,
    ) -> MinimizationResult:
        """
        Apply ddmin algorithm to minimize bytecode.

        The ddmin algorithm works by:
        1. Try removing half the input
        2. If still fails, try removing smaller chunks
        3. Repeat until no more reductions possible

        Args:
            bytecode: Original failing bytecode
            max_iterations: Maximum iterations to prevent infinite loops

        Returns:
            MinimizationResult with minimized bytecode
        """
        if not self._test_bytecode(bytecode):
            # Original doesn't even fail
            return MinimizationResult.from_bytecodes(bytecode, bytecode, 0)

        n = 2  # Start with 2 chunks
        iterations = 0
        current = bytecode

        while len(current) > 1 and iterations < max_iterations:
            iterations += 1
            chunks = self._split(current, n)

            found_reduction = False

            # Try each chunk
            for i, chunk in enumerate(chunks):
                # Calculate start position
                start = sum(len(chunks[j]) for j in range(i))
                candidate = self._complement(current, chunk, start)

                if len(candidate) > 0 and self._test_bytecode(candidate):
                    current = candidate
                    n = max(2, n - 1)  # Reduce chunk count
                    found_reduction = True
                    break

            if not found_reduction:
                if n >= len(current):
                    # Can't split any further
                    break
                n = min(n * 2, len(current))  # Try smaller chunks

        return MinimizationResult.from_bytecodes(bytecode, current, iterations)

    def minimize_linear(
        self,
        bytecode: bytes,
        max_iterations: int = 1000,
    ) -> MinimizationResult:
        """
        Simple linear minimization - try removing each byte.

        Slower than ddmin but may find smaller results.
        """
        if not self._test_bytecode(bytecode):
            return MinimizationResult.from_bytecodes(bytecode, bytecode, 0)

        current = bytecode
        iterations = 0
        changed = True

        while changed and iterations < max_iterations:
            changed = False
            i = 0

            while i < len(current) and iterations < max_iterations:
                iterations += 1
                candidate = current[:i] + current[i + 1:]

                if len(candidate) > 0 and self._test_bytecode(candidate):
                    current = candidate
                    changed = True
                    # Don't increment i, as we removed a byte
                else:
                    i += 1

        return MinimizationResult.from_bytecodes(bytecode, current, iterations)

    def minimize(
        self,
        bytecode: bytes,
        strategy: str = "ddmin",
        max_iterations: int = 1000,
    ) -> MinimizationResult:
        """
        Minimize bytecode using specified strategy.

        Args:
            bytecode: Original failing bytecode
            strategy: "ddmin" or "linear"
            max_iterations: Maximum iterations

        Returns:
            MinimizationResult with minimized bytecode
        """
        if strategy == "ddmin":
            return self.minimize_ddmin(bytecode, max_iterations)
        elif strategy == "linear":
            return self.minimize_linear(bytecode, max_iterations)
        else:
            raise ValueError(f"Unknown strategy: {strategy}")

    def minimize_divergence(
        self,
        divergence: Divergence,
        strategy: str = "ddmin",
    ) -> MinimizationResult:
        """Minimize the bytecode from a divergence."""
        return self.minimize(divergence.bytecode.code, strategy)


class CustomMinimizer:
    """Minimizer with custom test predicate."""

    def __init__(
        self,
        test_fn: Callable[[bytes], bool],
    ) -> None:
        """
        Args:
            test_fn: Function that returns True if bytecode "fails"
                     (i.e., exhibits the behavior we're trying to minimize)
        """
        self.test_fn = test_fn

    def minimize(
        self,
        bytecode: bytes,
        max_iterations: int = 1000,
    ) -> MinimizationResult:
        """Minimize bytecode using ddmin algorithm."""
        if not self.test_fn(bytecode):
            return MinimizationResult.from_bytecodes(bytecode, bytecode, 0)

        n = 2
        iterations = 0
        current = bytecode

        while len(current) > 1 and iterations < max_iterations:
            iterations += 1
            chunk_size = max(1, len(current) // n)
            found_reduction = False

            for i in range(n):
                start = i * chunk_size
                end = start + chunk_size if i < n - 1 else len(current)
                candidate = current[:start] + current[end:]

                if len(candidate) > 0 and self.test_fn(candidate):
                    current = candidate
                    n = max(2, n - 1)
                    found_reduction = True
                    break

            if not found_reduction:
                if n >= len(current):
                    break
                n = min(n * 2, len(current))

        return MinimizationResult.from_bytecodes(bytecode, current, iterations)
