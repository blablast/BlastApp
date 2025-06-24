from typing import List, Tuple

import pandas as pd
from Common.ColorCodes import *
from .BaseSolver import BaseSolver
from .BitProposition import BitProposition
from ..BinaryAlgebra.Ota import OtaFunction

from ..Tree.Nodes.BaseNode import BaseNode
from ..Tree.Nodes.ImportAllNodes import *


class BlastSolver(BaseSolver):
    """
    BlastSolver class for solving logic trees with BitPropositions.
    """
    def __init__(self, create_ota: bool = False):
        """
        Initialize the BlastSolver with a BitProposition and OtaFunction.

        :param create_ota: Whether to create an OtaFunction from the solution, defaults to False.
        :type create_ota: bool, optional
        """
        super().__init__()
        self.bit_solution: BitProposition = BitProposition()
        self.solution: OtaFunction = OtaFunction()
        self.create_ota = create_ota

    def _finalize_solution(self, proposition) -> OtaFunction | None:
        """
        Convert the final BitProposition into an OtaFunction for BlastSolver.

        :return: The solution as an OtaFunction if create_ota is True, otherwise None.
        :rtype: OtaFunction | None
        """
        self.bit_solution = proposition
        if self.is_bit_tautology():
            self.bit_solution = BitProposition(initial_solution = 1)
        elif self.is_bit_contradiction():
            self.bit_solution = BitProposition(initial_solution = 0)

        self.bit_solution.add_missed_variables()
        self.variables = self.bit_solution.variables

        return OtaFunction().from_bn(self.bit_solution.get_np_solution()) if self.create_ota else None

    def _process_constant_or_variable_node(self, node: BaseNode) -> BitProposition:
        """
        Process constant nodes like True, False, or variable nodes.

        :param node: The node to process.
        :type node: BaseNode
        :return: The resulting BitProposition.
        :rtype: BitProposition
        """
        if isinstance(node, NodeVar):
            return BitProposition().create_with_variable(node.index, node.is_negated)
        elif isinstance(node, (NodeTrue, NodeFalse)):
            return BitProposition(initial_solution = node.default)
        else:
            raise ValueError(f"Invalid node type: {type(node)}")

    # Main logical operations
    def compute_implication_operation(self, propositions: List[BitProposition]) -> BitProposition:
        """
        Compute the implication operation for the given propositions.

        :param propositions: A list of BitProposition objects.
        :type propositions: List[BitProposition]
        :return: The resulting proposition.
        :rtype: BitProposition
        """
        if len(propositions) != 2:
            raise ValueError("IMPLIES operation requires exactly 2 arguments")
        return self._apply_operation('IMP', propositions[0], propositions[1])


    def compute_negation(self, proposition: BitProposition) -> BitProposition:
        """
        Compute the negation of a proposition.

        :param proposition: The proposition to negate.
        :type proposition: BitProposition
        :return: The negated proposition.
        :rtype: BitProposition
        """

        return proposition.perform_negation()

    def _combine_propositions(self, operation: str, propositions: List[BitProposition]) -> BitProposition:
        """
        Combine propositions using the specified operation.

        :param operation: The logical operation to apply (AND, OR, etc.).
        :type operation: str
        :param propositions: A list of BitProposition objects.
        :type propositions: List[BitProposition]
        :return: The combined proposition.
        :rtype: BitProposition
        """
        if len(propositions) < 2:
            raise ValueError(f"{operation} operation requires at least 2 arguments")

        pending = propositions[:]
        while len(pending) > 1:
            selected, remaining = self._get_two_shortest_propositions(pending)
            combined = self._apply_operation(operation, selected[0], selected[1])
            if self._is_operation_complete(operation, combined):
                return self._get_trivial_result(operation)
            pending = remaining + [combined]

        return pending[0]

    @staticmethod
    def _get_two_shortest_propositions(statements: List[BitProposition]) \
            -> Tuple[List[BitProposition], List[BitProposition]]:
        """
        Select the best pair of propositions to compute next based on the maximum variable index.

        :param statements: A list of BitProposition objects.
        :type statements: List[BitProposition]
        :return: A tuple of the two shortest propositions and the remaining propositions.
        :rtype: Tuple[List[BitProposition], List[BitProposition]]
        """
        if len(statements) < 2:
            return [], statements

        max_indices = [(node, max(node.get_indices())) for node in statements]
        max_indices.sort(key=lambda x: x[1])
        selected = [max_indices[0][0], max_indices[1][0]]
        remaining = [node for node, _ in max_indices[2:]]

        return selected, remaining

    @staticmethod
    def _apply_operation(operation: str, left: BitProposition, right: BitProposition) -> BitProposition:
        """
        Apply the specified operation to two propositions.

        :param operation: The logical operation (AND, OR, etc.).
        :type operation: str
        :param left: The first proposition.
        :type left: BitProposition
        :param right: The second proposition.
        :type right: BitProposition
        :return: The resulting proposition.
        :rtype: BitProposition
        """
        return left.perform_logic_operation(operation, right)

    @staticmethod
    def _is_operation_complete(operation: str, result: BitProposition) -> bool:
        """
        Check if the operation has reached a trivial state.

        :param operation: The logical operation.
        :type operation: str
        :param result: The resulting proposition.
        :type result: BitProposition
        :return: True if the operation is complete, False otherwise.
        :rtype: bool
        """
        return (operation == 'AND' and result.is_false()) or (operation == 'OR' and result.is_true())

    @staticmethod
    def _get_trivial_result(operation: str) -> BitProposition:
        """Get the trivial result for AND & OR operations."""
        if operation == 'AND':
            return BitProposition(initial_solution = 0)
        elif operation == 'OR':
            return BitProposition(initial_solution = 1)
        raise ValueError(f"No trivial result for operation: {operation}")

    def count_bit_true_results(self) -> int:
        """
        Count the number of true results in the solution.

        :return: The number of true results.
        :rtype: int
        """
        return self.bit_solution.solution.bit_count()

    def print_bit_statistics(self) -> 'BlastSolver' :
        """
        Print statistics about the solution, including the count of true and false results.
        """
        self._print_statistics(1 << len(self.bit_solution.variables), self.count_bit_true_results(), 'Bit Statistics')
        return self

    def is_bit_tautology(self) -> bool:
        """
        Check if the solution is a tautology.
        :return: True if the solution is a tautology, False otherwise.
        :rtype: bool
        """
        count_variables = len(self.bit_solution.variables)
        return ((self.bit_solution.solution == ((1 << (1 << count_variables)) - 1) and (count_variables > 0))
                or (count_variables == 0 and self.bit_solution.solution == 1))

    def is_bit_contradiction(self) -> bool:
        """
        Check if the solution is a contradiction.
        :return: True if the solution is a contradiction, False otherwise.
        :rtype: bool
        """
        return self.bit_solution.solution == 0

    def print_bit_true_results(self) -> 'BlastSolver' :
        """
        Print all true results in a human-readable format.
        """
        is_tautology = self.is_bit_tautology()
        is_contradiction = self.is_bit_contradiction()
        count_variables = len(self.bit_solution.variables)
        if is_tautology or is_contradiction:
            self._print_tautology_or_contradiction_if_exists(is_tautology, is_contradiction)
        else:
            row = 1
            for i in range(1 << len(self.bit_solution.variables)):
                if self.bit_solution.solution & (1 << i):
                    print(f'{row:>4}: ({i:>5}) {self.get_logical_variables(i, count_variables, True)}')
                    row += 1
        return self

    def get_bit_statistics(self) -> dict:
        """
        Get statistics about the solution, including the count of true and false results.

        :return: Dictionary with keys: 'Total', 'True', 'False', 'Tautology', 'Contradiction'.
        :rtype: dict
        """
        total = 1 << len(self.bit_solution.variables)
        true = self.count_bit_true_results()
        return {
            'Total': total,
            'True': true,
            'False': total - true,
            'Tautology': self.is_bit_tautology(),
            'Contradiction': self.is_bit_contradiction()
        }

    def get_bit_true_results_old(self) -> pd.DataFrame:
        """
        Generate a DataFrame listing all possible combinations of variables
        and their corresponding boolean results.

        :return: DataFrame with columns: 'Index', 'Variables', 'Result'.
        :rtype: pd.DataFrame
        """
        if self.bit_solution is None:
            return pd.DataFrame(columns = ['Index', 'Variables', 'Result'])

        count_variables = len(self.variables)
        data = [
            {
                'Index': i,
                'Variables': self.get_logical_variables(i, count_variables, False),
                'Result': 1 if self.bit_solution.solution & (1 << i) else 0
            }
            for i in range(1 << count_variables)
        ]
        return pd.DataFrame(data)

    def _get_i_result(self, i: int) -> bool:
        """Get the i-th result from the solution."""
        return bool(self.bit_solution.solution & (1 << i))

    def _get_row(self, binary_representation) -> dict:
        """Get a dictionary with the variable names and their values."""
        return {f"a{var['index']}": value for var, value in zip(reversed(self.variables), binary_representation)}