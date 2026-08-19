"""Algebra zdaniowa oparta na bitowej tablicy prawdy.

Cała tablica prawdy siedzi w jednej liczbie całkowitej, a operacje logiczne to operacje bitowe
na tej liczbie.

`BitTable` jest mutowalna i **nie opuszcza tego modułu** — na zewnątrz wychodzi niemutowalny
`TruthTable`. To jest granica, o którą chodzi w regule „niemutowalne granice, mutowalny
rdzeń" (#22).
"""

from collections.abc import Sequence

from blastapp.domain.representations.bit_table import BitTable
from blastapp.domain.solving.algebra import PropositionAlgebra
from blastapp.domain.solving.truth_table import TruthTable


class BitAlgebra(PropositionAlgebra[BitTable]):
    """Reprezentuje zdanie jako tablicę prawdy w jednej liczbie."""

    def constant(self, value: bool) -> BitTable:
        return BitTable(initial_solution=1 if value else 0)

    def variable(self, index: int, negated: bool) -> BitTable:
        return BitTable().create_with_variable(index, negated)

    def negation(self, proposition: BitTable) -> BitTable:
        proposition.negate_in_place()
        return proposition

    def conjunction(self, propositions: Sequence[BitTable]) -> BitTable:
        return self._combine("AND", propositions)

    def disjunction(self, propositions: Sequence[BitTable]) -> BitTable:
        return self._combine("OR", propositions)

    def equivalence(self, left: BitTable, right: BitTable) -> BitTable:
        left.apply_in_place("EQ", right)
        return left

    def implication(self, antecedent: BitTable, consequent: BitTable) -> BitTable:
        antecedent.apply_in_place("IMP", consequent)
        return antecedent

    def to_truth_table(self, proposition: BitTable) -> TruthTable:
        """Sprowadza tablicę bitową do wspólnej postaci wyniku.

        Najpierw dopełnia luki w pozycjach bitowych. Zdanie może nie zawierać zmiennej o niższym
        indeksie, bo wypadła przy uproszczeniu — `(a0 & ~a0) | a1` zostawia samo `a1` — a wtedy
        pozostałe zmienne siedzą na złych bitach. Dopełnienie musi nastąpić po zakończeniu
        wszystkich operacji, nie w trakcie.
        """
        proposition.add_missed_variables()
        return TruthTable(proposition.variable_count(), proposition.solution)

    def _combine(self, operation: str, propositions: Sequence[BitTable]) -> BitTable:
        """Łączy zdania parami, zawsze biorąc dwa o najniższym maksymalnym indeksie zmiennej.

        Niższy maksymalny indeks znaczy węższa tablica, a dołożenie zmiennej PODWAJA jej
        długość — taka kolejność trzyma wyniki pośrednie małe.

        Koniunkcja, która osiągnęła fałsz, i alternatywa, która osiągnęła prawdę, kończą się
        natychmiast: dalsze składniki nie mogą tego zmienić.
        """
        if len(propositions) < 2:
            raise ValueError(f"Operacja {operation} wymaga co najmniej dwóch argumentów")

        pending = sorted(propositions, key=lambda table: max(table.get_indices()), reverse=True)
        while len(pending) > 1:
            left, right = pending.pop(), pending.pop()
            left.apply_in_place(operation, right)
            if self._is_settled(operation, left):
                return BitTable(initial_solution=0 if operation == "AND" else 1)
            self._insert_by_width(pending, left)
        return pending[0]

    @staticmethod
    def _is_settled(operation: str, result: BitTable) -> bool:
        """Czy wynik nie może się już zmienić niezależnie od pozostałych składników."""
        return (operation == "AND" and result.is_false()) or (
            operation == "OR" and result.is_true()
        )

    @staticmethod
    def _insert_by_width(pending: list[BitTable], table: BitTable) -> None:
        """Wstawia tablicę tak, by lista pozostała posortowana malejąco po szerokości."""
        width = max(table.get_indices())
        position = len(pending)
        while position > 0 and max(pending[position - 1].get_indices()) < width:
            position -= 1
        pending.insert(position, table)
