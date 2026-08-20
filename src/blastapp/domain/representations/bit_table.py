"""Tablica prawdy formuły zakodowana w tablicy bajtów numpy.

Bit `i` tablicy to wynik dla wartościowania `i`; bajt `b` trzyma bity `8b..8b+7`, licząc od
najmniej znaczącego. Szerokość to `2^len(variables)` bitów, a bity powyżej niej są zerowe —
na tym niezmienniku opiera się negacja i porównanie z prawdą.

DLACZEGO NUMPY, A NIE JEDNA LICZBA CAŁKOWITA. Na tablicy 8 MB operacje bitowe na `np.uint8`
są trzykrotnie szybsze niż na wielkiej liczbie (0.52 ms wobec 1.61 ms), a dołożenie zmiennej —
najgorętsza operacja, bo podwaja tablicę — pięćdziesięciokrotnie, bo sprowadza się do powielenia
bajtów zamiast do rozsuwania bitów maskami. Rozwiązanie pośrednie, liczące w numpy i trzymające
wynik jako liczbę, nie daje nic: `int.to_bytes` i `int.from_bytes` kosztują tyle, ile oszczędza
sam przebieg. Liczba całkowita powstaje więc RAZ, na granicy modułu.

MUTOWALNA, i to jest decyzja, nie niedopatrzenie. Dołożenie zmiennej PODWAJA długość tablicy:
przy 25 zmiennych to około 4 MB. Kopiowanie obu argumentów przy każdej operacji podwoiłoby ruch
pamięci w gorącej pętli i przewróciło dokładnie ten benchmark, dla którego ta aplikacja powstała.

Warunki, na jakich mutacja tu obowiązuje:

1. Nazwy zapowiadają efekt: `align_with`, `apply_in_place` i `negate_in_place` zwracają `None`,
   bo są poleceniami, nie zapytaniami (#04, #08).
2. Argument przekazany do `apply_in_place` jest **zużyty** — `align_with` dopisuje mu brakujące
   zmienne, więc po wywołaniu nie wolno go użyć ponownie.
3. Klasa nie opuszcza warstwy algebry bitowej; na zewnątrz wychodzi niemutowalny `TruthTable`.
"""

from bisect import bisect_right
from typing import assert_never

import numpy as np

from blastapp.domain.operators import Operator


def _duplication_table(group_bits: int) -> np.ndarray:
    """
    Tablica bajt -> słowo, w której każda grupa `group_bits` bitów występuje dwukrotnie.

    Grupy węższe od bajtu nie dają się powielić przestawieniem bajtów, a droga przez
    `unpackbits` alokuje ośmiokrotność danych. Podstawienie z tablicy 256-elementowej
    załatwia to jednym przebiegiem numpy.

    :param group_bits: Szerokość grupy w bitach; 1, 2 albo 4.
    :type group_bits: int
    :return: Tablica 256 słów szesnastobitowych w porządku little-endian.
    :rtype: np.ndarray
    """
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


#: Tablice powielania zależą wyłącznie od szerokości grupy i mają po 512 bajtów, więc komplet
#: mieści się w pamięci bez żadnego budżetu — inaczej niż maski o szerokości całej tablicy.
_DUPLICATION_TABLES: dict[int, np.ndarray] = {}


#: Od tylu zmiennych tablica ma szerokość będącą wielokrotnością bajtu, więc wszystkie bajty
#: są pełne i niezmiennik "bity powyżej szerokości są zerem" utrzymuje się sam.
_VARIABLES_PER_FULL_BYTE = 3


