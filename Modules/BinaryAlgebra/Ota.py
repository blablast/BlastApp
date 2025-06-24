from typing import List, Tuple
import re
import numpy as np
import pandas as pd
from Modules.BinaryAlgebra.NS import NSSquares
from Common.ColorCodes import *

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
        self.tn = None
        self.bn = None
        self.squares_ns = None
        self.variables_count = 0
        self.tn_type = np.int8
        self.bn_type = np.int8
        self.c_type = np.int8

    ### Factory Methods ###
    @classmethod
    def from_bn(cls, bn: np.ndarray) -> 'OtaFunction':
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
    def from_tn(cls, tn: np.ndarray) -> 'OtaFunction':
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
        if input_sequence is None:
            raise ValueError("Input sequence must not be None.")

        if isinstance(input_sequence, list):
            input_sequence = np.array(input_sequence)

        if not isinstance(input_sequence, np.ndarray) or not np.issubdtype(input_sequence.dtype, np.integer):
            raise TypeError("Input sequence must be a NumPy array of integers.")
        if len(input_sequence.shape) > 1:
            input_sequence = input_sequence.flatten()

        self.c = np.zeros_like(input_sequence, dtype = self.c_type)
        self.tn = np.zeros_like(input_sequence, dtype = self.tn_type)
        self.bn = np.zeros_like(input_sequence, dtype = self.bn_type)

        if is_bn:
            self.bn = input_sequence.astype(self.bn.dtype)
            self.c[0] = self.tn[0] = self.bn[0]
        else:
            self.tn = input_sequence.astype(self.tn.dtype)
            self.c[0] = self.bn[0] = self.tn[0]

    ### Padding Helper ###
    def _pad_arrays(self, other: 'OtaFunction') -> tuple[np.ndarray, np.ndarray]:
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
        self._initialize(self.tn, is_bn = False)
        for i in range(1, len(self.c)):
            self.c[i] = self._calculate_bn_recursive(i, 0)
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
        for i in range(1, len(self.tn)):
            self.tn[i] = self._calculate_tn_recursive(i, 0)
        self._truncate_to_power_of_two()

    ### Recursive Calculations ###
    def _calculate_bn_recursive(self, index: int, offset: int) -> int:
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
        power_of_two = self._largest_power_of_two(index)
        if index == power_of_two:
            return self.tn[offset + index] - sum(self.tn[offset + i] for i in range(1, index))
        half_index = index % power_of_two
        return (self._calculate_bn_recursive(half_index, offset + power_of_two)
                + self._calculate_bn_recursive(half_index, offset))

    def _calculate_tn_recursive(self, index: int, offset: int) -> int:
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
        power_of_two = self._largest_power_of_two(index)
        if index == power_of_two:
            return sum(self.c[offset + i] for i in range(1, index + 1))
        half_index = index % power_of_two
        return (self._calculate_tn_recursive(half_index, offset + power_of_two)
                - self._calculate_tn_recursive(half_index, offset))

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
    def __add__(self, other: 'OtaFunction') -> 'OtaFunction':
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

    def __sub__(self, other: 'OtaFunction') -> 'OtaFunction':
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

    def __mul__(self, other: 'OtaFunction') -> 'OtaFunction':
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
        result_tn = np.array([
            multiplied[self.squares_ns[i].nonzero()].sum() for i in range(len(padded_self))
        ], dtype = self.tn.dtype)

        result = OtaFunction().from_tn(result_tn)
        result._truncate_to_power_of_two()
        return result

    def __pow__(self, power, modulo=None):
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
            return self

        result = self
        for _ in range(power - 1):
            result *= self
            if modulo is not None:
                result %= modulo

        return result

    def __len__(self):
        """
        Returns the length of the OtaFunction.

        :return: The length of the tn array.
        :rtype: int
        """
        return len(self.tn) if self.tn is not None else 0

    def _truncate_to_power_of_two(self) -> None:
        """
        Truncates the tn array to the smallest possible length that is a power of two
        while retaining all non-zero elements.

        This operation reduces the size of the tn array if the trailing elements are zero,
        ensuring the new length is a power of two and contains all meaningful data.

        :return: None
        """
        if self.tn is None or len(self.tn) == 0:
            raise ValueError("The tn array is not initialized or is empty.")

        # Find the last non-zero index in tn
        last_non_zero_index = np.where(self.tn != 0)[0]
        if len(last_non_zero_index) == 0:
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
    def get_expression(self, reverse: bool=True, multiply_sign: str="·") -> str:
        """
        Converts the OtaFunction to a mathematical expression.

        :param reverse: Whether to reverse the term order in the expression.
        :type reverse: bool
        :param multiply_sign: Symbol used for multiplication in the output.
        :type multiply_sign: str
        :return: The formatted mathematical expression as a string.
        :rtype: str
        """
        terms = [
            f"{coefficient}{multiply_sign}{self.get_term(i)}".rstrip(multiply_sign)
            for i, coefficient in enumerate(self.tn)
            if coefficient != 0
        ]

        if reverse:
            terms.reverse()
        return (' ' + " + ".join(terms)).replace("+ -", "- ").replace(f'*',multiply_sign).replace(f' 1{multiply_sign}',' ').strip()

    def get_equation(self, expression: str = None, reverse:bool = True) -> str:
        """
        Formats the expression for use in MS Word equations.

        :param expression: The expression to format. If None, the expression is generated.
        :type expression: str, optional
        :param reverse: Whether to reverse the term order in the expression.
        :type reverse: bool
        :return: The formatted word equation as a string.
        :rtype: str
        """
        if expression is None:
            expression = self.get_expression(reverse)

        return f"x̃̇_(T=2^{self.variables_count}) = " + expression.replace("a", "a_")

    def get_solution_table(self, add_underscore: bool = False) -> pd.DataFrame:
        """
        Generates a DataFrame for get_solution_table.

        :return: DataFrame with variables, bn, tn, terms.
        :rtype: pd.DataFrame
        """
        rows = {
            i: {
                "n": i,
                "terms": self.get_term(i, '·').replace("a", "a_") if add_underscore else self.get_term(i, '·'),
                "bn": bn_val,
                "tn": tn_val
            }
            for i, (bn_val, tn_val) in enumerate(zip(self.bn, self.tn))
        }

        return pd.DataFrame.from_dict(rows, orient='index')

    def get_term(self, number: int, multiple_sign = '*') -> str:
        """
        Returns the term for a given index.

        :param multiple_sign: The symbol used for multiplication in the output.
        :type multiple_sign: str
        :param number: The index of the term to retrieve.
        :type number: int
        :return: The term at the specified index.
        :rtype: str
        """
        return multiple_sign.join([f'a{self.variables_count - n - 1}' for n in range(self.variables_count)
                         if f'{number:0{self.variables_count}b}'[n] == '1'] if number >0 else ['1'])



    def __str__(self, print_equation: bool = True) -> str:
        """
        Generates a formatted string representation of the OtaFunction,
        including the n, bn, and tn arrays.

        :param print_equation: Whether to include the formatted equation in the output.
        :type print_equation: bool
        :return: Formatted string showing the values of n, bn, and tn arrays.
        :rtype: str
        """
        if self.bn is None or self.tn is None or self.c is None:
            return 'No data to show.'

        def format_row(label: str, array: np.ndarray, cell_width: int = 0) -> str:
            """
            Formats a single row of the output, including labels and values.

            This function formats a row for display, with optional coloring for the
            'bn' and 'tn' rows based on specific criteria. The 'n:' row is displayed
            as default indices without additional coloring.

            :param label: The label for the row (e.g., "n:", "bn:", "tn:").
            :type label: str
            :param array: The array of values to display.
            :type array: np.ndarray
            :param cell_width: The width of each cell for alignment. Defaults to 0.
            :type cell_width: int
            :return: A formatted string representing the row, with labels and aligned values.
            :rtype: str
            :raises ValueError: If an unsupported label is provided.
            """
            color_map = {
                # bn values
                'bn_nonzero': (BG_LIGHT_BLUE, WHITE_TEXT),
                'bn_zero': (BG_LIGHT_GRAY, BLACK_TEXT),
                # tn values
                'tn_positive': (BG_GREEN, WHITE_TEXT),
                'tn_one': (BG_LIGHT_YELLOW, BLACK_TEXT),
                'tn_negative': (BG_RED, WHITE_TEXT),
                'tn_negative_large': (BG_MAGENTA, WHITE_TEXT),
                'tn_zero': (BG_DARK_GRAY, WHITE_TEXT),
                'tn_other': (BG_LIGHT_GRAY, BLACK_TEXT),
            }
            label_padding = 4  # Padding for the label column

            def color_bn_value(value: int) -> str:
                """
                Applies conditional coloring to 'bn' values.

                This function determines the color of each 'bn' value based on whether
                it is zero or non-zero.

                :param value: The value to format.
                :type value: int
                :return: Colored and formatted string for the 'bn' value.
                :rtype: str
                """
                bg_color, text_color = (
                    color_map['bn_nonzero'] if value != 0 else color_map['bn_zero']
                )
                return f'{bg_color}{text_color}{value:^{cell_width + 1}}{RESET}'

            def color_tn_value(value: int) -> str:
                """
                Applies conditional coloring to 'tn' values based on their magnitude.

                :param value: The value to format.
                :type value: int
                :return: Colored and formatted string for the 'tn' value.
                :rtype: str
                """
                if value == 1:
                    bg_color, text_color = color_map['tn_one']
                elif value > 1:
                    bg_color, text_color = color_map['tn_positive']
                elif value == -1:
                    bg_color, text_color = color_map['tn_negative']
                elif value < -1:
                    bg_color, text_color = color_map['tn_negative_large']
                elif value == 0:
                    bg_color, text_color = color_map['tn_zero']
                else:
                    bg_color, text_color = color_map['tn_other']

                return f'{bg_color}{text_color}{value:^{cell_width + 1}}{RESET}'

            if label == 'n:':
                # Format index row with default coloring
                formatted_values = ' '.join(f'{num:>{cell_width}}' for num in array[::-1])
                return f'{label:<{label_padding}} [{BLUE}{formatted_values}{RESET}]'

            if label == 'bn:':
                # Format bn row with conditional coloring
                formatted_values = ''.join(color_bn_value(num) for num in array[::-1])
                return f'{label:<{label_padding}} [{formatted_values}]'

            if label == 'tn:':
                # Format tn row with advanced value-based coloring
                formatted_values = ''.join(color_tn_value(value,) for value in array[::-1])
                return f'{label:<{label_padding}} [{formatted_values}]'


        # Prepare array indices for the range
        indices = np.arange(0, len(self))

        # Calculate cell width based on the largest absolute value
        min_value = min(indices.min(), self.bn.min(), self.tn.min(), self.c.min())
        max_value = max(indices.max(), self.bn.max(), self.tn.max(), self.c.max())
        cell_width = max(len(str(min_value)), len(str(max_value)))

        # Format header and rows
        output = (
                f'\n{BG_MAGENTA}{WHITE_TEXT} ' + '- ' * len(self) + 'OTA' + ' -' * len(self) + f' {RESET}\n'
                + format_row('n:', indices, cell_width) + '\n'
                + format_row('bn:', self.bn, cell_width) + '\n'
                + format_row('tn:', self.tn, cell_width) + '\nOTA = '
                + self.get_expression(reverse = False) + '\n'
        )
        if print_equation:
            output += self.get_equation(reverse = False) + '\n'
        return output

    def get_html_table(self, max_width: int = 40) -> str:
        """
        Renders a table for Streamlit with properly enforced column widths.

        :param max_width: Maximum width in pixels for table columns.
        :return: HTML string for the table.
        """

        dark_grey = '#555555'
        light_blue = '#00AAEE'
        def format_value(value, row_type):
            """
            Formats a value with appropriate coloring based on the row type (`bn` or `tn`).

            :param value: The value to format.
            :param row_type: The row type ('bn' or 'tn').
            :return: HTML string for the table cell with styling.
            """
            styles = {
                "bn": {
                    "non_zero": f'background-color:{light_blue}; color:#FFFFFF;',  # Light Blue
                    "zero": f'background-color:{dark_grey}; color:#FFFFFF;'  # Light Gray
                },
                "tn": {
                    "1": 'background-color:#FFCC00; color:#000000;',  # Light Yellow
                    "positive": 'background-color:#03AA00; color:#FFFFFF;',  # Green
                    "-1": 'background-color:#FF0000; color:#FFFFFF;',  # Red
                    "negative": 'background-color:#FF00FF; color:#FFFFFF;',  # Magenta
                    "zero": f'background-color:{dark_grey}; color:#FFFFFF;',  # Dark Gray
                    "default": 'background-color:#CCCCCC; color:#000000;'  # Light Gray
                }
            }

            if row_type == "bn":
                style = styles["bn"]["non_zero"] if value != 0 else styles["bn"]["zero"]
            elif row_type == "tn":
                if value == 1:
                    style = styles["tn"]["1"]
                elif value > 1:
                    style = styles["tn"]["positive"]
                elif value == -1:
                    style = styles["tn"]["-1"]
                elif value < -1:
                    style = styles["tn"]["negative"]
                elif value == 0:
                    style = styles["tn"]["zero"]
                else:
                    style = styles["tn"]["default"]
            else:
                raise ValueError("Invalid row type. Use 'bn' or 'tn'.")

            return f'<td style="{style} max-width:{max_width}px; width:{max_width}px; overflow:hidden; text-overflow:ellipsis; white-space:nowrap;">{value}</td>'

        # Header row
        html = (
            '<table style="border-collapse: collapse; width: auto; text-align: center; table-layout: fixed;">'
        )
        html += f'<thead style="background-color: {dark_grey}; color: {light_blue};">'
        html += (
                f'<tr><th style="max-width:{max_width}px; width:{max_width}px; overflow:hidden;">n:</th>'
                + "".join(
            f'<th style="max-width:{max_width}px; width:{max_width}px; overflow:hidden;">{i}</th>'
            for i in range(len(self) - 1, -1, -1)
        )
                + "</tr>"
        )
        html += "</thead><tbody>"

        # `bn` row
        html += f'<tr><td style="max-width:{max_width}px; width:{max_width}px; overflow:hidden;">bn:</td>' + ''.join(format_value(value, "bn") for value in self.bn[::-1]) + '</tr>'

        # `tn` row
        html += f'<tr><td style="max-width:{max_width}px; width:{max_width}px; overflow:hidden;">tn:</td>' + ''.join(format_value(value, "tn") for value in self.tn[::-1]) + '</tr>'

        # End table
        html += "</tbody></table>"

        return html
