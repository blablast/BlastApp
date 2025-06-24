from heapq import nsmallest
import numpy as np
from Modules.BinaryAlgebra.Ota import OtaFunction
from Modules.Solvers.BaseSolver import BaseSolver
from Modules.Tree.Nodes.ImportAllNodes import *
from Modules.Tree.Nodes.BaseNode import BaseNode

class OtaSolver(BaseSolver):
    """
    OTA Solver class for solving logic trees with OTA functions
    """

    def __init__(self):
        """
        Initialize the OTA solver with common properties.
        """
        super().__init__()

    def _process_constant_or_variable_node(self, node: BaseNode) -> OtaFunction:
        """
        Process constant or variable nodes and create an OTA function proposition.

        :param node: The node to process.
        :return: The resulting OTA function proposition.
        """
        if isinstance(node, NodeVar):
            result = self._create_variable(node)
        else:
            result = OtaFunction().from_tn(np.array([node.proposition]))
        return result

    def _finalize_solution(self, proposition) -> OtaFunction:
        """
        Directly assign the proposition as the solution for OtaSolver.
        """
        self.variables = []
        for index in range(proposition.variables_count):
            self.variables.append(f"a{index}")
        return proposition

    @staticmethod
    def _create_variable(node: NodeVar) -> OtaFunction:
        """
        Create an OTA function proposition for a variable node.

        :param node: The variable node containing index and negation flag.
        :type node: NodeVar
        :return: The resulting OTA function proposition.
        :rtype: OtaFunction
        """
        tn = np.zeros(1 << (node.index + 1), dtype=int)
        tn[1 << node.index] = -1 if node.is_negated else 1
        tn[0] = 1 if node.is_negated else 0
        return OtaFunction().from_tn(tn)

    def compute_implication_operation(self, propositions: list[OtaFunction]) -> OtaFunction:
        """
        Compute the implication operation for the given propositions.

        :param propositions: A list of OTA function propositions.
        :type propositions: list[OtaFunction]
        :return: The resulting proposition after the implication operation.
        :rtype: OtaFunction
        """
        return self.compute_negation(propositions[0] * self.compute_negation(propositions[1]))

    def compute_negation(self, proposition: OtaFunction) -> OtaFunction:
        """
        Compute the negation of a proposition.

        :param proposition: The OTA function proposition to negate.
        :type proposition: OtaFunction
        :return: The negated proposition.
        :rtype: OtaFunction
        """
        proposition.tn = -proposition.tn
        proposition.tn[0] += 1
        proposition.recalculate_bn()
        return proposition

    def _combine_propositions(self, operation: str, propositions: list[OtaFunction]) -> OtaFunction:
        """
        Combine the given propositions using the specified operation.

        :param operation: The logical operation (AND, OR, EQ).
        :type operation: str
        :param propositions: A list of OTA function propositions.
        :type propositions: list[OtaFunction]
        :return: The combined proposition.
        :rtype: OtaFunction
        """
        if len(propositions) < 2:
            raise ValueError(f"{operation} operation requires at least two arguments")

        pending = propositions[:]
        while len(pending) > 1:
            shortest, remaining = self._get_two_shortest_propositions(pending)
            combined = self._apply_operation(operation, shortest[0], shortest[1])
            pending = remaining + [combined]

        return pending[0]

    @staticmethod
    def _get_two_shortest_propositions(propositions: list[OtaFunction]) -> tuple[list[OtaFunction], list[OtaFunction]]:
        """
        Select and remove the two shortest propositions from the list.

        :param propositions: A list of OTA function propositions.
        :type propositions: list[OtaFunction]
        :return: A tuple of the two shortest propositions and the remaining propositions.
        :rtype: tuple[list[OtaFunction], list[OtaFunction]]
        """
        if len(propositions) < 2:
            return [], propositions
        shortest = nsmallest(2, propositions, key=len)
        remaining = [prop for prop in propositions if prop not in shortest]
        return shortest, remaining

    def _apply_operation(self, operation: str, left: OtaFunction, right: OtaFunction) -> OtaFunction:
        """
        Apply the specified operation between two propositions.

        :param operation: The logical operation (AND, OR, EQ).
        :type operation: str
        :param left: The left proposition operand.
        :type left: OtaFunction
        :param right: The right proposition operand.
        :type right: OtaFunction
        :return: The resulting proposition.
        :rtype: OtaFunction
        """
        if operation == "AND":
            return left * right
        elif operation == "OR":
            return self.compute_negation(self.compute_negation(left) * self.compute_negation(right))
        elif operation == "EQ":
            return self.compute_negation((left - right) ** 2)
        raise ValueError(f"Unsupported operation: {operation}")