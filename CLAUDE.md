# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this is

BlastApp solves propositional logic formulas by computing **all** satisfying assignments at once (no truth-table
enumeration, no SAT search). Two engines implement the same algebra contract, `PropositionAlgebra`:

- **OTA** (`OtaAlgebra`) — algebraic. Represents a formula as an *OTA function*: a `tn` coefficient vector over
  `2^n` terms with a parallel `bn` vector of truth values. Operations are arithmetic (`*`, `-`, `**`) on numpy
  arrays. Practical up to 10 variables — it allocates `2^n` arrays per subformula.
- **Blast** (`BitAlgebra`) — bitwise. Represents a formula as a single Python arbitrary-precision integer whose
  bit `i` is the result for assignment `i`. Operations are `&`, `|`, `^`, `~` on that integer. Goes much further.

Both are exposed through a Streamlit GUI, a CLI, and a benchmark harness comparing against PySAT/SymPy/PyEDA.

## Commands

Dependencies are uv-managed (`pyproject.toml` + `uv.lock`); there is no `requirements.txt`.

```bash
uv sync                                        # create/refresh .venv (Python >= 3.13) + dev tools
uv run streamlit run app.py                    # GUI at http://localhost:8501
uv run python solve.py "(a1 & ~a0) | a2"       # CLI, both solvers
uv run python solve.py "p => q" -s blast       # one solver: ota | blast | both
uv run python -m blastapp.benchmarks.main      # benchmark suite (see caveats below)
```

Quality gate — all four must pass before any commit:

```bash
uv run pytest                                  # unit, oracle, layering, GUI smoke; ~8 s
uv run ruff check . && uv run ruff format --check .
uv run mypy                                    # strict, scoped to src/blastapp + tests
```

### Testing

`tests/` is the real pytest suite. The performance harness lives in `src/blastapp/benchmarks/`; the top-level
`benchmarks/` directory now only holds outputs (`results/`, gitignored) and the archived earlier run.

**`tests/reference_evaluator.py` is the oracle.** It evaluates a formula naively over all `2^n` assignments straight
off the AST, using no solver code at all. Both engines are checked against it in
`tests/domain/test_engines_agree.py` and `tests/domain/test_algebra.py`. **When you change solving, check against
the evaluator — never against what the code currently prints.** Agreement between two engines that share a bug
proves nothing.

`tests/domain/test_known_bugs.py` collects the cases the solver has been known to get wrong; they exist to stop
those from coming back. `tests/test_layering.py` parses the domain's imports and fails if anything there reaches
for pandas, streamlit, graphviz, plotly or pysat.

**Beware: macOS filesystems are case-insensitive.** `tests/` and `Tests/` are the same directory, so a capitalised
variant of an existing name silently merges into it instead of creating something new.

### Environment caveats

- **Graphviz is a system package, not a Python dependency** — `uv sync` does not install it. Both the CLI and the
  GUI catch `ExecutableNotFound`: the CLI prints a note and carries on, the GUI falls back to `st.graphviz_chart`
  (browser-side, and less reliable). The GUI also always prints the tree as text, so the tree is visible either
  way. Solving itself never needs Graphviz.
- **PyEDA segfaults on this machine.** `satisfy_all()` in pyeda 0.29.0 kills the process with SIGSEGV (exit 139),
  independent of this repo's code. A segfault cannot be caught, so `PyEdaAdapter` is deliberately absent from
  `DEFAULT_ADAPTERS` in `blastapp/benchmarks/main.py`; adding it back aborts the whole run.

## Architecture

### Pipeline

```
text ─ parse_formula ─→ Formula (frozen AST) ─┬─ FormulaEvaluator + algebra ─→ TruthTable ─→ SolverResult
                                              └─ presentation: tree / graph / expression
```

`Formula` is the boundary. Everything downstream works on frozen dataclasses; the parser is one entry point,
not a thing you hold on to.

**`domain/expressions/parsing.py`** — `parse_formula(text, registry=None) -> Formula` is the only entry point.
It validates (`validation.py`), normalizes symbols to keywords (`normalization.py`, `~ ⌐ ! → NOT`, `& ∧ /\ → AND`,
`| ∨ \/ → OR`, `^ → XOR`, `=> ==> → IMP`, `<=> → EQ`), splits recursively on the lowest-precedence operator, and
pulls negations into the leaves (`rewriting.py`). `parse_sequential(text)` is the same with positions handed out
in first-occurrence order.

It builds the frozen AST **directly**. Associative operators are flattened by building a new operand tuple —
the pre-refactor parser did it by taking over the left node's children and returning that node as the parent,
so one object could appear in the tree in two roles.

