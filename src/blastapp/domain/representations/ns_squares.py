"""Pary indeksów używane przy mnożeniu funkcji OTA.

Zbiór o indeksie k zawiera te pary (i, j), dla których `i | j == k`. Mnożenie funkcji OTA
sprowadza się do zsumowania iloczynów współczynników po tych parach, więc zbiory leżą w gorącej
ścieżce i powstają leniwie, dopiero gdy dany indeks jest potrzebny.

Pary są trzymane wprost jako dwie tablice indeksów, a nie jako macierz rzadka. Mnożeniu
potrzebne są wyłącznie pozycje niezerowe, a `csr_matrix.nonzero()` buduje wewnętrznie
`coo_matrix` przy KAŻDYM wywołaniu — przy odpytywaniu po kolei dla każdego indeksu daje to
dwa rzędy wielkości więcej konstrukcji scipy, niż jest samych zbiorów.
"""

import numpy as np

Pairs = tuple[np.ndarray, np.ndarray]


class NSSquares:
    """Kolekcja par indeksów, rosnąca na żądanie."""

    def __init__(self, max_power_of_two: int = 2) -> None:
        """
        :param max_power_of_two: Najwyższa potęga dwójki, dla której pary powstają od razu.
        :type max_power_of_two: int
        """
        if max_power_of_two < 0:
            raise ValueError(f"Potęga dwójki nie może być ujemna: {max_power_of_two}")
        self.pairs: list[Pairs] = []
        self.max_power_of_two = max_power_of_two
        self.get_pairs((1 << max_power_of_two) - 1)

    def __getitem__(self, index: int) -> Pairs:
        """Pary o podanym indeksie, gotowe do indeksowania tablicy dwuwymiarowej."""
        return self.get_pairs(index)

    def get_pairs(self, index: int) -> Pairs:
        """
        Zwraca pary (i, j) spełniające `i | j == index`, dobudowując brakujące.

        :param index: Indeks zbioru par.
        :type index: int
        :return: Wiersze i kolumny jako dwie tablice indeksów.
        :rtype: Pairs
        :raises ValueError: Gdy indeks jest ujemny.
        """
        if index < 0:
            raise ValueError("Mask index cannot be negative.")
        if len(self.pairs) <= index:
            # Dobudowa idzie do najbliższej potęgi dwójki, nie do samego `index`. Mnożenie
            # odpytuje indeksy po kolei, więc rozbudowa co jeden dawałaby jedną przebudowę
            # na indeks — czyli z powrotem koszt sześcienny.
            self._build_up_to((1 << index.bit_length()) - 1)
        return self.pairs[index]

    def _build_up_to(self, index: int) -> None:
        """
        Buduje zbiory par od zera do `index` włącznie, jednym przebiegiem.

        Zbiór po zbiorze kosztuje `O(n^3)`: każdy robi własny `outer` o boku równym swojemu
        indeksowi. Jeden `outer` na cały zakres i pogrupowanie par po wartości `i | j` schodzi
        do `O(n^2 log n)` — a zbiory i tak są potrzebne wszystkie naraz, bo mnożenie przebiega
        po kolejnych indeksach.

        Wołający dobiera `index` tak, by przebudów było logarytmicznie wiele.

        :param index: Najwyższy potrzebny indeks.
        :type index: int
        :return: None
        """
        size = index + 1
        combined = np.bitwise_or.outer(np.arange(size), np.arange(size)).ravel()
        order = np.argsort(combined, kind="stable")
        # Granice grup: pary o tej samej wartości `i | j` leżą po sortowaniu obok siebie.
        boundaries = np.searchsorted(combined[order], np.arange(size + 1))

        self.pairs = []
        for value in range(size):
            rows, columns = np.divmod(order[boundaries[value] : boundaries[value + 1]], size)
            self.pairs.append((rows, columns))
