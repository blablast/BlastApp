"""Tabela operatorów: składnia, priorytety i arność.

Wartości oczekiwane są wpisane wprost, a nie czytane z kodu produkcyjnego — test odczytujący
wartość, którą sprawdza, nie sprawdza niczego.
"""

from blastapp.domain.operators import (
    OPERATORS,
    Arity,
    Operator,
    aliases_longest_first,
    keywords_by_precedence,
    keywords_with_arity,
    spec_for_keyword,
    spec_of,
)


def test_precedence_follows_the_classical_convention() -> None:
    """Kolejność podręcznikowa: ~ > & > XOR > | > => > <=>."""
    assert keywords_by_precedence() == {"EQ": 1, "IMP": 2, "OR": 3, "XOR": 4, "AND": 5, "NOT": 6}


def test_every_operator_binds_differently() -> None:
    """Żadnego remisu: przy równych priorytetach o korzeniu decyduje pozycja w tekście."""
    precedences = list(keywords_by_precedence().values())
    assert len(set(precedences)) == len(precedences)


def test_binary_and_unary_split_is_unchanged() -> None:
    binary = set(keywords_with_arity(Arity.BINARY)) | set(keywords_with_arity(Arity.ASSOCIATIVE))
    assert binary == {"EQ", "IMP", "OR", "XOR", "AND"}
    assert keywords_with_arity(Arity.UNARY) == ("NOT",)


def test_associative_operators_are_exactly_and_or() -> None:
    """Tylko AND i OR spłaszczają się do n argumentów; reszta zostaje binarna."""
    assert set(keywords_with_arity(Arity.ASSOCIATIVE)) == {"AND", "OR"}


def test_every_operator_has_a_spec() -> None:
    assert {spec.operator for spec in OPERATORS} == set(Operator)


def test_keyword_is_derived_from_operator_value() -> None:
    for spec in OPERATORS:
        assert spec.keyword == spec.operator.value
        assert spec_of(spec.operator) is spec
        assert spec_for_keyword(spec.keyword) is spec


def test_unknown_keyword_gives_none_not_exception() -> None:
    assert spec_for_keyword("NAND") is None


def test_aliases_cover_the_symbols_the_parser_accepted() -> None:
    by_keyword: dict[str, set[str]] = {}
    for alias, keyword in aliases_longest_first():
        by_keyword.setdefault(keyword, set()).add(alias)
    assert by_keyword["NOT"] == {"~", "⌐", "!"}
    assert by_keyword["AND"] == {"&", "∧", "/\\"}
    assert by_keyword["OR"] == {"|", "∨", "\\/"}
    assert by_keyword["EQ"] == {"<=>"}
    assert by_keyword["IMP"] == {"==>", "=>"}
    assert by_keyword["XOR"] == {"^"}


def test_longer_aliases_come_first() -> None:
    """`=>` jest fragmentem `<=>` i `==>`, więc musi być próbowany jako ostatni z tej trójki."""
    aliases = [alias for alias, _ in aliases_longest_first()]
    assert aliases.index("<=>") < aliases.index("=>")
    assert aliases.index("==>") < aliases.index("=>")
    lengths = [len(alias) for alias in aliases]
    assert lengths == sorted(lengths, reverse=True)


def test_specs_are_immutable() -> None:
    """Tabeli nie da się podmienić w trakcie działania (#22)."""
    import dataclasses

    import pytest

    with pytest.raises(dataclasses.FrozenInstanceError):
        OPERATORS[0].precedence = 99  # type: ignore[misc]
