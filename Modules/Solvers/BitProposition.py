import numpy as np
import sys
import math

class BitProposition:
    def __init__(self, initial_solution: int = 0):
        """
        Initialize the BitProposition with an initial solution.

        :param initial_solution: The initial solution value.
        :type initial_solution: int
        """
        self.solution = initial_solution
        self.variables = []

        # number_of_bits_in_word = sys.maxsize.bit_count() + 1
        # max_number_of_variables = int(math.log2(number_of_bits_in_word))
        #
        # if 1 << max_number_of_variables != number_of_bits_in_word:
        #     raise ValueError("Number of bits in word is not a power of 2!")
        # else:
        #     self.max_number_of_variables = max_number_of_variables
        #     self.true_masks= [((1 << (1 << i)) - 1) for i in range(max_number_of_variables+1)]

    @classmethod
    def create_with_variable(cls, variable_index: int, is_negated: bool = False) -> 'BitProposition':
        """
        Create a new instance of the BitProposition with variable set.

        :param variable_index: The index of the variable.
        :type variable_index: int
        :param is_negated: The negation flag, defaults to False.
        :type is_negated: bool, optional
        :return: A new instance of the BitProposition.
        :rtype: BitProposition
        """
        instance = cls()
        instance._add_variable_to_solution(variable_index, is_negated, True)
        return instance

    def add_missed_variables(self) -> None:
        """
        Add any missed variables to the solution.

        :return: None
        """
        if len(self.variables) > 0:
            last_index = max(self.get_indices())
            for i in range(last_index):
                self._add_variable_to_solution(i)

    def get_np_solution(self) -> np.ndarray:
        """
        Convert a large integer into a NumPy array of bits using an alternative method.

        :return: A NumPy array of 0s and 1s representing the bits of the integer.
        :rtype: np.ndarray
        """
        if self.solution in [0, 1]:
            return np.array([self.solution])

        # Determine the number of bits required to represent the integer
        num_bits_required = self._number_of_bits_required()
        integer_value = self.solution

        # Convert integer to binary string and pad with zeros to match the required bit length
        if integer_value < 0:
            raise ValueError("Negative values are not supported.")
        binary_string = bin(integer_value)[2:]
        bit_array = np.array([int(bit) for bit in binary_string], dtype = np.uint8)

        # Reverse the bit order
        bit_array = bit_array[::-1]

        # Calculate the required padding length
        total_bits = (1 << len(self.variables))
        if len(bit_array) < total_bits:
            bit_array = np.pad(bit_array, (0, total_bits - len(bit_array)), 'constant')

        return bit_array.astype(np.int8)

    def get_indices(self) -> list[int]:
        """
        Get the indices of the variables in the proposition.

        :return: A list of variable indices.
        :rtype: list[int]
        """
        return [variable['index'] for variable in self.variables] if len(self.variables)>0 else [-1]

    def is_true(self) -> bool:
        """
        Check if the proposition is true.

        :return: True if the proposition is true, False otherwise.
        :rtype: bool
        """
        return (self.solution == 1 and len(self.variables) == 0) or self.solution == self._get_true_value()

    def is_false(self) -> bool:
        """
        Check if the proposition is false.

        :return: True if the proposition is false, False otherwise.
        :rtype: bool
        """
        return self.solution == 0

    def perform_negation(self):
        return self.perform_logic_operation('NOT')

    def _negate(self, solution: int = None) -> int:
        return (self.solution if solution is None else solution) ^ self._get_true_value()

    def perform_logic_operation(self, operation: str, other: 'BitProposition' = None) -> 'BitProposition':
        """
        Perform a logic operation on the proposition.

        :param operation: The logic operation.
        :type operation: str
        :param other: The other proposition.
        :type other: BitProposition
        :return: The updated BitProposition.
        :rtype: BitProposition
        """

        if operation == 'NOT':
            # self.solution = ~self.solution
            self.solution = self._negate()
        else:
            normalized_other = self._normalize_variables(other)

            if other is None:
                raise ValueError("Other proposition is required for this operation.")
            elif operation == 'AND':
                self.solution &= normalized_other.solution
            elif operation == 'OR':
                self.solution |= normalized_other.solution
            elif operation == 'NAND':
                self.solution = self._negate(self.solution & normalized_other.solution)
            elif operation == 'NOR':
                self.solution = self._negate(self.solution | normalized_other.solution)
            elif operation == 'XOR':
                self.solution ^= normalized_other.solution
            elif operation == 'IMP':
                self.solution = self._negate() | normalized_other.solution
            elif operation == 'EQ':
                self.solution = self._negate(self.solution ^ normalized_other.solution)
            else:
                raise ValueError(f"Unknown operation: {operation}")

        return self

    # Utility methods
    def _add_variable_to_solution(self, variable_index: int, is_negated: bool = False, initialize_solution: bool = True)\
            -> None or 'BitProposition':
        """
        Add a variable to the solution.

        :param variable_index: The index of the variable.
        :param is_negated:  The negation flag.
        :param initialize_solution:  The flag to initialize the solution.
        :return:  The updated BitProposition.
        """
        if any(variable['index'] == variable_index for variable in self.variables):
            return

        index = self._insert_variable(variable_index)
        if len(self.variables) == 1 and initialize_solution:
            if is_negated:
                self.solution = 0b1
            else:
                self.solution = 0b10
        else:
            self.solution = self._expand_bit_groups(value = self.solution,bit_group_size = index)

        not_expanded_solution = self.solution
        self._expand_variables()
        return self

    def _expand_bit_groups(self, value:int, bit_group_size:int) -> int:
        """
        Expand the number by duplicating the bit groups.

        This method takes a value and replicates its groups of bits to expand its representation.
        Used primarily for variable alignment in logical operations.

        :param value: The number to expand.
        :type value: int
        :param bit_group_size: The size of each bit group in the value.
        :type bit_group_size: int
        :return: The expanded number.
        :rtype: int

        Example:
            For value=5 (binary 101) and group_size=1:
            Expanded result = 110011 (binary).
        """
        group_size = 1 << bit_group_size
        group_mask = (1 << group_size) - 1
        expanded_value = 0
        bit_shift = 0
        num_bits = self._number_of_bits_required(value)

        for i in range(0, num_bits, group_size):
            group = value & group_mask
            expanded_value |= (group << bit_shift) | (group << (bit_shift + group_size))
            bit_shift += 2 * group_size
            value >>= group_size

        return expanded_value

    def _expand_variables(self) -> None:
        """
        Expand the variables to match the length ot the solution.

        :return: None
        """
        bits_required = max(self._number_of_bits_required(), 1 << len(self.variables))

        for index, variable in enumerate(self.variables):
            value = variable['value']
            if value is None:
                value = self._get_variable_value(index)

            variable_bits_required = self._number_of_bits_required(value)
            while variable_bits_required < bits_required:
                value |= (value << variable_bits_required)
                variable_bits_required <<= 1
            self.variables[index]['value'] = value

    def _get_true_value(self) -> int:
        """
        Get the true value for the current number of variables.

        :return: The true value for the current number of variables.
        :rtype: int
        """
        mask = (1 << (1 << len(self.variables))) - 1
        return mask

    @staticmethod
    def _get_variable_value(variable_index: int) -> int:
        """
        Get the value of a variable at the given index.

        :param variable_index: The index of the variable.
        :type variable_index: int
        :return: The value of the variable.
        :rtype: int
        """
        bit_shift = 1 << variable_index
        shifted = 1 << bit_shift
        return (shifted << bit_shift) - shifted

    def _insert_variable(self, variable_index: int) -> int:
        """
        Insert a variable into the proposition.

        :param variable_index: The index of the variable.
        :type variable_index: int
        :return:  The index of the inserted variable.
        :rtype: int
        """

        item = {'index': variable_index, 'value': None}
        insert_position = next((i for i, var in enumerate(self.variables) if var['index'] > variable_index),
                               len(self.variables))

        self.variables.insert(insert_position, item)
        if insert_position < len(self.variables) - 1:
            self.variables[-1]['value'] = None
        return insert_position

    def _normalize_variables(self, other: 'BitProposition') -> 'BitProposition':
        """
        Normalize the variables of the self and other proposition to match.

        :param other: The other proposition.
        :type other: BitProposition
        :return: The normalized other proposition.
        :rtype: BitProposition
        """
        # Add missing variables only if necessary
        other_missing = [var for var in self.variables if var['index'] not in other.get_indices()]
        self_missing = [var for var in other.variables if var['index'] not in self.get_indices()]

        for variable in other_missing:
            other._add_variable_to_solution(variable['index'], False, False)
        for variable in self_missing:
            self._add_variable_to_solution(variable['index'], False, False)

        return other

    def _number_of_bits_required(self, value: int = None) -> int:
        """
        Get the number of bits required to represent the value.

        :param value: The value to represent.
        :type value: int
        :return: The number of bits required.
        :rtype: int
        """
        if value is None:
            value = self.solution

        bit_length = value.bit_length()
        return max(2, 1 << (bit_length - 1).bit_length())
