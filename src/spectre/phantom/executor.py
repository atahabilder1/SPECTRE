"""Differential execution engine for comparing EVM implementations."""

from __future__ import annotations

from collections.abc import Callable, Iterator
from dataclasses import dataclass, field
from enum import Enum, auto

from ethereum.common.types import (
    ZERO_ADDRESS,
    Account,
    Environment,
    ExecutionResult,
    Message,
    State,
)
from ethereum.frontier.vm.interpreter import Interpreter as FrontierInterpreter
from ethereum.homestead.vm.interpreter import HomesteadInterpreter
from ethereum.shanghai.vm.interpreter import ShanghaiInterpreter
from spectre.phantom.generator import GeneratedBytecode


class Fork(Enum):
    """Supported EVM forks."""

    FRONTIER = auto()
    HOMESTEAD = auto()
    SHANGHAI = auto()


class DivergenceType(Enum):
    """Types of divergence between implementations."""

    SUCCESS_MISMATCH = auto()  # One succeeds, other fails
    RETURN_DATA_MISMATCH = auto()  # Different return data
    GAS_USED_MISMATCH = auto()  # Different gas consumption
    ERROR_MISMATCH = auto()  # Different error messages
    LOGS_MISMATCH = auto()  # Different logs emitted
    STATE_MISMATCH = auto()  # Different final state


@dataclass
class ExecutionTrace:
    """Trace of a single execution."""

    fork: Fork
    result: ExecutionResult
    final_state: State


@dataclass
class Divergence:
    """A divergence found between implementations."""

    divergence_type: DivergenceType
    bytecode: GeneratedBytecode
    trace_a: ExecutionTrace
    trace_b: ExecutionTrace
    description: str

    def is_expected(self) -> bool:
        """Check if this divergence is expected based on EIP changes."""
        # PUSH0 is only available in Shanghai
        if b"\x5f" in self.bytecode.code:
            if self.trace_a.fork != Fork.SHANGHAI or self.trace_b.fork != Fork.SHANGHAI:
                return True

        return False


@dataclass
class DifferentialResult:
    """Result of differential fuzzing."""

    total_executions: int = 0
    divergences: list[Divergence] = field(default_factory=list)
    expected_divergences: int = 0
    unexpected_divergences: int = 0

    @property
    def divergence_rate(self) -> float:
        """Calculate divergence rate."""
        if self.total_executions == 0:
            return 0.0
        return len(self.divergences) / self.total_executions * 100


