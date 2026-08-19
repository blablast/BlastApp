"""Kontrakt algebry zdaniowej: co musi umieć reprezentacja, żeby ewaluator mógł na niej pracować.

Osiem metod, wszystkie potrzebne każdej implementacji — żadna nie rzuca `NotImplementedError`,
bo to byłby znak, że interfejs jest za gruby (#13).
"""

from abc import ABC, abstractmethod
from collections.abc import Sequence

from blastapp.domain.solving.truth_table import TruthTable


class PropositionAlgebra[P](ABC):
    """Wykonuje operacje logiczne na jednej reprezentacji zdania."""

    @abstractmethod
    def constant(self, value: bool) -> P:
        """Zdanie o stałej wartości."""

    @abstractmethod
    def variable(self, index: int, negated: bool) -> P:
        """Zdanie złożone z jednej zmiennej na podanej pozycji bitowej."""

    @abstractmethod
    def negation(self, proposition: P) -> P:
        """Negacja zdania."""

    @abstractmethod
    def conjunction(self, propositions: Sequence[P]) -> P:
        """Koniunkcja co najmniej dwóch zdań."""

    @abstractmethod
    def disjunction(self, propositions: Sequence[P]) -> P:
        """Alternatywa co najmniej dwóch zdań."""

    @abstractmethod
    def equivalence(self, left: P, right: P) -> P:
        """Równoważność dwóch zdań."""

    @abstractmethod
    def implication(self, antecedent: P, consequent: P) -> P:
        """Implikacja: poprzednik pociąga następnik."""

    @abstractmethod
    def to_truth_table(self, proposition: P) -> TruthTable:
        """Sprowadza zdanie do wspólnej, niemutowalnej postaci wyniku."""
