"""Common types for EVM implementation."""

from __future__ import annotations

from copy import deepcopy
from enum import IntEnum
from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field

# Type aliases with constraints
U256 = Annotated[int, Field(ge=0, lt=2**256)]
Address = Annotated[bytes, Field(min_length=20, max_length=20)]
Hash32 = Annotated[bytes, Field(min_length=32, max_length=32)]

# Constants
MAX_U256 = 2**256 - 1
ZERO_ADDRESS = b"\x00" * 20
ZERO_HASH = b"\x00" * 32


def u256(value: int) -> int:
    """Ensure value fits in U256 range (mod 2^256)."""
    return value & MAX_U256


def signed_to_unsigned(value: int) -> int:
    """Convert signed 256-bit integer to unsigned."""
    if value >= 0:
        return value
    return value + 2**256


def unsigned_to_signed(value: int) -> int:
    """Convert unsigned 256-bit integer to signed."""
    if value < 2**255:
        return value
    return value - 2**256


class Account(BaseModel):
    """EVM account state."""

    model_config = ConfigDict(frozen=True, arbitrary_types_allowed=True)

    nonce: int = 0
    balance: int = 0
    code: bytes = b""
    storage: dict[int, int] = Field(default_factory=dict)

    def copy_with(
        self,
        nonce: int | None = None,
        balance: int | None = None,
        code: bytes | None = None,
        storage: dict[int, int] | None = None,
    ) -> Account:
        """Create a copy with updated fields."""
        return Account(
            nonce=nonce if nonce is not None else self.nonce,
            balance=balance if balance is not None else self.balance,
            code=code if code is not None else self.code,
            storage=storage if storage is not None else deepcopy(self.storage),
        )


class State(BaseModel):
    """EVM world state - mapping of addresses to accounts."""

    model_config = ConfigDict(arbitrary_types_allowed=True)

    accounts: dict[bytes, Account] = Field(default_factory=dict)

    def get_account(self, address: bytes) -> Account:
        """Get account at address, or empty account if not exists."""
        return self.accounts.get(address, Account())

    def set_account(self, address: bytes, account: Account) -> None:
        """Set account at address."""
        self.accounts[address] = account

    def get_balance(self, address: bytes) -> int:
        """Get balance of address."""
        return self.get_account(address).balance

    def set_balance(self, address: bytes, balance: int) -> None:
        """Set balance of address."""
        account = self.get_account(address)
        self.accounts[address] = account.copy_with(balance=balance)

    def get_code(self, address: bytes) -> bytes:
        """Get code at address."""
        return self.get_account(address).code

    def set_code(self, address: bytes, code: bytes) -> None:
        """Set code at address."""
        account = self.get_account(address)
        self.accounts[address] = account.copy_with(code=code)

    def get_storage(self, address: bytes, key: int) -> int:
        """Get storage value at address and key."""
        account = self.get_account(address)
        return account.storage.get(key, 0)

    def set_storage(self, address: bytes, key: int, value: int) -> None:
        """Set storage value at address and key."""
        account = self.get_account(address)
        new_storage = deepcopy(account.storage)
        if value == 0:
            new_storage.pop(key, None)
        else:
            new_storage[key] = value
        self.accounts[address] = account.copy_with(storage=new_storage)

    def increment_nonce(self, address: bytes) -> None:
        """Increment nonce of address."""
        account = self.get_account(address)
        self.accounts[address] = account.copy_with(nonce=account.nonce + 1)

    def copy(self) -> State:
        """Create a deep copy of the state."""
        return State(accounts=deepcopy(self.accounts))

    def account_exists(self, address: bytes) -> bool:
        """Check if account exists (has non-default values)."""
        if address not in self.accounts:
            return False
        account = self.accounts[address]
        return account.nonce != 0 or account.balance != 0 or account.code != b""


class Transaction(BaseModel):
    """EVM transaction."""

    model_config = ConfigDict(frozen=True, arbitrary_types_allowed=True)

    sender: bytes = Field(..., min_length=20, max_length=20)
    to: bytes | None = Field(default=None)  # None for contract creation
    value: int = 0
    data: bytes = b""
    gas: int = 21000
    gas_price: int = 0
    nonce: int = 0