class DifferentialExecutor:
    """
    Execute bytecode across different EVM implementations.

    Compares execution results to find divergences.
    """

    def __init__(
        self,
        fork_a: Fork = Fork.FRONTIER,
        fork_b: Fork = Fork.SHANGHAI,
        gas_limit: int = 1_000_000,
    ) -> None:
        self.fork_a = fork_a
        self.fork_b = fork_b
        self.gas_limit = gas_limit

    def _create_interpreter(
        self, fork: Fork, state: State, env: Environment
    ) -> FrontierInterpreter | HomesteadInterpreter | ShanghaiInterpreter:
        """Create interpreter for the specified fork."""
        if fork == Fork.FRONTIER:
            return FrontierInterpreter(state, env)
        elif fork == Fork.HOMESTEAD:
            return HomesteadInterpreter(state, env)
        elif fork == Fork.SHANGHAI:
            return ShanghaiInterpreter(state, env)
        else:
            raise ValueError(f"Unknown fork: {fork}")

    def _create_initial_state(self) -> State:
        """Create initial state for execution."""
        state = State()
        # Fund test accounts
        state.set_account(
            ZERO_ADDRESS,
            Account(balance=10**18),
        )
        state.set_account(
            b"\x00" * 19 + b"\x01",
            Account(balance=10**18),
        )
        state.set_account(
            b"\x00" * 19 + b"\x02",
            Account(balance=10**18),
        )
        return state

    def _create_environment(self) -> Environment:
        """Create execution environment."""
        return Environment(
            caller=b"\x00" * 19 + b"\x01",
            origin=b"\x00" * 19 + b"\x01",
            coinbase=b"\x00" * 19 + b"\xff",
            number=1000000,
            gas_limit=self.gas_limit,
            gas_price=1,
            timestamp=1000000,
            difficulty=1,
            chain_id=1,
        )

    def execute_single(
        self, code: bytes, fork: Fork
    ) -> ExecutionTrace:
        """Execute bytecode on a single fork."""
        state = self._create_initial_state()
        env = self._create_environment()

        # Deploy code to test contract
        contract_addr = b"\x00" * 19 + b"\x02"
        state.set_code(contract_addr, code)

        interpreter = self._create_interpreter(fork, state, env)

        message = Message(
            caller=b"\x00" * 19 + b"\x01",
            target=contract_addr,
            value=0,
            data=b"",
            gas=self.gas_limit,
            depth=0,
            code=code,
        )

        result = interpreter.execute(message)

        return ExecutionTrace(
            fork=fork,
            result=result,
            final_state=state,
        )

    def compare_executions(
        self,
        trace_a: ExecutionTrace,
        trace_b: ExecutionTrace,
        bytecode: GeneratedBytecode,
    ) -> list[Divergence]:
        """Compare two execution traces for divergences."""
        divergences: list[Divergence] = []

        # Compare success status
        if trace_a.result.success != trace_b.result.success:
            divergences.append(Divergence(
                divergence_type=DivergenceType.SUCCESS_MISMATCH,
                bytecode=bytecode,
                trace_a=trace_a,
                trace_b=trace_b,
                description=f"Success mismatch: {trace_a.result.success} vs {trace_b.result.success}",
            ))

        # Compare return data
        if trace_a.result.return_data != trace_b.result.return_data:
            divergences.append(Divergence(
                divergence_type=DivergenceType.RETURN_DATA_MISMATCH,
                bytecode=bytecode,
                trace_a=trace_a,
                trace_b=trace_b,
                description=f"Return data mismatch: {len(trace_a.result.return_data)} vs {len(trace_b.result.return_data)} bytes",
            ))

        # Compare gas used (allow small variations)
        gas_diff = abs(trace_a.result.gas_used - trace_b.result.gas_used)
        if gas_diff > 0 and trace_a.result.success == trace_b.result.success:
            divergences.append(Divergence(
                divergence_type=DivergenceType.GAS_USED_MISMATCH,
                bytecode=bytecode,
                trace_a=trace_a,
                trace_b=trace_b,
                description=f"Gas mismatch: {trace_a.result.gas_used} vs {trace_b.result.gas_used} (diff: {gas_diff})",
            ))

        # Compare logs
        if len(trace_a.result.logs) != len(trace_b.result.logs):
            divergences.append(Divergence(
                divergence_type=DivergenceType.LOGS_MISMATCH,
                bytecode=bytecode,
                trace_a=trace_a,
                trace_b=trace_b,
                description=f"Log count mismatch: {len(trace_a.result.logs)} vs {len(trace_b.result.logs)}",
            ))

        return divergences

    def execute_differential(
        self, bytecode: GeneratedBytecode
    ) -> list[Divergence]:
        """Execute bytecode on both forks and compare."""
        trace_a = self.execute_single(bytecode.code, self.fork_a)
        trace_b = self.execute_single(bytecode.code, self.fork_b)

        return self.compare_executions(trace_a, trace_b, bytecode)

    def run(
        self,
        bytecodes: Iterator[GeneratedBytecode],
        max_divergences: int | None = None,
        callback: Callable[[Divergence], None] | None = None,
    ) -> DifferentialResult:
        """
        Run differential fuzzing on generated bytecode.

        Args:
            bytecodes: Iterator of bytecode samples
            max_divergences: Stop after finding this many divergences
            callback: Called for each divergence found

        Returns:
            DifferentialResult with all findings
        """
        result = DifferentialResult()

        for bytecode in bytecodes:
            result.total_executions += 1

            divergences = self.execute_differential(bytecode)

            for div in divergences:
                if div.is_expected():
                    result.expected_divergences += 1
                else:
                    result.unexpected_divergences += 1
                    result.divergences.append(div)

                    if callback:
                        callback(div)

                    if max_divergences and result.unexpected_divergences >= max_divergences:
                        return result

        return result

    def find_divergence(
        self,
        bytecodes: Iterator[GeneratedBytecode],
    ) -> Divergence | None:
        """Find the first unexpected divergence."""
        result = self.run(bytecodes, max_divergences=1)
        return result.divergences[0] if result.divergences else None


def compare_forks(
    fork_a: Fork,
    fork_b: Fork,
    bytecode: bytes,
) -> list[Divergence]:
    """Quick helper to compare two forks on specific bytecode."""
    executor = DifferentialExecutor(fork_a, fork_b)
    generated = GeneratedBytecode(
        code=bytecode,
        strategy=None,  # type: ignore
        description="Manual test",
    )
    return executor.execute_differential(generated)
