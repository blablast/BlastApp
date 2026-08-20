"""A naive model counter: the reference point for this application's engines.

It exists to say when an engine actually contributes something. The PySAT adapter counts models by
blocking each one it finds, so it costs Omega(#models) solver calls — beating that proves nothing.
This baseline is written plainly, with no caching and no decomposition into independent
components, and still often beats the bitwise engine: its cost follows the structure of the
instance rather than 2^n.
"""

from collections.abc import Sequence

from blastapp.benchmarks.engine_adapter import SolverAdapter


class NaiveDpllAdapter(SolverAdapter):
    """Counts models by unit propagation and splitting into two cases."""

    name = "Naiwny DPLL"

    def count_solutions(self, clauses: Sequence[Sequence[int]]) -> int:
        # The universe reaches the LARGEST variable used, not the count of distinct ones: literal n
        # sits at position |n|-1, so `[[1, -3]]` is three variables, and a1 occurs in no clause yet
        # doubles the count. `formula_from_clauses` counts the same way, which is the only reason
        # this baseline agrees with the engines on instances with gaps in the numbering.
        variable_count = max(abs(literal) for clause in clauses for literal in clause)
        return _count([list(clause) for clause in clauses], 0, variable_count)


def _count(clauses: list[list[int]], assigned: int, total: int) -> int:
    """Count the assignments satisfying `clauses`, given `assigned` variables already fixed."""
    clauses, assigned, consistent = _propagate(clauses, assigned)
    if not consistent:
        return 0
    if not clauses:
        # Every clause satisfied: each unfixed variable is free and doubles the count.
        return 1 << (total - assigned)

    variable = abs(clauses[0][0])
    return sum(_count(clauses + [[sign * variable]], assigned, total) for sign in (1, -1))


def _propagate(clauses: list[list[int]], assigned: int) -> tuple[list[list[int]], int, bool]:
    """Force unit clauses while any remain.

    A one-literal clause leaves no choice, so forcing it loses no solutions — the only step allowed
    without branching.
    """
    while True:
        unit = next((clause[0] for clause in clauses if len(clause) == 1), None)
        if unit is None:
            return clauses, assigned, True

        assigned += 1
        reduced: list[list[int]] = []
        for clause in clauses:
            if unit in clause:
                continue  # clause satisfied, drops out of the instance
            if -unit not in clause:
                reduced.append(clause)
                continue
            shortened = [literal for literal in clause if literal != -unit]
            if not shortened:
                return clauses, assigned, False  # empty clause: contradiction
            reduced.append(shortened)
        clauses = reduced
