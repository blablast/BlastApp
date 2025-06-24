from Common.ColorCodes import *
import numpy as np


class BitPropositionDebug:
    def __init__(self, initial_solution: int = 0, debug_mode: bool = False):
        """
        Initialize the BitProposition with an initial solution and debug mode flag.

        :param initial_solution: The initial solution value.
        :type initial_solution: int
        :param debug_mode: The debug mode flag.
        :type debug_mode: bool
        """
        self.variables = []
        self._solution:int = initial_solution
        self.debug_mode: bool = debug_mode
        self._debug_indent:int = 0

    @classmethod
    def create_with_debug(cls, debug_mode:bool) -> 'BitProposition':
        """
        Create a new instance of the BitProposition with debug mode set.

        :param debug_mode: The debug mode flag.
        :type debug_mode: bool
        :return: A new instance of the BitProposition.
        :rtype: BitProposition
        """
        return cls(debug_mode=debug_mode)

    @property
    def solution(self) -> int:
        """
        Get the solution value for the proposition.

        :return: The solution value.
        :rtype: int
        """
        return self._solution

    @solution.setter
    def solution(self, value: int) -> None:
        """
        Set the solution value for the proposition.

        :param value: The new solution value.
        :type value: int
        """
        self._debug_set_solution(value)
        self._solution = value & self._get_true_value()

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
        Convert a large integer into a NumPy array of bits.

        :return: A NumPy array of 0s and 1s representing the bits of the integer.
        :rtype: np.ndarray
        """
        if self.solution in [0, 1]:
            return np.array([self.solution])

        # Determine the number of bits required to represent the integer
        num_bits_required = self._number_of_bits_required()
        integer_value = self.solution

        # Extract the bits of the integer
        bit_positions = np.arange(num_bits_required - 1, -1, -1)
        bit_array = (integer_value >> bit_positions) & 1

        # Reverse the bit order
        bit_array = bit_array[::-1]

        # Calculate the required padding length
        padding_length = (1 << len(self.variables)) - num_bits_required
        bit_array = np.pad(bit_array, (0, padding_length), 'constant')

        return bit_array.astype(np.int8)

    def get_indices(self) -> list[int]:
        """
        Get the indices of the variables in the proposition.

        :return: A list of variable indices.
        :rtype: list[int]
        """
        return [variable['index'] for variable in self.variables]

    def is_true(self) -> bool:
        """
        Check if the proposition is true.

        :return: True if the proposition is true, False otherwise.
        :rtype: bool
        """
        result = (self.solution == 1 and len(self.variables) == 0) or self.solution == self._get_true_value()
        self._debug_mode_is_('TRUE', result)
        return result

    def is_false(self) -> bool:
        """
        Check if the proposition is false.

        :return: True if the proposition is false, False otherwise.
        :rtype: bool
        """
        result = self.solution == 0
        self._debug_mode_is_('FALSE', result)
        return result

    def perform_negation(self):
        return self.perform_logic_operation('NOT')

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
        self._debug_perform_logic_operation_header(operation, other)

        if operation == 'NOT':
            self.solution = ~self.solution
        else:
            normalized_other = self._normalize_variables(other)

            if other is None:
                raise ValueError("Other proposition is required for this operation.")
            elif operation == 'AND':
                self.solution &= normalized_other.solution
            elif operation == 'OR':
                self.solution |= normalized_other.solution
            elif operation == 'NAND':
                self.solution = ~(self.solution & normalized_other.solution)
            elif operation == 'NOR':
                self.solution = ~(self.solution | normalized_other.solution)
            elif operation == 'XOR':
                self.solution ^= normalized_other.solution
            elif operation == 'IMP':
                self.solution = ~self.solution | normalized_other.solution
            elif operation == 'EQ':
                self.solution = ~(self.solution ^ normalized_other.solution)
            else:
                raise ValueError(f"Unknown operation: {operation}")

        self._debug_perform_logic_operation_done(operation, other)
        return self

    def print_solution(self):
        debug = self.debug_mode
        self.debug_mode = True
        self._debug_print_solution()
        self.debug_mode = debug

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
        self._debug_adding_variable_header(variable_index, is_negated)

        new_index = self._insert_variable(variable_index)
        if len(self.variables) == 1 and initialize_solution:
            self.solution = 0b01 if is_negated else 0b10
            self._debug_add_first_variable_done(variable_index)
        else:
            self.solution = self._expand_bit_groups(value = self.solution,bit_group_size = new_index)

        self._expand_variables()
        self._debug_adding_variable_done(variable_index)

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
        initial_value = value
        self._debug_expanding_bit_groups_header(value, bit_group_size)

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

        self._debug_expanding_bit_groups_done(expanded_value, initial_value, bit_group_size)

        return expanded_value

    def _expand_variables(self) -> None:
        """
        Expand the variables to match the length ot the solution.

        :return: None
        """
        bits_required = max(self._number_of_bits_required(), 1 << len(self.variables))

        for index, variable in enumerate(self.variables):
            initial_value = variable['value']
            if initial_value is None:
                initial_value = self._get_variable_value(index)

            value = initial_value
            expanded = False
            variable_bits_required = self._number_of_bits_required(value)
            while variable_bits_required < bits_required:
                value |= (value << variable_bits_required)
                variable_bits_required <<= 1
                expanded = True
            self.variables[index]['value'] = value

            if expanded:
                self._debug_expanding_variable_done(variable, bits_required)

    def _get_true_value(self) -> int:
        """
        Get the true value for the current number of variables.

        :return: The true value for the current number of variables.
        :rtype: int
        """
        return (1 << (1 << len(self.variables))) - 1

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

        self._debug_normalize_variables_done(other)
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

    # ------------------------------------------------------------------------------------------------------------------
    # D E B U G   M E T H O D S
    def _format_binary(self, num:int, bit_width:int=None):
        if bit_width is None:
            bit_width = self._number_of_bits_required(num)
        if num < 0:
            num += (1 << bit_width)
        return f"0b{num:0{bit_width}b}"

# ------------------------------------------------------------------------------------------------------------------
# D E B U G   M E T H O D S

    def _debug_message(self, message: str, color: str, multi_line: bool = False):
        """
        Print a debug message with the specified color and optional multi-line support.

        :param message: The debug message to print.
        :type message: str
        :param color: The color code for the message.
        :type color: str
        :param multi_line: Whether the message spans multiple lines.
        :type multi_line: bool
        """
        if self.debug_mode:
            indent = ' ' * self._debug_indent
            if multi_line:
                print(f"DEBUG: {indent}{color}{message}{RESET}".replace('\n', f'\nDEBUG: {indent}{color}'))
            else:
                print(f"DEBUG: {indent}{color}{message}{RESET}")

    def _debug_update_indent(self, value: int):
        self._debug_indent += value

    def _debug_adding_variable_header(self, variable_index: int, is_negated: bool):
        if self.debug_mode:
            self._debug_message(f"Adding variable: {variable_index} {'(negated)' if is_negated else ''}", f'{BG_YELLOW}{BLACK}')
            self._debug_update_indent(2)

    def _debug_adding_variable_done(self, variable_index: int):
        if self.debug_mode:
            self._debug_print_solution()
            self._debug_print_variables()
            self._debug_update_indent(-2)
            self._debug_message(f"Variable {variable_index} added", f'{BG_YELLOW}{BLACK}')

    def _debug_add_first_variable_done(self, variable_index: int):
        self._debug_message(f"First variable {variable_index} added", f'{BG_GREEN}{WHITE}')
        self._debug_print_solution()

    def _debug_expanding_bit_groups_header(self, value: int, bit_group_size: int) -> None:
        self._debug_message(f"Expanding number {self._format_binary(value)} for bit group size: {1<<bit_group_size}", f'{BG_BLUE}{WHITE}')

    def _debug_expanding_bit_groups_done(self, expanded_value: int, initial_value: int, bit_group_size: int):
        """
        Debug message for when bit groups are expanded.

        :param expanded_value: The result of the bit group expansion.
        :type expanded_value: int
        :param initial_value: The original value before expansion.
        :type initial_value: int
        :param bit_group_size: The size of each bit group in the value.
        :type bit_group_size: int
        """
        self._debug_message(
            f"Expanded {self._format_binary(initial_value)} to {self._format_binary(expanded_value)} "
            f"using bit group size {1 << bit_group_size}",
            f'{BG_BLUE}{WHITE}'
        )

    def _debug_expanding_variable_done(self, variable, bits_required: int) -> None:
        self._debug_message(f"Variable {variable['index']} expanded to {bits_required} bits", f'{BG_BLUE}{WHITE}')

    def _debug_mode_is_(self, mode_type: str, result: bool):
        self._debug_message(f"Checking if the proposition is {mode_type}", f'{BG_YELLOW}{BLACK}')
        self._debug_print_solution()
        self._debug_print_variables()
        self._debug_message(f"Result: {result}", f'{BG_YELLOW}{BLACK}')

    def _debug_normalize_variables_done(self, other: 'BitProposition') -> None:
        self._debug_message("Variables normalized", f'{BG_YELLOW}{BLACK}')
        self._debug_print_variables()
        other._debug_print_variables()

        self._debug_message("Solutions normalized", f'{BG_YELLOW}{BLACK}')
        self._debug_print_solution("Self:")
        other._debug_print_solution("Other:")

    def _debug_perform_logic_operation_header(self, operation: str, other: 'BitProposition') -> None:
        if self.debug_mode:
            self._debug_message(f"Performing {operation} operation with other proposition", f'{BG_RED}{WHITE}')
            self._debug_update_indent(2)

    def _debug_perform_logic_operation_done(self, operation: str, other: 'BitProposition') -> None:
        if self.debug_mode:
            self._debug_update_indent(-2)
            self._debug_message(f"Operation {operation} done", f'{BG_RED}{WHITE}')
            self._debug_print_solution()

    def _debug_perform_variables_operation_header(self, variable_index: int, operand: str):
        self._debug_message(f"Performing {operand} operation on variable {variable_index}", f'{BG_YELLOW}{BLACK}')

    def _debug_set_solution(self, value:int):
        self._debug_message(f"Setting solution to {self._format_binary(value)}", f'{BG_RED}{BLACK}')

    def _debug_print_solution(self, title: str = None):
        """
        Print the current solution for debugging purposes.

        :param title: Optional title for the debug message.
        :type title: str
        """
        if self.debug_mode:
            try:
                header = f"{title}: " if title else ""
                self._debug_message(f"{header}Solution: {self._format_binary(self.solution)} ({self.solution})",
                                    f'{BG_LIGHT_MAGENTA}{BLACK}')
            except Exception as e:
                self._debug_message(f"Error while printing solution: {str(e)}", f'{BG_RED}{BLACK}')

    def _debug_print_variables(self):
        """
        Print the current variables for debugging purposes.
        """
        self._debug_message("Variables:", f'{LIGHT_MAGENTA}')
        for i, item in enumerate(self.variables):
            try:
                self._debug_message(
                    f"  - Index: {i:2}, Variable: {item['index']:2}, "
                    f"Value: {self._format_binary(item['value'])} ({item['value']:10})",
                    f'{LIGHT_MAGENTA}'
                )
            except Exception as e:
                self._debug_message(f"Error while printing variable at index {i}: {str(e)}", f'{BG_RED}{BLACK}')




