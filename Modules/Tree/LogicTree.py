from graphviz import Digraph
from Common.ColorCodes import generate_color_palette, get_contrast_color
from Modules.Tree.Nodes.ImportAllNodes import *
from Modules.Tree.Nodes.BaseNode import BaseNode
from typing import Optional, Type
from pysat.formula import CNF
import re

class LogicTree:
    """
    Constructs and manages logical trees based on user-provided logical expressions.

    The `LogicTree` class handles logical expressions, adhering to operator precedence:
        1. EQ (Equivalent)
        2. IMP (Implies), OR, XOR
        3. AND
        4. NOT

    Key Features:
        - Supports nested expressions and parentheses.
        - Maps variables for clarity and reusability.
        - Simplifies logical structures (e.g., reducing negations).
        - Visualizes trees using Graphviz with unique colors for variables.

    Attributes:
        operator_precedence (dict): Operator precedence rules.
        binary_operators (list): List of supported binary operators.
        unary_operators (list): List of supported unary operators.
        node_counter (int): Counter for assigning unique node IDs.
        expression (str): The parsed logical expression.
        expression_errors (list): List of errors encountered during parsing.
        root (BaseNode): Root node of the logical tree.
        variable_indices (dict): Maps variable names to unique indices.
        variable_aliases (dict): Maps variables to their user-friendly names.
        variable_color_map (dict): Maps variables to assigned colors for visualization.
        output_format (str): Format for visualized output (e.g., PNG, PDF).
        graph (Digraph): Graphviz object for visualization.
        recognize_variables (bool): Whether to automatically map variables.
        debug (bool): Debugging flag for additional logs.
    """
    VALID_EXPRESSION_REGEX = re.compile(
        r"^(\s*(NOT\s+)?[a-zA-Z]\d*\s*|\s*\(\s*(NOT\s+)?[a-zA-Z]\d*\s*\)\s*)"
        r"(\s*(AND|OR|XOR|IMP|EQ)\s+(\s*(NOT\s+)?[a-zA-Z]\d*\s*|\s*\(\s*(NOT\s+)?[a-zA-Z]\d*\s*\)\s*))*$"
    )

    ### INITIALIZATION BLOCK ###

    def __init__(self, expression=None, output_format='png', recognize_variables=True):
        """
        Initialize the LogicTree instance.

        This method initializes all necessary attributes for parsing and managing logical trees, such as operator
        precedence, variable mappings, and visualization settings. If a logical expression is provided, the method
        validates and attempts to parse the expression into a logical tree.

        :param expression: Logical expression to parse (optional).
        :type expression: str, optional
        :param output_format: Format for output graph visualization (default: 'png').
        :type output_format: str, optional
        :param recognize_variables: Whether to automatically map variables (default: True).
        :type recognize_variables: bool, optional

        :raises ValueError: If the provided expression contains invalid characters or unbalanced parentheses.

        """
        # Operator precedence and supported operations
        self.operator_precedence = {'EQ': 1, 'IMP': 2, 'OR': 2, 'XOR': 2, 'AND': 3, 'NOT': 4}
        self.binary_operators = ['EQ', 'IMP', 'OR', 'XOR', 'AND']
        self.unary_operators = ['NOT']

        # Tree-related properties
        self.node_counter = 1  # Counter to assign unique node IDs
        self.expression = ''
        self.expression_errors = []
        self.root = None

        # Variable mappings
        self.variable_indices = {}
        self.variable_aliases = {}
        self.variable_color_map = {}

        # Visualization properties
        self.output_format = output_format
        self.graph = None

        # Configuration flags
        self.recognize_variables = recognize_variables
        self.debug = False

        # Initialize tree if an expression is provided
        if expression:
            self._initialize_tree(expression)

    def load_cnf(self, cnf):
        """
        Constructs a logical tree from a CNF formula.

        :param cnf: A CNF formula in PySAT format.
        :type cnf: pysat.formula.CNF
        :return: A logical tree constructed from the CNF formula.
        :rtype: LogicTree
        """
        # Check if the input is a valid CNF formula
        if not isinstance(cnf, CNF):
            return

        # Convert the CNF formula to a logical expression
        expressions = []
        for clause in cnf.clauses :
            sub_expressions = []
            for variable in clause :
                sub_expressions.append(f'a{variable - 1}' if variable > 0 else f'~a{-variable - 1}')
            expressions.append(' | '.join(sub_expressions))
        expression = '(' + ') & ('.join(expressions) + ')'

        # Initialize a new LogicTree instance
        self._initialize_tree(expression)



    def get_variable_mapping(self):
        """
        Returns a mapping of original variable names to their aliases (e.g., a0, a1).
        """
        return {alias: original for original, alias in self.variable_aliases.items()}

    ### TREE INITIALIZATION AND PARSING ###

    def _check_expression(self, expression: str) -> None:
        """
        Validates the structure of the given logical expression.

        :param expression: Logical expression to validate.
        :type expression: str
        :return: None

        :raises ValueError: If the expression is None or empty.
        """
        if expression is None:
            raise ValueError("Expression cannot be None.")

        expression = expression.strip()

        if not expression:
            raise ValueError("Expression cannot be empty.")

        # Check for balanced parentheses
        if not self._are_parentheses_balanced(expression):
            self.expression_errors.append("Error: Parentheses are not balanced.")

        # Check for invalid characters or operators
        if not re.match(r"^[a-zA-Z\d\s_\(\)~&\|<>!\^=/\\∧∨⌐]+$", expression, flags = re.UNICODE):
            self.expression_errors.append("Error: Expression contains invalid characters.")

    def _initialize_tree(self, expression: str) -> None:
        """
        Parses and constructs the logical tree from the provided expression.

        :param expression: Logical expression to parse.
        :type expression: str
        :return: None

        :raises ValueError: If the expression is invalid or cannot be parsed.

        """
        # Validate the input expression
        self._check_expression(expression)
        if len(self.expression_errors) > 0:
            return

        # Format the input expression
        self.expression = self._format_expression(expression)

        # Recognize variables in the expression
        if self.recognize_variables:
            matches = re.findall(r'a(\d+)', self.expression)
            variable_numbers = [int(match) for match in matches]
            for variable_number in variable_numbers:
                variable_name = f'a{variable_number}'
                self.variable_indices[variable_name] = variable_number
                self.variable_aliases[variable_name] = variable_name

        # Build the tree structure
        self.root = self.build_logic_tree(self.expression)

        if len(self.expression_errors) > 0:
            self.root = None
            return

        # Simplify the tree structure
        self._reduce_negations(self.root)

        # Assign colors for visualization
        self.variable_color_map = self._assign_variable_colors()

    @staticmethod
    def _format_expression(expression: str) -> str:
        """
        Standardizes logical expressions by replacing symbols with keywords.

        :param expression: The raw logical expression to be formatted.
        :type expression: str
        :return: The standardized logical expression as a string.
        :rtype: str

        :raises ValueError: If the input expression is not a string or is empty.
        """
        if not isinstance(expression, str) or not expression.strip():
            raise ValueError("Input expression must be a non-empty string.")

        replacements = {
            r'~': ' NOT ',r'⌐': ' NOT ',
            r'\b∧\b': ' AND ', r'/\\': ' AND ', r'&': ' AND ', r'∧': ' AND ',
            r'\b∨\b': ' OR ', r'\\/': ' OR ', r'\|': ' OR ', r'∨': ' OR ',
            '<=>': ' EQ ',
            '==>': ' IMP ', '=>': ' IMP ',
            r'\bTRUE\b': ' True ',
            r'\bFALSE\b': ' False ',
            r'\[': ' (', r'\]': ') ',
            r'\n': ' ', r' {2,}': ' ',
            '  ': ' '
        }

        # Replace logical symbols and keywords
        for old, new in replacements.items():
            expression = re.sub(old, new, expression, flags = re.IGNORECASE)

        expression = re.sub(' {2}', ' ', expression, flags=re.IGNORECASE)


        # Replace variables of the form a_0, a_1, etc. with a0, a1
        expression = re.sub(r'a_(\d+)', r'a\1', expression)

        return expression

    def _reverse_format_expression(self) -> str:
        """
        Converts standardized logical expressions with keywords back to symbols.

        :return: The expression with symbols instead of keywords.
        :rtype: str

        :raises ValueError: If the input expression is not a string or is empty.
        """
        if not isinstance(self.expression, str) or not self.expression.strip():
            raise ValueError("Input expression must be a non-empty string.")

        replacements = {
            r' AND ': ' & ',
            r' OR ': ' | ',
            r'NOT ': '~',
            r' IMP ': ' => ',
            r' EQ ': ' <=> '
        }

        formatted_expression = self.expression
        for old, new in replacements.items():
            formatted_expression = re.sub(old, new, formatted_expression, flags = re.IGNORECASE)

        # Remove extra spaces if added during formatting
        formatted_expression = re.sub(r'\s+', ' ', formatted_expression).strip()
        return formatted_expression


    def _update_variable_mapping(self, variable: str) -> None:
        """
        Maps a variable to a unique identifier.

        :param variable: The variable name, potentially prefixed with `~` for negation.
        :type variable: str
        :return: None
        """
        base_variable = variable.lstrip('~')
        if base_variable not in self.variable_aliases:
            variable_id = len(self.variable_indices)
            variable_name = f'a{variable_id}'
            self.variable_aliases[base_variable] = variable_name
            self.variable_indices[variable_name] = variable_id

    ### TREE CONSTRUCTION ###

    def build_logic_tree(self, expression: str) -> Optional[BaseNode]:
        """
        Recursively builds the logic tree from the expression.

        :param expression: Logical expression to parse.
        :type expression: str
        :return: Root node of the constructed logic tree, or None if the expression is invalid.
        :rtype: Optional[BaseNode]
        """
        if len(self.expression_errors) > 0:
            return None

        expression = self._remove_outer_parentheses(expression)
        position, operator = self._find_main_operator(expression)

        # Base case: No operator found
        if operator is None:
            expression = expression.strip()
            if expression.lower() in ['true', 'false']:
                return NodeTrue(self.node_counter) if expression.lower() == 'true' else NodeFalse(self.node_counter)
            elif re.match(r"^[a-zA-Z]\d*$", expression):  # Match variable names like a0, b1
                self._update_variable_mapping(expression)
                return NodeVar(self.variable_indices[self.variable_aliases[expression]],
                               self.variable_aliases[expression])
            else:
                self.expression_errors.append(f"Error: Invalid variable or literal: '{expression}'")
                return None
        # Increment node counter
        self.node_counter += 1

        # Split the expression into left and right parts
        operator_length = len(operator)
        right_expression = expression[position + operator_length:].strip()

        # Handle unary operators
        if operator in self.unary_operators:
            if not right_expression:
                self.expression_errors.append(f"Error: Missing operand for unary operator '{operator}' in '{expression}'")
                return None

            return NodeNot(self.node_counter, self.build_logic_tree(right_expression))

        # Handle binary operators
        left_expression = expression[:position].strip()
        if not left_expression or not right_expression:
            self.expression_errors.append(f"Error: Missing operand for binary operator '{operator}' in '{expression}'")
            return None

        operator_to_node_map = {
            'AND': NodeAnd,
            'OR': NodeOr,
            'XOR': NodeXor,
            'IMP': NodeImp,
            'EQ': NodeEq,
        }

        if operator in ['AND', 'OR']:
            return self._merge_children(operator_to_node_map[operator], left_expression, right_expression)
        elif operator in operator_to_node_map:
            left_node = self.build_logic_tree(left_expression)
            right_node = self.build_logic_tree(right_expression)
            return operator_to_node_map[operator](self.node_counter, left_node, right_node)

        self.expression_errors.append(f"Error: Invalid operator: '{operator}' in '{expression}'")

    def _merge_children(self, node_class: Type[BaseNode], left_expression: str, right_expression: str) -> Optional[BaseNode]:
        """
        Merge child nodes for binary operators ('AND', 'OR').

        :param node_class: Class of the node to create (e.g., `NodeAnd`, `NodeOr`).
        :type node_class: type
        :param left_expression: Expression for the left-hand child.
        :type left_expression: str
        :param right_expression: Expression for the right-hand child.
        :type right_expression: str
        :return: Node representing the merged result, or None if the expression is invalid.
        :rtype: Optional[BaseNode]
        """
        left_node = self.build_logic_tree(left_expression)
        right_node = self.build_logic_tree(right_expression)

        if left_node is None or right_node is None:
            self.expression_errors.append(
                f"Error: Invalid children for node: '{left_expression} {node_class.__name__} {right_expression}'")
            return None

        if isinstance(left_node, node_class):
            node = left_node
        else:
            node = node_class(self.node_counter)
            node.add_child(left_node)

        if isinstance(right_node, node_class):
            node.children.extend(right_node.children)
        else:
            node.add_child(right_node)

        return node

    ### TREE SIMPLIFICATION ###

    def _reduce_negations(self, node: BaseNode) -> None:
        """
        Simplify the tree by propagating NOT nodes to variables.

        :param node: Current node in the tree.
        :type node: BaseNode
        """
        for i in range(len(node.children) - 1, -1, -1):  # Iterate over children in reverse order
            child = node.children[i]

            # Check if the child is a NOT node and its first child is a variable
            if isinstance(child, NodeNot) and len(child.children) == 1 and isinstance(child.children[0], NodeVar):
                original_variable = child.children[0]
                assert isinstance(original_variable, NodeVar)  # Optional: Explicit assertion for clarity

                # Create a new negated variable
                new_child = NodeVar(
                    index = original_variable.index,
                    name = original_variable.name,
                    is_negated = not original_variable.is_negated
                )
                # Replace the current child with the new negated variable
                node.children[i] = new_child
            else:
                # Recursively process other children
                self._reduce_negations(child)

    ### VISUALIZATION ###
    # Print the logical tree in a human-readable format
    def print_tree(self, node:Optional[BaseNode]=None, depth:int=0, is_last_child:bool=True, prefix:str=""):
        """
        Prints the logical tree in a hierarchical structure.

        Each node is indented and connected with branches to represent its position
        in the tree.

        :param node: The current node of the logical tree. Defaults to the root node.
        :type node: BaseNode, optional
        :param depth: The current depth in the tree for indentation.
        :type depth: int
        :param is_last_child: Whether the current node is the last child of its parent.
        :type is_last_child: bool
        :param prefix: The prefix string used for indentation and branching.
        :type prefix: str
        """

        def _get_node_text(node_to_process: BaseNode) -> str:
            """
            Get the display text for a node based on its type.

            :param node_to_process: A node of the tree.
            :type node_to_process: BaseNode
            :return: The display text for the node.
            :rtype: str
            """
            if isinstance(node_to_process, (NodeAnd, NodeOr, NodeNot, NodeImp, NodeEq, NodeXor)):
                return type(node_to_process).__name__.replace("Node", "")
            elif isinstance(node_to_process, NodeVar):
                remapped_name = self.get_variable_mapping().get(node_to_process.name, node_to_process.name)
                return f"{'~' if node_to_process.is_negated else ''}{remapped_name}"
            elif isinstance(node_to_process, NodeTrue):
                return "True"
            elif isinstance(node_to_process, NodeFalse):
                return "False"
            return f"Unknown({type(node_to_process).__name__})"

        if node is None:
            node = self.root

        if node is None:
            print("(Empty Tree)")
            return

        # Determine the branch type
        connector = "└── " if is_last_child else "├── "
        print(f"{prefix}{connector}{_get_node_text(node)}")

        # Prepare the prefix for children
        child_prefix = prefix + ("    " if is_last_child else "│   ")

        # Recursively print children
        for idx, child in enumerate(getattr(node, "children", [])):
            self.print_tree(
                node = child,
                depth = depth + 1,
                is_last_child = (idx == len(node.children) - 1),
                prefix = child_prefix
            )

    def visualize_tree(self, title:str=None) -> Digraph:
        """
        Visualize the logical tree using Graphviz.

        :param title: Title for the visualization.
        :type title: str, optional
        :return:  A `Digraph` object representing the logical tree.
        :rtype: Digraph
        """
        self.graph = Digraph(comment="Logic Tree", format=self.output_format)
        self.graph.attr(bgcolor = 'transparent')
        self.graph.attr("node", shape="ellipse", style="filled", fontname="Helvetica-Bold")
        self.graph.attr("edge", fontname="Helvetica", color="gold")
        self.graph.attr(rankdir="TB")
        if title is None:
            title = self._reverse_format_expression()
        self.graph.attr(label=f"\n{title}", fontsize="12", fontname="Helvetica-Bold", fontcolor="gold")

        self._visualize_recursively(self.root)
        return self.graph

    def _visualize_recursively(self, node: BaseNode, parent: Optional[BaseNode]=None, parent_id: str=None, depth:int=0) -> None:
        """
        Recursively add nodes and edges to the Graphviz graph.

        :param node: Current node.
        :type node: BaseNode
        :param parent_id: Parent node ID.
        :type parent_id: str, optional
        :param depth: Depth of the current node.
        :type depth: int
        :return: None
        """
        if node is None:
            return

        #unique_node_id = f"{node.index}_{depth}_{id(node)}"
        unique_node_id = f"{node.index}_{depth}_{id(node)}_{hash(node)}"
        color, label = self._get_node_properties(node)

        if isinstance(node, (NodeAnd, NodeOr, NodeNot, NodeImp, NodeEq, NodeXor)):
            self.graph.node(
                name=unique_node_id,
                label=label,
                fillcolor=color,
                fontcolor=get_contrast_color(color),
                color = 'white',)
        elif isinstance(node, NodeVar):
            remapped_name = self.get_variable_mapping().get(node.name, node.name)
            self.graph.node(
                unique_node_id,
                label=f"{'~' if node.is_negated else ''}{remapped_name}",
                shape="hexagon",
                style="filled",
                fillcolor=self.variable_color_map.get(node.name, "grey"),
                fontcolor=get_contrast_color(self.variable_color_map.get(node.name, "grey")),
                color = ('#AA0000' if node.is_negated else 'white'),
                penwidth = ('3' if node.is_negated else '1')
            )
        elif isinstance(node, NodeTrue):
            self.graph.node(unique_node_id, label="TRUE", shape="octagon",fillcolor=color)
        elif isinstance(node, NodeFalse):
            self.graph.node(unique_node_id, label="FALSE", shape="octagon", fillcolor=color)

        if parent_id:
            if isinstance(parent, NodeImp):
                if parent.children[0] == node:
                    self.graph.edge(parent_id, unique_node_id, dir = "back", label = "if", fontcolor="gold")
                else:
                    self.graph.edge(parent_id, unique_node_id, label = "then", fontcolor="gold")
            else:
                self.graph.edge(parent_id, unique_node_id)

        if hasattr(node, "children"):
            for child in node.children:
                self._visualize_recursively(child, node, unique_node_id, depth + 1)

    ### HELPER FUNCTIONS ###

    @staticmethod
    def _are_parentheses_balanced(expression: str) -> bool:
        """
        Checks if parentheses in the expression are balanced.

        :param expression: Logical expression as a string.
        :type expression: str
        :return: True if balanced, False otherwise.
        :rtype: bool
        """
        balance = 0
        for char in expression:
            if char == '(':
                balance += 1
            elif char == ')':
                balance -= 1
            if balance < 0:
                return False
        return balance == 0

    def _remove_outer_parentheses(self, expression: str) -> str:
        """
        Removes outermost parentheses if balanced.

        :param expression: Expression string.
        :type expression: str
        :return: Expression without outermost parentheses.
        :rtype: str
        """
        expression = expression.strip()
        if expression.startswith('(') and expression.endswith(')'):
            level = 0
            for i in range(len(expression) - 1):
                if expression[i] == '(':
                    level += 1
                elif expression[i] == ')':
                    level -= 1
                if level == 0:
                    return expression
            return self._remove_outer_parentheses(expression[1:-1])
        return expression

    def _find_main_operator(self, expression: str) -> tuple:
        """
        Identify the main operator in an expression.

        :param expression: Logical expression.
        :type expression: str
        :return: Tuple (position, operator).
        :rtype: tuple[int, str]
        """
        stack_level = 0
        operator_candidates = []
        index = 0

        while index < len(expression):
            char = expression[index]

            if char == '(':
                stack_level += 1
            elif char == ')':
                stack_level -= 1
            elif stack_level == 0:
                for operator in self.binary_operators + self.unary_operators:
                    if expression.startswith(operator, index):
                        operator_candidates.append((self.operator_precedence[operator], index, operator))
                        index += len(operator) - 1
                        break
            index += 1

        if operator_candidates:
            operator_candidates.sort()
            return operator_candidates[0][1], operator_candidates[0][2]

        return None, None

    def _assign_variable_colors(self) -> dict:
        """
        Assign unique colors to variables.

        :return: Mapping of variables to colors.
        :rtype: dict
        """
        color_map = {}
        color_palette = generate_color_palette()
        for variable, index in self.variable_indices.items():
            color_map[variable] = color_palette[index % len(color_palette)]
        return color_map

    @staticmethod
    def _get_node_properties(node: BaseNode) -> tuple:
        """
        Retrieve visual properties for a node.

        :param node: Tree node.
        :type node: BaseNode
        :return: Tuple (color, label).
        :rtype: tuple
        """
        return dict(NodeAnd = ("#A9DFBF", "AND"), NodeOr = ("#F8C471", "OR"), NodeNot = ("#CB4335", "NOT"),
                          NodeImp = ("#5DADE2", "IMPLIES"), NodeEq = ("#34495E", "EQUIVALENT"),
                          NodeXor = ("#9B59B6", "XOR"), NodeTrue = ("#58D68D", "TRUE"),
                          NodeFalse = ("#EC7063", "FALSE")).get(node.__class__.__name__, ("#000000", "UNKNOWN"))