Bit positions come from a registry (`domain/expressions/variables.py`), chosen by which entry point you call:
- `parse_formula` → `IndexedVariableRegistry`. Every `aN` in the text is *reserved* at position `N` before
  parsing starts; any other name takes the **first free** position. Reserving up front is what stops `p` in
  `p & a0` from taking position 0 out from under `a0`.
- `parse_sequential` → `SequentialVariableRegistry`. Positions go in first-occurrence order and the digit is
  ignored, so `a5 & a3` becomes positions 0 and 1.

The position is used arithmetically as `1 << position`, so two names sharing one position are two variables fused
into one — that was the alias-collision bug. `VariableMap` refuses such a map in its constructor.

`domain/expressions/clauses.formula_from_clauses(clauses)` builds a formula from DIMACS-style clauses (literal
`n` → variable at position `|n|-1`) without going near the parser. The old path rendered the CNF back into a
string and re-parsed it.

Precedence is the classical one, `~ > & > XOR > | > => > <=>`, and every operator binds at its own level — a test
asserts there are no ties, because a tie means the *position* of an operator in the text decides the root instead of
its binding strength. `=>` stays right-associative: it is the only non-associative operator (for `p=q=r=F`,
`(p=>q)=>r` is F while `p=>(q=>r)` is T), so for `&`, `|`, `XOR` and `<=>` the direction is invisible in results.

**Parse failures raise; they are never collected.** `src/blastapp/domain/expressions/errors.py` defines
`ExpressionError` and four subtypes — `EmptyExpressionError`, `UnbalancedParenthesesError`,
`InvalidCharacterError`, `MalformedExpressionError`. Every one carries the offending text in `.expression`, so the
presentation layer can build its own message instead of forwarding raw technical English. There is no error list
and no partial result: `parse_formula` returns a complete `Formula` or raises.

`reduce_negations(node)` returns the node that should stand in that position, so the rule applies at the root as
well as inside: `~a0` is a negated `VariableNode`, not `NOT` over a variable. Double negation is *not* simplified —
`~~a0` stays `NOT` over a negated variable.

**`src/blastapp/domain/operators.py` is the single operator table.** `OPERATORS` carries syntax, aliases,
precedence and arity for every operator; the scanner, the normalizer, the expression writer and the graph styling
all derive from it. Adding or changing an operator starts there. Visual styling stays out of it deliberately — it
changes for a different reason and lives in `presentation/theme.py`.

The AST is three frozen dataclasses (`VariableNode`, `ConstantNode`, `OperationNode`) that enforce arity at
construction. Deliberately absent: **no field for the solver's result** (it would make solving mutate the tree and
force every caller to pass a copy) and **no link to the parent** (it would put cycles into copying, and rendering
passes the parent down the recursion anyway). Do not add either.

### Result types — `src/blastapp/domain/solving/`

Nothing above the engines asks which one ran. `SolverResult` carries `engine`, a `TruthTable`, the `VariableMap`,
the duration and an optional OTA function; `SolutionStatistics.of(table)` derives counts, tautology and
contradiction in one place. If you find yourself branching on the engine in the GUI or CLI, the missing piece
belongs on `SolverResult`, not in an `isinstance`.

`TruthTable` is one integer: bit `i` is the result for assignment `i`. Both engines truncate their result to the
variables the formula actually depends on (a tautology collapses to zero variables), so the adapter always calls
`widened_to(variable_count)` before handing it over — an added variable doubles the rows without changing any
result.

`engines.py` holds the registry: `ENGINES` is an explicit tuple, no auto-registration. `SolverEngine.accepts(n)`
replaces the bare `variable_count <= 10` that used to sit nested in the GUI — and the GUI now says why it skipped
an engine instead of silently not running it. Adding a third engine means one entry there; the CLI loop, the
sidebar checkboxes and the timing chart all iterate `ENGINES`.



### Solving — composition, not inheritance

`PropositionAlgebra[P]` (`domain/solving/algebra.py`) is the contract: `constant`, `variable`,
`negation`, `conjunction`, `disjunction`, `equivalence`, `implication`, `to_truth_table`. Eight methods, all
needed by both implementations — none raises `NotImplementedError`.

`FormulaEvaluator` walks the AST once, for every algebra; `LogicSolver` times it and packs a `SolverResult`.
`OtaAlgebra` and `BitAlgebra` are the two implementations. Solving does not mutate the formula — the result never
lands on an AST node — so the same `Formula` can go through both engines without being copied. `XOR = NOT(EQ)` is
written once, in the evaluator.

