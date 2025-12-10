"""EVM stack implementation with 1024 depth limit."""

from __future__ import annotations

from ethereum.common.types import u256


class StackOverflowError(Exception):
    """Raised when stack exceeds maximum depth."""

    pass


class StackUnderflowError(Exception):
    """Raised when popping from empty stack."""

    pass


class Stack:
    """
    EVM stack with 1024 depth limit.

    Stack values are 256-bit unsigned integers.
    """

    MAX_DEPTH = 1024

    def __init__(self) -> None:
        self._data: list[int] = []

    def __len__(self) -> int:
        return len(self._data)

    def __repr__(self) -> str:
        return f"Stack({self._data})"

    def push(self, value: int) -> None:
        """Push a value onto the stack."""
        if len(self._data) >= self.MAX_DEPTH:
            raise StackOverflowError(f"Stack depth exceeds {self.MAX_DEPTH}")
        # Ensure value is within U256 range
        self._data.append(u256(value))

    def pop(self) -> int:
        """Pop a value from the stack."""
        if not self._data:
            raise StackUnderflowError("Cannot pop from empty stack")
        return self._data.pop()

    def peek(self, depth: int = 0) -> int:
        """
        Peek at a value on the stack without removing it.

        Args:
            depth: How far down to look (0 = top of stack)

        Returns:
            The value at the specified depth

        Raises:
            StackUnderflowError: If depth exceeds stack size
        """
        if depth >= len(self._data):
            raise StackUnderflowError(f"Cannot peek at depth {depth}, stack size is {len(self._data)}")
        return self._data[-(depth + 1)]

    def set(self, depth: int, value: int) -> None:
        """
        Set a value at a specific depth.

        Args:
            depth: How far down to set (0 = top of stack)
            value: The value to set
        """
        if depth >= len(self._data):
            raise StackUnderflowError(f"Cannot set at depth {depth}, stack size is {len(self._data)}")
        self._data[-(depth + 1)] = u256(value)

    def dup(self, n: int) -> None:
        """
        Duplicate the nth stack item to the top.

        DUP1 duplicates the top item, DUP2 duplicates the second item, etc.

        Args:
            n: Which item to duplicate (1-indexed, 1-16)
        """
        if n < 1 or n > 16:
            raise ValueError(f"Invalid DUP depth: {n}")
        if n > len(self._data):
            raise StackUnderflowError(f"Cannot DUP{n}, stack size is {len(self._data)}")
        if len(self._data) >= self.MAX_DEPTH:
            raise StackOverflowError(f"Stack depth exceeds {self.MAX_DEPTH}")
        self._data.append(self._data[-n])

    def swap(self, n: int) -> None:
        """
        Swap the top stack item with the (n+1)th item.

        SWAP1 swaps positions 1 and 2, SWAP2 swaps positions 1 and 3, etc.

        Args:
            n: How far down to swap (1-indexed, 1-16)
        """
        if n < 1 or n > 16:
            raise ValueError(f"Invalid SWAP depth: {n}")
        if n + 1 > len(self._data):
            raise StackUnderflowError(f"Cannot SWAP{n}, stack size is {len(self._data)}")
        self._data[-1], self._data[-(n + 1)] = self._data[-(n + 1)], self._data[-1]

    def clear(self) -> None:
        """Clear the stack."""
        self._data.clear()

    def copy(self) -> Stack:
        """Create a copy of the stack."""
        new_stack = Stack()
        new_stack._data = self._data.copy()
        return new_stack

    def as_list(self) -> list[int]:
        """Return a copy of the stack data as a list (bottom to top)."""
        return self._data.copy()
