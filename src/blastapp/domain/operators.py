"""The single source of truth for operator syntax and binding strength.

The scanner, the normalizer, the expression writer and the character validator all derive from
here. Visual styling deliberately does not: it changes for a different reason and lives in
`presentation/theme.py`.
"""

from dataclasses import dataclass
from enum import Enum, StrEnum, auto


class Operator(StrEnum):
    """A logical operator; the enum value doubles as the normalized keyword."""

    NOT = "NOT"
    AND = "AND"
    OR = "OR"
    XOR = "XOR"
    IMP = "IMP"
    EQ = "EQ"


class Arity(Enum):
    """How many operands an operator takes in the tree."""

    UNARY = auto()
    BINARY = auto()
    ASSOCIATIVE = auto()  # AND and OR flatten to any number of operands


@dataclass(frozen=True, slots=True)
class OperatorSpec:
    """One operator: how it is written and how tightly it binds."""

    operator: Operator
    symbol: str  # canonical output form
    aliases: tuple[str, ...]  # wszystkie akceptowane zapisy symboliczne
    precedence: int  # higher number binds tighter
    arity: Arity

    @property
    def keyword(self) -> str:
        """The normalized keyword, e.g. 'AND'."""
        return self.operator.value


# Textbook order: ~ > & > XOR > | > => > <=>. XOR sits between & and | just as `^` sits between
# `&` and `|` in Python.
#
# No two operators share a level, and that is a requirement rather than a coincidence: on a tie
# the root is decided by position in the text instead of binding strength, so the same operators
# would bind differently depending on how they were written. A test guards this.
#
# Implication is the only non-associative operator — for p=q=r=F, `(p=>q)=>r` is F while
# `p=>(q=>r)` is T — and binds to the right by classical convention. For &, |, XOR and <=> the
# direction is invisible in the results, since all four are associative.
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

    return _BY_OPERATOR[operator]


def spec_for_keyword(keyword: str) -> OperatorSpec | None:
    """The spec for a keyword, or None when no operator uses it."""
    try:
        return _BY_OPERATOR[Operator(keyword)]
    except ValueError:
        return None


def keywords_by_precedence() -> dict[str, int]:
    """Keyword -> precedence, in the shape the scanner expects."""
    return {spec.keyword: spec.precedence for spec in OPERATORS}


def keywords_with_arity(arity: Arity) -> tuple[str, ...]:
    """Keywords of the operators with the given arity."""
    return tuple(spec.keyword for spec in OPERATORS if spec.arity is arity)


def aliases_longest_first() -> tuple[tuple[str, str], ...]:
    """(alias, keyword) pairs, longest alias first.

    The order matters: `=>` is a fragment of `<=>` and `==>`, so the shorter alias must be tried
    last, or equivalence falls apart into implication.
    """
    pairs = [(alias, spec.keyword) for spec in OPERATORS for alias in spec.aliases]
    return tuple(sorted(pairs, key=lambda pair: len(pair[0]), reverse=True))
