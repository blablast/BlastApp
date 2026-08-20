"""Propositional algebra over the OTA function.

Logical operations are arithmetic on the coefficient vector: conjunction is multiplication,
disjunction follows from De Morgan, equivalence from the squared difference.
"""

from collections.abc import Callable, Sequence
from heapq import nsmallest

import numpy as np

from blastapp.domain.representations.ns_squares import NSSquares
from blastapp.domain.representations.ota_function import OtaFunction
from blastapp.domain.solving.algebra import PropositionAlgebra
from blastapp.domain.solving.truth_table import TruthTable


class OtaAlgebra(PropositionAlgebra[OtaFunction]):
    def __init__(self, squares: NSSquares | None = None) -> None:
        """The index-pair sets are injected, not kept on an operand: otherwise their size would
        depend on which multiplication happened to run first (#14)."""
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
        """Merge propositions pairwise, always taking the two shortest vectors.

        Shorter vectors mean fewer variables, so this order keeps intermediates small.

        Selection goes by POSITION in the list, not by value: `OtaFunction` defines no `__eq__`,
        so filtering with `not in` would compare identity and drop both occurrences of the same
        object at once, silently losing an operand.
        """
        if len(propositions) < 2:
            raise ValueError("Operation needs at least two operands")

        pending = list(propositions)
        while len(pending) > 1:
            first, second = nsmallest(2, range(len(pending)), key=lambda i: len(pending[i]))
            left, right = pending[first], pending[second]
            pending = [
                item for position, item in enumerate(pending) if position not in (first, second)
            ]
            pending.append(apply(left, right))
        return pending[0]
