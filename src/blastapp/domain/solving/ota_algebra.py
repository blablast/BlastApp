"""Algebra zdaniowa oparta na funkcji OTA.

Operacje logiczne są tu działaniami arytmetycznymi na wektorze współczynników: koniunkcja to
mnożenie, alternatywa wychodzi z praw de Morgana, a równoważność z kwadratu różnicy.
"""

from collections.abc import Callable, Sequence
from heapq import nsmallest

import numpy as np

from blastapp.domain.representations.ns_squares import NSSquares
from blastapp.domain.representations.ota_function import OtaFunction
from blastapp.domain.solving.algebra import PropositionAlgebra
from blastapp.domain.solving.truth_table import TruthTable


class OtaAlgebra(PropositionAlgebra[OtaFunction]):
    """Reprezentuje zdanie jako funkcję OTA."""

    def __init__(self, squares: NSSquares | None = None) -> None:
        """
        :param squares: Współdzielony zbiór masek do mnożenia; domyślnie tworzony na miejscu.

        Maski są wstrzykiwane, a nie trzymane przy operandzie: inaczej ich rozmiar zależałby od
        tego, które mnożenie wykonano jako pierwsze (#14).
        """
        self._squares = squares if squares is not None else NSSquares()

    def constant(self, value: bool) -> OtaFunction:
        return OtaFunction().from_tn(np.array([1 if value else 0], dtype=np.int64))

    def variable(self, index: int, negated: bool) -> OtaFunction:
        tn = np.zeros(1 << (index + 1), dtype=np.int64)
        tn[1 << index] = -1 if negated else 1
        tn[0] = 1 if negated else 0
        return OtaFunction().from_tn(tn)

    def negation(self, proposition: OtaFunction) -> OtaFunction:
        return proposition.negated()

    def conjunction(self, propositions: Sequence[OtaFunction]) -> OtaFunction:
        return self._combine(
            propositions, lambda left, right: left.multiplied_by(right, self._squares)
        )

    def disjunction(self, propositions: Sequence[OtaFunction]) -> OtaFunction:
        return self._combine(
            propositions,
            lambda left, right: (
                left.negated().multiplied_by(right.negated(), self._squares).negated()
            ),
        )

    def equivalence(self, left: OtaFunction, right: OtaFunction) -> OtaFunction:
        difference = left - right
        return difference.multiplied_by(difference, self._squares).negated()

    def implication(self, antecedent: OtaFunction, consequent: OtaFunction) -> OtaFunction:
        return antecedent.multiplied_by(consequent.negated(), self._squares).negated()

    def to_truth_table(self, proposition: OtaFunction) -> TruthTable:
        return TruthTable.from_values([bool(value) for value in proposition.bn])

    def _combine(
        self,
        propositions: Sequence[OtaFunction],
        apply: Callable[[OtaFunction, OtaFunction], OtaFunction],
    ) -> OtaFunction:
        """Łączy zdania parami, zawsze biorąc dwa najkrótsze wektory.

        Krótsze wektory znaczą mniej zmiennych, więc taka kolejność trzyma wyniki pośrednie małe.

        Wybór idzie po POZYCJACH w liście, nie po wartościach: `OtaFunction` nie definiuje
        `__eq__`, więc filtrowanie przez `not in` byłoby porównaniem tożsamości i usunęłoby oba
        wystąpienia tego samego obiektu naraz, cicho gubiąc składnik.
        """
        if len(propositions) < 2:
            raise ValueError("Operacja wymaga co najmniej dwóch argumentów")

        pending = list(propositions)
        while len(pending) > 1:
            first, second = nsmallest(2, range(len(pending)), key=lambda i: len(pending[i]))
            left, right = pending[first], pending[second]
            pending = [
                item for position, item in enumerate(pending) if position not in (first, second)
            ]
            pending.append(apply(left, right))
        return pending[0]
