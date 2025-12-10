"""Gas schedule and calculations for Frontier fork."""

from __future__ import annotations

from dataclasses import dataclass
from typing import ClassVar


@dataclass(frozen=True)
class GasSchedule:
    """Gas costs for EVM operations in Frontier."""

    # Zero gas
    G_ZERO: ClassVar[int] = 0

    # Base gas costs
    G_BASE: ClassVar[int] = 2
    G_VERYLOW: ClassVar[int] = 3
    G_LOW: ClassVar[int] = 5
    G_MID: ClassVar[int] = 8
    G_HIGH: ClassVar[int] = 10

    # Memory operations
    G_MEMORY: ClassVar[int] = 3
    G_COPY: ClassVar[int] = 3  # Per word copied

    # Storage operations
    G_SLOAD: ClassVar[int] = 50  # Frontier value (changed in later forks)
    G_SSET: ClassVar[int] = 20000  # Setting storage from 0 to non-0
    G_SRESET: ClassVar[int] = 5000  # Setting storage from non-0 to non-0
    G_SCLEAR: ClassVar[int] = 5000  # Refund for clearing storage

    # Contract operations
    G_CREATE: ClassVar[int] = 32000
    G_CODEDEPOSIT: ClassVar[int] = 200  # Per byte of deployed code
    G_CALL: ClassVar[int] = 40  # Frontier value
    G_CALLVALUE: ClassVar[int] = 9000  # Extra for non-zero value transfer
    G_CALLSTIPEND: ClassVar[int] = 2300  # Free gas for receiving contract
    G_NEWACCOUNT: ClassVar[int] = 25000  # Creating a new account

    # Other
    G_JUMPDEST: ClassVar[int] = 1
    G_EXP: ClassVar[int] = 10
    G_EXPBYTE: ClassVar[int] = 10  # Per byte of exponent (Frontier)
    G_SHA3: ClassVar[int] = 30
    G_SHA3WORD: ClassVar[int] = 6  # Per word of input
    G_BALANCE: ClassVar[int] = 20  # Frontier value
    G_EXTCODESIZE: ClassVar[int] = 20  # Frontier value
    G_EXTCODECOPY: ClassVar[int] = 20  # Frontier value
    G_BLOCKHASH: ClassVar[int] = 20
    G_LOG: ClassVar[int] = 375
    G_LOGDATA: ClassVar[int] = 8  # Per byte of log data
    G_LOGTOPIC: ClassVar[int] = 375  # Per topic
    G_SELFDESTRUCT: ClassVar[int] = 0  # Frontier value

    # Transaction costs
    G_TRANSACTION: ClassVar[int] = 21000
    G_TXCREATE: ClassVar[int] = 53000  # Contract creation (21000 + 32000)
    G_TXDATAZERO: ClassVar[int] = 4  # Per zero byte in tx data
    G_TXDATANONZERO: ClassVar[int] = 68  # Per non-zero byte in tx data

    @classmethod
    def memory_expansion_cost(cls, current_words: int, new_words: int) -> int:
        """
        Calculate gas cost for memory expansion.

        Memory cost formula: 3 * words + words^2 / 512
        Returns the delta (additional cost) for expanding from current to new.
        """
        if new_words <= current_words:
            return 0

        def cost(words: int) -> int:
            return cls.G_MEMORY * words + (words * words) // 512

        return cost(new_words) - cost(current_words)

    @classmethod
    def copy_cost(cls, size: int) -> int:
        """Calculate gas cost for copying data (CALLDATACOPY, CODECOPY, etc.)."""
        words = (size + 31) // 32
        return cls.G_COPY * words

    @classmethod
    def sha3_cost(cls, size: int) -> int:
        """Calculate gas cost for SHA3 operation."""
        words = (size + 31) // 32
        return cls.G_SHA3 + cls.G_SHA3WORD * words

    @classmethod
    def exp_cost(cls, exponent: int) -> int:
        """Calculate gas cost for EXP operation."""
        if exponent == 0:
            return cls.G_EXP
        # Count bytes in exponent
        byte_length = (exponent.bit_length() + 7) // 8
        return cls.G_EXP + cls.G_EXPBYTE * byte_length

    @classmethod
    def log_cost(cls, data_size: int, num_topics: int) -> int:
        """Calculate gas cost for LOG operation."""
        return cls.G_LOG + cls.G_LOGDATA * data_size + cls.G_LOGTOPIC * num_topics

    @classmethod
    def call_cost(
        cls,
        value: int,
        target_exists: bool,
        is_cold: bool = False,
    ) -> int:
        """
        Calculate gas cost for CALL operation.

        Args:
            value: Value being transferred
            target_exists: Whether the target account exists
            is_cold: Whether this is a cold access (post-Berlin)
        """
        cost = cls.G_CALL
        if value > 0:
            cost += cls.G_CALLVALUE
            if not target_exists:
                cost += cls.G_NEWACCOUNT
        return cost

    @classmethod
    def sstore_cost(cls, current_value: int, new_value: int) -> int:
        """
        Calculate gas cost for SSTORE operation (Frontier).

        Frontier uses simple rules:
        - Setting from 0 to non-0: G_SSET (20000)
        - Otherwise: G_SRESET (5000)
        """
        if current_value == 0 and new_value != 0:
            return cls.G_SSET
        return cls.G_SRESET

    @classmethod
    def sstore_refund(cls, current_value: int, new_value: int) -> int:
        """Calculate gas refund for SSTORE operation (Frontier)."""
        if current_value != 0 and new_value == 0:
            return cls.G_SCLEAR
        return 0

    @classmethod
    def transaction_intrinsic_gas(cls, data: bytes, is_create: bool) -> int:
        """Calculate intrinsic gas for a transaction."""
        gas = cls.G_TXCREATE if is_create else cls.G_TRANSACTION

        for byte in data:
            if byte == 0:
                gas += cls.G_TXDATAZERO
            else:
                gas += cls.G_TXDATANONZERO

        return gas
