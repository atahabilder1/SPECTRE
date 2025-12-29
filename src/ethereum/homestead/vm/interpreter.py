"""Homestead EVM interpreter with EIP-2 changes.

EIP-2: Homestead Hard-fork Changes
- Increased CREATE gas cost
- Transaction signature validation changes
- Invalid CREATE from CALL with insufficient gas now properly handled
"""

from __future__ import annotations

from ethereum.common.types import (
    Environment,
    State,
)
from ethereum.frontier.vm.gas import GasSchedule
from ethereum.frontier.vm.interpreter import Interpreter


class HomesteadGasSchedule(GasSchedule):
    """Gas schedule with Homestead modifications."""

    # EIP-2: Increased cost for CREATE called from CALL
    G_CREATE: int = 32000

    # Contract creation minimum gas for callee
    G_CREATE_MIN_CALLEE_GAS: int = 0


class HomesteadInterpreter(Interpreter):
    """
    EVM interpreter for the Homestead fork.

    Key changes from Frontier:
    - EIP-2: Contracts created via CREATE from a CALL with insufficient gas
      now properly fail instead of creating an empty contract
    - Transaction signature uses different validation rules
    """

    fork_name: str = "Homestead"

    def __init__(
        self,
        state: State,
        env: Environment,
        gas_schedule: type[GasSchedule] = HomesteadGasSchedule,
    ) -> None:
        super().__init__(state, env, gas_schedule)

    def _validate_create_gas(self, gas_available: int, init_code_size: int) -> bool:
        """
        Validate that there's enough gas for CREATE operation.

        EIP-2 specifies that CREATE from CALL must have enough gas
        to execute the init code, or the CREATE fails.
        """
        # In Homestead, CREATE requires minimum gas to be forwarded
        # The callee gets all gas minus 1/64 (EIP-150 rule applied later)
        return gas_available >= self.gas_schedule.G_CREATE
