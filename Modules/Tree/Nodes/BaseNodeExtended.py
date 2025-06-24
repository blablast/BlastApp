from .BaseNode import BaseNode
from .NodeFalse import NodeFalse
from .NodeTrue import NodeTrue
from .NodeVar import NodeVar

class BaseNodeExtended(BaseNode):
    """
    Extends the base logical node class to include functionality for checking
    whether the node's children consist only of variables or constants.

    Attributes:
        Inherits all attributes from BaseNode.
    """

    def are_variables_only(self) -> bool:
        """
        Checks if all children of this node are variable nodes ('NodeVar').

        :return: True if all children are instances of 'NodeVar', otherwise False.
        :rtype: bool

        Example:
            >>> node = BaseNodeExtended(index=1)
            >>> node.add_child(NodeVar(index=2, name = 'a0'))
            >>> node.add_child(NodeVar(index=3, name = 'a1'))
            >>> node.are_variables_only()
            True
        """
        return all(isinstance(child, NodeVar) for child in self.children)

    def are_variables_or_constants_only(self) -> bool:
        """
        Checks if all children of this node are variable nodes ('NodeVar')
        or constants ('NodeTrue' or 'NodeFalse').

        :return: True if all children are instances of 'NodeVar', 'NodeTrue', or 'NodeFalse'.
        :rtype: bool

        Example:
            >>> node = BaseNodeExtended(index=1)
            >>> node.add_child(NodeVar(index=2, name = 'a0'))
            >>> node.add_child(NodeTrue(index=3))
            >>> node.are_variables_or_constants_only()
            True
        """
        return all(isinstance(child, (NodeVar, NodeTrue, NodeFalse)) for child in self.children)
