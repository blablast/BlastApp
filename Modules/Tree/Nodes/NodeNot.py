from .BaseNode import BaseNode
from .BaseNodeExtended import BaseNodeExtended

class NodeNot(BaseNodeExtended):
    """
    Represents a logical NOT node.

    This node performs the logical NOT operation on a single operand.
    It inherits from `BaseNodeExtended` and ensures the node has exactly
    one child representing the operand to negate.

    Attributes:
        Inherits all attributes from BaseNodeExtended.
    """

    def __init__(self, index: int, operand: 'BaseNode', parent: 'BaseNode' = None) -> None:
        """
        Initializes a logical NOT node.

        :param index: Unique identifier for the node.
        :type index: int
        :param operand: The operand (child node) to negate.
        :type operand: BaseNodeExtended
        :param parent: Reference to the parent node. Defaults to None.
        :type parent: BaseNodeExtended, optional
        """
        super().__init__(index, parent)
        self.add_child(operand)