class BitTable:
    def __init__(self, initial_solution: int = 0):
        """
        :param initial_solution: Wartość zdania bez zmiennych: 0 albo 1.
        :type initial_solution: int
        """
        # Pozycje bitowe zmiennych, rosnąco. Sama pozycja wystarcza: maski zmiennych nikt tu
        # nie czyta, a dają się wyliczyć z pozycji i szerokości tablicy.
        self.variables: list[int] = []
        self.words = np.array([initial_solution & 1], dtype=np.uint8)

    @classmethod
    def create_with_variable(cls, variable_index: int, is_negated: bool = False) -> "BitTable":
        """
        :param variable_index: Pozycja bitowa zmiennej.
        :type variable_index: int
        :param is_negated: Czy zmienna występuje zanegowana.
        :type is_negated: bool
        :return: Tablica opisująca pojedynczy literał.
        :rtype: BitTable
        """
        instance = cls()
        instance._add_variable_to_solution(variable_index, is_negated, True)
        return instance

    @property
    def solution(self) -> int:
        """Tablica jako jedna liczba całkowita — postać na granicę modułu, nie do liczenia."""
        return int.from_bytes(self.words.tobytes(), "little")

    def add_missed_variables(self) -> None:
        """Dopełnia luki w pozycjach bitowych zmiennymi, które wypadły przy uproszczeniu.

        Bez tego zmienne, które przetrwały, siedzą na złych bitach: `(a0 & ~a0) | a1` zostawia
        samo `a1`, a wynik odczytany bez dopełnienia opisywałby zupełnie inną formułę.
        """
        if len(self.variables) > 0:
            last_index = self.highest_index()
            for i in range(last_index):
                self._add_variable_to_solution(i)

    def highest_index(self) -> int:
        """Najwyższa pozycja bitowa; `-1` dla tablicy bez zmiennych, żeby porównania miały sens.

        `variables` jest utrzymywane rosnąco, więc wystarczy ostatni element — bez kopiowania
        listy, bo kolejność łączenia odpytuje o to przy każdym porównaniu.
        """
        return self.variables[-1] if self.variables else -1

    def is_true(self) -> bool:
        """Czy zdanie jest tautologią.

        Porównanie z gotowym wzorcem wymagałoby zaalokowania tablicy tej samej szerokości —
        a sprawdzenie wypada po każdym scaleniu pary, więc przy 28 zmiennych byłoby to
        kilkadziesiąt megabajtów na jedno pytanie. `min()` przechodzi dane bez alokacji.
        """
        if len(self.variables) >= _VARIABLES_PER_FULL_BYTE:
            return int(self.words.min()) == 0xFF
        return int(self.words[0]) == self._tail_mask()

    def is_false(self) -> bool:
        """Czy zdanie jest sprzecznością."""
        return not bool(self.words.any())

    def negate_in_place(self) -> None:
        """Neguje tablicę w miejscu."""
        self.words = self._negated_words()

    def _negated_words(self) -> np.ndarray:
        """Dopełnienie bitowe tablicy."""
        return self._negated(self.words)

    def _negated(self, words: np.ndarray) -> np.ndarray:
        """
        Dopełnienie bitowe utrzymujące niezmiennik: bity powyżej szerokości zostają zerem.

        Od trzech zmiennych w górę wszystkie bajty są pełne, więc samo `bitwise_not` już go
        utrzymuje i maska jest zbędna — a kosztowałaby dwa dodatkowe przebiegi po całej tablicy.

        :param words: Bajty do zanegowania.
        :type words: np.ndarray
        :return: Zanegowane bajty.
        :rtype: np.ndarray
        """
        negated: np.ndarray = np.bitwise_not(words)
        if len(self.variables) < _VARIABLES_PER_FULL_BYTE:
            negated &= self._tail_mask()
        return negated

    def apply_in_place(self, operation: Operator, other: "BitTable") -> None:
        """
        Wykonuje operację dwuargumentową, zapisując wynik w tej tablicy.

        Dopasowanie jest wyczerpujące wobec `Operator`, więc dopisanie tam nowego operatora
        zatrzyma sprawdzanie typów właśnie tutaj — a nie dopiero na wyjątku w czasie działania.
        `NOT` jest jednoargumentowy i ma `negate_in_place`, a `XOR` evaluator rozkłada na
        negację równoważności; oba są tu błędem wołającego.

        :param operation: Operacja do wykonania.
        :type operation: Operator
        :param other: Druga tablica; po wywołaniu jest ZUŻYTA, bo `align_with` ją rozszerza.
        :type other: BitTable
        :return: None
        :raises ValueError: Gdy operator nie jest dwuargumentowy w tej algebrze.
        """
        normalized_other = self.align_with(other)

        match operation:
            case Operator.AND:
                self.words = np.bitwise_and(self.words, normalized_other.words)
            case Operator.OR:
                self.words = np.bitwise_or(self.words, normalized_other.words)
            case Operator.IMP:
                self.words = np.bitwise_or(self._negated_words(), normalized_other.words)
            case Operator.EQ:
                self.words = self._negated(np.bitwise_xor(self.words, normalized_other.words))
            case Operator.NOT | Operator.XOR:
                raise ValueError(f"{operation} nie jest tu operacją dwuargumentową")
            case _:
                assert_never(operation)

    def _add_variable_to_solution(
        self, variable_index: int, is_negated: bool = False, initialize_solution: bool = True
    ) -> None:
        """
        Dokłada zmienną, podwajając szerokość tablicy.

        :param variable_index: Pozycja bitowa zmiennej.
        :type variable_index: int
        :param is_negated: Czy pierwsza zmienna tablicy występuje zanegowana.
        :type is_negated: bool
        :param initialize_solution: Czy pierwsza zmienna ma nadać tablicy wartość literału;
            przy dorównywaniu zmiennych tablica zachowuje dotychczasową treść.
        :type initialize_solution: bool
        :return: None
        """
        # Jedna bisekcja daje i odpowiedź "czy już jest", i miejsce wstawienia — a `variables`
        # jest posortowane, więc liniowe przeszukanie byłoby tu podwójną pracą.
        index = bisect_right(self.variables, variable_index)
        if index and self.variables[index - 1] == variable_index:
            return

        self.variables.insert(index, variable_index)
        if len(self.variables) == 1 and initialize_solution:
            self.words = np.array([0b01 if is_negated else 0b10], dtype=np.uint8)
        else:
            self.words = self._expand_bit_groups(self.words, index)

    def _expand_bit_groups(self, words: np.ndarray, bit_group_size: int) -> np.ndarray:
        """
        Powiela każdą grupę bitów, bo dołożenie zmiennej podwaja tablicę.

        Grupa obejmująca całe bajty sprowadza się do powtórzenia wierszy, węższa — do
        podstawienia z `_duplication_table`. Wynik przycinamy do szerokości wynikającej
        z liczby zmiennych: przy tablicach węższych od bajtu podstawienie zwraca dwa bajty,
        z których drugi jest zerem, bo bity nadmiarowe wejścia też są zerowe.

        :param words: Bajty tablicy przed dołożeniem zmiennej.
        :type words: np.ndarray
        :param bit_group_size: Logarytm rozmiaru grupy; grupa ma 2^bit_group_size bitów.
        :type bit_group_size: int
        :return: Bajty tablicy po dołożeniu zmiennej.
        :rtype: np.ndarray
        """
        group_size = 1 << bit_group_size
        if group_size >= 8:
            bytes_per_group = group_size // 8
            if bytes_per_group == 1:
                # Powtórzenie elementów nie wymaga zmiany kształtu, a przy najwęższych
                # tablicach narzut `reshape` i `ravel` jest widoczny obok samej pracy.
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
        """Ile bajtów zajmuje tablica przy obecnej liczbie zmiennych; co najmniej jeden."""
        return max(1, (1 << len(self.variables)) // 8)

    def _tail_mask(self) -> int:
        """Maska jedynego, częściowego bajtu tablicy węższej niż bajt."""
        return (1 << (1 << len(self.variables))) - 1

    def align_with(self, other: "BitTable") -> "BitTable":
        """
        Dorównuje obie tablice do wspólnego zbioru zmiennych.

        Operacje bitowe wymagają tej samej szerokości i tego samego przyporządkowania bitów
        do wartościowań, więc brakujące zmienne trzeba dołożyć po obu stronach.

        :param other: Druga tablica; zostaje rozszerzona, czyli ZUŻYTA.
        :type other: BitTable
        :return: Ta sama druga tablica, już dorównana.
        :rtype: BitTable
        """
        # Zbiory przed pętlą: sprawdzenie wewnątrz wyrażenia listowego przebudowywałoby
        # kolekcję przy każdym indeksie, co daje koszt kwadratowy zamiast liniowego.
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
        """Liczba zmiennych, które ta tablica opisuje."""
        return len(self.variables)
