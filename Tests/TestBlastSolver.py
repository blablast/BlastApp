from Modules.Solvers.BlastSolver import BlastSolver
from Modules.Tree.LogicTree import LogicTree
from Tests.AbstractTestSolver import AbstractTestSolver


class TestBlastSolverTest(AbstractTestSolver) :

    def __init__(self) :
        super().__init__("BlastSolver")
        self.logic_tree = None
        self.solver = BlastSolver(create_ota=False)

    def _set(self, cnf) :
        self.logic_tree = LogicTree()
        self.logic_tree.load_cnf(cnf)
        if self.logic_tree.expression_errors:
            for error in self.logic_tree.expression_errors:
                print(error)
            raise ValueError("Invalid CNF formula.")

    def _count_solutions(self) :
        return self.solver.count_bit_true_results()

    def _solve(self) :
        """Solve using the BlastSolver."""
        self.solver.solve(self.logic_tree)
