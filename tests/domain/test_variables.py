"""Bit position assignment: the registries and how the parser uses them.

The position is used arithmetically as `1 << position`, so two names on one position are two
variables fused into one — and a formula computing something other than what the user wrote.
"""

import pytest

from blastapp.domain.expressions.parsing import parse_formula, parse_sequential
from blastapp.domain.expressions.variables import (
    IndexedVariableRegistry,
    SequentialVariableRegistry,
    VariableMap,
)


def positions_of(expression: str, *, recognize: bool) -> dict[str, int]:
    formula = parse_formula(expression) if recognize else parse_sequential(expression)
    return dict(formula.variables.positions)


class TestSequentialRegistry:
    def test_positions_follow_first_occurrence(self) -> None:
        registry = SequentialVariableRegistry()
        assert registry.position_for("a5") == 0
        assert registry.position_for("a3") == 1
        assert registry.position_for("a5") == 0, "ta sama nazwa musi dostac te sama pozycje"

    def test_digit_in_the_name_is_ignored(self) -> None:
        registry = SequentialVariableRegistry()
        registry.position_for("a5")
        assert registry.snapshot().positions == {"a5": 0}


class TestIndexedRegistry:
    def test_reserved_names_keep_their_digit(self) -> None:
        registry = IndexedVariableRegistry()
        registry.reserve("a1", 1)
        assert registry.position_for("a1") == 1

    def test_other_names_take_the_first_free_position(self) -> None:
        """The first FREE position, not the one after however many are already assigned."""
        registry = IndexedVariableRegistry()
        registry.reserve("a1", 1)
        assert registry.position_for("p") == 0
        assert registry.position_for("q") == 2

    def test_reserving_a_taken_position_is_refused(self) -> None:
        registry = IndexedVariableRegistry()
        registry.reserve("a0", 0)
        with pytest.raises(ValueError, match="already taken"):
            registry.reserve("a1", 0)

    def test_reserving_the_same_name_twice_is_harmless(self) -> None:
        """A name can occur several times in the text, so the reservation repeats."""
        registry = IndexedVariableRegistry()
        registry.reserve("a2", 2)
        registry.reserve("a2", 2)
        assert registry.snapshot().positions == {"a2": 2}


class TestVariableMap:
    def test_rejects_two_names_on_one_position(self) -> None:
        with pytest.raises(ValueError, match="tej samej pozycji"):
            VariableMap({"p": 0, "q": 0})

    def test_count_is_the_highest_position_plus_one(self) -> None:
        assert VariableMap({"a0": 0, "a3": 3}).count == 4
        assert VariableMap({}).count == 0

    def test_aliases_map_back_to_original_names(self) -> None:
        assert VariableMap({"p": 0, "q": 1}).aliases() == {"a0": "p", "a1": "q"}


class TestParserIntegration:
    @pytest.mark.parametrize(
        ("expression", "expected"),
        [
            ("a1 & p & q", {"a1": 1, "p": 0, "q": 2}),
            ("p & a0", {"a0": 0, "p": 1}),
            ("p & q & r", {"p": 0, "q": 1, "r": 2}),
            ("a5 & a3", {"a5": 5, "a3": 3}),
            ("p & a2 & q & a0", {"a2": 2, "a0": 0, "p": 1, "q": 3}),
        ],
    )
    def test_indexed_mode(self, expression: str, expected: dict[str, int]) -> None:
        assert positions_of(expression, recognize=True) == expected

    def test_sequential_mode_renumbers_from_zero(self) -> None:
        assert positions_of("a5 & a3", recognize=False) == {"a5": 0, "a3": 1}

    def test_named_variables_never_share_a_position(self) -> None:
        """`a1 & p & q` has three distinct variables; fusing them would give `a1 & a1 & a1`."""
        positions = positions_of("a1 & p & q", recognize=True)
        assert len(set(positions.values())) == 3
