from .BaseNode import BaseNode

class NodeTrue(BaseNode):
    """
    Represents a logical TRUE node.

    This node always evaluates to logical TRUE in logical expressions.
    It inherits from the `BaseNode` class and does not add additional
    functionality beyond its role as a constant.

    Attributes:
        Inherits all attributes from BaseNode.
    """

    def __init__(self, index: int, parent: 'BaseNode' = None) -> None:
        """
        Initializes a logical TRUE node.

        :param index: Unique identifier for the node.
        :type index: int
        :param parent: Reference to the parent node. Defaults to None.
        :type parent: BaseNode, optional
        """
        super().__init__(index, parent)
        self.default = 1