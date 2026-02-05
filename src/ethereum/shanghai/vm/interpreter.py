"""Shanghai EVM interpreter with EIP-3855 (PUSH0) support.

EIP-3855: PUSH0 Instruction
- Adds new opcode PUSH0 (0x5F) that pushes the value 0 onto the stack
- Gas cost: 2 (G_BASE)
- More efficient than PUSH1 0x00 which costs 3 gas
"""

from __future__ import annotations

from ethereum.common.types import (
    Environment,
    ExecutionResult,
    Log,
    Message,
    Opcode,
    State,
)
from ethereum.frontier.vm.gas import GasSchedule
from ethereum.frontier.vm.interpreter import (
    EVMError,
    Interpreter,
    InvalidJumpError,
    InvalidOpcodeError,
    OutOfGasError,
    WriteProtectionError,
)
from ethereum.frontier.vm.memory import Memory
from ethereum.frontier.vm.stack import Stack, StackOverflowError, StackUnderflowError


class ShanghaiGasSchedule(GasSchedule):
    """Gas schedule with Shanghai modifications."""

    # EIP-3855: PUSH0 costs G_BASE (2)
    G_PUSH0: int = 2  # Same as G_BASE


class ShanghaiInterpreter(Interpreter):
    """
    EVM interpreter for the Shanghai fork.

    Key changes:
    - EIP-3855: PUSH0 opcode (0x5F) that pushes 0 onto the stack
    - EIP-3651: Warm COINBASE
    - EIP-3860: Limit and meter initcode
    - EIP-4895: Beacon chain push withdrawals as operations
    """

    fork_name: str = "Shanghai"

    def __init__(
        self,
        state: State,
        env: Environment,
        gas_schedule: type[GasSchedule] = ShanghaiGasSchedule,
    ) -> None:
        super().__init__(state, env, gas_schedule)

    def execute(self, message: Message) -> ExecutionResult:
        """
        Execute a message call with Shanghai rules.

        Supports PUSH0 opcode (0x5F).
        """
        if message.depth > 1024:
            return ExecutionResult(
                success=False,
                gas_used=message.gas,
                gas_remaining=0,
                error="Call depth exceeded",
            )

        stack = Stack()
        memory = Memory()
        pc = 0
        gas_remaining = message.gas
        logs: list[Log] = []
        code = message.code

        valid_jumpdests = self._find_jumpdests(code)

        try:
            while pc < len(code):
                opcode_byte = code[pc]

                # Handle PUSH0 (EIP-3855) - supported in Shanghai
                if opcode_byte == Opcode.PUSH0:
                    gas_remaining = self._charge_gas(gas_remaining, ShanghaiGasSchedule.G_PUSH0)
                    stack.push(0)
                    pc += 1
                    continue

                # Dispatch other opcodes to parent implementation
                result = self._execute_opcode(
                    opcode_byte,
                    pc,
                    code,
                    stack,
                    memory,
                    message,
                    gas_remaining,
                    logs,
                    valid_jumpdests,
                )

                if result.done:
                    return ExecutionResult(
                        success=result.success,
                        gas_used=message.gas - result.gas_remaining,
                        gas_remaining=result.gas_remaining,
                        return_data=result.return_data,
                        logs=logs,
                        error=result.error,
                        created_address=result.created_address,
                    )

                pc = result.pc
                gas_remaining = result.gas_remaining

        except StackOverflowError as e:
            return ExecutionResult(
                success=False,
                gas_used=message.gas,
                gas_remaining=0,
                error=f"Stack overflow: {e}",
            )
        except StackUnderflowError as e:
            return ExecutionResult(
                success=False,
                gas_used=message.gas,
                gas_remaining=0,
                error=f"Stack underflow: {e}",
            )
        except OutOfGasError:
            return ExecutionResult(
                success=False,
                gas_used=message.gas,
                gas_remaining=0,
                error="Out of gas",
            )
        except InvalidOpcodeError as e:
            return ExecutionResult(
                success=False,
                gas_used=message.gas,
                gas_remaining=0,
                error=str(e),
            )
        except InvalidJumpError as e:
            return ExecutionResult(
                success=False,
                gas_used=message.gas,
                gas_remaining=0,
                error=str(e),
            )
        except WriteProtectionError as e:
            return ExecutionResult(
                success=False,
                gas_used=message.gas,
                gas_remaining=0,
                error=str(e),
            )
        except EVMError as e:
            return ExecutionResult(
                success=False,
                gas_used=message.gas,
                gas_remaining=0,
                error=str(e),
            )

        return ExecutionResult(
            success=True,
            gas_used=message.gas - gas_remaining,
            gas_remaining=gas_remaining,
            logs=logs,
        )