Both `_combine` implementations pick the two cheapest pending propositions first (OTA by vector length, Blast by
lowest max variable index — narrower table) so intermediates stay small. Blast additionally stops early: an AND
that reaches false, or an OR that reaches all-true, cannot be changed by the remaining operands.

**`BitAlgebra.to_truth_table` must call `add_missed_variables()` first.** A variable can drop out during
simplification (`(a0 & ~a0) | a1`), leaving the survivors on the wrong bit positions.

`with_ota_function=False` skips building the OTA function. For the bit engine that conversion costs far more
than solving — at 14 variables it is ~1.2 ms of solving against ~80 ms of conversion — so the benchmark adapter
turns it off.

### Representations

**`domain/representations/ota_function.py` (`OtaFunction`)** — `from_bn` / `from_tn` construct from either
vector and derive the other; `negated()` returns a new object rather than rewriting `tn` in place. Coefficients
are `int64`: with `int8` a XOR chain overflowed from six variables up, and numpy 2.x raises rather than wrapping.
The `tn ↔ bn` conversions memoise their recursion — without it, converting a 14-variable result took over two
seconds and grew ~3× per variable. Multiplication uses sparse triangular masks from
`domain/representations/ns_squares.py`, injected into `OtaAlgebra` rather than cached on the left operand.

Rendering lives in `presentation/ota_render.py`: `expression_text`, `equation_text`, `ansi_table`, `html_table`.

**`domain/representations/bit_table.py` (`BitTable`)** — the whole truth table is one big int, with `variables`
an index-sorted list of slots. `_expand_bit_groups` / `_expand_variables` duplicate the bit pattern group-wise when
a variable is added, doubling the table's width.

**`BitTable` is deliberately mutable, and that is the one exception to rule #22 here.** Adding a variable doubles
the table; at 25 variables it is a ~4 MB integer, so copying both operands per operation would double memory
traffic in the hot loop. The terms: commands are named for their effect and return `None` (`align_with`,
`apply_in_place`, `negate_in_place`); **the operand passed to `apply_in_place` is consumed** — `align_with` grows
it — so it must not be reused; and `BitTable` never leaves `domain/solving/bit_algebra.py`, which hands out an
immutable `TruthTable` instead. Immutable boundaries, mutable core.

### Streamlit app — `src/blastapp/presentation/web/`

`app.py` at the repo root is a three-line entry point. The page is composed from
`web/{app,sidebar,formula_input,solver_section,ota_section,timing_chart,solving}.py`, each a single section.
`web/app.py` loops over `ENGINES`, so a third engine needs no change here; an engine over its `variable_limit`
gets an explicit message rather than silently not running.

**The timeout is real.** `web/solving.py` runs the solve in a separate *process* and kills it on expiry. A thread
cannot give you this: a CPU-bound Python thread is not interruptible, and an executor's `with` block joins its
workers on exit, so control waits for the runaway solve regardless of what the UI reports. `ProcessPoolExecutor`
only got a public `terminate_workers()` in Python 3.14, so on 3.13 this uses `multiprocessing` directly, where
`Process.terminate()` is public API.

**`app.py` must keep its `if __name__ == "__main__":` guard.** `spawn` recreates the child by running the
parent's main file again under the name `__mp_main__`, and under `streamlit run` that file *is* `app.py` — so
without the guard every solve rebuilds the whole page in the worker, outside the Streamlit runtime. `AppTest`
cannot catch this (there the main module is the test file), which is why
`tests/presentation/test_entry_point.py` checks it directly. Everything crossing the process boundary is frozen and picklable: `Formula`
out, `SolverResult` back. Spawn costs ~250 ms per solve.

**Read the queue before joining the process.** A child cannot exit until the parent drains the pipe, so
`process.join(timeout)` placed *before* `queue.get()` blocks for the full timeout on any result large enough to
fill the pipe buffer — a 12-variable formula took 10 s and then reported a timeout. `queue.get(timeout=…)` first,
`join()` in the `finally`.

`tests/presentation/test_app_smoke.py` drives the app headlessly through `streamlit.testing.v1.AppTest` — that is
how to check a GUI change without a browser. Note that a section header is emitted *before* the engine runs, so
asserting on headers alone proves nothing about the result; assert on `dataframe`/`error` too.

Default UI language is **Polish**, defined once in `i18n/catalog.py`. It used to be ambiguous: session state
defaulted to English while the translation lookup fell back to Polish.

### Presentation layer — `src/blastapp/presentation/`

