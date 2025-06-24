import re
import numpy as np
import streamlit as st
import plotly.graph_objects as go
import pandas as pd
from Modules.Solvers.BlastSolver import BlastSolver
from Modules.Solvers.OtaSolver import OtaSolver
from Modules.Tree.LogicTree import LogicTree
from Data.Tautologies import all_tautologies
from copy import deepcopy
from languages import LANGUAGES as l
from concurrent.futures import ThreadPoolExecutor, TimeoutError


class LogicSolverApp:
    """
    Application for solving logical expressions using OTA and BlastBit solvers.
    """

    def __init__(self):
        """
        Initialize the application with default language and page configuration.
        """
        self.timeout = 10
        self.solver_selection = None
        self.lang_code = st.session_state.get("lang_code", "en")
        self.t = self.get_translations(self.lang_code)
        self.execution_times = {
            "OTASolver": 0,
            "BlastSolver": 0,
        }
        self.setup_page_configuration()

    @staticmethod
    def setup_page_configuration():
        """
        Configure the Streamlit page layout and title.
        """
        st.set_page_config(
            page_title="Logic BlastSolver App",
            layout="wide",
            initial_sidebar_state="collapsed"
        )

    @staticmethod
    def get_translations(lang):
        """
        Retrieve translations for the given language.

        :param lang: Language code (e.g., 'pl', 'en').
        :return: Translations dictionary for the given language.
        """
        return l.get(lang, l["pl"])

    def render_html_statistics(self, statistics):
        """
        Generate HTML for displaying statistics.

        :param statistics: Dictionary containing statistical data.
        :return: HTML string for statistics.
        """
        return f'''
        <div style="background-color: #e5bf00; color: black; font-size: 1.2em; border-radius: 10px; text-align: center; padding: 10px;">
            {self.t['statistics_found']} <strong>{statistics['Total']} {self.t['statistics_results']}</strong>: 
            <strong style="color: green;">{statistics['True']} x {self.t['true_results']}</strong> 
            {self.t['and']} <strong style="color: red;">{statistics['False']} x {self.t['false_results']}</strong>.
        </div>
        '''

    def display_logic_tree(self, logic_tree):
        """
        Display the logic tree visualization using Graphviz.

        :param logic_tree: Instance of LogicTree.
        """
        try:
            with st.expander("Logic tree visualization"):
                st.image(logic_tree.visualize_tree().pipe(format = "png"))
                #st.graphviz_chart(logic_tree.visualize_tree().source)
        except Exception as e:
            st.error(self.t['logic_tree_error'] + str(e))

    def display_results(self, solver):
        col1, col2 = st.columns(2)
        results = solver.get_true_results()

        def print_results(header, result):
            st.subheader(header)
            st.dataframe(results[results['Result'] == result], use_container_width = True)

        with col1:
            print_results(self.t["true_results"], 1)
        with col2:
            print_results(self.t["false_results"], 0)

    def display_execution_time(self, solver):
        st.write(f'{solver.__class__.__name__} {self.t["solved_in"]} {solver.execution_time * 1000:.4f} ms')

    def display_statistics(self, solver):
        if isinstance(solver, OtaSolver):
            statistics = solver.get_ota_statistics()
        elif isinstance(solver, BlastSolver):
            statistics = solver.get_bit_statistics()
        else:
            st.error(self.t["error"])
            return

        if statistics:
            st.markdown(self.render_html_statistics(statistics), unsafe_allow_html = True)
        else:
            st.error(self.t["statistics_not_available"])

    @staticmethod
    def display_new_section(header):
        st.divider()
        st.subheader(header)

    def solve_expression(self, expression):
        """
        Solve a given logical expression and display results.

        :param expression: Logical expression to solve.
        """
        try:
            logic_tree = LogicTree(expression=expression)

            if logic_tree.expression_errors:
                for error in logic_tree.expression_errors:
                    st.error(self.t['logic_tree_error'] + error)
                return

            self.display_new_section(self.t["logic_tree"])
            print(logic_tree)
            self.display_logic_tree(logic_tree)

            # Check if number of variables is below 10 to display the OTA Function section
            variable_count = len(logic_tree.get_variable_mapping())
            if variable_count <= 10 :
                self.display_new_section("OTA Function")
                ota_expander = st.expander(f"OTA Function Details ({variable_count} variables)")

                # Solve using OTASolver
                if self.solver_selection.get("OTASolver"):
                    with st.spinner(self.t["solving"]) :
                        self.solve_with_solver(OtaSolver, logic_tree, self.t["ota_solver"], ota_expander = ota_expander)


            # Solve using BlastSolver
            if self.solver_selection.get("BlastSolver") :
                with st.spinner(f'{self.t["solving"]} BlastSolver') :
                    self.solve_with_solver(BlastSolver, logic_tree, self.t["blast_solver"], create_ota=True)

            self.display_new_section('Time comparison')
            self.plot_execution_time()

        except Exception as e:
            st.exception(e)

    @staticmethod
    def display_latex_equation(solver: OtaSolver, max_length = 255):
        if not isinstance(solver, OtaSolver):
            return

        expression = re.sub(r"a_(\d+)", r"a_{\1}", solver.solution.get_equation())

        # Define colors for variables (keys should match the format `a_{0}`)
        variable_colors = {'a_{0}': '#00b050', 'a_{1}': '#0088ff', 'a_{2}': '#ffaa44', 'a_{3}': '#bb55ff', 'a_{4}': '#ff0000'}

        # Function to apply color formatting
        def color_variable(match):
            var = match.group(0)  # Full variable match (e.g., a_{0})
            color = variable_colors.get(var, "#BBBBBB")[1:]  # Remove '#' from color code
            return rf'\textcolor{{{color}}}{{{var}}}'

        # Apply coloring to variables
        expression = re.sub(r'(a_\{\d+\})', color_variable, expression)

        # Split expression into tokens and wrap lines
        def strip_latex_content(token) :
            """
            Strips LaTeX formatting from a token for length measurement.

            :param token: Token to clean.
            :return: Token without LaTeX commands and brackets.
            """
            return re.sub(r'\\textcolor\{[^\}]+\}|\{|\}', '', token)

        # Split expression into tokens and wrap lines
        split_expression = []
        current_line = ""
        for token in re.split(r'(\s?\+\s?|\s?-\s?|\*|/)', expression) :
            stripped_token = strip_latex_content(token).strip()
            if len(strip_latex_content(current_line)) + len(stripped_token) > max_length :
                if current_line.strip() :
                    split_expression.append(current_line.strip() + r" \\")
                current_line = token
            else :
                current_line += f" {token}"

        if current_line.strip() :
            split_expression.append(current_line.strip())

        # Combine split lines into a single LaTeX expression
        wrapped_expression = " ".join(split_expression)

        # Display LaTeX in Streamlit
        st.latex(wrapped_expression)

    @staticmethod
    def get_ota_table(bn: np.ndarray, tn: np.ndarray, max_width: int = 50, max_columns: int = 32) -> str :
        """
        Generates an HTML table for bn and tn values.

        :param bn: The bn array.
        :type bn: np.ndarray
        :param tn: The tn array.
        :type tn: np.ndarray
        :param max_width: Maximum width for table columns.
        :type max_width: int
        :param max_columns: Maximum number of columns per row.
        :type max_columns: int
        :return: HTML string for the table.
        :rtype: str
        """

        base_styles = {"background_color" : {"non_zero" : "#00AAEE",  # Light Blue
            "zero" : "#555555",  # Dark Gray
            "positive" : "#03AA00",  # Green
            "negative" : "#FF00FF",  # Magenta
            "1" : "#FFCC00",  # Light Yellow
            "-1" : "#FF0000",  # Red
            "default" : "#CCCCCC"  # Light Gray
        }, "text_color" : {"default" : "#FFFFFF",  # Default Text Color
            "1" : "#000000",  # Black for Light Yellow Background
            "default_dark" : "#000000"  # For light gray
        }}

        row_base_style = f'max-width:{max_width}px; width:{max_width}px; overflow:hidden;'

        def get_style(value, row_type) :
            bg_color = base_styles["background_color"]["non_zero"] if row_type == "bn" and value != 0 else \
            base_styles["background_color"]["zero"]
            text_color = base_styles["text_color"]["default"]
            if row_type == "tn" :
                if value == 1 :
                    bg_color = base_styles["background_color"]["1"]
                    text_color = base_styles["text_color"]["1"]
                elif value > 1 :
                    bg_color = base_styles["background_color"]["positive"]
                elif value == -1 :
                    bg_color = base_styles["background_color"]["-1"]
                elif value < -1 :
                    bg_color = base_styles["background_color"]["negative"]
                elif value == 0 :
                    bg_color = base_styles["background_color"]["zero"]
                else :
                    bg_color = base_styles["background_color"]["default"]
                    text_color = base_styles["text_color"]["default_dark"]

            return f'background-color:{bg_color}; color:{text_color};'

        def format_value(value: int, row_type: str) -> str :
            style = get_style(value, row_type)
            return f'<td style="{row_base_style} text-overflow:ellipsis; white-space:nowrap; {style}">{value}</td>'

        def generate_row(label: str, data: np.ndarray, row_type: str, start: int, end: int) -> str :
            return (
                    f'<tr><td style="{row_base_style}">{label}</td>' + ''.join(
                format_value(value, row_type) for value in data[start :end]) + '</tr>')

        total_columns = len(bn)
        rows = (total_columns + max_columns - 1) // max_columns  # Calculate the number of rows needed
        html = ""
        for row_idx in range(rows) :
            start_idx = row_idx * max_columns
            end_idx = min(start_idx + max_columns, total_columns)

            # Start table
            html += '<table style="border-collapse: collapse; width: auto; text-align: center; table-layout: fixed; margin-bottom: 5px;">'

            # Header row
            html += f'<thead style="background-color: #555555; color: #00AAEE;"><tr><th style="{row_base_style}">n:</th>'
            html += ''.join(f'<th style="{row_base_style}">{i}</th>' for i in range(start_idx, end_idx))
            html += '</tr></thead>'

            # `bn` and `tn` rows
            html += generate_row('bn:', bn, 'bn', start_idx, end_idx)
            html += generate_row('tn:', tn, 'tn', start_idx, end_idx)

            # End table
            html += '</table>'

        return html

    def solve_with_solver(self, solver_class, logic_tree, header, ota_expander=None, **solver_kwargs):
        """
        Solve the logical expression using a specific solver.

        :param ota_expander: Streamlit expander for displaying OTA function details.
        :param solver_class: Class of the solver to use.
        :param logic_tree: LogicTree instance of the expression.
        :param header: Header for the solver section.
        :param solver_kwargs: Additional keyword arguments for the solver.
        """
        import time
        start_time = time.time()
        self.display_new_section(header)
        solver = solver_class(**solver_kwargs)
        # Execute solver with timeout
        with ThreadPoolExecutor() as executor :
            future = executor.submit(solver.solve, deepcopy(logic_tree))
            try :
                future.result(timeout = self.timeout)
            except TimeoutError :
                solver.solution = None
                st.error(self.t["timeout_error"].format(timeout = self.timeout))
                return  # Exit if timeout occurs
        print(f'Solved in {time.time() - start_time:.4f} seconds')
        if isinstance(solver, OtaSolver):
            self.execution_times["OTASolver"] = solver.execution_time
        elif isinstance(solver, BlastSolver):
            self.execution_times["BlastSolver"] = solver.execution_time

        self.display_execution_time(solver)

        if isinstance(solver, OtaSolver) :
            # Display OTA Function details in the expander if applicable
            if solver.solution is not None and ota_expander is not None :
                with ota_expander :
                    self.display_latex_equation(solver)
                    st.markdown(self.get_ota_table(solver.solution.bn, solver.solution.tn), unsafe_allow_html = True)

                    mapping_dict = logic_tree.get_variable_mapping()
                    if len(mapping_dict) > 0:
                        st.write('Mapping of propositional variables to binary algebra variables:')

                        # Retrieve the variable mapping
                        variable_mapping = pd.DataFrame(list(mapping_dict.items()),
                            columns = ['Binary Algebra Variable', 'Propositional Variable'])

                        # Transpose the DataFrame
                        variable_mapping = variable_mapping.T

                        # Reset column names after transposing
                        variable_mapping.columns = range(variable_mapping.shape[1])

                        # Define a function to highlight mismatched cells
                        def highlight_mismatched_cells(row) :
                            if row['Binary Algebra Variable'] != row['Propositional Variable'] :
                                return 'background-color: #FFAAAA; color: #000000;'  # Light red background
                            return ''

                        # Apply conditional formatting using `Styler`
                        styled_df = variable_mapping.style.apply(
                            lambda col : [highlight_mismatched_cells( col) for _ in variable_mapping.index],
                            axis = 0)

                        # Display the styled DataFrame
                        st.dataframe(styled_df)


        if ((isinstance(solver, OtaSolver) and solver.is_ota_tautology())
                or (isinstance(solver, BlastSolver) and solver.is_bit_tautology())):
            st.success(self.t["tautology"])
        elif ((isinstance(solver, OtaSolver) and solver.is_ota_contradiction())
              or (isinstance(solver, BlastSolver) and solver.is_bit_contradiction())):
            st.error(self.t["contradiction"])
        else:
            self.display_statistics(solver)
            with st.expander("Solution Details"):
                self.display_results(solver)

    def setup_sidebar(self):
        """
        Set up the sidebar for language selection.
        """
        with st.sidebar:
            col1, col2 = st.columns(2)
            with col1:
                if st.button("🇵🇱 Polski"):
                    self.lang_code = "pl"
            with col2:
                if st.button("🇬🇧 English"):
                    self.lang_code = "en"

            st.session_state["lang_code"] = self.lang_code
            self.t = self.get_translations(self.lang_code)

            st.divider()

            st.write(self.t["solver_selection"])
            self.solver_selection = {
                "OTASolver": st.checkbox("OTASolver", value = True),
                "BlastSolver": st.checkbox("BlastSolver", value = True),
            }

            st.divider()

            # Add timeout slider
            st.write(self.t["timeout_setting"])
            self.timeout = st.slider(self.t["timeout_label"], min_value = 1, max_value = 30, value = self.timeout)

    def plot_execution_time(self):
        self.display_new_section("Logic Solver App - Execution Times")
        st.write("Below is a chart showing the execution times for each solver:")
        data = {k: v*1000 for k, v in self.execution_times.items() if v > 0}
        y = list(data.values())
        fig = go.Figure(data = [go.Bar(x = list(data.keys()), y = y, text = [f"{time:.4f} ms" for time in y])])
        fig.update_layout(title = "Execution Times by Solver", xaxis_title = "Solver",
                          yaxis_title = "Execution Time (ms)", template = "plotly_dark")
        st.plotly_chart(fig)

    def run(self):
        """
        Main entry point for running the application.
        """
        self.setup_sidebar()

        st.title(self.t["title"])
        st.write(self.t["description"])

        # Split layout into two columns
        col1, col2 = st.columns(2)

        with col1 :
            user_expression = st.text_input(self.t["input_expression"])
            solve_button_1 = st.button(self.t["solve_button"], key = "solve1")

        with col2 :
            selected_tautology = st.selectbox(self.t["choose_tautology"],
                [self.t["none"]] + [f"{name}: {formula}" for name, formula in all_tautologies])
            solve_button_2 = st.button(self.t["solve_button"], key = "solve2")

        # Logic for solving or changing the language
        expression_to_solve = None
        if solve_button_1:
            expression_to_solve = user_expression.strip()

        if solve_button_2:
            expression_to_solve = next((formula for name, formula in all_tautologies if f"{name}: {formula}" == selected_tautology), '')

        if (solve_button_1 or solve_button_2) and len(expression_to_solve.strip()) > 0:
            self.solve_expression(expression_to_solve)