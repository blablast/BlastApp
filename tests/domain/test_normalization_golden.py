"""Dokładny tekst po normalizacji symboli.

Czerwony wynik tutaj znaczy, że zmienił się akceptowany zapis wejściowy — a to musi być decyzja,
nie efekt uboczny zmiany w tabeli operatorów.
"""

import pytest

from blastapp.domain.expressions.normalization import normalize
from blastapp.domain.expressions.parsing import parse_formula
from blastapp.presentation.text.expression_writer import write_formula


@pytest.mark.parametrize(
    ("raw", "normalized"),
    [
        ("a0 & a1", "a0 AND a1"),
        ("a0 | a1", "a0 OR a1"),
        ("a0 => a1", "a0 IMP a1"),
        ("a0 ==> a1", "a0 IMP a1"),
        ("a0 <=> a1", "a0 EQ a1"),
        ("~a0", " NOT a0"),
        ("⌐a0", " NOT a0"),
        ("a0 ∧ a1", "a0 AND a1"),
        ("a0 ∨ a1", "a0 OR a1"),
        ("a0 /\\ a1", "a0 AND a1"),
        ("a0 \\/ a1", "a0 OR a1"),
        ("a0 XOR a1", "a0 XOR a1"),
        ("(a1 & ~a0) | a2", "(a1 AND NOT a0) OR a2"),
        ("p => q", "p IMP q"),
        ("[a0 & a1]", " (a0 AND a1) "),
        ("a_0 & a_1", "a0 AND a1"),
        ("a0<=>a1", "a0 EQ a1"),
        ("a0=>a1<=>a2", "a0 IMP a1 EQ a2"),
        ("~(~(a0)) => a0", " NOT ( NOT (a0)) IMP a0"),
        ("a0 & a1 | a2 => a3 <=> a4", "a0 AND a1 OR a2 IMP a3 EQ a4"),
    ],
)
def test_normalization_is_unchanged(raw: str, normalized: str) -> None:
    assert normalize(raw) == normalized


@pytest.mark.parametrize(
    ("raw", "symbolic"),
    [
        ("a0 & a1", "a0 & a1"),
        ("a0 AND a1", "a0 & a1"),
        ("a0 | a1", "a0 | a1"),
        ("a0 => a1", "a0 => a1"),
        ("a0 <=> a1", "a0 <=> a1"),
        ("~a0 & a1", "~a0 & a1"),
        ("a0 XOR a1", "a0 XOR a1"),
        ("a0 ^ a1", "a0 XOR a1"),
        ("p => q", "p => q"),
        ("(a0 & a1) | a2", "(a0 & a1) | a2"),
    ],
)
def test_expression_is_written_back_from_the_tree(raw: str, symbolic: str) -> None:
    """Zapis wyjściowy powstaje z DRZEWA, więc nie może rozjechać się z zapisem wejściowym."""
    assert write_formula(parse_formula(raw)) == symbolic
