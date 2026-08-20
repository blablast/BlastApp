# BlastApp — solving propositional formulas with binary logic

## What it is

**BlastApp** is an interactive GUI application (built on [Streamlit](https://streamlit.io/)) for
solving and analysing propositional sentences using **binary logic**. Two engines are implemented:
the algebraic **OTA Solver** and the bitwise **Blast Solver**, both of which find *all* satisfying
assignments of a formula at once. The application visualises syntax trees, computes the OTA
function and presents results — without ever enumerating a traditional truth table row by row.

---

## Binary logic in brief

**Binary logic** joins classical Boolean algebra (1 = TRUE, 0 = FALSE) with an algebra that
describes solutions through the OTA function. The idea is to treat 0 and 1 as integers rather than
as symbols.

### What that buys:

- **No truth tables** — every combination follows from the OTA function, computed once.
- **No need to recall logical laws** — logical operations become arithmetic ones.
- **Speed** — a formula over twenty variables is solved in a fraction of a second.

The **OTA function** encodes the result for all combinations of n variables as a sequence of
$2^n$ coefficients $t_i$. For two variables:
$\Phi = t_3\cdot a_1 a_0 + t_2\cdot a_1 + t_1\cdot a_0 + t_0$

---

## Installation and running

The application runs on **Windows**, **Linux** and **macOS**.

### Requirements:

- Python 3.13+
- [uv](https://docs.astral.sh/uv/) — package and environment manager (replaces `pip` and `venv`)
- **Graphviz** — *recommended*. The syntax tree is always shown as text, so the application works
  without it. Graphviz adds the drawing: a locally rendered PNG in the GUI, and a file written by
  `solve.py`. Without it the GUI falls back to rendering in the browser, which is less reliable.

### Installing uv:

```bash
# macOS / Linux
curl -LsSf https://astral.sh/uv/install.sh | sh

# Windows (PowerShell)
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
```

Alternatively: `brew install uv` (macOS) or `pipx install uv`.

### Installing Graphviz (recommended):

```bash
# macOS
brew install graphviz

# Linux (Debian/Ubuntu)
sudo apt install graphviz
```

On **Windows**, download the installer from [graphviz.org](https://graphviz.org/download/) and add
its `bin` directory to PATH.

To check that it worked:

```bash
dot -V          # should print a version, e.g. "dot - graphviz version 12.2.1"
```

Graphviz is a system package, not a Python dependency — `uv sync` will not install it. The Python
`graphviz` package is only a wrapper around that binary.

### Installing dependencies:

1. Change into the project directory.
2. Create the environment and install everything with one command:
    ```bash
    uv sync
    ```
   `uv` fetches the right Python version, creates `.venv` and installs exactly the versions pinned
   in `uv.lock`. There is no environment to activate by hand.

### Running:

From the project directory:

```bash
uv run streamlit run app.py
```

The application opens in a browser (by default at http://localhost:8501).

An expression can also be solved straight from the command line:

```bash
uv run python solve.py "(a1 & ~a0) | a2"
uv run python solve.py "(a1 & ~a0) | a2" --solver blast   # ota | blast | both
```

Performance comparison against external solvers:

```bash
uv run python -m blastapp.benchmarks.main
```

Results land in `benchmarks/results/results.csv`. A full run takes a long time; the range and the
number of repetitions are set through `BenchmarkSettings`.

The suite includes a **naive DPLL model counter** as a reference point. It is deliberately plain —
unit propagation plus `2^(free variables)`, no caching, no component decomposition — and it exists
to show when an engine genuinely contributes something. Reading the chart without that column is
misleading.

### Expression syntax

| Operator | Notation | Binding |
| --- | --- | --- |
| negation | `~` `⌐` `!` `NOT` | tightest |
| conjunction | `&` `∧` `/\` `AND` | |
| exclusive or | `^` `XOR` | |
| disjunction | `\|` `∨` `\/` `OR` | |
| implication | `=>` `==>` `IMP` | |
| equivalence | `<=>` `EQ` | loosest |

Precedence follows the textbook convention (`¬ > ∧ > XOR > ∨ > → > ↔`). Implication binds to the
right: `p => q => r` means `p => (q => r)`. It is the only operator whose binding direction changes
the result — the others are associative.

Variables can be named freely (`p`, `q`, `x1`). Names of the form `aN` are special: the digit sets
the bit position, so `a5` occupies position 5.

### Managing dependencies:

```bash
uv add <package>        # add a dependency (updates pyproject.toml and uv.lock)
uv remove <package>     # remove one
uv lock --upgrade       # upgrade to the newest versions
```

Dependencies are declared in `pyproject.toml`, their exact pinned versions in `uv.lock`. Both files
belong in the repository.

---

## Example

Take the expression:
(a0 AND a1) OR (a1 AND a2) OR (a2 AND a0)

For three variables the application automatically:

- shows the **syntax tree**:

  ![Syntax tree](img/screenshot_tree.png)

- computes the **OTA function** and its coefficients for every combination:

  ![OTA table](img/screenshot_ota.png)

- presents the **result tables**:

  ![Results](img/screenshot_results.png)

- compares the engines' timings (OTA / Blast):

  ![Engine comparison](img/screenshot_timing.png)

---

## For developers

### Layout

```
src/blastapp/
├── domain/          — expression parser, syntax tree, algebras and representations.
│                      Depends on no pandas, Streamlit or Graphviz.
├── presentation/    — CLI, GUI, text, LaTeX, HTML and chart rendering
└── benchmarks/      — comparison against external solvers
```

Dependencies point one way: `presentation` and `benchmarks` know `domain`, never the other way
round. `tests/test_layering.py` enforces that.

Adding a third engine means implementing `PropositionAlgebra` and one entry in `ENGINES` — the CLI,
the GUI sidebar and the timing chart all iterate the registry.

### Tests and quality

```bash
uv run pytest                                    # about 8 s
uv run ruff check . && uv run ruff format --check .
uv run mypy
```

The tests check both engines against an **independent oracle**: `tests/reference_evaluator.py`
evaluates a formula naively over all `2^n` assignments, using no solver code at all. Agreement
between two engines that share a bug would prove nothing.

The project follows the rules in `clean_code.md`.

## Author

**Błażej Strus**
  e-mail: b.strus@gmail.com
  phone: +48 501 165 889

---

## License

No license specified. If you would like to use the code, please contact the author.

---
