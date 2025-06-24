from pysat.solvers import Glucose3

from Tests.AbstractTestSolver import AbstractTestSolver


class TestPySATSolverTest(AbstractTestSolver) :
    def __init__(self) :
        super().__init__("PySAT")
        self.solver = Glucose3()
        self.solutions = 0

    def _count_solutions(self) :
        return self.solutions

    def _set(self, cnf) :
        self.solver.append_formula(cnf)
        pass

    def _solve(self) :
        self.solutions = 0
        while self.solver.solve() :
            self.solutions += 1
            model = self.solver.get_model()
            self.solver.add_clause([-lit for lit in model])
