"""Rzadkie maski trójkątne używane przy mnożeniu funkcji OTA.

Maska o indeksie k zaznacza te pary (i, j), dla których `i | j == k`. Mnożenie funkcji OTA
sprowadza się do zsumowania iloczynów współczynników po tych parach, więc maski leżą w gorącej
ścieżce i powstają leniwie, dopiero gdy dany indeks jest potrzebny.
"""

import numpy as np
from scipy.sparse import csr_matrix


class NSSquares:
    """Kolekcja masek trójkątnych, rosnąca na żądanie."""

    def __init__(self, max_power_of_two: int = 2) -> None:
        """
        :param max_power_of_two: Najwyższa potęga dwójki, dla której maski powstają od razu.
        :type max_power_of_two: int
        """
        if max_power_of_two < 0:
            raise ValueError(f"Potęga dwójki nie może być ujemna: {max_power_of_two}")
        self.masks: list[csr_matrix] = []
        self.max_power_of_two = max_power_of_two
        self.get_mask((1 << max_power_of_two) - 1)

    def __getitem__(self, index: int) -> csr_matrix:
        """Maska o podanym indeksie."""
        return self.get_mask(index)

    def get_mask(self, index: int) -> csr_matrix:
        """
        Zwraca maskę o podanym indeksie, dobudowując brakujące.

        :param index: Indeks maski.
        :type index: int
        :return: Maska rzadka.
        :rtype: csr_matrix
        :raises ValueError: Gdy indeks jest ujemny.
        """
        if index < 0:
            raise ValueError("Mask index cannot be negative.")
        while len(self.masks) <= index:
            self.masks.append(self._create_sparse_triangle_mask(len(self.masks)))
        return self.masks[index]

    @staticmethod
    def _create_sparse_triangle_mask(target_value: int) -> csr_matrix:
        """
        Buduje maskę zaznaczającą pary (i, j) spełniające `i | j == target_value`.

        :param target_value: Wartość, do której ma się składać alternatywa bitowa.
        :type target_value: int
        :return: Dwuwymiarowa maska logiczna.
        :rtype: csr_matrix
        :raises ValueError: Gdy wartość jest ujemna.
        """
        if target_value < 0:
            raise ValueError("Target value must be non-negative.")
        size = target_value + 1

        row_indices, col_indices = np.where(
            np.bitwise_or.outer(np.arange(size), np.arange(size)) == target_value
        )
        data = np.ones_like(row_indices, dtype=bool)
        return csr_matrix((data, (row_indices, col_indices)), shape=(size, size))
