import pandas as pd
import os
from Common.ColorCodes import *
from Tests.SATProblemGenerator import SATProblemGenerator
from Tests.TestBlastSolver import TestBlastSolverTest as TestBlastSolver
from Tests.TestPyEDASolver import TestPyEDASolverTest as TestPyEDASolver
from Tests.TestPySATSolver import TestPySATSolverTest as TestPySATSolver
from Tests.TestSymPySolver import TestSymPySolverTest as TestSymPySolver

# Maximum allowed time threshold per solver
TIME_THRESHOLD = 20  # seconds
max_times = {}  # Dictionary to track the max solving time for each solver individually

def solve_and_record(solver, cnf, test_id, num_vars, clause_size, num_clauses, results):
    """Runs solver, measures time, and returns results"""
    global max_times
    name = solver.__class__.__name__

    def append_result(true_results=None, solving_time=None):
        results.append({
            "Test ID": test_id,
            "Solver": name,
            "Variables": num_vars,
            "Clause Size": clause_size,
            "Clauses": num_clauses,
            "Solving Time (s)": solving_time,
            "Solutions Found": true_results
        })

    # Skip solver if its previous test with the same variable count exceeded the time threshold
    if name in max_times and max_times[name] > TIME_THRESHOLD:
        print(f"{RED}[WARNING] Skipping {name} for Test {test_id} due to previous excessive runtime.{RESET}")
        append_result()
        return

    print(f"{YELLOW}[DEBUG] Running {name} on Test {test_id} ({num_vars} vars, {num_clauses} clauses){RESET}")

    result, solving = solver.benchmark(cnf)

    print(f"{GREEN}[INFO] {name} completed Test {test_id} in {solving:.4f} seconds. Solutions found: {result}{RESET}")

    # Update max time for the specific solver and variable count
    max_times[name] = solving
    append_result(result, solving)

# Test configuration
pg = SATProblemGenerator()
variable_range = range(10, 26)  # Variables from 10 to 20
num_tests_per_case = 10  # 10 tests per case
clause_to_variable_ratio = 10  # 10 clauses per variable

# List of solvers to test
solvers = [TestBlastSolverTest, TestPySATSolverTest, TestSymPySolverTest, TestPyEDASolverTest]
results = []

# # Test BlastSolver for variable range 20 to 32
# variable_range = range(24, 33)
# num_tests_per_case = 1
# solvers = [TestBlastSolver]
# clause_to_variable_ratio = 4

# Generating and running test cases
test_id = 1
total_tests = len(variable_range) * num_tests_per_case * len(solvers)
completed_tests = 0

print(f"{CYAN}[INFO] Starting tests: {total_tests} total cases to run.{RESET}")

for num_vars in variable_range:
        test_cases = pg.generate_test_suite(
            num_tests=num_tests_per_case,
            variable_range=(num_vars, num_vars),
            clause_size_range=(num_vars, num_vars),
            clause_to_variable_ratio=clause_to_variable_ratio
        )

        for cnf, num_vars, clause_size, num_clauses in test_cases:
            print(f"{BLUE}[INFO] Running Test {test_id}: {num_vars} variables, {num_clauses} clauses, {num_vars} literals{RESET}")

            for solver_class in solvers:
                solver = solver_class()
                solve_and_record(solver, cnf, test_id, num_vars, clause_size, num_clauses, results)
                completed_tests += 1
                print(f"{MAGENTA}[DEBUG] Progress: {completed_tests}/{total_tests} tests completed.{RESET}")
            test_id += 1

# Creating DataFrame and saving to CSV
df = pd.DataFrame(results)
output_dir = "Tests"
output_file = os.path.join(output_dir, "results.csv")

os.makedirs(output_dir, exist_ok=True)
df.to_csv(output_file, index=False)

print(f"{GREEN}[INFO] All tests completed. Results saved to {output_file}{RESET}")
