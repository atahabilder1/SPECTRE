"""EIP analysis for test generation."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Any


class EIPCategory(Enum):
    """Categories of EIPs."""

    CORE = auto()  # Core protocol changes
    NETWORKING = auto()  # P2P networking
    INTERFACE = auto()  # API/RPC changes
    ERC = auto()  # Token standards
    META = auto()  # Process documents
    INFORMATIONAL = auto()  # Guidelines


class OpcodeChange(Enum):
    """Types of opcode changes in an EIP."""

    NEW_OPCODE = auto()  # Adds new opcode
    MODIFIED_BEHAVIOR = auto()  # Changes existing opcode behavior
    GAS_CHANGE = auto()  # Changes gas costs
    DEPRECATED = auto()  # Deprecates opcode


@dataclass
class OpcodeSpec:
    """Specification of an opcode change."""

    opcode: int
    name: str
    change_type: OpcodeChange
    gas_cost: int | None = None
    stack_input: int = 0
    stack_output: int = 0
    description: str = ""


@dataclass
class EIPSpec:
    """Parsed EIP specification."""

    number: int
    title: str
    category: EIPCategory
    status: str
    opcodes: list[OpcodeSpec] = field(default_factory=list)
    gas_changes: dict[str, int] = field(default_factory=dict)
    boundary_values: list[int] = field(default_factory=list)
    related_eips: list[int] = field(default_factory=list)
    test_vectors: list[dict[str, Any]] = field(default_factory=list)


# Known EIP specifications
KNOWN_EIPS: dict[int, EIPSpec] = {
    2: EIPSpec(
        number=2,
        title="Homestead Hard-fork Changes",
        category=EIPCategory.CORE,
        status="Final",
        opcodes=[
            OpcodeSpec(
                opcode=0xF0,
                name="CREATE",
                change_type=OpcodeChange.MODIFIED_BEHAVIOR,
                gas_cost=32000,
                stack_input=3,
                stack_output=1,
                description="CREATE with insufficient gas now properly fails",
            ),
        ],
        gas_changes={"CREATE": 32000},
        boundary_values=[0, 1, 32000, 32001],
        related_eips=[7, 8],
    ),
    145: EIPSpec(
        number=145,
        title="Bitwise shifting instructions in EVM",
        category=EIPCategory.CORE,
        status="Final",
        opcodes=[
            OpcodeSpec(
                opcode=0x1B,
                name="SHL",
                change_type=OpcodeChange.NEW_OPCODE,
                gas_cost=3,
                stack_input=2,
                stack_output=1,
                description="Shift left",
            ),
            OpcodeSpec(
                opcode=0x1C,
                name="SHR",
                change_type=OpcodeChange.NEW_OPCODE,
                gas_cost=3,
                stack_input=2,
                stack_output=1,
                description="Logical shift right",
            ),
            OpcodeSpec(
                opcode=0x1D,
                name="SAR",
                change_type=OpcodeChange.NEW_OPCODE,
                gas_cost=3,
                stack_input=2,
                stack_output=1,
                description="Arithmetic shift right",
            ),
        ],
        gas_changes={"SHL": 3, "SHR": 3, "SAR": 3},
        boundary_values=[0, 1, 255, 256, 2**255, 2**256 - 1],
    ),
    1014: EIPSpec(
        number=1014,
        title="Skinny CREATE2",
        category=EIPCategory.CORE,
        status="Final",
        opcodes=[
            OpcodeSpec(
                opcode=0xF5,
                name="CREATE2",
                change_type=OpcodeChange.NEW_OPCODE,
                gas_cost=32000,
                stack_input=4,
                stack_output=1,
                description="Create contract with deterministic address",
            ),
        ],
        gas_changes={"CREATE2": 32000},
        boundary_values=[0, 1, 32],
        related_eips=[],
    ),
    3855: EIPSpec(
        number=3855,
        title="PUSH0 instruction",
        category=EIPCategory.CORE,
        status="Final",
        opcodes=[
            OpcodeSpec(
                opcode=0x5F,
                name="PUSH0",
                change_type=OpcodeChange.NEW_OPCODE,
                gas_cost=2,
                stack_input=0,
                stack_output=1,
                description="Push the constant value 0 onto the stack",
            ),
        ],
        gas_changes={"PUSH0": 2},
        boundary_values=[0],
        test_vectors=[
            {"code": [0x5F, 0x00], "expected_stack": [0]},
            {"code": [0x5F, 0x5F, 0x01], "expected_stack": [0, 0]},
        ],
    ),
    3860: EIPSpec(
        number=3860,
        title="Limit and meter initcode",
        category=EIPCategory.CORE,
        status="Final",
        opcodes=[],
        gas_changes={"INITCODE_WORD_COST": 2},
        boundary_values=[0, 49152, 49153],  # 2 * MAX_CODE_SIZE
        related_eips=[170],
    ),
}


class EIPAnalyzer:
    """Analyze EIPs to extract test requirements."""

    def __init__(self) -> None:
        self.eips = KNOWN_EIPS.copy()

    def get_eip(self, number: int) -> EIPSpec | None:
        """Get EIP specification by number."""
        return self.eips.get(number)

    def get_opcodes_for_eip(self, number: int) -> list[OpcodeSpec]:
        """Get all opcodes affected by an EIP."""
        eip = self.get_eip(number)
        return eip.opcodes if eip else []

    def get_boundary_values(self, number: int) -> list[int]:
        """Get boundary values for testing an EIP."""
        eip = self.get_eip(number)
        if not eip:
            return []

        # Start with explicit boundary values
        values = list(eip.boundary_values)

        # Add gas-related boundaries
        for gas in eip.gas_changes.values():
            values.extend([gas - 1, gas, gas + 1])

        # Add standard EVM boundaries
        values.extend([
            0, 1,
            255, 256,
            2**15 - 1, 2**15,
            2**16 - 1, 2**16,
            2**32 - 1, 2**32,
            2**64 - 1, 2**64,
            2**128 - 1, 2**128,
            2**255 - 1, 2**255,
            2**256 - 1,
        ])

        return sorted(set(values))

    def get_related_eips(self, number: int) -> list[int]:
        """Get EIPs related to this one."""
        eip = self.get_eip(number)
        return eip.related_eips if eip else []

    def analyze_opcode_interactions(
        self, number: int
    ) -> list[tuple[int, int]]:
        """Find opcodes that might interact with EIP changes."""
        eip = self.get_eip(number)
        if not eip:
            return []

        interactions = []
        eip_opcodes = {op.opcode for op in eip.opcodes}

        # Common interaction patterns
        interaction_groups = [
            # Stack operations
            {0x50, 0x80, 0x81, 0x82, 0x90, 0x91, 0x92},  # POP, DUP, SWAP
            # Memory operations
            {0x51, 0x52, 0x53},  # MLOAD, MSTORE, MSTORE8
            # Storage operations
            {0x54, 0x55},  # SLOAD, SSTORE
            # Call operations
            {0xF0, 0xF1, 0xF2, 0xF4, 0xF5, 0xFA},  # CREATE, CALL, etc.
        ]

        for group in interaction_groups:
            if eip_opcodes & group:
                for op_a in eip_opcodes & group:
                    for op_b in group:
                        if op_a != op_b:
                            interactions.append((op_a, op_b))

        return interactions

    def get_test_vectors(self, number: int) -> list[dict[str, Any]]:
        """Get predefined test vectors for an EIP."""
        eip = self.get_eip(number)
        return eip.test_vectors if eip else []

    def list_all_eips(self) -> list[int]:
        """List all known EIP numbers."""
        return sorted(self.eips.keys())

    def get_eips_by_category(self, category: EIPCategory) -> list[EIPSpec]:
        """Get all EIPs in a category."""
        return [eip for eip in self.eips.values() if eip.category == category]

    def get_new_opcodes(self, number: int) -> list[OpcodeSpec]:
        """Get only new opcodes introduced by an EIP."""
        eip = self.get_eip(number)
        if not eip:
            return []
        return [op for op in eip.opcodes if op.change_type == OpcodeChange.NEW_OPCODE]

    def get_gas_changes(self, number: int) -> dict[str, int]:
        """Get gas cost changes from an EIP."""
        eip = self.get_eip(number)
        return eip.gas_changes if eip else {}
