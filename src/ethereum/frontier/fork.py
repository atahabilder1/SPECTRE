"""Frontier fork state transition function."""

from __future__ import annotations

from ethereum.common.types import (
    ZERO_ADDRESS,
    Environment,
    ExecutionResult,
    Message,
    State,
    Transaction,
)
from ethereum.frontier.vm.gas import GasSchedule
from ethereum.frontier.vm.interpreter import Interpreter


def validate_transaction(tx: Transaction, state: State) -> str | None:
    """
    Validate a transaction before execution.

    Returns:
        Error message if invalid, None if valid
    """
    # Check sender exists and has sufficient balance
    sender_account = state.get_account(tx.sender)

    # Check nonce
    if sender_account.nonce != tx.nonce:
        return f"Invalid nonce: expected {sender_account.nonce}, got {tx.nonce}"

    # Calculate intrinsic gas
    is_create = tx.to is None
    intrinsic_gas = GasSchedule.transaction_intrinsic_gas(tx.data, is_create)

    if tx.gas < intrinsic_gas:
        return f"Intrinsic gas too low: {tx.gas} < {intrinsic_gas}"

    # Check balance covers gas * gas_price + value
    required = tx.gas * tx.gas_price + tx.value
    if sender_account.balance < required:
        return f"Insufficient balance: {sender_account.balance} < {required}"

    return None


def state_transition(
    state: State,
    tx: Transaction,
    env: Environment,
) -> tuple[State, ExecutionResult]:
    """
    Execute a transaction and return the new state.

    This is the main entry point for executing transactions in the Frontier fork.

    Args:
        state: Current world state
        tx: Transaction to execute
        env: Block environment

    Returns:
        Tuple of (new_state, execution_result)
    """
    # Make a copy of state for modifications
    state = state.copy()

    # Validate transaction
    error = validate_transaction(tx, state)
    if error:
        return state, ExecutionResult(
            success=False,
            error=error,
            gas_used=0,
        )

    # Deduct upfront gas cost
    sender_account = state.get_account(tx.sender)
    upfront_cost = tx.gas * tx.gas_price
    state.set_balance(tx.sender, sender_account.balance - upfront_cost)

    # Increment sender nonce
    state.increment_nonce(tx.sender)

    # Calculate intrinsic gas
    is_create = tx.to is None
    intrinsic_gas = GasSchedule.transaction_intrinsic_gas(tx.data, is_create)
    gas_remaining = tx.gas - intrinsic_gas

    # Create environment with transaction context
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

    # Create interpreter
    interpreter = Interpreter(state, tx_env)

    if is_create:
        # Contract creation
        from ethereum.common.types import create_address

        contract_address = create_address(tx.sender, sender_account.nonce)

        # Transfer value to new contract
        if tx.value > 0:
            state.set_balance(tx.sender, state.get_balance(tx.sender) - tx.value)
            state.set_balance(contract_address, state.get_balance(contract_address) + tx.value)

        # Create message for init code execution
        message = Message(
            caller=tx.sender,
            target=contract_address,
            value=tx.value,
            data=b"",
            gas=gas_remaining,
            depth=0,
            code=tx.data,  # Init code
            is_create=True,
        )

        result = interpreter.execute(message)

        if result.success:
            # Deploy the returned code
            deploy_gas = len(result.return_data) * GasSchedule.G_CODEDEPOSIT
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
                # Out of gas for deployment
                result = ExecutionResult(
                    success=False,
                    gas_used=tx.gas,
                    gas_remaining=0,
                    error="Out of gas for code deployment",
                )
    else:
        # Message call
        target = tx.to or ZERO_ADDRESS
        code = state.get_code(target)

        # Transfer value
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

    # Calculate gas used and refund
    total_gas_used = intrinsic_gas + result.gas_used if result.success else tx.gas

    # Refund unused gas to sender
    refund = (tx.gas - total_gas_used) * tx.gas_price
    state.set_balance(tx.sender, state.get_balance(tx.sender) + refund)

    # Pay coinbase
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


def apply_block(
    state: State,
    transactions: list[Transaction],
    env: Environment,
) -> tuple[State, list[ExecutionResult]]:
    """
    Apply a block of transactions to the state.

    Args:
        state: Current world state
        transactions: List of transactions to execute
        env: Block environment

    Returns:
        Tuple of (new_state, list_of_results)
    """
    results: list[ExecutionResult] = []

    for tx in transactions:
        state, result = state_transition(state, tx, env)
        results.append(result)

    return state, results
