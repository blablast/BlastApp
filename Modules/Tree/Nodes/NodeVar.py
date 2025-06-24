from .BaseNode import BaseNode

class NodeVar(BaseNode):
    """
    Represents a logical variable node.

    This class is used to model variables in logical expressions, with optional
    support for negation. It inherits from the `BaseNode` class and adds specific
    attributes for variable representation.

    Attributes:
        name (str): The name or identifier of the variable.
        is_negated (bool): Indicates whether the variable is negated.
    """

    def __init__(self, index: int, name: str, is_negated: bool = False, parent: 'BaseNode' = None) -> None:
        """
        Initializes a logical variable node.

        :param index: Unique identifier for the node.
        :type index: int
        :param name: The name or identifier of the variable.
        :type name: str
        :param is_negated: Whether the variable is negated. Defaults to False.
        :type is_negated: bool
        :param parent: Reference to the parent node. Defaults to None.
        :type parent: BaseNode, optional
        """
        super().__init__(index, parent)
        self.name = name  # Name or identifier of the variable
        self.is_negated = is_negated  # Negation flag
