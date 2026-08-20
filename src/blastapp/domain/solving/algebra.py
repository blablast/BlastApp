"""What a representation must offer for the evaluator to work on it.

Eight methods, all needed by every implementation — none raises `NotImplementedError`, which
would mean the interface is too fat (#13).
"""

from abc import ABC, abstractmethod
from collections.abc import Sequence

from blastapp.domain.solving.truth_table import TruthTable


class PropositionAlgebra[P](ABC):
    """Logical operations over one proposition representation."""

    @abstractmethod
    def constant(self, value: bool) -> P:
        """A proposition of constant value."""

    @abstractmethod
    def variable(self, index: int, negated: bool) -> P:
        """A proposition made of one variable at the given bit position."""

    @abstractmethod
    def negation(self, proposition: P) -> P:
        """Negation."""

    @abstractmethod
    def conjunction(self, propositions: Sequence[P]) -> P:
        """Conjunction of at least two propositions."""

    @abstractmethod
    def disjunction(self, propositions: Sequence[P]) -> P:
        """Disjunction of at least two propositions."""

    @abstractmethod
    def equivalence(self, left: P, right: P) -> P:
        """Equivalence of two propositions."""

    @abstractmethod
    def implication(self, antecedent: P, consequent: P) -> P:
        """Implication: the antecedent entails the consequent."""

    @abstractmethod
    def to_truth_table(self, proposition: P) -> TruthTable:
        """Reduce to the shared, immutable result form."""
