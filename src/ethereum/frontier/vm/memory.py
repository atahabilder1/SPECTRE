"""EVM memory implementation with 32-byte word expansion."""

from __future__ import annotations


class Memory:
    """
    EVM memory with dynamic expansion.

    Memory is byte-addressable but expands in 32-byte words.
    Expansion incurs gas costs.
    """

    def __init__(self) -> None:
        self._data: bytearray = bytearray()

    def __len__(self) -> int:
        return len(self._data)

    def __repr__(self) -> str:
        return f"Memory({len(self._data)} bytes)"

    @staticmethod
    def word_size(size: int) -> int:
        """Calculate the number of 32-byte words needed for given size."""
        return (size + 31) // 32

    def _expand(self, offset: int, size: int) -> int:
        """
        Expand memory to accommodate access at offset with given size.

        Returns:
            The number of new words allocated
        """
        if size == 0:
            return 0

        end = offset + size
        current_words = self.word_size(len(self._data))
        required_words = self.word_size(end)

        if required_words > current_words:
            new_size = required_words * 32
            self._data.extend(b"\x00" * (new_size - len(self._data)))
            return required_words - current_words

        return 0

    def expansion_cost(self, offset: int, size: int) -> int:
        """
        Calculate the gas cost for expanding memory.

        Memory cost formula:
            cost = 3 * words + words^2 / 512

        Returns:
            The additional gas cost for this expansion (delta)
        """
        if size == 0:
            return 0

        end = offset + size
        current_words = self.word_size(len(self._data))
        required_words = self.word_size(end)

        if required_words <= current_words:
            return 0

        def memory_cost(words: int) -> int:
            return 3 * words + (words * words) // 512

        return memory_cost(required_words) - memory_cost(current_words)

    def load(self, offset: int, size: int = 32) -> bytes:
        """
        Load bytes from memory.

        Args:
            offset: Starting byte offset
            size: Number of bytes to load

        Returns:
            The bytes at the specified location (zero-padded if needed)
        """
        if size == 0:
            return b""

        self._expand(offset, size)
        return bytes(self._data[offset : offset + size])

    def load_word(self, offset: int) -> int:
        """Load a 256-bit word from memory as big-endian integer."""
        data = self.load(offset, 32)
        return int.from_bytes(data, "big")

    def store(self, offset: int, data: bytes) -> None:
        """
        Store bytes in memory.

        Args:
            offset: Starting byte offset
            data: Bytes to store
        """
        if not data:
            return

        self._expand(offset, len(data))
        self._data[offset : offset + len(data)] = data

    def store_word(self, offset: int, value: int) -> None:
        """Store a 256-bit word in memory as big-endian bytes."""
        data = (value & ((1 << 256) - 1)).to_bytes(32, "big")
        self.store(offset, data)

    def store_byte(self, offset: int, value: int) -> None:
        """Store a single byte in memory."""
        self._expand(offset, 1)
        self._data[offset] = value & 0xFF

    def size(self) -> int:
        """Return the current size of memory in bytes."""
        return len(self._data)

    def copy(self) -> Memory:
        """Create a copy of the memory."""
        new_memory = Memory()
        new_memory._data = bytearray(self._data)
        return new_memory

    def as_bytes(self) -> bytes:
        """Return memory contents as immutable bytes."""
        return bytes(self._data)

    def copy_within(self, dest_offset: int, src_offset: int, size: int) -> None:
        """
        Copy data within memory (for MCOPY - EIP-5656).

        Args:
            dest_offset: Destination offset
            src_offset: Source offset
            size: Number of bytes to copy
        """
        if size == 0:
            return

        # Expand memory for both source and destination
        self._expand(src_offset, size)
        self._expand(dest_offset, size)

        # Use temporary copy to handle overlapping regions
        data = bytes(self._data[src_offset : src_offset + size])
        self._data[dest_offset : dest_offset + size] = data
