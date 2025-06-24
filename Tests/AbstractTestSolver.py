from abc import ABC, abstractmethod
import time


class AbstractTestSolver(ABC) :
    def __init__(self, name) :
        self.name = name
        self.result = None
        self.expression = None

    @abstractmethod
    def _count_solutions(self) :
        """Count the number of solutions to the given CNF formula."""
        pass

    @abstractmethod
    def _set(self, cnf) :
        """Set the CNF formula to solve."""
        pass

    @abstractmethod
    def _solve(self) :
        """Solve the given CNF formula."""
        pass


    def benchmark(self, cnf) :
        """Measure time taken to solve the problem."""
        start_time = time.time()
        self._set(cnf)
        self._solve()
        return self._count_solutions(), time.time() - start_time
