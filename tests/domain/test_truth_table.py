"""The result form both engines share."""

import pytest

from blastapp.domain.solving.statistics import SolutionStatistics
from blastapp.domain.solving.truth_table import TruthTable


class TestConstruction:
    def test_bit_i_is_the_result_for_assignment_i(self) -> None:
        table = TruthTable(2, 0b1010)
        assert [table.value_at(i) for i in range(4)] == [False, True, False, True]

    def test_from_values_round_trips(self) -> None:
        values = [False, True, True, False]
        assert TruthTable.from_values(values).as_values() == values

    def test_zero_variables_is_a_single_constant(self) -> None:
        assert TruthTable(0, 1).as_values() == [True]
        assert TruthTable(0, 0).as_values() == [False]

    @pytest.mark.parametrize("count", [-1, -5])
    def test_negative_variable_count_is_refused(self, count: int) -> None:
        with pytest.raises(ValueError, match="negative"):
            TruthTable(count, 0)

    def test_values_wider_than_the_table_are_refused(self) -> None:
        """A surplus bit would be a result for an assignment that does not exist."""
        with pytest.raises(ValueError, match="bits"):
            TruthTable(1, 0b1000)

    def test_length_that_is_not_a_power_of_two_is_refused(self) -> None:
        with pytest.raises(ValueError, match="power of two"):
            TruthTable.from_values([True, False, True])


class TestWidening:
    def test_added_variable_does_not_change_the_result(self) -> None:
        """A variable the formula does not depend on only doubles the rows."""
        narrow = TruthTable.from_values([False, True])
        assert narrow.widened_to(2).as_values() == [False, True, False, True]

    def test_tautology_stays_a_tautology(self) -> None:
        assert TruthTable(0, 1).widened_to(3).as_values() == [True] * 8

    def test_contradiction_stays_a_contradiction(self) -> None:
        assert TruthTable(0, 0).widened_to(3).as_values() == [False] * 8

    def test_widening_to_the_same_width_is_a_no_op(self) -> None:
        table = TruthTable(2, 0b0110)
        assert table.widened_to(2) is table

    def test_narrowing_is_refused(self) -> None:
        with pytest.raises(ValueError, match="Cannot narrow"):
            TruthTable(3, 0).widened_to(1)


class TestAccess:
    def test_true_assignments_lists_satisfying_rows(self) -> None:
        assert list(TruthTable(2, 0b1010).true_assignments()) == [1, 3]

    def test_assignment_out_of_range_is_refused(self) -> None:
        with pytest.raises(IndexError, match="out of range"):
            TruthTable(2, 0).value_at(4)


class TestStatistics:
    def test_counts_come_from_the_table(self) -> None:
        statistics = SolutionStatistics.of(TruthTable(2, 0b1011))
        assert (statistics.total, statistics.true_count, statistics.false_count) == (4, 3, 1)

    def test_tautology_and_contradiction_are_derived_not_stored(self) -> None:
        """Derived from the table rather than stored, so there is nothing to desynchronise."""
        assert SolutionStatistics.of(TruthTable(2, 0b1111)).is_tautology
        assert SolutionStatistics.of(TruthTable(2, 0)).is_contradiction
        middling = SolutionStatistics.of(TruthTable(2, 0b0110))
        assert not middling.is_tautology and not middling.is_contradiction

    def test_more_true_than_total_is_refused(self) -> None:
        with pytest.raises(ValueError, match="true out of"):
            SolutionStatistics(total=2, true_count=3)
