from pyeda.inter import expr, And, Or

from Tests.AbstractTestSolver import AbstractTestSolver


class TestPyEDASolverTest(AbstractTestSolver) :

    def __init__(self) :
        super().__init__("PyEDA")

    def _count_solutions(self) :
        return len(list(self.result))

    def _set(self, cnf) :
        variables = {abs(lit) : expr(f"x{abs(lit)}") for clause in cnf.clauses for lit in clause}
        self.expression = And(
            *[
                Or(
                    *[
                        variables[abs(lit)] if lit > 0 else ~variables[abs(lit)]
                        for lit in clause
                    ]
                ) for clause in cnf.clauses
            ]
        )

    def _solve(self) :
        self.result = self.expression.satisfy_all()


