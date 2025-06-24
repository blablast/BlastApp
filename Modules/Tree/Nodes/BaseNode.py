class BaseNode:
    """
    Represents a base logical node in a tree structure.

    Each node has:
    - A unique identifier ('index').
    - A reference to its parent node ('parent').
    - A list of child nodes ('children').
    - An optional 'proposition' attribute for associated logical propositions.

    Attributes:
        index (int): Unique identifier for the node.
        parent (BaseNode or None): Reference to the parent node.
        children (list[BaseNode]): List of child nodes.
        proposition (str or None): Optional logical proposition associated with the node.
    """

    def __init__(self, index: int, parent: 'BaseNode' = None) -> None:
        """
        Initializes a BaseNode instance.

        :param index: Unique identifier for the node.
        :type index: int
        :param parent: Reference to the parent node, or None if it is a root node.
        :type parent: BaseNode, optional
        """
        self.index:int = index  # Unique identifier for the node
        self.parent = parent  # Reference to the parent node
        self.children: list['BaseNode'] = []  # List of child nodes
        self.proposition = None  # Holds an associated logical proposition

    def add_child(self, child: 'BaseNode') -> None:
        """
        Adds a child node to this node.

        :param child: The child node to add.
        :type child: BaseNode
        :return: None        :rtype:
        """
        self.children.append(child)