class Environment(BaseModel):
    """Block environment context."""

    model_config = ConfigDict(frozen=True, arbitrary_types_allowed=True)

    caller: bytes = Field(default=ZERO_ADDRESS, min_length=20, max_length=20)
    origin: bytes = Field(default=ZERO_ADDRESS, min_length=20, max_length=20)
    block_hashes: dict[int, bytes] = Field(default_factory=dict)
    coinbase: bytes = Field(default=ZERO_ADDRESS, min_length=20, max_length=20)
    number: int = 0
    gas_limit: int = 10_000_000
    gas_price: int = 0
    timestamp: int = 0
    difficulty: int = 0
    chain_id: int = 1
    base_fee: int = 0  # EIP-1559


class Log(BaseModel):
    """EVM log entry."""

    model_config = ConfigDict(frozen=True, arbitrary_types_allowed=True)

    address: bytes = Field(..., min_length=20, max_length=20)
    topics: list[bytes] = Field(default_factory=list)
    data: bytes = b""


class Message(BaseModel):
    """Call frame context for EVM execution."""

    model_config = ConfigDict(arbitrary_types_allowed=True)

    caller: bytes = Field(..., min_length=20, max_length=20)
    target: bytes = Field(..., min_length=20, max_length=20)
    value: int = 0
    data: bytes = b""
    gas: int = 0
    depth: int = 0
    code: bytes = b""
    code_address: bytes = Field(default=ZERO_ADDRESS, min_length=20, max_length=20)
    is_static: bool = False
    is_create: bool = False


class ExecutionResult(BaseModel):
    """Result of EVM execution."""

    model_config = ConfigDict(arbitrary_types_allowed=True)

    success: bool = True
    gas_used: int = 0
    gas_remaining: int = 0
    return_data: bytes = b""
    logs: list[Log] = Field(default_factory=list)
    error: str | None = None
    created_address: bytes | None = None


class Opcode(IntEnum):
    """EVM opcodes."""

    # Stop and Arithmetic
    STOP = 0x00
    ADD = 0x01
    MUL = 0x02
    SUB = 0x03
    DIV = 0x04
    SDIV = 0x05
    MOD = 0x06
    SMOD = 0x07
    ADDMOD = 0x08
    MULMOD = 0x09
    EXP = 0x0A
    SIGNEXTEND = 0x0B

    # Comparison & Bitwise Logic
    LT = 0x10
    GT = 0x11
    SLT = 0x12
    SGT = 0x13
    EQ = 0x14
    ISZERO = 0x15
    AND = 0x16
    OR = 0x17
    XOR = 0x18
    NOT = 0x19
    BYTE = 0x1A
    SHL = 0x1B  # EIP-145
    SHR = 0x1C  # EIP-145
    SAR = 0x1D  # EIP-145

    # SHA3
    SHA3 = 0x20

    # Environmental Information
    ADDRESS = 0x30
    BALANCE = 0x31
    ORIGIN = 0x32
    CALLER = 0x33
    CALLVALUE = 0x34
    CALLDATALOAD = 0x35
    CALLDATASIZE = 0x36
    CALLDATACOPY = 0x37
    CODESIZE = 0x38
    CODECOPY = 0x39
    GASPRICE = 0x3A
    EXTCODESIZE = 0x3B
    EXTCODECOPY = 0x3C
    RETURNDATASIZE = 0x3D  # EIP-211
    RETURNDATACOPY = 0x3E  # EIP-211
    EXTCODEHASH = 0x3F  # EIP-1052

    # Block Information
    BLOCKHASH = 0x40
    COINBASE = 0x41
    TIMESTAMP = 0x42
    NUMBER = 0x43
    DIFFICULTY = 0x44
    GASLIMIT = 0x45
    CHAINID = 0x46  # EIP-1344
    SELFBALANCE = 0x47  # EIP-1884
    BASEFEE = 0x48  # EIP-3198

    # Stack, Memory, Storage and Flow Operations
    POP = 0x50
    MLOAD = 0x51
    MSTORE = 0x52
    MSTORE8 = 0x53
    SLOAD = 0x54
    SSTORE = 0x55
    JUMP = 0x56
    JUMPI = 0x57
    PC = 0x58
    MSIZE = 0x59
    GAS = 0x5A
    JUMPDEST = 0x5B
    PUSH0 = 0x5F  # EIP-3855 (Shanghai)

    # Push Operations (PUSH1 to PUSH32)
    PUSH1 = 0x60
    PUSH2 = 0x61
    PUSH3 = 0x62
    PUSH4 = 0x63
    PUSH5 = 0x64
    PUSH6 = 0x65
    PUSH7 = 0x66
    PUSH8 = 0x67
    PUSH9 = 0x68
    PUSH10 = 0x69
    PUSH11 = 0x6A
    PUSH12 = 0x6B
    PUSH13 = 0x6C
    PUSH14 = 0x6D
    PUSH15 = 0x6E
    PUSH16 = 0x6F
    PUSH17 = 0x70
    PUSH18 = 0x71
    PUSH19 = 0x72
    PUSH20 = 0x73
    PUSH21 = 0x74
    PUSH22 = 0x75
    PUSH23 = 0x76
    PUSH24 = 0x77
    PUSH25 = 0x78
    PUSH26 = 0x79
    PUSH27 = 0x7A
    PUSH28 = 0x7B
    PUSH29 = 0x7C
    PUSH30 = 0x7D
    PUSH31 = 0x7E
    PUSH32 = 0x7F

    # Duplication Operations (DUP1 to DUP16)
    DUP1 = 0x80
    DUP2 = 0x81
    DUP3 = 0x82
    DUP4 = 0x83
    DUP5 = 0x84
    DUP6 = 0x85
    DUP7 = 0x86
    DUP8 = 0x87
    DUP9 = 0x88
    DUP10 = 0x89
    DUP11 = 0x8A
    DUP12 = 0x8B
    DUP13 = 0x8C
    DUP14 = 0x8D
    DUP15 = 0x8E
    DUP16 = 0x8F

    # Exchange Operations (SWAP1 to SWAP16)
    SWAP1 = 0x90
    SWAP2 = 0x91
    SWAP3 = 0x92
    SWAP4 = 0x93
    SWAP5 = 0x94
    SWAP6 = 0x95
    SWAP7 = 0x96
    SWAP8 = 0x97
    SWAP9 = 0x98
    SWAP10 = 0x99
    SWAP11 = 0x9A
    SWAP12 = 0x9B
    SWAP13 = 0x9C
    SWAP14 = 0x9D
    SWAP15 = 0x9E
    SWAP16 = 0x9F

    # Logging Operations
    LOG0 = 0xA0
    LOG1 = 0xA1
    LOG2 = 0xA2
    LOG3 = 0xA3
    LOG4 = 0xA4

    # System Operations
    CREATE = 0xF0
    CALL = 0xF1
    CALLCODE = 0xF2
    RETURN = 0xF3
    DELEGATECALL = 0xF4  # EIP-7
    CREATE2 = 0xF5  # EIP-1014
    STATICCALL = 0xFA  # EIP-214
    REVERT = 0xFD  # EIP-140
    INVALID = 0xFE
    SELFDESTRUCT = 0xFF

    @classmethod
    def from_byte(cls, byte: int) -> Opcode | None:
        """Get opcode from byte value, or None if invalid."""
        try:
            return cls(byte)
        except ValueError:
            return None


