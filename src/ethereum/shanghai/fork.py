"""Shanghai fork state transition function.

Implements EIP-3855 (PUSH0) and other Shanghai improvements.
"""

from __future__ import annotations

from ethereum.common.types import (
    ZERO_ADDRESS,
    Environment,
    ExecutionResult,
    Message,
    State,
    Transaction,
)
from ethereum.shanghai.vm.interpreter import ShanghaiGasSchedule, ShanghaiInterpreter


def validate_transaction(tx: Transaction, state: State) -> str | None:
    """
    Validate a transaction before execution.

    Returns:
        Error message if invalid, None if valid
    """
    sender_account = state.get_account(tx.sender)

    if sender_account.nonce != tx.nonce:
        return f"Invalid nonce: expected {sender_account.nonce}, got {tx.nonce}"

    is_create = tx.to is None
    intrinsic_gas = ShanghaiGasSchedule.transaction_intrinsic_gas(tx.data, is_create)

    if tx.gas < intrinsic_gas:
        return f"Intrinsic gas too low: {tx.gas} < {intrinsic_gas}"

    required = tx.gas * tx.gas_price + tx.value
    if sender_account.balance < required:
        return f"Insufficient balance: {sender_account.balance} < {required}"

    # EIP-3860: Limit initcode size (Shanghai)
    if is_create and len(tx.data) > 49152:  # 2 * MAX_CODE_SIZE
        return f"Initcode too large: {len(tx.data)} > 49152"

    return None


def state_transition(
    state: State,
    tx: Transaction,
    env: Environment,
) -> tuple[State, ExecutionResult]:
    """
    Execute a transaction under Shanghai rules.

    Key features:
    - EIP-3855: PUSH0 opcode support
    - EIP-3860: Limit and meter initcode

    Args:
        state: Current world state
        tx: Transaction to execute
        env: Block environment

    Returns:
        Tuple of (new_state, execution_result)
    """
    state = state.copy()

    error = validate_transaction(tx, state)
    if error:
        return state, ExecutionResult(
            success=False,
            error=error,
            gas_used=0,
        )

    sender_account = state.get_account(tx.sender)
    upfront_cost = tx.gas * tx.gas_price
    state.set_balance(tx.sender, sender_account.balance - upfront_cost)

    state.increment_nonce(tx.sender)

    is_create = tx.to is None
    intrinsic_gas = ShanghaiGasSchedule.transaction_intrinsic_gas(tx.data, is_create)

    # EIP-3860: Add initcode gas cost
    if is_create:
        initcode_words = (len(tx.data) + 31) // 32
        initcode_gas = 2 * initcode_words  # INITCODE_WORD_COST = 2
        intrinsic_gas += initcode_gas

    gas_remaining = tx.gas - intrinsic_gas

    tx_env = Environment(
        caller=tx.sender,
        origin=tx.sender,
        block_hashes=env.block_hashes,
        coinbase=env.coinbase,
        number=env.number,
        gas_limit=env.gas_limit,
        gas_price=tx.gas_price,
        timestamp=env.timestamp,
        difficulty=env.difficulty,
        chain_id=env.chain_id,
        base_fee=env.base_fee,
    )

    interpreter = ShanghaiInterpreter(state, tx_env)

    if is_create:
        from ethereum.common.types import create_address

        contract_address = create_address(tx.sender, sender_account.nonce)

        if tx.value > 0:
            state.set_balance(tx.sender, state.get_balance(tx.sender) - tx.value)
            state.set_balance(contract_address, state.get_balance(contract_address) + tx.value)

        message = Message(
            caller=tx.sender,
            target=contract_address,
            value=tx.value,
            data=b"",
            gas=gas_remaining,
            depth=0,
            code=tx.data,
            is_create=True,
        )

        result = interpreter.execute(message)

        if result.success:
            # Check code size limit (EIP-170)
            if len(result.return_data) > 24576:
                result = ExecutionResult(
                    success=False,
                    gas_used=tx.gas,
                    gas_remaining=0,
                    error="Code size limit exceeded",
                )
            else:
                deploy_gas = len(result.return_data) * ShanghaiGasSchedule.G_CODEDEPOSIT
                if result.gas_remaining >= deploy_gas:
                    state.set_code(contract_address, result.return_data)
                    result = ExecutionResult(
                        success=True,
                        gas_used=tx.gas - result.gas_remaining + deploy_gas,
                        gas_remaining=result.gas_remaining - deploy_gas,
                        return_data=result.return_data,
                        logs=result.logs,
                        created_address=contract_address,
                    )
                else:
                    result = ExecutionResult(
                        success=False,
                        gas_used=tx.gas,
                        gas_remaining=0,
                        error="Out of gas for code deployment",
                    )
    else:
        target = tx.to or ZERO_ADDRESS
        code = state.get_code(target)

        if tx.value > 0:
            state.set_balance(tx.sender, state.get_balance(tx.sender) - tx.value)
            state.set_balance(target, state.get_balance(target) + tx.value)

        message = Message(
            caller=tx.sender,
            target=target,
            value=tx.value,
            data=tx.data,
            gas=gas_remaining,
            depth=0,
            code=code,
        )

        result = interpreter.execute(message)

    total_gas_used = intrinsic_gas + result.gas_used if result.success else tx.gas

    refund = (tx.gas - total_gas_used) * tx.gas_price
    state.set_balance(tx.sender, state.get_balance(tx.sender) + refund)

    coinbase_reward = total_gas_used * tx.gas_price
    state.set_balance(env.coinbase, state.get_balance(env.coinbase) + coinbase_reward)

    return state, ExecutionResult(
        success=result.success,
        gas_used=total_gas_used,
        gas_remaining=tx.gas - total_gas_used,
        return_data=result.return_data,
        logs=result.logs if result.success else [],
        error=result.error,
        created_address=result.created_address if result.success else None,
    )
