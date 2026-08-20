"""Exceptions of the expression layer.

The parser either returns a complete formula or raises — there is no partial state and no error
list to walk (#25).

Four types, because that is how many situations a caller can react to differently. Each carries
the original text in `expression`, so the presentation layer can build its own message instead of
forwarding raw technical English.
"""


class ExpressionError(Exception):
    """The expression cannot be parsed. Base for every error of this layer."""

    def __init__(self, message: str, expression: str = "") -> None:
        super().__init__(message)
        self.expression = expression


class EmptyExpressionError(ExpressionError):
    """Nothing to parse.

    A separate type because to the interface this is an empty field rather than a syntax error,
    and it deserves a different message.
    """

    def __init__(self, expression: str = "") -> None:
        super().__init__("Expression cannot be empty.", expression)


class UnbalancedParenthesesError(ExpressionError):
    """Parentheses do not balance."""

    def __init__(self, expression: str) -> None:
        super().__init__("Parentheses are not balanced.", expression)


class InvalidCharacterError(ExpressionError):
    """The expression contains a character the syntax does not allow."""

    def __init__(self, expression: str) -> None:
        super().__init__("Expression contains invalid characters.", expression)


class MalformedExpressionError(ExpressionError):
    """The characters are allowed but do not form a formula.

    Covers an unrecognised atom, an operator without an operand and an operator in the wrong
    place — to the caller these are one situation: the user has to fix the text. The detail lives
    in the message, not in a separate type (#21).
    """

    def __init__(self, message: str, expression: str) -> None:
        super().__init__(message, expression)
