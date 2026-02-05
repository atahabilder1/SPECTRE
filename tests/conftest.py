"""Pytest fixtures and helpers for EVM testing."""

from __future__ import annotations

import pytest

from ethereum.common.types import (
    ZERO_ADDRESS,
    Account,
    Environment,
    Message,
    State,
)
from ethereum.frontier.vm.interpreter import Interpreter as FrontierInterpreter
from ethereum.frontier.vm.memory import Memory
from ethereum.frontier.vm.stack import Stack
from ethereum.homestead.vm.interpreter import HomesteadInterpreter
from ethereum.shanghai.vm.interpreter import ShanghaiInterpreter


@pytest.fixture
def empty_state() -> State:
    """Create an empty EVM state."""
    return State()


@pytest.fixture
def simple_state() -> State:
    """Create a state with a funded account."""
    state = State()
    sender = b"\x00" * 19 + b"\x01"
    state.set_account(
        sender,
        Account(
            nonce=0,
            balance=10**18,  # 1 ETH
            code=b"",
            storage={},
        ),
    )
    return state


@pytest.fixture
def default_env() -> Environment:
    """Create a default block environment."""
    return Environment(
        caller=ZERO_ADDRESS,
        origin=ZERO_ADDRESS,
        block_hashes={},
        coinbase=b"\x00" * 19 + b"\xff",
        number=1000,
        gas_limit=10_000_000,
        gas_price=1,
        timestamp=1000000,
        difficulty=1,
        chain_id=1,
        base_fee=0,
    )


@pytest.fixture
def stack() -> Stack:
    """Create an empty stack."""
    return Stack()


@pytest.fixture
def memory() -> Memory:
    """Create empty memory."""
    return Memory()


@pytest.fixture
def frontier_interpreter(empty_state: State, default_env: Environment) -> FrontierInterpreter:
    """Create a Frontier interpreter."""
    return FrontierInterpreter(empty_state, default_env)


@pytest.fixture
def homestead_interpreter(empty_state: State, default_env: Environment) -> HomesteadInterpreter:
    """Create a Homestead interpreter."""
    return HomesteadInterpreter(empty_state, default_env)


@pytest.fixture
def shanghai_interpreter(empty_state: State, default_env: Environment) -> ShanghaiInterpreter:
    """Create a Shanghai interpreter."""
    return ShanghaiInterpreter(empty_state, default_env)


def create_message(
    code: bytes,
    data: bytes = b"",
    value: int = 0,
    gas: int = 1_000_000,
    caller: bytes = ZERO_ADDRESS,
    target: bytes | None = None,
) -> Message:
    """Helper to create a message for testing."""
    if target is None:
        target = b"\x00" * 19 + b"\x02"
    return Message(
        caller=caller,
        target=target,
        value=value,
        data=data,
        gas=gas,
        depth=0,
        code=code,
    )


def assemble(*opcodes: int | bytes) -> bytes:
    """
    Assemble opcodes into bytecode.

    Args:
        *opcodes: Opcode bytes or integers

    Returns:
        Assembled bytecode
    """
    result = bytearray()
    for op in opcodes:
        if isinstance(op, int):
            result.append(op)
        elif isinstance(op, bytes):
            result.extend(op)
    return bytes(result)


def push(value: int, size: int = 0) -> bytes:
    """
    Create a PUSH instruction.

    Args:
        value: Value to push
        size: Size in bytes (0 = auto)

    Returns:
        PUSH opcode followed by value bytes
    """
    if size == 0:
        if value == 0:
            size = 1
        else:
            size = (value.bit_length() + 7) // 8

    size = min(max(size, 1), 32)
    opcode = 0x5F + size  # PUSH1 = 0x60
    value_bytes = value.to_bytes(size, "big")
    return bytes([opcode]) + value_bytes
