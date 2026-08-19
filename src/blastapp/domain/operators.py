"""Jedyne źródło prawdy o składni i sile wiązania operatorów.

Czerpią stąd: skaner wyrażeń, normalizator zapisu, generator zapisu symbolicznego i walidator
znaków. Style wizualne celowo tu nie należą — zmieniają się z innego powodu i mieszkają
w `presentation/theme.py`.
"""

from dataclasses import dataclass
from enum import Enum, StrEnum, auto


class Operator(StrEnum):
    """Operator logiczny; wartość enuma jest zarazem słowem kluczowym postaci znormalizowanej."""

    NOT = "NOT"
    AND = "AND"
    OR = "OR"
    XOR = "XOR"
    IMP = "IMP"
    EQ = "EQ"


class Arity(Enum):
    """Ile argumentów przyjmuje operator w drzewie."""

    UNARY = auto()
    BINARY = auto()
    ASSOCIATIVE = auto()  # AND i OR spłaszczają się do dowolnej liczby argumentów


@dataclass(frozen=True, slots=True)
class OperatorSpec:
    """Pełny opis jednego operatora: jak się go zapisuje i jak mocno wiąże."""

    operator: Operator
    symbol: str  # kanoniczny zapis wyjściowy
    aliases: tuple[str, ...]  # wszystkie akceptowane zapisy symboliczne
    precedence: int  # wyższa liczba = mocniejsze wiązanie
    arity: Arity

    @property
    def keyword(self) -> str:
        """Słowo kluczowe w postaci znormalizowanej, np. 'AND'."""
        return self.operator.value


# Kolejność podręcznikowa: ~ > & > XOR > | > => > <=>. XOR wypada między & a | tak samo, jak `^`
# między `&` a `|` w Pythonie.
#
# Żadne dwa operatory nie dzielą poziomu, i to jest wymóg, nie zbieg okoliczności: przy remisie
# o korzeniu decyduje pozycja operatora w tekście, a nie siła wiązania, więc ten sam zestaw
# operatorów wiązałby się różnie zależnie od kolejności zapisu. Pilnuje tego test.
#
# Implikacja jest jedynym operatorem niełącznym — dla p=q=r=F `(p=>q)=>r` daje F, a `p=>(q=>r)`
# daje T — i wiąże w prawo, zgodnie z konwencją klasyczną. Dla &, |, XOR i <=> kierunek wiązania
# jest niewidoczny w wynikach, bo wszystkie cztery są łączne.
OPERATORS: tuple[OperatorSpec, ...] = (
    OperatorSpec(Operator.EQ, "<=>", ("<=>",), 1, Arity.BINARY),
    OperatorSpec(Operator.IMP, "=>", ("==>", "=>"), 2, Arity.BINARY),
    OperatorSpec(Operator.OR, "|", ("|", "∨", "\\/"), 3, Arity.ASSOCIATIVE),
    OperatorSpec(Operator.XOR, "XOR", ("^",), 4, Arity.BINARY),
    OperatorSpec(Operator.AND, "&", ("&", "∧", "/\\"), 5, Arity.ASSOCIATIVE),
    OperatorSpec(Operator.NOT, "~", ("~", "⌐", "!"), 6, Arity.UNARY),
)

_BY_OPERATOR: dict[Operator, OperatorSpec] = {spec.operator: spec for spec in OPERATORS}


def spec_of(operator: Operator) -> OperatorSpec:
    """Zwraca opis podanego operatora."""
    return _BY_OPERATOR[operator]


def spec_for_keyword(keyword: str) -> OperatorSpec | None:
    """Zwraca opis operatora o podanym słowie kluczowym albo None, gdy takiego nie ma."""
    try:
        return _BY_OPERATOR[Operator(keyword)]
    except ValueError:
        return None


def keywords_by_precedence() -> dict[str, int]:
    """Słowo kluczowe -> priorytet, w postaci oczekiwanej przez skaner wyrażeń."""
    return {spec.keyword: spec.precedence for spec in OPERATORS}


def keywords_with_arity(arity: Arity) -> tuple[str, ...]:
    """Słowa kluczowe operatorów o podanej arności."""
    return tuple(spec.keyword for spec in OPERATORS if spec.arity is arity)


def aliases_longest_first() -> tuple[tuple[str, str], ...]:
    """Pary (alias, słowo kluczowe) posortowane od najdłuższego aliasu.

    Kolejność jest istotna: `=>` jest fragmentem `<=>` i `==>`, więc krótszy alias musi być
    próbowany dopiero po dłuższych — inaczej równoważność rozpadnie się na implikację.
    """
    pairs = [(alias, spec.keyword) for spec in OPERATORS for alias in spec.aliases]
    return tuple(sorted(pairs, key=lambda pair: len(pair[0]), reverse=True))