Everything the user sees is built here and *returned as data*; only the GUI and CLI call `st.*` / `print`.

| Module | Renders |
|---|---|
| `text/expression_writer.py` | formula back to symbols, **from the AST** — so it cannot drift from the input syntax |
| `text/tree_printer.py` | ASCII tree |
| `graph.py` | Graphviz `Digraph` |
| `ota_render.py` | OTA as text, equation, ANSI table, HTML table |
| `latex.py` | coloured, line-wrapped LaTeX equation |
| `html.py` | OTA coefficient table for Streamlit |
| `tables.py` | pandas frames from a `SolverResult` |
| `theme.py` | every hex colour: operator styles, variable palette, contrast |
| `ansi.py` | the 22 ANSI codes actually in use (there were 40 defined) |
| `i18n/{catalog,pl,en}.py` | UI strings; `translations(lang)` with **one** default language |
| `samples.py` | the 31 sample tautologies |

Graph node ids come from the **path in the tree**, not `id()`: frozen nodes with equal content are the same
object, so identity would merge two occurrences of one subformula into a single node.

### Benchmarks — `src/blastapp/benchmarks/`

`SolverAdapter` is one method: `count_solutions(clauses) -> int`. Timing belongs to `BenchmarkRunner`, which
returns `Measurement` records; writing the CSV and printing progress belong to `main.py`. The old contract had
three methods with the result travelling between them through per-adapter attributes.

`main.py` runs under `if __name__ == "__main__"`. The old runner was module-level code, so *importing* it started
a multi-hour run and overwrote the committed results file. Results now go to `benchmarks/results/`, which is
gitignored; `benchmarks/results-archiwum.csv` keeps the earlier run.

`SatProblemGenerator` owns a `random.Random(seed)` instead of seeding the global module — any other use of
`random` in the process used to change the generated instances.

`BlastAdapter` and **`OtaAdapter`** both exist; the OTA engine was previously absent from the comparison
entirely. Both run with `with_ota_function=False` — building the OTA function costs far more than solving and
would distort the measurement. Adapters take plain `list[list[int]]` clauses and go through
`domain/expressions/clauses.formula_from_clauses`, so **the benchmarks no longer touch the parser at all**.

The time threshold keeps the *slowest* time per solver, and a solver that crossed it stays skipped — instances
grow monotonically, so one that missed on a smaller case will not make a larger one. The old code stored the
*last* time and put the assignment after an early `return`, so a skipped solver never updated its record.

## Refactor status

The repo follows `clean_code.md` — 28 rules, the owner's own standard. **Read it before writing code here**; it is
the authority for naming, function size, SRP/SOLID, immutability and the tooling expectations below.

`src/blastapp/{domain,presentation,benchmarks}` is the destination and holds almost everything. `domain` imports
no pandas, streamlit, graphviz, plotly, pysat or ANSI — `tests/test_layering.py` enforces that by parsing imports.

**Everything lives in `src/blastapp` now.** Outside it there are only `app.py` and `solve.py` — a three-line
Streamlit entry point and the CLI — plus `benchmarks/` holding *outputs*, not code. `ruff` covers the whole repo
and `mypy --strict` covers `src/` and `tests/`, so nothing escapes the quality gate.

The package is genuinely installable: `blastapp` imports and solves from any working directory. Keep it that way —
an import reaching outside `src/` breaks the wheel while still "working" from the repo root, which is exactly the
failure that is easy to miss.

Decisions the owner has taken, worth knowing when reading the code:
- Operator precedence is the classical order, with `<=>` loosest. PyEDA orders it the other way (`=>` loosest);
  that was considered and rejected.
- The GUI timeout must genuinely interrupt — hence a separate process, not a thread.

## Conventions

- `src`-layout with a real package: every module has an `__init__.py` and imports are absolute
  (`from blastapp.domain... import ...`). No `sys.path` tricks, no dependence on the working directory.
- Docstrings are reStructuredText (`:param:` / `:type:` / `:return:`) — match that style. A one-line docstring is
  fine when the signature already says everything; spend the words on *why*, per rule #02.
- Comments state a constraint, a trade-off or a decision, **in the present tense**. No history — that is what git
  is for. "Adding a variable doubles the table, so copying both operands would double memory traffic in the hot
  loop" is useful; "this used to be a method of the parser" is not. The same goes for test docstrings: say which
  invariant the test guards, not what once broke.
- User-facing text is bilingual PL/EN. Identifiers stay English. **New** comments and docstrings are written in
  Polish per `clean_code.md` rule #02 (they explain *why*, not *what*); pre-refactor code still has English ones.
  README is Polish.
