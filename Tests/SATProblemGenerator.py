import random
from pysat.formula import CNF


class SATProblemGenerator :
    """
    Class responsible for generating random k-SAT problems in Conjunctive Normal Form (CNF).
    This class ensures reproducibility of test cases by setting a random seed.
    """

    def __init__(self, random_seed = 42) :
        """
        Initializes the SAT problem generator with a given seed for reproducibility.

        :param random_seed: Integer seed for random number generation.
        """
        if not isinstance(random_seed, int) :
            raise ValueError("random_seed must be an integer.")

        self.random_seed = random_seed
        random.seed(random_seed)

    @staticmethod
    def generate_random_cnf(num_variables, num_clauses, clause_size) :
        """
        Generates a random k-SAT problem in CNF format.

        :param num_variables: Number of boolean variables (must be >= 1).
        :param num_clauses: Number of clauses in the CNF formula (must be >= 1).
        :param clause_size: Number of literals per clause (1 <= clause_size <= num_variables).
        :return: A CNF formula generated using pysat.
        """
        if not isinstance(num_variables, int) or num_variables < 1 :
            raise ValueError(f"num_variables ({num_variables}) must be a positive integer (>= 1).")
        if not isinstance(num_clauses, int) or num_clauses < 1 :
            raise ValueError(f"num_clauses ({num_clauses}) must be a positive integer (>= 1).")
        if not isinstance(clause_size, int) or clause_size < 1 :
            raise ValueError(f"clause_size ({clause_size}) must be an integer in range 1 to num_variables ({num_variables}).")

        clause_size = min(clause_size, num_variables)  # Ensure clause_size <= num_variables

        clauses = []
        for _ in range(num_clauses) :
            # Select `clause_size` distinct variables randomly
            selected_vars = random.sample(range(1, num_variables + 1), clause_size)
            # Randomly negate variables in the clause
            clause = [var if random.choice([True, False]) else -var for var in selected_vars]
            clauses.append(clause)

        return CNF(from_clauses = clauses)

    def generate_test_suite(self, num_tests, variable_range, clause_size_range, clause_to_variable_ratio) :
        """
        Generates multiple test cases for benchmarking solvers.

        :param num_tests: Number of test cases to generate (must be >= 1).
        :param variable_range: Tuple (min_vars, max_vars), where min_vars >= 1 and min_vars <= max_vars.
        :param clause_size_range: Tuple (min_k, max_k), where 1 <= min_k <= max_k <= max_vars.
        :param clause_to_variable_ratio: Ratio defining number of clauses relative to variables (must be > 0).
        :return: List of generated test cases as tuples (CNF formula, num_variables, clause_size, num_clauses).
        """

        # Validate num_tests
        if not isinstance(num_tests, int) or num_tests < 1 :
            raise ValueError("num_tests must be a positive integer (>= 1).")

        # Validate variable_range
        if (not isinstance(variable_range, tuple) or len(variable_range) != 2 or not all(
            isinstance(v, int) for v in variable_range) or variable_range[0] < 1 or variable_range[0] > variable_range[
            1]) :
            raise ValueError(
                "variable_range must be a tuple (min_vars, max_vars) with min_vars >= 1 and min_vars <= max_vars.")

        min_vars, max_vars = variable_range

        # Validate clause_to_variable_ratio
        if not isinstance(clause_to_variable_ratio, (int, float)) or clause_to_variable_ratio <= 0 :
            raise ValueError("clause_to_variable_ratio must be a positive number (float or int).")

        test_cases = []
        for _ in range(num_tests) :
            num_variables = random.randint(*variable_range)  # Randomly select number of variables
            clause_size = random.randint(*clause_size_range)  # Randomly select clause size (k)
            num_clauses = int(num_variables * clause_to_variable_ratio)  # Compute number of clauses

            cnf_formula = self.generate_random_cnf(num_variables, num_clauses, clause_size)
            test_cases.append((cnf_formula, num_variables, clause_size, num_clauses))

        return test_cases
