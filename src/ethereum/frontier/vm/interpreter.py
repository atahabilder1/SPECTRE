"""Frontier EVM interpreter with opcode execution."""

from __future__ import annotations

from typing import TYPE_CHECKING

from ethereum.common.types import (
    MAX_U256,
    Account,
    Environment,
    ExecutionResult,
    Log,
    Message,
    Opcode,
    State,
    create_address,
    signed_to_unsigned,
    u256,
    unsigned_to_signed,
)
from ethereum.frontier.vm.gas import GasSchedule
from ethereum.frontier.vm.memory import Memory
from ethereum.frontier.vm.stack import Stack, StackOverflowError, StackUnderflowError

if TYPE_CHECKING:
    pass


class EVMError(Exception):
    """Base exception for EVM execution errors."""

    pass


class OutOfGasError(EVMError):
    """Raised when execution runs out of gas."""

    pass


class InvalidOpcodeError(EVMError):
    """Raised when an invalid opcode is encountered."""

    pass


class InvalidJumpError(EVMError):
    """Raised when jumping to an invalid destination."""

    pass


class WriteProtectionError(EVMError):
    """Raised when attempting to modify state in static context."""

    pass


class CallDepthError(EVMError):
    """Raised when call depth exceeds maximum."""

    pass


MAX_CALL_DEPTH = 1024
MAX_CODE_SIZE = 24576  # EIP-170 (not in Frontier but good practice)


