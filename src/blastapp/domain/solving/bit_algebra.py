"""Propositional algebra over a bitwise truth table.

`BitTable` is mutable and **never leaves this module** — an immutable `TruthTable` goes out
instead. That is the boundary the "immutable edges, mutable core" rule (#22) is about.
"""

from collections.abc import Sequence

from blastapp.domain.operators import Operator
from blastapp.domain.representations.bit_table import BitTable
from blastapp.domain.solving.algebra import PropositionAlgebra
from blastapp.domain.solving.truth_table import TruthTable


class BitAlgebra(PropositionAlgebra[BitTable]):
    def constant(self, value: bool) -> BitTable:
        return BitTable(initial_solution=1 if value else 0)

    def variable(self, index: int, negated: bool) -> BitTable:
        return BitTable().create_with_variable(index, negated)

    def negation(self, proposition: BitTable) -> BitTable:
        proposition.negate_in_place()
        return proposition

    def conjunction(self, propositions: Sequence[BitTable]) -> BitTable:
        return self._combine(Operator.AND, propositions)

    def disjunction(self, propositions: Sequence[BitTable]) -> BitTable:
        return self._combine(Operator.OR, propositions)

    def equivalence(self, left: BitTable, right: BitTable) -> BitTable:
        left.apply_in_place(Operator.EQ, right)
        return left

    def implication(self, antecedent: BitTable, consequent: BitTable) -> BitTable:
        """`~antecedent | consequent`, composed here because the table only exposes what numpy
        does in a single operation."""
        antecedent.negate_in_place()
        antecedent.apply_in_place(Operator.OR, consequent)
        return antecedent

    def to_truth_table(self, proposition: BitTable) -> TruthTable:
        """Reduce to the shared result form.

        Gaps in bit positions are filled first: a proposition may have lost a lower-indexed
        variable to simplification — `(a0 & ~a0) | a1` leaves only `a1` — and the survivors would
        then sit on the wrong bits. That has to happen after every operation, not during.
        """
        proposition.add_missed_variables()
        return TruthTable(proposition.variable_count(), proposition.solution)

    def _combine(self, operation: Operator, propositions: Sequence[BitTable]) -> BitTable:
        """Merge propositions pairwise, always taking the two narrowest.

        Adding a variable DOUBLES the table, so the order decides how large the intermediates get.
        A conjunction that reached false and a disjunction that reached true stop immediately: the
        remaining operands cannot change either.
        """
        if len(propositions) < 2:
            raise ValueError(f"Operation {operation} needs at least two operands")

        pending = sorted(propositions, key=self._width_key, reverse=True)
        while len(pending) > 1:
            left, right = pending.pop(), pending.pop()
            left.apply_in_place(operation, right)
            if self._is_settled(operation, left):
                return BitTable(initial_solution=0 if operation is Operator.AND else 1)
            self._insert_by_width(pending, left)
        return pending[0]

    @staticmethod
    def _is_settled(operation: Operator, result: BitTable) -> bool:
        return (operation is Operator.AND and result.is_false()) or (
            operation is Operator.OR and result.is_true()
        )

    @staticmethod
    def _width_key(table: BitTable) -> tuple[int, int]:
        """Highest variable index, then how many variables there are.

        The highest index says how wide the table becomes once gaps are filled, and it groups
        propositions over the same variable range, so merged pairs often already share variables.
        The count breaks ties because it is what sets the width right now.
        """
        return table.highest_index(), table.variable_count()

    @classmethod
    def _insert_by_width(cls, pending: list[BitTable], table: BitTable) -> None:
        key = cls._width_key(table)
        position = len(pending)
        while position > 0 and cls._width_key(pending[position - 1]) < key:
            position -= 1
        pending.insert(position, table)
