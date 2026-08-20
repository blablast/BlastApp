"""Index pairs used when multiplying OTA functions.

The set at index k holds the pairs (i, j) with `i | j == k`. Multiplication sums coefficient
products over those pairs, so the sets sit in the hot path and are built lazily.

They are kept as two plain index arrays rather than a sparse matrix: multiplication only needs the
non-zero positions, and `csr_matrix.nonzero()` builds a `coo_matrix` internally on EVERY call.
"""

import numpy as np

Pairs = tuple[np.ndarray, np.ndarray]


class NSSquares:
    """Index-pair sets, grown on demand."""

    def __init__(self, max_power_of_two: int = 2) -> None:
        if max_power_of_two < 0:
            raise ValueError(f"Power of two cannot be negative: {max_power_of_two}")
        self.pairs: list[Pairs] = []
        self.max_power_of_two = max_power_of_two
        self.get_pairs((1 << max_power_of_two) - 1)

    def __getitem__(self, index: int) -> Pairs:
        return self.get_pairs(index)

    def get_pairs(self, index: int) -> Pairs:
        """Pairs (i, j) with `i | j == index`, building the missing sets first.

        :raises ValueError: when the index is negative.
        """
        if index < 0:
            raise ValueError("Mask index cannot be negative.")
        if len(self.pairs) <= index:
            # Grow to the next power of two, not to `index` itself. Multiplication asks for indices
            # in order, so growing one at a time would rebuild once per index.
            self._build_up_to((1 << index.bit_length()) - 1)
        return self.pairs[index]

    def _build_up_to(self, index: int) -> None:
        """Build every set from zero to `index` in one pass.

        Set by set is cubic — each would run its own `outer` sized to its index. One `outer` over
        the whole range plus grouping the pairs by `i | j` brings it down, and the sets are needed
        together anyway. The caller picks `index` so that rebuilds stay logarithmic in number.
        """
        size = index + 1
        combined = np.bitwise_or.outer(np.arange(size), np.arange(size)).ravel()
        order = np.argsort(combined, kind="stable")
        # Group boundaries: pairs sharing `i | j` end up adjacent once sorted.
        boundaries = np.searchsorted(combined[order], np.arange(size + 1))

        self.pairs = []
        for value in range(size):
            rows, columns = np.divmod(order[boundaries[value] : boundaries[value + 1]], size)
            self.pairs.append((rows, columns))
