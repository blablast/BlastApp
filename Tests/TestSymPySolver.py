from sympy import symbols, And, Or, Not, satisfiable

from Tests.AbstractTestSolver import AbstractTestSolver


class TestSymPySolverTest(AbstractTestSolver) :
    def __init__(self) :
        super().__init__("SymPy")

    def _count_solutions(self) :
        return len(list(self.result))

    def _set(self, cnf) :
        variables = {abs(lit) : symbols(f"x{abs(lit)}") for clause in cnf.clauses for lit in clause}
        sympy_clauses = [Or(*[variables[abs(lit)] if lit > 0 else Not(variables[abs(lit)]) for lit in clause]) for
                         clause in cnf.clauses]
        self.expression = And(*sympy_clauses)

    def _solve(self) :
        self.result = satisfiable(self.expression, all_models = True)

