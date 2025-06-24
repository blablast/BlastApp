from collections.abc import Callable
from time import perf_counter
from abc import abstractmethod
import re
import pandas as pd

from Modules.Tree.LogicTree import LogicTree
from Modules.Tree.Nodes.BaseNode import BaseNode
from Modules.Tree.Nodes.ImportAllNodes import *
from Common.ColorCodes import *

class BaseSolver:
    """
    Base class for solving logic trees with different solvers.
    """
    def __init__(self):
        """
        Initialize the base solver with common properties.
        """
        self.variables_map = None
        self.solution = None  # Placeholder for solution object
        self.execution_time = 0
        self.repeat_count = 1
        self.print_equations = False
        self.variables = []

    def solve(self, logic_tree: LogicTree) -> 'BaseSolver':
        """
        Solve the logic tree and compute the solution proposition.

        :param logic_tree: The logic tree to be solved.
        :type logic_tree: LogicTree
        """
        self.variables_map = logic_tree.get_variable_mapping()
        # get the time of execution
        start_time = perf_counter()
        final_proposition = None
        for _ in range(self.repeat_count):
            final_proposition = self._compute_recursive_solution(logic_tree.root)
        self.execution_time = perf_counter() - start_time
        if final_proposition is not None:
            self.solution = self._finalize_solution(final_proposition)
        return self

    def _compute_recursive_solution(self, node: BaseNode, depth: int = 0) -> 'BaseNode':
        """
        Recursively solve a node and its children.

        :param node: The current node in the logic tree.
        :type node: BaseNode
        :param depth: The current depth in the logic tree, defaults to 0.
        :type depth: int
        :return: The proposition computed for the node.
        """
        # Recursively solve child nodes
        for child_node in node.children:
            if child_node.proposition is None:
                child_node.proposition = self._compute_recursive_solution(child_node, depth + 1)
            elif isinstance(child_node, (NodeVar, NodeTrue, NodeFalse)):
                child_node.proposition = self._process_constant_or_variable_node(child_node)

        # Compute the proposition for the current node
        node.proposition = self._process_node(node)
        return node.proposition

    @abstractmethod
    def _finalize_solution(self, proposition):
        """
        Finalize the solution at depth 0. Subclasses must implement this.
        :param proposition: The proposition.
        """
        pass

    def _process_node(self, node: BaseNode):
        """
        Perform the operation associated with the given node type.

        :param node: The current node to process.
        :type node: BaseNode
        :return: The resulting proposition.
        :rtype: T
        """
        if isinstance(node, NodeTrue):
            pass
        propositions = [child.proposition for child in node.children]
        if isinstance(node, NodeAnd):
            return self.compute_and_operation(propositions)
        elif isinstance(node, NodeOr):
            return self.compute_or_operation(propositions)
        elif isinstance(node, NodeImp):
            return self.compute_implication_operation(propositions)
        elif isinstance(node, NodeEq):
            return self.compute_equivalence_operation(propositions)
        elif isinstance(node, NodeXor):
            return self.compute_negation(self.compute_equivalence_operation(propositions))
        elif isinstance(node, NodeNot):
            return self.compute_negation(propositions[0])
        elif isinstance(node, (NodeVar, NodeTrue, NodeFalse)):
            return self._process_constant_or_variable_node(node)
        else:
            raise ValueError(f"Unsupported node type: {type(node)}")

    @abstractmethod
    def _process_constant_or_variable_node(self, node: BaseNode):
        """
        Process constant nodes like True, False, or variable nodes.

        :param node: The node to process.
        :type node: BaseNode
        :return: The resulting proposition.
        :rtype: T
        """
        pass

    @abstractmethod
    def compute_implication_operation(self, propositions: list):
        """
        Compute the implication operation for the given propositions.

        :param propositions: A list of BitProposition objects.
        :type propositions: List[T]
        :return: The resulting proposition.
        :rtype: T
        """
        pass

    @abstractmethod
    def compute_negation(self, proposition):
        """
        Compute the negation of a proposition.

        :param proposition: The proposition to negate.
        :type proposition: T
        :return: The negated proposition.
        :rtype: T
        """
        pass

    def compute_and_operation(self, propositions: list):
        """
        Compute the AND operation for the given propositions.

        :param propositions: A list of objects.
        :type propositions: List[T]
        :return: The resulting proposition after the AND operation.
        :rtype: T
        """
        return self._combine_propositions("AND", propositions)

    def compute_or_operation(self, propositions: list):
        """
        Compute the OR operation for the given propositions.

        :param propositions: A list of objects.
        :type propositions: List[T]
        :return: The resulting proposition after the OR operation.
        :rtype: T
        """
        return self._combine_propositions("OR", propositions)

    def compute_equivalence_operation(self, propositions: list):
        """
        Compute the equivalence operation for the given propositions.

        :param propositions: A list of objects
        :type propositions: List[T]
        :return: The resulting proposition after the equivalence operation.
        :rtype: T
        """
        return self._combine_propositions("EQ", propositions)

    @abstractmethod
    def _combine_propositions(self, operation: str, propositions: list):
        """
        Combine propositions using the specified operation.

        :param operation: The logical operation to apply (AND, OR, etc.).
        :type operation: str
        :param propositions: A list of propositions.
        :type propositions: List[T]
        :return: The combined proposition.
        :rtype: T
        """
        pass

    @staticmethod
    def _print_statistics( total_results: int, total_true_results: int, title:str = 'OTA Statistics'):
        """
        Print statistics about the solution, including the count of true and false results.

        :param total_results: The total number of results.
        :type total_results: int
        :param total_true_results: The total number of true results.
        :type total_true_results: int
        """
        print('- ' * 7 + title + ' -' * 7)
        print(
            f'{BG_LIGHT_YELLOW}{BLACK} Found {total_results}: {total_true_results} true results and {total_results - total_true_results} false results. {RESET}')

    def print_ota_statistics(self) -> 'BaseSolver':
        """
        Print statistics about the solution, including the count of true and false results.
        """
        statistics = self.get_ota_statistics()
        if statistics:
            self._print_statistics(statistics.get('Total', 0), statistics.get('True', 0))
        return self

    def print_time(self) -> 'BaseSolver':
        """
        Print the time taken to solve the logic tree.
        """
        print(f'{LIGHT_BLUE}Solved in {self.execution_time:.6f} seconds.{RESET}')
        return self

    def print_ota_solution(self) -> 'BaseSolver':
        """
        Print the time taken to solve the logic tree.
        """
        print(self.solution)
        return self

    def is_ota_tautology(self) -> bool:
        """
        Check if the solution is a tautology.
        :return: True if the solution is a tautology, False otherwise.
        :rtype: bool
        """
        return (self.solution is not None) and ((self.solution.tn[0] == 1) and (len(self.solution.tn) == 1))

    def is_ota_contradiction(self) -> bool:
        """
        Check if the solution is a contradiction.
        :return: True if the solution is a contradiction, False otherwise.
        :rtype: bool
        """
        return (self.solution is not None) and ((self.solution.tn[0] == 0) and (len(self.solution.tn) == 1))

    @staticmethod
    def _print_tautology_or_contradiction_if_exists(is_tautology:bool, is_contradiction:bool) -> None:
        """
        Print a message if the solution is a tautology or contradiction.
        :return: None
        """
        if is_tautology:
            print(f'{BG_LIGHT_GREEN}{BLACK} T  A  U  T  O  L  O  G  Y {RESET}')
        elif is_contradiction:
            print(f'{BG_RED}{WHITE} C O N T R A D I C T I O N {RESET}')

    def get_ota_statistics(self) -> dict:
        """
        Get statistics about the solution, including the count of true and false results.

        :return: Dictionary with keys: 'Total', 'True', 'False', 'Tautology', 'Contradiction'.
        :rtype: dict
        """
        if self.solution is None:
            return {}

        total = len(self.solution.tn)
        true = self.solution.bn.sum()
        return {
            'Total': total,
            'True': true,
            'False': total - true,
            'Tautology': self.is_ota_tautology(),
            'Contradiction': self.is_ota_contradiction()
        }

    def get_logical_variables(self, number: int, count_variables:int = None, add_color:bool = False) -> str:
        """
        Returns the logical expression for a given number in binary form using the variable indices.

        :param number: The number representing the binary configuration of variables.
        :type number: int
        :param count_variables: The number of variables to consider, defaults to None.
        :type count_variables: int, optional
        :param add_color: Whether to add color codes to the output, defaults to False.
        :type add_color: bool, optional
        :return: A logical expression corresponding to the binary representation of the number.
        :rtype: str
        """
        if count_variables is None:
            count_variables = len(self.variables)
        return (f'{GRAY} & ' if add_color else ' & ').join(
            [((f'{RED}~' if add_color else '~') if not (number & (1 << (count_variables - n - 1))) else (f'{GREEN} ' if add_color else ' ')) + f'a{count_variables - n - 1}'
             for n in range(count_variables)]
        ) + (RESET if add_color else '')

    def _get_i_result(self, i:int) -> bool:
        """
        Get the result for a given index i.

        :param i: The index to get the result for.
        :type i: int
        :return: The result for the given index.
        :rtype: bool
        """
        return bool(self.solution.bn[i])

    def _get_row(self, binary_representation) -> dict:
        return {f"{var}": value for var, value in zip(reversed(self.variables), binary_representation)}

    def get_true_results(self, get_i_result_function: Callable[[int], bool] = None) -> pd.DataFrame:
        """
        Generate a DataFrame listing all possible combinations of variables
        and their corresponding boolean results.

        :param get_i_result_function: The function to get the result for a given index i.
        :type get_i_result_function: Callable[[int], bool], optional

        :return: DataFrame with columns: 'Index', 'Variables', 'Result'.
        :rtype: pd.DataFrame
        """

        if get_i_result_function is None:
            get_i_result_function = self._get_i_result

        if self.solution is None:
            return pd.DataFrame()

        data = []
        count_variables = len(self.variables)
        for i in range(1 << count_variables):
            binary_representation = [(i >> bit) & 1 == 1 for bit in range(count_variables - 1, -1, -1)]
            row = self._get_row(binary_representation)
            row['Result'] = get_i_result_function(i)
            data.append(row)

        # Create a DataFrame from the data
        df = pd.DataFrame(data)

        # Update column headers based on `self.variables_map`
        df.columns = [self.variables_map.get(header, header) for header in df.columns]

        # Sorting function
        def sort_key(col):
            if col == "Result": # Ensure 'Result' is placed last
                return float("inf"), float("inf")
            match = re.match(r"([a-zA-Z]+)(\d*)", col) # Split column into the alphabetical part and numerical part (if any)
            if match:
                alpha, num = match.groups()
                return -ord(alpha[0]), -int(num) if num else 0
            return 0, 0

        data = df[sorted([col for col in df.columns], key = sort_key)].to_dict(orient = 'records')

        return pd.DataFrame(data)