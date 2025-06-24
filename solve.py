import argparse
from IPython.display import display
from copy import deepcopy
from Modules.Tree.LogicTree import LogicTree
from Modules.Solvers.OtaSolver import OtaSolver
from Modules.Solvers.BlastSolver import BlastSolver
from Common.ColorCodes import *
import pandas as pd

def solve_using_ota_solver(expression):
    logic_tree = LogicTree(expression, recognize_variables=False)
    if logic_tree.expression_errors:
        for error in logic_tree.expression_errors:
            print(error)
    else:
        logic_tree.visualize_tree().render('logic_tree', cleanup = True, view = True)

        print('\n\nSolving using OtaSolver')
        solver = OtaSolver()
        solver.solve(deepcopy(logic_tree)).print_time().print_ota_solution().print_ota_statistics()
        if solver.is_ota_tautology():
            print("🟢🟢🟢🟢 O T A   T  A  U  T  O  L  O  G  Y 🟢🟢🟢🟢")
        elif solver.is_ota_contradiction():
            print("🔴🔴🔴🔴 O T A   C O N T R A D I C T I O N 🔴🔴🔴🔴")
        elif solver.solution:
            df = pd.DataFrame(list(logic_tree.get_variable_mapping().items()),
                              columns=['Binary Algebra Variable', 'Propositional Variable'])
            print(df)
            #print(solver.solution.get_html_table())
            display(solver.get_true_results())

def solve_using_blast_bit_solver(expression):
    logic_tree = LogicTree(expression = expression, recognize_variables = True)
    logic_tree.print_tree()
    if logic_tree.expression_errors:
        for error in logic_tree.expression_errors:
            print(error)
    else:
        print('\n\nSolving using BlastSolver')
        solver = BlastSolver()
        solver.create_ota = True
        solver.solve(deepcopy(logic_tree)).print_time().print_ota_solution().print_bit_statistics()
        if solver.is_bit_tautology():
            print("🟢🟢🟢🟢 B I T   T  A  U  T  O  L  O  G  Y 🟢🟢🟢🟢")
        elif solver.is_bit_contradiction():
            print("🔴🔴🔴🔴 B I T   C O N T R A D I C T I O N 🔴🔴🔴🔴")
        elif solver.solution:
            display(solver.get_true_results())
            pass


import argparse
from Modules.Tree.LogicTree import LogicTree

if __name__ == "__main__" :
    parser = argparse.ArgumentParser(
        description = "Solve logical expressions with OTA and BlastBit solvers."
    )

    parser.add_argument(
        'expression',
        type = str,
        help = 'Logical expression to solve (e.g., "(a1 & ~a0) | a2")'
    )

    parser.add_argument(
        '--solver',
        '-s',
        choices = ['ota', 'blast', 'both'],
        default = 'both',
        help = 'Choose solver: ota, blast, or both (default: both)'
    )

    args = parser.parse_args()
    expression = args.expression
    solver_choice = args.solver

    print(f"{BG_GREEN}{WHITE}Solving logical expression:{RESET} {expression}")

    if solver_choice in ['ota', 'both'] :
        print(f'\n{BG_BLUE}{WHITE} OTA Solver {RESET}')
        solve_using_ota_solver(expression)

    if solver_choice in ['blast', 'both'] :
        print(f'\n{BG_MAGENTA}{WHITE} Blast Solver {RESET}')
        solve_using_blast_bit_solver(expression)
