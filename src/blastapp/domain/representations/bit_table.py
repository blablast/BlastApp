"""Truth table stored as a numpy byte array: bit `i` is the result for assignment `i`.

Width is `2^len(variables)` bits and every bit above it stays zero; negation and the tautology
check rely on that invariant.

Bytes rather than one big integer: numpy bitwise ops beat integer ones on wide tables, and adding
a variable — the hot operation, since it doubles the table — becomes a byte duplication instead of
a masked bit spread. Computing in numpy while keeping the value as an integer gains nothing, since
the round trip through `to_bytes`/`from_bytes` costs what the faster pass saves. The integer is
therefore built once, at the module boundary.

Mutable on purpose. Adding a variable doubles the table — about 4 MB at 25 variables — so copying
both operands per operation would double memory traffic in the hot loop. The terms: commands are
named for their effect and return `None`; the operand passed to `apply_in_place` is **consumed**,
because `align_with` grows it; and the class never leaves the bit algebra, which hands out an
immutable `TruthTable` instead.
"""

from bisect import bisect_right
from typing import Self, assert_never

import numpy as np

from blastapp.domain.operators import Operator

# Byte -> word lookups, keyed by group width. Groups narrower than a byte cannot be duplicated by
# moving bytes around, and `unpackbits` would allocate eight times the data.
_DUPLICATION_TABLES: dict[int, np.ndarray] = {}

# From these many variables up the width is a whole number of bytes, so every byte is full, and the
# "bits above the width are zero" invariant holds without masking.
_VARIABLES_PER_FULL_BYTE = 3


def _duplication_table(group_bits: int) -> np.ndarray:
    """Lookup where every group of `group_bits` bits in a byte appears twice."""
    table = _DUPLICATION_TABLES.get(group_bits)
    if table is None:
        table = np.zeros(256, dtype="<u2")
        for byte in range(256):
            widened = 0
            for slot in range(8 // group_bits):
                group = (byte >> (slot * group_bits)) & ((1 << group_bits) - 1)
                widened |= (group << (2 * slot * group_bits)) | (
                    group << ((2 * slot + 1) * group_bits)
                )
            table[byte] = widened
        _DUPLICATION_TABLES[group_bits] = table
    return table


class BitTable:
    def __init__(self, initial_solution: int = 0):
        # Bit positions, ascending. The position alone is enough: variable masks are never read
        # here and follow from the position and the table width.
        self.variables: list[int] = []
        self.words = np.array([initial_solution & 1], dtype=np.uint8)

    @classmethod
    def create_with_variable(cls, variable_index: int, is_negated: bool = False) -> Self:
        instance = cls()
        instance._add_variable_to_solution(variable_index, is_negated, True)
        return instance

    @property
    def solution(self) -> int:
        """The table as one integer — the boundary form, not something to compute with."""
        return int.from_bytes(self.words.tobytes(), "little")

    def add_missed_variables(self) -> None:
        """Fill gaps left by variables that dropped out during simplification.

        Without it the survivors sit on the wrong bits: `(a0 & ~a0) | a1` leaves only `a1`, and
        the result read back would describe a different formula.
        """
        if self.variables:
            for index in range(self.highest_index()):
                self._add_variable_to_solution(index)

    def highest_index(self) -> int:
        """Highest bit position, or `-1` when there are no variables."""
        return self.variables[-1] if self.variables else -1

    def is_true(self) -> bool:
        """Whether the proposition is a tautology.

        Comparing against a ready pattern would allocate a table of the same width on every call,
        and the check runs after every merged pair. `min()` walks the data without allocating.
        """
        if len(self.variables) >= _VARIABLES_PER_FULL_BYTE:
            return int(self.words.min()) == 0xFF
        return int(self.words[0]) == self._tail_mask()

    def is_false(self) -> bool:
        return not bool(self.words.any())

    def negate_in_place(self) -> None:
        self.words = self._negated(self.words)

    def apply_in_place(self, operation: Operator, other: Self) -> None:
        """Apply a binary operation, storing the result here; `other` is consumed.

        The match is exhaustive over `Operator`, so adding one there stops type checking right
        here instead of at a runtime error. Only operations numpy does in a single instruction
        live here; `NOT`, `XOR` and `IMP` are composed by the algebra.

        :raises ValueError: when the operator is not one of the primitives.
        """
        normalized_other = self.align_with(other)

        match operation:
            case Operator.AND:
                self.words = np.bitwise_and(self.words, normalized_other.words)
            case Operator.OR:
                self.words = np.bitwise_or(self.words, normalized_other.words)
            case Operator.EQ:
                self.words = self._negated(np.bitwise_xor(self.words, normalized_other.words))
            case Operator.NOT | Operator.XOR | Operator.IMP:
                raise ValueError(f"{operation} is not a primitive here")
            case _:
                assert_never(operation)

    def align_with(self, other: Self) -> Self:
        """Grow both tables to a common variable set and return `other`, now consumed."""
        # Sets up front: testing membership inside the comprehension would rebuild the collection
        # per index, turning linear work into quadratic.
        other_indices = set(other.variables)
        self_indices = set(self.variables)
        other_missing = [index for index in self.variables if index not in other_indices]
        self_missing = [index for index in other.variables if index not in self_indices]

        for index in other_missing:
            other._add_variable_to_solution(index, False, False)
        for index in self_missing:
            self._add_variable_to_solution(index, False, False)

        return other

    def variable_count(self) -> int:
        return len(self.variables)

    def _negated(self, words: np.ndarray) -> np.ndarray:
        """Bitwise complement that keeps bits above the width zero.

        From three variables up every byte is full, so `bitwise_not` alone keeps the invariant and
        masking would only add passes over the whole table.
        """
        negated: np.ndarray = np.bitwise_not(words)
        if len(self.variables) < _VARIABLES_PER_FULL_BYTE:
            negated &= self._tail_mask()
        return negated

    def _add_variable_to_solution(
        self, variable_index: int, is_negated: bool = False, initialize_solution: bool = True
    ) -> None:
        # One bisection answers both "is it already there" and "where does it go"; `variables` is
        # sorted, so a linear scan would be duplicate work.
        index = bisect_right(self.variables, variable_index)
        if index and self.variables[index - 1] == variable_index:
            return

        self.variables.insert(index, variable_index)
        if len(self.variables) == 1 and initialize_solution:
            self.words = np.array([0b01 if is_negated else 0b10], dtype=np.uint8)
        else:
            self.words = self._expand_bit_groups(self.words, index)

    def _expand_bit_groups(self, words: np.ndarray, bit_group_size: int) -> np.ndarray:
        """Duplicate every group of `2^bit_group_size` bits, because adding a variable doubles
        the table.

        The result is trimmed to the width implied by the variable count: for tables narrower than
        a byte the lookup returns two bytes, the second of them zero.
        """
        group_size = 1 << bit_group_size
        if group_size >= 8:
            bytes_per_group = group_size // 8
            if bytes_per_group == 1:
                widened = np.repeat(words, 2)
            else:
                widened = np.repeat(words.reshape(-1, bytes_per_group), 2, axis=0).ravel()
        else:
            widened = _duplication_table(group_size)[words].view(np.uint8)

        expected = self._byte_count()
        if widened.size == expected:
            return widened
        if widened.size > expected:
            return widened[:expected].copy()
        return np.pad(widened, (0, expected - widened.size))

    def _byte_count(self) -> int:
        return max(1, (1 << len(self.variables)) // 8)

    def _tail_mask(self) -> int:
        """Mask of the single partial byte of a table narrower than a byte."""
        return (1 << (1 << len(self.variables))) - 1