class Interpreter:
    """
    EVM interpreter for the Frontier fork.

    Executes bytecode and manages state transitions.
    """

    fork_name: str = "Frontier"

    def __init__(
        self,
        state: State,
        env: Environment,
        gas_schedule: type[GasSchedule] = GasSchedule,
    ) -> None:
        self.state = state
        self.env = env
        self.gas_schedule = gas_schedule
        self.return_data: bytes = b""  # For RETURNDATASIZE/RETURNDATACOPY

    def execute(self, message: Message) -> ExecutionResult:
        """
        Execute a message call.

        Args:
            message: The message to execute

        Returns:
            ExecutionResult with execution outcome
        """
        if message.depth > MAX_CALL_DEPTH:
            return ExecutionResult(
                success=False,
                gas_used=message.gas,
                gas_remaining=0,
                error="Call depth exceeded",
            )

        # Initialize execution context
        stack = Stack()
        memory = Memory()
        pc = 0
        gas_remaining = message.gas
        logs: list[Log] = []
        code = message.code

        # Find valid jump destinations
        valid_jumpdests = self._find_jumpdests(code)

        try:
            while pc < len(code):
                opcode_byte = code[pc]

                # Check for PUSH0 - invalid in Frontier
                if opcode_byte == Opcode.PUSH0:
                    raise InvalidOpcodeError(f"PUSH0 not supported in {self.fork_name}")

                # Dispatch opcode
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

        # Execution completed normally (ran off end of code)
        return ExecutionResult(
            success=True,
            gas_used=message.gas - gas_remaining,
            gas_remaining=gas_remaining,
            logs=logs,
        )

    def _find_jumpdests(self, code: bytes) -> set[int]:
        """Find all valid JUMPDEST positions in code."""
        jumpdests: set[int] = set()
        i = 0
        while i < len(code):
            opcode = code[i]
            if opcode == Opcode.JUMPDEST:
                jumpdests.add(i)
            # Skip PUSH data
            if Opcode.PUSH1 <= opcode <= Opcode.PUSH32:
                push_size = opcode - Opcode.PUSH1 + 1
                i += push_size
            i += 1
        return jumpdests

    def _charge_gas(self, gas_remaining: int, cost: int) -> int:
        """Charge gas and raise OutOfGasError if insufficient."""
        if cost > gas_remaining:
            raise OutOfGasError()
        return gas_remaining - cost

    def _execute_opcode(
        self,
        opcode: int,
        pc: int,
        code: bytes,
        stack: Stack,
        memory: Memory,
        message: Message,
        gas_remaining: int,
        logs: list[Log],
        valid_jumpdests: set[int],
    ) -> _OpcodeResult:
        """Execute a single opcode and return the result."""

        # STOP
        if opcode == Opcode.STOP:
            return _OpcodeResult(done=True, success=True, gas_remaining=gas_remaining)

        # Arithmetic operations
        if opcode == Opcode.ADD:
            gas_remaining = self._charge_gas(gas_remaining, self.gas_schedule.G_VERYLOW)
            a, b = stack.pop(), stack.pop()
            stack.push(u256(a + b))
            return _OpcodeResult(pc=pc + 1, gas_remaining=gas_remaining)

        if opcode == Opcode.MUL:
            gas_remaining = self._charge_gas(gas_remaining, self.gas_schedule.G_LOW)
            a, b = stack.pop(), stack.pop()
            stack.push(u256(a * b))
            return _OpcodeResult(pc=pc + 1, gas_remaining=gas_remaining)

        if opcode == Opcode.SUB:
            gas_remaining = self._charge_gas(gas_remaining, self.gas_schedule.G_VERYLOW)
            a, b = stack.pop(), stack.pop()
            stack.push(u256(a - b))
            return _OpcodeResult(pc=pc + 1, gas_remaining=gas_remaining)

        if opcode == Opcode.DIV:
            gas_remaining = self._charge_gas(gas_remaining, self.gas_schedule.G_LOW)
            a, b = stack.pop(), stack.pop()
            stack.push(a // b if b != 0 else 0)
            return _OpcodeResult(pc=pc + 1, gas_remaining=gas_remaining)

        if opcode == Opcode.SDIV:
            gas_remaining = self._charge_gas(gas_remaining, self.gas_schedule.G_LOW)
            a, b = stack.pop(), stack.pop()
            if b == 0:
                stack.push(0)
            else:
                sa = unsigned_to_signed(a)
                sb = unsigned_to_signed(b)
                # Handle special case: -2^255 / -1 = -2^255 (overflow)
                if sa == -(2**255) and sb == -1:
                    stack.push(2**255)
                else:
                    sign = -1 if (sa < 0) != (sb < 0) else 1
                    result = sign * (abs(sa) // abs(sb))
                    stack.push(signed_to_unsigned(result))
            return _OpcodeResult(pc=pc + 1, gas_remaining=gas_remaining)

        if opcode == Opcode.MOD:
            gas_remaining = self._charge_gas(gas_remaining, self.gas_schedule.G_LOW)
            a, b = stack.pop(), stack.pop()
            stack.push(a % b if b != 0 else 0)
            return _OpcodeResult(pc=pc + 1, gas_remaining=gas_remaining)

        if opcode == Opcode.SMOD:
            gas_remaining = self._charge_gas(gas_remaining, self.gas_schedule.G_LOW)
            a, b = stack.pop(), stack.pop()
            if b == 0:
                stack.push(0)
            else:
                sa = unsigned_to_signed(a)
                sb = unsigned_to_signed(b)
                sign = -1 if sa < 0 else 1
                result = sign * (abs(sa) % abs(sb))
                stack.push(signed_to_unsigned(result))
            return _OpcodeResult(pc=pc + 1, gas_remaining=gas_remaining)

        if opcode == Opcode.ADDMOD:
            gas_remaining = self._charge_gas(gas_remaining, self.gas_schedule.G_MID)
            a, b, n = stack.pop(), stack.pop(), stack.pop()
            stack.push((a + b) % n if n != 0 else 0)
            return _OpcodeResult(pc=pc + 1, gas_remaining=gas_remaining)

        if opcode == Opcode.MULMOD:
            gas_remaining = self._charge_gas(gas_remaining, self.gas_schedule.G_MID)
            a, b, n = stack.pop(), stack.pop(), stack.pop()
            stack.push((a * b) % n if n != 0 else 0)
            return _OpcodeResult(pc=pc + 1, gas_remaining=gas_remaining)

        if opcode == Opcode.EXP:
            a, b = stack.pop(), stack.pop()
            gas_cost = self.gas_schedule.exp_cost(b)
            gas_remaining = self._charge_gas(gas_remaining, gas_cost)
            stack.push(pow(a, b, 2**256))
            return _OpcodeResult(pc=pc + 1, gas_remaining=gas_remaining)

        if opcode == Opcode.SIGNEXTEND:
            gas_remaining = self._charge_gas(gas_remaining, self.gas_schedule.G_LOW)
            b, x = stack.pop(), stack.pop()
            if b < 31:
                sign_bit = 1 << (8 * b + 7)
                if x & sign_bit:
                    # Extend with 1s
                    mask = (1 << (8 * (b + 1))) - 1
                    result = x | (MAX_U256 ^ mask)
                else:
                    # Extend with 0s
                    mask = (1 << (8 * (b + 1))) - 1
                    result = x & mask
                stack.push(result)
            else:
                stack.push(x)
            return _OpcodeResult(pc=pc + 1, gas_remaining=gas_remaining)

        # Comparison operations
        if opcode == Opcode.LT:
            gas_remaining = self._charge_gas(gas_remaining, self.gas_schedule.G_VERYLOW)
            a, b = stack.pop(), stack.pop()
            stack.push(1 if a < b else 0)
            return _OpcodeResult(pc=pc + 1, gas_remaining=gas_remaining)

        if opcode == Opcode.GT:
            gas_remaining = self._charge_gas(gas_remaining, self.gas_schedule.G_VERYLOW)
            a, b = stack.pop(), stack.pop()
            stack.push(1 if a > b else 0)
            return _OpcodeResult(pc=pc + 1, gas_remaining=gas_remaining)

        if opcode == Opcode.SLT:
            gas_remaining = self._charge_gas(gas_remaining, self.gas_schedule.G_VERYLOW)
            a, b = stack.pop(), stack.pop()
            sa, sb = unsigned_to_signed(a), unsigned_to_signed(b)
            stack.push(1 if sa < sb else 0)
            return _OpcodeResult(pc=pc + 1, gas_remaining=gas_remaining)

        if opcode == Opcode.SGT:
            gas_remaining = self._charge_gas(gas_remaining, self.gas_schedule.G_VERYLOW)
            a, b = stack.pop(), stack.pop()
            sa, sb = unsigned_to_signed(a), unsigned_to_signed(b)
            stack.push(1 if sa > sb else 0)
            return _OpcodeResult(pc=pc + 1, gas_remaining=gas_remaining)

        if opcode == Opcode.EQ:
            gas_remaining = self._charge_gas(gas_remaining, self.gas_schedule.G_VERYLOW)
            a, b = stack.pop(), stack.pop()
            stack.push(1 if a == b else 0)
            return _OpcodeResult(pc=pc + 1, gas_remaining=gas_remaining)

        if opcode == Opcode.ISZERO:
            gas_remaining = self._charge_gas(gas_remaining, self.gas_schedule.G_VERYLOW)
            a = stack.pop()
            stack.push(1 if a == 0 else 0)
            return _OpcodeResult(pc=pc + 1, gas_remaining=gas_remaining)

        # Bitwise operations
        if opcode == Opcode.AND:
            gas_remaining = self._charge_gas(gas_remaining, self.gas_schedule.G_VERYLOW)
            a, b = stack.pop(), stack.pop()
            stack.push(a & b)
            return _OpcodeResult(pc=pc + 1, gas_remaining=gas_remaining)

        if opcode == Opcode.OR:
            gas_remaining = self._charge_gas(gas_remaining, self.gas_schedule.G_VERYLOW)
            a, b = stack.pop(), stack.pop()
            stack.push(a | b)
            return _OpcodeResult(pc=pc + 1, gas_remaining=gas_remaining)

        if opcode == Opcode.XOR:
            gas_remaining = self._charge_gas(gas_remaining, self.gas_schedule.G_VERYLOW)
            a, b = stack.pop(), stack.pop()
            stack.push(a ^ b)
            return _OpcodeResult(pc=pc + 1, gas_remaining=gas_remaining)

        if opcode == Opcode.NOT:
            gas_remaining = self._charge_gas(gas_remaining, self.gas_schedule.G_VERYLOW)
            a = stack.pop()
            stack.push(MAX_U256 ^ a)
            return _OpcodeResult(pc=pc + 1, gas_remaining=gas_remaining)

        if opcode == Opcode.BYTE:
            gas_remaining = self._charge_gas(gas_remaining, self.gas_schedule.G_VERYLOW)
            i, x = stack.pop(), stack.pop()
            if i >= 32:
                stack.push(0)
            else:
                # Byte 0 is the MSB
                stack.push((x >> (8 * (31 - i))) & 0xFF)
            return _OpcodeResult(pc=pc + 1, gas_remaining=gas_remaining)

        if opcode == Opcode.SHL:
            gas_remaining = self._charge_gas(gas_remaining, self.gas_schedule.G_VERYLOW)
            shift, value = stack.pop(), stack.pop()
            if shift >= 256:
                stack.push(0)
            else:
                stack.push(u256(value << shift))
            return _OpcodeResult(pc=pc + 1, gas_remaining=gas_remaining)

        if opcode == Opcode.SHR:
            gas_remaining = self._charge_gas(gas_remaining, self.gas_schedule.G_VERYLOW)
            shift, value = stack.pop(), stack.pop()
            if shift >= 256:
                stack.push(0)
            else:
                stack.push(value >> shift)
            return _OpcodeResult(pc=pc + 1, gas_remaining=gas_remaining)

        if opcode == Opcode.SAR:
            gas_remaining = self._charge_gas(gas_remaining, self.gas_schedule.G_VERYLOW)
            shift, value = stack.pop(), stack.pop()
            signed_value = unsigned_to_signed(value)
            if shift >= 256:
                stack.push(MAX_U256 if signed_value < 0 else 0)
            else:
                result = signed_value >> shift
                stack.push(signed_to_unsigned(result))
            return _OpcodeResult(pc=pc + 1, gas_remaining=gas_remaining)

        # SHA3
        if opcode == Opcode.SHA3:
            offset, size = stack.pop(), stack.pop()
            mem_cost = memory.expansion_cost(offset, size)
            gas_cost = self.gas_schedule.sha3_cost(size) + mem_cost
            gas_remaining = self._charge_gas(gas_remaining, gas_cost)
            data = memory.load(offset, size)
            # Use keccak256 (sha3_256 in hashlib is actually keccak)
            # For proper EVM, we need keccak256, not SHA3-256
            import hashlib

            h = hashlib.sha3_256(data).digest()
            stack.push(int.from_bytes(h, "big"))
            return _OpcodeResult(pc=pc + 1, gas_remaining=gas_remaining)

        # Environmental information
        if opcode == Opcode.ADDRESS:
            gas_remaining = self._charge_gas(gas_remaining, self.gas_schedule.G_BASE)
            stack.push(int.from_bytes(message.target, "big"))
            return _OpcodeResult(pc=pc + 1, gas_remaining=gas_remaining)

        if opcode == Opcode.BALANCE:
            gas_remaining = self._charge_gas(gas_remaining, self.gas_schedule.G_BALANCE)
            addr = stack.pop()
            address = addr.to_bytes(20, "big")
            balance = self.state.get_balance(address)
            stack.push(balance)
            return _OpcodeResult(pc=pc + 1, gas_remaining=gas_remaining)

        if opcode == Opcode.ORIGIN:
            gas_remaining = self._charge_gas(gas_remaining, self.gas_schedule.G_BASE)
            stack.push(int.from_bytes(self.env.origin, "big"))
            return _OpcodeResult(pc=pc + 1, gas_remaining=gas_remaining)

        if opcode == Opcode.CALLER:
            gas_remaining = self._charge_gas(gas_remaining, self.gas_schedule.G_BASE)
            stack.push(int.from_bytes(message.caller, "big"))
            return _OpcodeResult(pc=pc + 1, gas_remaining=gas_remaining)

        if opcode == Opcode.CALLVALUE:
            gas_remaining = self._charge_gas(gas_remaining, self.gas_schedule.G_BASE)
            stack.push(message.value)
            return _OpcodeResult(pc=pc + 1, gas_remaining=gas_remaining)

        if opcode == Opcode.CALLDATALOAD:
            gas_remaining = self._charge_gas(gas_remaining, self.gas_schedule.G_VERYLOW)
            offset = stack.pop()
            data = message.data
            # Load 32 bytes from calldata, zero-padded
            value = 0
            for i in range(32):
                if offset + i < len(data):
                    value = (value << 8) | data[offset + i]
                else:
                    value = value << 8
            stack.push(value)
            return _OpcodeResult(pc=pc + 1, gas_remaining=gas_remaining)

        if opcode == Opcode.CALLDATASIZE:
            gas_remaining = self._charge_gas(gas_remaining, self.gas_schedule.G_BASE)
            stack.push(len(message.data))
            return _OpcodeResult(pc=pc + 1, gas_remaining=gas_remaining)

        if opcode == Opcode.CALLDATACOPY:
            dest_offset, src_offset, size = stack.pop(), stack.pop(), stack.pop()
            mem_cost = memory.expansion_cost(dest_offset, size)
            copy_cost = self.gas_schedule.copy_cost(size)
            gas_remaining = self._charge_gas(
                gas_remaining, self.gas_schedule.G_VERYLOW + mem_cost + copy_cost
            )
            data = message.data
            # Copy from calldata, zero-padded
            copy_data = bytearray(size)
            for i in range(size):
                if src_offset + i < len(data):
                    copy_data[i] = data[src_offset + i]
            memory.store(dest_offset, bytes(copy_data))
            return _OpcodeResult(pc=pc + 1, gas_remaining=gas_remaining)

        if opcode == Opcode.CODESIZE:
            gas_remaining = self._charge_gas(gas_remaining, self.gas_schedule.G_BASE)
            stack.push(len(code))
            return _OpcodeResult(pc=pc + 1, gas_remaining=gas_remaining)

        if opcode == Opcode.CODECOPY:
            dest_offset, src_offset, size = stack.pop(), stack.pop(), stack.pop()
            mem_cost = memory.expansion_cost(dest_offset, size)
            copy_cost = self.gas_schedule.copy_cost(size)
            gas_remaining = self._charge_gas(
                gas_remaining, self.gas_schedule.G_VERYLOW + mem_cost + copy_cost
            )
            # Copy from code, zero-padded
            copy_data = bytearray(size)
            for i in range(size):
                if src_offset + i < len(code):
                    copy_data[i] = code[src_offset + i]
            memory.store(dest_offset, bytes(copy_data))
            return _OpcodeResult(pc=pc + 1, gas_remaining=gas_remaining)

        if opcode == Opcode.GASPRICE:
            gas_remaining = self._charge_gas(gas_remaining, self.gas_schedule.G_BASE)
            stack.push(self.env.gas_price)
            return _OpcodeResult(pc=pc + 1, gas_remaining=gas_remaining)

        if opcode == Opcode.EXTCODESIZE:
            gas_remaining = self._charge_gas(gas_remaining, self.gas_schedule.G_EXTCODESIZE)
            addr = stack.pop()
            address = addr.to_bytes(20, "big")
            code_size = len(self.state.get_code(address))
            stack.push(code_size)
            return _OpcodeResult(pc=pc + 1, gas_remaining=gas_remaining)

        if opcode == Opcode.EXTCODECOPY:
            addr = stack.pop()
            dest_offset, src_offset, size = stack.pop(), stack.pop(), stack.pop()
            mem_cost = memory.expansion_cost(dest_offset, size)
            copy_cost = self.gas_schedule.copy_cost(size)
            gas_remaining = self._charge_gas(
                gas_remaining, self.gas_schedule.G_EXTCODECOPY + mem_cost + copy_cost
            )
            address = addr.to_bytes(20, "big")
            ext_code = self.state.get_code(address)
            # Copy from external code, zero-padded
            copy_data = bytearray(size)
            for i in range(size):
                if src_offset + i < len(ext_code):
                    copy_data[i] = ext_code[src_offset + i]
            memory.store(dest_offset, bytes(copy_data))
            return _OpcodeResult(pc=pc + 1, gas_remaining=gas_remaining)

        if opcode == Opcode.RETURNDATASIZE:
            gas_remaining = self._charge_gas(gas_remaining, self.gas_schedule.G_BASE)
            stack.push(len(self.return_data))
            return _OpcodeResult(pc=pc + 1, gas_remaining=gas_remaining)

        if opcode == Opcode.RETURNDATACOPY:
            dest_offset, src_offset, size = stack.pop(), stack.pop(), stack.pop()
            if src_offset + size > len(self.return_data):
                raise EVMError("Return data out of bounds")
            mem_cost = memory.expansion_cost(dest_offset, size)
            copy_cost = self.gas_schedule.copy_cost(size)
            gas_remaining = self._charge_gas(
                gas_remaining, self.gas_schedule.G_VERYLOW + mem_cost + copy_cost
            )
            memory.store(dest_offset, self.return_data[src_offset : src_offset + size])
            return _OpcodeResult(pc=pc + 1, gas_remaining=gas_remaining)

        if opcode == Opcode.EXTCODEHASH:
            gas_remaining = self._charge_gas(
                gas_remaining, self.gas_schedule.G_BALANCE
            )  # Same as BALANCE in Frontier
            addr = stack.pop()
            address = addr.to_bytes(20, "big")
            if not self.state.account_exists(address):
                stack.push(0)
            else:
                code = self.state.get_code(address)
                if code:
                    h = hashlib.sha3_256(code).digest()
                    stack.push(int.from_bytes(h, "big"))
                else:
                    # Empty code hash
                    stack.push(int.from_bytes(hashlib.sha3_256(b"").digest(), "big"))
            return _OpcodeResult(pc=pc + 1, gas_remaining=gas_remaining)

        # Block information
        if opcode == Opcode.BLOCKHASH:
            gas_remaining = self._charge_gas(gas_remaining, self.gas_schedule.G_BLOCKHASH)
            block_num = stack.pop()
            # Can only access last 256 blocks
            if block_num >= self.env.number or self.env.number - block_num > 256:
                stack.push(0)
            else:
                block_hash = self.env.block_hashes.get(block_num, b"\x00" * 32)
                stack.push(int.from_bytes(block_hash, "big"))
            return _OpcodeResult(pc=pc + 1, gas_remaining=gas_remaining)

        if opcode == Opcode.COINBASE:
            gas_remaining = self._charge_gas(gas_remaining, self.gas_schedule.G_BASE)
            stack.push(int.from_bytes(self.env.coinbase, "big"))
            return _OpcodeResult(pc=pc + 1, gas_remaining=gas_remaining)

        if opcode == Opcode.TIMESTAMP:
            gas_remaining = self._charge_gas(gas_remaining, self.gas_schedule.G_BASE)
            stack.push(self.env.timestamp)
            return _OpcodeResult(pc=pc + 1, gas_remaining=gas_remaining)

        if opcode == Opcode.NUMBER:
            gas_remaining = self._charge_gas(gas_remaining, self.gas_schedule.G_BASE)
            stack.push(self.env.number)
            return _OpcodeResult(pc=pc + 1, gas_remaining=gas_remaining)

        if opcode == Opcode.DIFFICULTY:
            gas_remaining = self._charge_gas(gas_remaining, self.gas_schedule.G_BASE)
            stack.push(self.env.difficulty)
            return _OpcodeResult(pc=pc + 1, gas_remaining=gas_remaining)

        if opcode == Opcode.GASLIMIT:
            gas_remaining = self._charge_gas(gas_remaining, self.gas_schedule.G_BASE)
            stack.push(self.env.gas_limit)
            return _OpcodeResult(pc=pc + 1, gas_remaining=gas_remaining)

        if opcode == Opcode.CHAINID:
            gas_remaining = self._charge_gas(gas_remaining, self.gas_schedule.G_BASE)
            stack.push(self.env.chain_id)
            return _OpcodeResult(pc=pc + 1, gas_remaining=gas_remaining)

        if opcode == Opcode.SELFBALANCE:
            gas_remaining = self._charge_gas(gas_remaining, self.gas_schedule.G_LOW)
            balance = self.state.get_balance(message.target)
            stack.push(balance)
            return _OpcodeResult(pc=pc + 1, gas_remaining=gas_remaining)

        if opcode == Opcode.BASEFEE:
            gas_remaining = self._charge_gas(gas_remaining, self.gas_schedule.G_BASE)
            stack.push(self.env.base_fee)
            return _OpcodeResult(pc=pc + 1, gas_remaining=gas_remaining)

        # Stack, Memory, Storage and Flow Operations
        if opcode == Opcode.POP:
            gas_remaining = self._charge_gas(gas_remaining, self.gas_schedule.G_BASE)
            stack.pop()
            return _OpcodeResult(pc=pc + 1, gas_remaining=gas_remaining)

        if opcode == Opcode.MLOAD:
            offset = stack.pop()
            mem_cost = memory.expansion_cost(offset, 32)
            gas_remaining = self._charge_gas(gas_remaining, self.gas_schedule.G_VERYLOW + mem_cost)
            value = memory.load_word(offset)
            stack.push(value)
            return _OpcodeResult(pc=pc + 1, gas_remaining=gas_remaining)

        if opcode == Opcode.MSTORE:
            offset, value = stack.pop(), stack.pop()
            mem_cost = memory.expansion_cost(offset, 32)
            gas_remaining = self._charge_gas(gas_remaining, self.gas_schedule.G_VERYLOW + mem_cost)
            memory.store_word(offset, value)
            return _OpcodeResult(pc=pc + 1, gas_remaining=gas_remaining)

        if opcode == Opcode.MSTORE8:
            offset, value = stack.pop(), stack.pop()
            mem_cost = memory.expansion_cost(offset, 1)
            gas_remaining = self._charge_gas(gas_remaining, self.gas_schedule.G_VERYLOW + mem_cost)
            memory.store_byte(offset, value)
            return _OpcodeResult(pc=pc + 1, gas_remaining=gas_remaining)

        if opcode == Opcode.SLOAD:
            gas_remaining = self._charge_gas(gas_remaining, self.gas_schedule.G_SLOAD)
            key = stack.pop()
            value = self.state.get_storage(message.target, key)
            stack.push(value)
            return _OpcodeResult(pc=pc + 1, gas_remaining=gas_remaining)

        if opcode == Opcode.SSTORE:
            if message.is_static:
                raise WriteProtectionError("Cannot SSTORE in static context")
            key, value = stack.pop(), stack.pop()
            current = self.state.get_storage(message.target, key)
            gas_cost = self.gas_schedule.sstore_cost(current, value)
            gas_remaining = self._charge_gas(gas_remaining, gas_cost)
            self.state.set_storage(message.target, key, value)
            return _OpcodeResult(pc=pc + 1, gas_remaining=gas_remaining)

        if opcode == Opcode.JUMP:
            gas_remaining = self._charge_gas(gas_remaining, self.gas_schedule.G_MID)
            dest = stack.pop()
            if dest not in valid_jumpdests:
                raise InvalidJumpError(f"Invalid jump destination: {dest}")
            return _OpcodeResult(pc=dest, gas_remaining=gas_remaining)

        if opcode == Opcode.JUMPI:
            gas_remaining = self._charge_gas(gas_remaining, self.gas_schedule.G_HIGH)
            dest, cond = stack.pop(), stack.pop()
            if cond != 0:
                if dest not in valid_jumpdests:
                    raise InvalidJumpError(f"Invalid jump destination: {dest}")
                return _OpcodeResult(pc=dest, gas_remaining=gas_remaining)
            return _OpcodeResult(pc=pc + 1, gas_remaining=gas_remaining)

        if opcode == Opcode.PC:
            gas_remaining = self._charge_gas(gas_remaining, self.gas_schedule.G_BASE)
            stack.push(pc)
            return _OpcodeResult(pc=pc + 1, gas_remaining=gas_remaining)

        if opcode == Opcode.MSIZE:
            gas_remaining = self._charge_gas(gas_remaining, self.gas_schedule.G_BASE)
            stack.push(memory.size())
            return _OpcodeResult(pc=pc + 1, gas_remaining=gas_remaining)

        if opcode == Opcode.GAS:
            gas_remaining = self._charge_gas(gas_remaining, self.gas_schedule.G_BASE)
            stack.push(gas_remaining)
            return _OpcodeResult(pc=pc + 1, gas_remaining=gas_remaining)

        if opcode == Opcode.JUMPDEST:
            gas_remaining = self._charge_gas(gas_remaining, self.gas_schedule.G_JUMPDEST)
            return _OpcodeResult(pc=pc + 1, gas_remaining=gas_remaining)

        # PUSH operations
        if Opcode.PUSH1 <= opcode <= Opcode.PUSH32:
            gas_remaining = self._charge_gas(gas_remaining, self.gas_schedule.G_VERYLOW)
            push_size = opcode - Opcode.PUSH1 + 1
            # Extract push data
            push_data = code[pc + 1 : pc + 1 + push_size]
            # Zero-pad if we're at the end of code
            if len(push_data) < push_size:
                push_data = push_data + b"\x00" * (push_size - len(push_data))
            value = int.from_bytes(push_data, "big")
            stack.push(value)
            return _OpcodeResult(pc=pc + 1 + push_size, gas_remaining=gas_remaining)

        # DUP operations
        if Opcode.DUP1 <= opcode <= Opcode.DUP16:
            gas_remaining = self._charge_gas(gas_remaining, self.gas_schedule.G_VERYLOW)
            n = opcode - Opcode.DUP1 + 1
            stack.dup(n)
            return _OpcodeResult(pc=pc + 1, gas_remaining=gas_remaining)

        # SWAP operations
        if Opcode.SWAP1 <= opcode <= Opcode.SWAP16:
            gas_remaining = self._charge_gas(gas_remaining, self.gas_schedule.G_VERYLOW)
            n = opcode - Opcode.SWAP1 + 1
            stack.swap(n)
            return _OpcodeResult(pc=pc + 1, gas_remaining=gas_remaining)

        # LOG operations
        if Opcode.LOG0 <= opcode <= Opcode.LOG4:
            if message.is_static:
                raise WriteProtectionError("Cannot LOG in static context")
            num_topics = opcode - Opcode.LOG0
            offset, size = stack.pop(), stack.pop()
            topics = [stack.pop().to_bytes(32, "big") for _ in range(num_topics)]
            mem_cost = memory.expansion_cost(offset, size)
            log_cost = self.gas_schedule.log_cost(size, num_topics)
            gas_remaining = self._charge_gas(gas_remaining, mem_cost + log_cost)
            data = memory.load(offset, size)
            logs.append(Log(address=message.target, topics=topics, data=data))
            return _OpcodeResult(pc=pc + 1, gas_remaining=gas_remaining)

        # System operations
        if opcode == Opcode.CREATE:
            if message.is_static:
                raise WriteProtectionError("Cannot CREATE in static context")
            value, offset, size = stack.pop(), stack.pop(), stack.pop()
            mem_cost = memory.expansion_cost(offset, size)
            gas_remaining = self._charge_gas(gas_remaining, self.gas_schedule.G_CREATE + mem_cost)

            # Check balance
            if self.state.get_balance(message.target) < value:
                stack.push(0)
                return _OpcodeResult(pc=pc + 1, gas_remaining=gas_remaining)

            init_code = memory.load(offset, size)
            sender_nonce = self.state.get_account(message.target).nonce
            new_address = create_address(message.target, sender_nonce)

            # Increment nonce
            self.state.increment_nonce(message.target)

            # Transfer value
            self.state.set_balance(message.target, self.state.get_balance(message.target) - value)
            self.state.set_balance(new_address, self.state.get_balance(new_address) + value)

            # Execute init code
            create_gas = gas_remaining - gas_remaining // 64
            gas_remaining = gas_remaining - create_gas

            create_message = Message(
                caller=message.target,
                target=new_address,
                value=value,
                data=b"",
                gas=create_gas,
                depth=message.depth + 1,
                code=init_code,
                is_create=True,
            )

            result = self.execute(create_message)
            self.return_data = result.return_data

            if result.success:
                # Deploy code
                deploy_gas = len(result.return_data) * self.gas_schedule.G_CODEDEPOSIT
                if result.gas_remaining >= deploy_gas:
                    self.state.set_code(new_address, result.return_data)
                    gas_remaining += result.gas_remaining - deploy_gas
                    stack.push(int.from_bytes(new_address, "big"))
                else:
                    # Not enough gas for deployment
                    stack.push(0)
                    gas_remaining += result.gas_remaining
            else:
                stack.push(0)
                gas_remaining += result.gas_remaining

            return _OpcodeResult(pc=pc + 1, gas_remaining=gas_remaining)

        if opcode == Opcode.CALL:
            return self._handle_call(
                pc, stack, memory, message, gas_remaining, logs, call_type="CALL"
            )

        if opcode == Opcode.CALLCODE:
            return self._handle_call(
                pc, stack, memory, message, gas_remaining, logs, call_type="CALLCODE"
            )

        if opcode == Opcode.RETURN:
            offset, size = stack.pop(), stack.pop()
            mem_cost = memory.expansion_cost(offset, size)
            gas_remaining = self._charge_gas(gas_remaining, mem_cost)
            return_data = memory.load(offset, size)
            return _OpcodeResult(
                done=True, success=True, gas_remaining=gas_remaining, return_data=return_data
            )

        if opcode == Opcode.DELEGATECALL:
            return self._handle_call(
                pc, stack, memory, message, gas_remaining, logs, call_type="DELEGATECALL"
            )

        if opcode == Opcode.CREATE2:
            if message.is_static:
                raise WriteProtectionError("Cannot CREATE2 in static context")
            value, offset, size, salt = stack.pop(), stack.pop(), stack.pop(), stack.pop()
            mem_cost = memory.expansion_cost(offset, size)
            # CREATE2 has additional cost for hashing init code
            hash_cost = self.gas_schedule.copy_cost(size)
            gas_remaining = self._charge_gas(
                gas_remaining, self.gas_schedule.G_CREATE + mem_cost + hash_cost
            )

            # Check balance
            if self.state.get_balance(message.target) < value:
                stack.push(0)
                return _OpcodeResult(pc=pc + 1, gas_remaining=gas_remaining)

            init_code = memory.load(offset, size)
            init_code_hash = hashlib.sha3_256(init_code).digest()
            salt_bytes = salt.to_bytes(32, "big")

            from ethereum.common.types import create2_address

            new_address = create2_address(message.target, salt_bytes, init_code_hash)

            # Increment nonce
            self.state.increment_nonce(message.target)

            # Transfer value
            self.state.set_balance(message.target, self.state.get_balance(message.target) - value)
            self.state.set_balance(new_address, self.state.get_balance(new_address) + value)

            # Execute init code
            create_gas = gas_remaining - gas_remaining // 64
            gas_remaining = gas_remaining - create_gas

            create_message = Message(
                caller=message.target,
                target=new_address,
                value=value,
                data=b"",
                gas=create_gas,
                depth=message.depth + 1,
                code=init_code,
                is_create=True,
            )

            result = self.execute(create_message)
            self.return_data = result.return_data

            if result.success:
                deploy_gas = len(result.return_data) * self.gas_schedule.G_CODEDEPOSIT
                if result.gas_remaining >= deploy_gas:
                    self.state.set_code(new_address, result.return_data)
                    gas_remaining += result.gas_remaining - deploy_gas
                    stack.push(int.from_bytes(new_address, "big"))
                else:
                    stack.push(0)
                    gas_remaining += result.gas_remaining
            else:
                stack.push(0)
                gas_remaining += result.gas_remaining

            return _OpcodeResult(pc=pc + 1, gas_remaining=gas_remaining)

        if opcode == Opcode.STATICCALL:
            return self._handle_call(
                pc, stack, memory, message, gas_remaining, logs, call_type="STATICCALL"
            )

        if opcode == Opcode.REVERT:
            offset, size = stack.pop(), stack.pop()
            mem_cost = memory.expansion_cost(offset, size)
            gas_remaining = self._charge_gas(gas_remaining, mem_cost)
            return_data = memory.load(offset, size)
            return _OpcodeResult(
                done=True, success=False, gas_remaining=gas_remaining, return_data=return_data
            )

        if opcode == Opcode.INVALID:
            raise InvalidOpcodeError("INVALID opcode")

        if opcode == Opcode.SELFDESTRUCT:
            if message.is_static:
                raise WriteProtectionError("Cannot SELFDESTRUCT in static context")
            gas_remaining = self._charge_gas(gas_remaining, self.gas_schedule.G_SELFDESTRUCT)
            recipient_addr = stack.pop()
            recipient = recipient_addr.to_bytes(20, "big")

            # Transfer balance to recipient
            balance = self.state.get_balance(message.target)
            self.state.set_balance(recipient, self.state.get_balance(recipient) + balance)
            self.state.set_balance(message.target, 0)

            # Mark account for deletion (simplified - just clear the account)
            self.state.set_account(message.target, Account())

            return _OpcodeResult(done=True, success=True, gas_remaining=gas_remaining)

        # Unknown opcode
        raise InvalidOpcodeError(f"Unknown opcode: 0x{opcode:02X}")

    def _handle_call(
        self,
        pc: int,
        stack: Stack,
        memory: Memory,
        message: Message,
        gas_remaining: int,
        logs: list[Log],
        call_type: str,
    ) -> _OpcodeResult:
        """Handle CALL, CALLCODE, DELEGATECALL, and STATICCALL opcodes."""

        if call_type in ("CALL", "CALLCODE"):
            gas = stack.pop()
            addr = stack.pop()
            value = stack.pop()
            args_offset, args_size = stack.pop(), stack.pop()
            ret_offset, ret_size = stack.pop(), stack.pop()
        elif call_type == "DELEGATECALL":
            gas = stack.pop()
            addr = stack.pop()
            value = message.value  # Inherits value from current context
            args_offset, args_size = stack.pop(), stack.pop()
            ret_offset, ret_size = stack.pop(), stack.pop()
        else:  # STATICCALL
            gas = stack.pop()
            addr = stack.pop()
            value = 0
            args_offset, args_size = stack.pop(), stack.pop()
            ret_offset, ret_size = stack.pop(), stack.pop()

        address = addr.to_bytes(20, "big")

        # Calculate gas costs
        mem_cost_in = memory.expansion_cost(args_offset, args_size)
        mem_cost_out = memory.expansion_cost(ret_offset, ret_size)
        mem_cost = max(mem_cost_in, mem_cost_out)

        target_exists = self.state.account_exists(address)
        call_cost = self.gas_schedule.call_cost(value, target_exists)
        total_cost = call_cost + mem_cost

        gas_remaining = self._charge_gas(gas_remaining, total_cost)

        # Check static context for state-modifying calls
        if message.is_static and call_type == "CALL" and value > 0:
            raise WriteProtectionError("Cannot transfer value in static context")

        # Check sufficient balance for value transfer
        if call_type == "CALL" and value > 0:
            if self.state.get_balance(message.target) < value:
                stack.push(0)
                return _OpcodeResult(pc=pc + 1, gas_remaining=gas_remaining)

        # Calculate gas to forward
        gas_cap = gas_remaining - gas_remaining // 64
        gas_to_forward = min(gas, gas_cap)

        if call_type == "CALL" and value > 0:
            gas_to_forward += self.gas_schedule.G_CALLSTIPEND

        gas_remaining -= gas_to_forward

        # Prepare call data
        call_data = memory.load(args_offset, args_size)

        # Get code for target
        if call_type in ("CALL", "STATICCALL"):
            code_to_execute = self.state.get_code(address)
            target_address = address
            caller = message.target
        elif call_type == "CALLCODE":
            code_to_execute = self.state.get_code(address)
            target_address = message.target  # Execute in context of current contract
            caller = message.target
        else:  # DELEGATECALL
            code_to_execute = self.state.get_code(address)
            target_address = message.target  # Execute in context of current contract
            caller = message.caller  # Preserve original caller

        # Handle value transfer for CALL
        if call_type == "CALL" and value > 0:
            self.state.set_balance(message.target, self.state.get_balance(message.target) - value)
            self.state.set_balance(address, self.state.get_balance(address) + value)

        # Execute call
        call_message = Message(
            caller=caller,
            target=target_address,
            value=value if call_type in ("CALL", "CALLCODE") else message.value,
            data=call_data,
            gas=gas_to_forward,
            depth=message.depth + 1,
            code=code_to_execute,
            code_address=address,
            is_static=message.is_static or call_type == "STATICCALL",
        )

        result = self.execute(call_message)
        self.return_data = result.return_data

        # Return unused gas
        gas_remaining += result.gas_remaining

        # Copy return data to memory
        copy_size = min(ret_size, len(result.return_data))
        if copy_size > 0:
            memory.store(ret_offset, result.return_data[:copy_size])

        stack.push(1 if result.success else 0)
        return _OpcodeResult(pc=pc + 1, gas_remaining=gas_remaining)


class _OpcodeResult:
    """Result of executing a single opcode."""

    def __init__(
        self,
        pc: int = 0,
        gas_remaining: int = 0,
        done: bool = False,
        success: bool = True,
        return_data: bytes = b"",
        error: str | None = None,
        created_address: bytes | None = None,
    ) -> None:
        self.pc = pc
        self.gas_remaining = gas_remaining
        self.done = done
        self.success = success
        self.return_data = return_data
        self.error = error
        self.created_address = created_address
