"""Funkcja OTA: wektor współczynników `tn` nad 2^n wyrazami i równoległy wektor wartości `bn`.

Dwie rzeczy, które trzeba tu wiedzieć:

**`tn` i `bn` opisują tę samą funkcję i muszą pozostać zgodne.** Kto przypisuje jeden z nich
wprost, odpowiada za przeliczenie drugiego — dlatego negacja jest metodą `negated()`, a nie
ręcznym grzebaniem w `tn` po stronie wywołującego.

**Przeliczenia między `tn` i `bn` pamiętają wyniki pośrednie.** Rekurencja mocno się nakłada;
bez pamięci konwersja przy 14 zmiennych zajmuje ponad dwie sekundy i rośnie około trzykrotnie
na każdą kolejną zmienną.
"""

import numpy as np

from blastapp.domain.representations.ns_squares import NSSquares


class OtaFunction:
    """
    Represents an OTA function for binary algebra.

    This class supports various operations such as addition, multiplication,
    conversion to mathematical expressions, and formatting for word equations.

    Attributes:
        tn (np.ndarray): Array storing tn coefficients, initialized as None.
        bn (np.ndarray): Array storing bn coefficients, initialized as None.
        c (np.ndarray): Array storing intermediate delta values, initialized as None.
        squares_ns (NSSquares): Precomputed sparse masks for multiplication, initialized as None.
        variables_count (int): Number of variables in the function, initialized as 0.
    """

    def __init__(self) -> None:
        """
        Initializes an empty OtaFunction with tn, bn, and c arrays.
        """
        # Puste tablice zamiast None: obiekt nigdy nie jest w stanie na wpół zbudowanym,
        # więc każda metoda może na nich pracować bez sprawdzania, czy już istnieją.
        self.tn: np.ndarray = np.zeros(0, dtype=np.int64)
        self.bn: np.ndarray = np.zeros(0, dtype=np.int64)
        self.c: np.ndarray = np.zeros(0, dtype=np.int64)
        self.squares_ns: NSSquares | None = None
        self.variables_count = 0
        # Współczynniki podwajają się co poziom XOR, więc int8 wystarcza tylko do pięciu
        # zmiennych — numpy 2.x zgłasza wtedy przepełnienie zamiast zawijać wartość.
        self.tn_type = np.int64
        self.bn_type = np.int64
        self.c_type = np.int64

    ### Factory Methods ###
    @classmethod
    def from_bn(cls, bn: np.ndarray) -> "OtaFunction":
        """
        Creates an OtaFunction instance from a bn sequence.

        :param bn: Input bn sequence as a NumPy array.
        :type bn: np.ndarray
        :return: Initialized instance with bn and tn sequence.
        :rtype: OtaFunction
        """
        instance = cls()
        instance.bn = bn
        instance.recalculate_tn()
        return instance

    @classmethod
    def from_tn(cls, tn: np.ndarray) -> "OtaFunction":
        """
        Creates an OtaFunction instance from a tn sequence.

        :param tn: Input tn sequence as a NumPy array.
        :type tn: np.ndarray
        :return: Initialized instance with bn and tn sequence.
        :rtype: OtaFunction
        """
        instance = cls()
        instance.tn = tn
        instance.recalculate_bn()
        return instance

    ### Initialization ###
    def _initialize(self, input_sequence: np.ndarray, is_bn: bool = True) -> None:
        """
        Initializes the tn, bn, and c arrays based on the input sequence.

        :param input_sequence: Sequence to initialize.
        :type input_sequence: np.ndarray
        :param is_bn: Whether the sequence represents bn values.
        :type is_bn: bool
        :raises TypeError: If the input is not a NumPy array of integers.
        :return: None
        :rtype:
        """
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

    ### Padding Helper ###
    def _pad_arrays(self, other: "OtaFunction") -> tuple[np.ndarray, np.ndarray]:
        """
        Pads the tn arrays of two OtaFunction objects to the same length.

        :param other: The other OtaFunction to align.
        :type other: OtaFunction
        :return: Padded tn arrays for both instances.
        :rtype: tuple[np.ndarray, np.ndarray]
        """
        max_length = max(len(self.tn), len(other.tn))
        padded_self = np.pad(self.tn, (0, max_length - len(self.tn)))
        padded_other = np.pad(other.tn, (0, max_length - len(other.tn)))
        return padded_self, padded_other

    ### Conversion Methods ###
    def recalculate_bn(self) -> None:
        """
        Recalculates the bn values based on the current tn values.

        :return: None
        :rtype:
        """
        self._initialize(self.tn, is_bn=False)
        memo: dict[tuple[int, int], int] = {}
        for i in range(1, len(self.c)):
            self.c[i] = self._calculate_bn_recursive(i, 0, memo)
            self.bn[i] = self.c[i] + self.bn[i - 1]
        self._truncate_to_power_of_two()

    def recalculate_tn(self) -> None:
        """
        Recalculates the tn values based on the current bn values.

        :return: None
        :rtype:
        """
        self._initialize(self.bn, is_bn=True)
        self.c[1:] = self.bn[1:] - self.bn[:-1]
        # Sumy prefiksowe zdejmują wewnętrzną pętlę sumującą z przypadku bazowego rekurencji.
        prefix = np.concatenate(([0], np.cumsum(self.c)))
        memo: dict[tuple[int, int], int] = {}
        for i in range(1, len(self.tn)):
            self.tn[i] = self._calculate_tn_recursive(i, 0, memo, prefix)
        self._truncate_to_power_of_two()

    ### Recursive Calculations ###
    def _calculate_bn_recursive(
        self, index: int, offset: int, memo: dict[tuple[int, int], int]
    ) -> int:
        """
        Recursively calculates the bn value at a given index.

        This method uses the structure of binary representations to efficiently
        compute the bn value based on precomputed tn coefficients and their offsets.

        :param index: The index at which the bn value is calculated.
        :type index: int
        :param offset: The offset to apply to the index during calculations.
        :type offset: int
        :return: The calculated bn value.
        :rtype: int
        :raises IndexError: If the index or offset exceeds the array bounds.
        """
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
        """
        Recursively calculates the tn value at a given index.

        This method computes the tn value by summing the 'c' coefficients, adjusted
        by the index and offset, using a recursive approach to handle binary splitting.

        :param index: The index at which the tn value is calculated.
        :type index: int
        :param offset: The offset to apply to the index during calculations.
        :type offset: int
        :return: The calculated tn value.
        :rtype: int
        :raises IndexError: If the index or offset exceeds the array bounds.
        """
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
        """
        Finds the largest power of 2 less than or equal to the given value.

        This method computes the largest power of 2 using bit manipulation.
        For example, for input '10', the output is '8' (as 2^3 = 8).

        :param value: The input value for which the largest power of 2 is determined.
        :type value: int
        :return: The largest power of 2 less than or equal to the input value.
        :rtype: int
        :raises ValueError: If the input value is less than 1.
        """
        if value < 1:
            raise ValueError("Input value must be greater than or equal to 1.")
        return 1 << (value.bit_length() - 1)

    ### Arithmetic Operators ###
    def __add__(self, other: "OtaFunction") -> "OtaFunction":
        """
        Adds two OtaFunction objects.

        :param other: The other OtaFunction to add.
        :type other: OtaFunction
        :return: A new OtaFunction representing the sum.
        :rtype: OtaFunction
        """
        padded_self, padded_other = self._pad_arrays(other)
        result = OtaFunction().from_tn(padded_self + padded_other)
        result._truncate_to_power_of_two()
        return result

    def __sub__(self, other: "OtaFunction") -> "OtaFunction":
        """
        Subtracts two OtaFunction objects.

        :param other: The other OtaFunction to subtract.
        :type other: OtaFunction
        :return: A new OtaFunction representing the difference.
        :rtype: OtaFunction
        """
        padded_self, padded_other = self._pad_arrays(other)
        result = OtaFunction().from_tn(padded_self - padded_other)
        result._truncate_to_power_of_two()
        return result

    def __mul__(self, other: "OtaFunction") -> "OtaFunction":
        """
        Multiplies two OtaFunction objects.

        :param other: The other OtaFunction to multiply.
        :type other: OtaFunction
        :return: A new OtaFunction representing the product.
        :rtype: OtaFunction
        """
        padded_self, padded_other = self._pad_arrays(other)

        if self.squares_ns is None:
            self.squares_ns = NSSquares(np.log2(len(padded_self)).astype(int))
        multiplied = np.outer(padded_self, padded_other)
        result_tn = np.array(
            [multiplied[self.squares_ns[i].nonzero()].sum() for i in range(len(padded_self))],
            dtype=self.tn.dtype,
        )

        result = OtaFunction().from_tn(result_tn)
        result._truncate_to_power_of_two()
        return result

    def __pow__(self, power: int, modulo: None = None) -> "OtaFunction":
        """
        Raises the OtaFunction to a power.

        :param power: The power to raise the OtaFunction to.
        :type power: int
        :param modulo: The modulo value for the operation.
        :type modulo: int, optional
        :return: A new OtaFunction representing the result of the operation.
        :rtype: OtaFunction
        """

        if modulo is not None or not isinstance(power, int) or power < 0:
            raise ValueError("Unsupported operation.")

        if power == 0:
            return OtaFunction().from_tn(np.array([1], dtype=self.tn.dtype))
        if power == 1:
            # Kopia, nie `self`: inaczej wynik potęgowania byłby tym samym obiektem co argument.
            return OtaFunction().from_tn(self.tn.copy())

        result = self
        for _ in range(power - 1):
            result *= self
            if modulo is not None:
                result %= modulo

        return result

    def __len__(self) -> int:
        """
        Returns the length of the OtaFunction.

        :return: The length of the tn array.
        :rtype: int
        """
        return int(self.tn.size)

    def _truncate_to_power_of_two(self) -> None:
        """
        Truncates the tn array to the smallest possible length that is a power of two
        while retaining all non-zero elements.

        This operation reduces the size of the tn array if the trailing elements are zero,
        ensuring the new length is a power of two and contains all meaningful data.

        :return: None
        """
        if self.tn.size == 0:
            raise ValueError("The tn array is not initialized or is empty.")

        # Find the last non-zero index in tn
        last_non_zero_index = np.where(self.tn != 0)[0]
        if last_non_zero_index.size == 0:
            # If all elements are zero, truncate to a single zero
            self.tn = np.zeros(1, dtype=self.tn.dtype)
            return

        last_non_zero_index = last_non_zero_index[-1] + 1  # Include the last non-zero element

        # Find the nearest power of two greater than or equal to last_non_zero_index
        new_length = self._largest_power_of_two(int(last_non_zero_index))
        if new_length < last_non_zero_index:
            new_length *= 2  # Ensure it's at least as large as last_non_zero_index

        new_length = max(new_length, 1)  # Ensure the length is at least 1

        # Truncate tn to the new length
        self.tn = self.tn[:new_length]

        # Adjust bn and c arrays to match the new length if they exist
        if self.bn is not None:
            self.bn = self.bn[:new_length]
        if self.c is not None:
            self.c = self.c[:new_length]

        self.variables_count = int(np.log2(len(self.tn)))

    ### Expression Conversion ###

    ### Negation ###
    def negated(self) -> "OtaFunction":
        """
        Zwraca negację funkcji jako nowy obiekt.

        Negacja w miejscu byłaby pułapką: wymaga przypisania `tn` i przeliczenia `bn`, a pominięcie
        drugiego kroku po cichu rozjeżdża oba wektory. Argument zostaje nietknięty.

        :return: Nowa funkcja OTA równa negacji tej funkcji.
        :rtype: OtaFunction
        """
        negated_tn = -self.tn
        negated_tn[0] += 1
        return OtaFunction().from_tn(negated_tn)
