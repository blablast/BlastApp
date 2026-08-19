"""Wyjątki warstwy wyrażeń.

Parser albo zwraca kompletną formułę, albo rzuca — nie ma stanu pośredniego ani listy błędów
do przejrzenia (#25).

Typów jest cztery, bo tyle jest sytuacji, na które wywołujący może zareagować inaczej. Każdy
niesie oryginalne wyrażenie w polu `expression`, żeby warstwa prezentacji mogła zbudować własny
komunikat zamiast przekazywać dalej goły tekst techniczny.
"""


class ExpressionError(Exception):
    """Wyrażenia nie da się sparsować. Baza dla wszystkich błędów tej warstwy."""

    def __init__(self, message: str, expression: str = "") -> None:
        super().__init__(message)
        self.expression = expression


class EmptyExpressionError(ExpressionError):
    """Brak wyrażenia do sparsowania.

    Osobny typ, bo dla interfejsu to nie jest błąd składni, tylko puste pole — inny komunikat
    i inna reakcja niż przy literówce.
    """

    def __init__(self, expression: str = "") -> None:
        super().__init__("Expression cannot be empty.", expression)


class UnbalancedParenthesesError(ExpressionError):
    """Nawiasy się nie domykają."""

    def __init__(self, expression: str) -> None:
        super().__init__("Parentheses are not balanced.", expression)


class InvalidCharacterError(ExpressionError):
    """Wyrażenie zawiera znak, którego składnia nie przewiduje."""

    def __init__(self, expression: str) -> None:
        super().__init__("Expression contains invalid characters.", expression)


class MalformedExpressionError(ExpressionError):
    """Znaki są dopuszczalne, ale nie układają się w formułę.

    Obejmuje nierozpoznany atom, operator bez argumentu i operator w złym miejscu — z punktu
    widzenia wywołującego to jedna sytuacja: użytkownik ma poprawić zapis. Szczegół siedzi
    w komunikacie, nie w osobnym typie (#21).
    """

    def __init__(self, message: str, expression: str) -> None:
        super().__init__(message, expression)
