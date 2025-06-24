from .BaseNode import BaseNode
from .BaseNodeExtended import BaseNodeExtended

class BaseNode2Sides(BaseNodeExtended):
    """
    Represents a logical node with two sides (e.g., AND, OR, IMPLIES).

    This class inherits from 'BaseNodeExtended' and is designed for nodes
    that have exactly two child nodes: a left-hand side ('left') and a
    right-hand side ('right').

    Attributes:
        left (BaseNode): The left-hand side child node.
        right (BaseNode): The right-hand side child node.
    """

    def __init__(self, index: int, left: 'BaseNode', right: 'BaseNode', parent: 'BaseNodeExtended' = None) -> None:
        """
        Initializes a logical node with two sides.

        :param index: Unique identifier for the node.
        :type index: int
        :param left: The left-hand side child node.
        :type left: BaseNod
        :param right: The right-hand side child node.
        :type right: BaseNode
        :param parent: Reference to the parent node, or None if it is a root node.
        :type parent: BaseNodeExtended, optional
        """
        super().__init__(index, parent)
        self.add_child(left)  # Add the left child node
        self.add_child(right)  # Add the right child node