def get_opcode_name(opcode: int) -> str:
    """Get the name of an opcode."""
    try:
        return Opcode(opcode).name
    except ValueError:
        return f"UNKNOWN(0x{opcode:02X})"


def create_address(sender: bytes, nonce: int) -> bytes:
    """Create contract address from sender and nonce (CREATE)."""
    import hashlib

    # RLP encode [sender, nonce]
    def rlp_encode_bytes(data: bytes) -> bytes:
        if len(data) == 1 and data[0] < 0x80:
            return data
        if len(data) < 56:
            return bytes([0x80 + len(data)]) + data
        len_bytes = len(data).to_bytes((len(data).bit_length() + 7) // 8, "big")
        return bytes([0xB7 + len(len_bytes)]) + len_bytes + data

    def rlp_encode_int(value: int) -> bytes:
        if value == 0:
            return b"\x80"
        if value < 0x80:
            return bytes([value])
        value_bytes = value.to_bytes((value.bit_length() + 7) // 8, "big")
        return rlp_encode_bytes(value_bytes)

    sender_encoded = rlp_encode_bytes(sender)
    nonce_encoded = rlp_encode_int(nonce)
    content = sender_encoded + nonce_encoded

    if len(content) < 56:
        rlp = bytes([0xC0 + len(content)]) + content
    else:
        len_bytes = len(content).to_bytes((len(content).bit_length() + 7) // 8, "big")
        rlp = bytes([0xF7 + len(len_bytes)]) + len_bytes + content

    return hashlib.sha3_256(rlp).digest()[-20:]


def create2_address(sender: bytes, salt: bytes, init_code_hash: bytes) -> bytes:
    """Create contract address from sender, salt, and init code hash (CREATE2)."""
    import hashlib

    data = b"\xff" + sender + salt + init_code_hash
    return hashlib.sha3_256(data).digest()[-20:]
