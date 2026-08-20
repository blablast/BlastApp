"""OTA function: a `tn` coefficient vector over 2^n terms and a parallel `bn` value vector.

`tn` and `bn` describe the same function and must stay consistent. Whoever assigns one owes the
other a recomputation — which is why negation is `negated()` rather than the caller reaching into
`tn`.

The conversions between them memoise: the recursion overlaps heavily, and without memoisation the
cost grows several-fold per added variable.
"""

from typing import Self

import numpy as np

from blastapp.domain.representations.ns_squares import NSSquares


class OtaFunction:
    def __init__(self) -> None:
        # Empty arrays rather than None: the object is never half-built, so no method has to check
        # whether its vectors exist yet.
        self.tn: np.ndarray = np.zeros(0, dtype=np.int64)
        # `bn` and `c` are computed on first read. Only `to_truth_table` at the end and the
        # presentation layer look at them, while every intermediate comes from `from_tn`.
        self._bn: np.ndarray | None = np.zeros(0, dtype=np.int64)
        self._c: np.ndarray | None = np.zeros(0, dtype=np.int64)
        self.variables_count = 0
        # Coefficients double per XOR level, so narrower integers overflow quickly and numpy 2.x
        # raises instead of wrapping.
        self.tn_type = np.int64
        self.bn_type = np.int64
        self.c_type = np.int64

    @property
    def bn(self) -> np.ndarray:
        if self._bn is None:
            self.recalculate_bn()
        assert self._bn is not None
        return self._bn

    @bn.setter
    def bn(self, value: np.ndarray) -> None:
        self._bn = value

    @property
    def c(self) -> np.ndarray:
        """Increments of `bn`, computed alongside it."""
        if self._c is None:
            self.recalculate_bn()
        assert self._c is not None
        return self._c

    @c.setter
    def c(self, value: np.ndarray) -> None:
        self._c = value

    @classmethod
    def from_bn(cls, bn: np.ndarray) -> Self:
        instance = cls()
        instance.bn = bn
        instance.recalculate_tn()
        return instance

    @classmethod
    def from_tn(cls, tn: np.ndarray) -> Self:
        instance = cls()
        instance._initialize(tn, is_bn=False)
        # Invalidate right after `_initialize`, which only zeroes them to seed the recursion. That
        # recursion is the expensive part of multiplication and pointless for an intermediate.
        instance._bn = None
        instance._c = None
        instance._truncate_to_power_of_two()
        return instance

    def _initialize(self, input_sequence: np.ndarray, is_bn: bool = True) -> None:
        """:raises TypeError: when the input is not an integer numpy array."""
        if isinstance(input_sequence, list):
            input_sequence = np.array(input_sequence)

        if not isinstance(input_sequence, np.ndarray) or not np.issubdtype(
            input_sequence.dtype, np.integer
        ):
            raise TypeError("Input sequence must be a NumPy array of integers.")
        if len(input_sequence.shape) > 1:
            input_sequence = input_sequence.flatten()

        self.c = np.zeros_like(input_sequence, dtype=self.c_type)
        self.tn = np.zeros_like(input_sequence, dtype=self.tn_type)
        self.bn = np.zeros_like(input_sequence, dtype=self.bn_type)

        if is_bn:
            self.bn = input_sequence.astype(self.bn.dtype)
            self.c[0] = self.tn[0] = self.bn[0]
        else:
            self.tn = input_sequence.astype(self.tn.dtype)
            self.c[0] = self.bn[0] = self.tn[0]

    def _pad_arrays(self, other: "OtaFunction") -> tuple[np.ndarray, np.ndarray]:
        max_length = max(len(self.tn), len(other.tn))
        padded_self = np.pad(self.tn, (0, max_length - len(self.tn)))
        padded_other = np.pad(other.tn, (0, max_length - len(other.tn)))
        return padded_self, padded_other

    def recalculate_bn(self) -> None:
        self._initialize(self.tn, is_bn=False)
        memo: dict[tuple[int, int], int] = {}
        for i in range(1, len(self.c)):
            self.c[i] = self._calculate_bn_recursive(i, 0, memo)
            self.bn[i] = self.c[i] + self.bn[i - 1]
        self._truncate_to_power_of_two()

    def recalculate_tn(self) -> None:
        self._initialize(self.bn, is_bn=True)
        self.c[1:] = self.bn[1:] - self.bn[:-1]
        # Prefix sums lift the inner summing loop out of the recursion's base case.
        prefix = np.concatenate(([0], np.cumsum(self.c)))
        memo: dict[tuple[int, int], int] = {}
        for i in range(1, len(self.tn)):
            self.tn[i] = self._calculate_tn_recursive(i, 0, memo, prefix)
        self._truncate_to_power_of_two()

    def _calculate_bn_recursive(
        self, index: int, offset: int, memo: dict[tuple[int, int], int]
    ) -> int:
        key = (index, offset)
        cached = memo.get(key)
        if cached is not None:
            return cached

        power_of_two = self._largest_power_of_two(index)
        if index == power_of_two:
            value = int(self.tn[offset + index]) - int(self.tn[offset + 1 : offset + index].sum())
        else:
            half_index = index % power_of_two
            value = self._calculate_bn_recursive(
                half_index, offset + power_of_two, memo
            ) + self._calculate_bn_recursive(half_index, offset, memo)

        memo[key] = value
        return value

    def _calculate_tn_recursive(
        self, index: int, offset: int, memo: dict[tuple[int, int], int], prefix: np.ndarray
    ) -> int:
        key = (index, offset)
        cached = memo.get(key)
        if cached is not None:
            return cached

        power_of_two = self._largest_power_of_two(index)
        if index == power_of_two:
            value = int(prefix[offset + index + 1] - prefix[offset + 1])
        else:
            half_index = index % power_of_two
            value = self._calculate_tn_recursive(
                half_index, offset + power_of_two, memo, prefix
            ) - self._calculate_tn_recursive(half_index, offset, memo, prefix)

        memo[key] = value
        return value

    @staticmethod
    def _largest_power_of_two(value: int) -> int:
        """:raises ValueError: when the value is below one."""
        if value < 1:
            raise ValueError("Input value must be greater than or equal to 1.")
        return 1 << (value.bit_length() - 1)

    def __add__(self, other: "OtaFunction") -> "OtaFunction":
        padded_self, padded_other = self._pad_arrays(other)
        result = OtaFunction().from_tn(padded_self + padded_other)
        result._truncate_to_power_of_two()
        return result

    def __sub__(self, other: "OtaFunction") -> "OtaFunction":
        padded_self, padded_other = self._pad_arrays(other)
        result = OtaFunction().from_tn(padded_self - padded_other)
        result._truncate_to_power_of_two()
        return result

    def multiplied_by(self, other: "OtaFunction", squares: NSSquares) -> "OtaFunction":
        """Multiply two functions using an externally owned set of index pairs.

        The pairs come from outside because every multiplication returns a NEW function: kept on
        the operand they would be rebuilt for each intermediate, and building them costs more than
        the multiplication itself.
        """
        padded_self, padded_other = self._pad_arrays(other)
        multiplied = np.outer(padded_self, padded_other)
        result_tn = np.array(
            [multiplied[squares[i]].sum() for i in range(len(padded_self))],
            dtype=self.tn.dtype,
        )

        result = OtaFunction().from_tn(result_tn)
        result._truncate_to_power_of_two()
        return result

    def __len__(self) -> int:
        """Length of the coefficient vector, i.e. 2^n assignments — NOT the variable count.

        The distinction matters here because `variables_count` sits right next to it.
        """
        return int(self.tn.size)

    def _truncate_to_power_of_two(self) -> None:
        """Shrink `tn` to the shortest power-of-two length that still holds every non-zero term."""
        if self.tn.size == 0:
            raise ValueError("The tn array is not initialized or is empty.")

        last_non_zero_index = np.where(self.tn != 0)[0]
        if last_non_zero_index.size == 0:
            self.tn = np.zeros(1, dtype=self.tn.dtype)
            return

        last_non_zero_index = last_non_zero_index[-1] + 1

        new_length = self._largest_power_of_two(int(last_non_zero_index))
        if new_length < last_non_zero_index:
            new_length *= 2
        new_length = max(new_length, 1)

        self.tn = self.tn[:new_length]

        # Private fields, not the properties: reading `self.bn` would compute what we are about to
        # throw away.
        if self._bn is not None:
            self._bn = self._bn[:new_length]
        if self._c is not None:
            self._c = self._c[:new_length]

        self.variables_count = int(np.log2(len(self.tn)))

    def negated(self) -> "OtaFunction":
        """Negation as a new object.

        Negating in place would be a trap: it needs `tn` assigned and `bn` recomputed, and skipping
        the second step silently desynchronises the two vectors.
        """
        negated_tn = -self.tn
        negated_tn[0] += 1
        return OtaFunction().from_tn(negated_tn)
