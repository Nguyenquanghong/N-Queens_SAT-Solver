# Assignment 1: N-Queens with SAT and exact solvers

Project for **Các vấn đề hiện đại KHMT**. The input is a positive integer `N`. The output is one valid arrangement of `N` queens, or a proof that no arrangement exists. Internal solutions use zero-based columns; CLI and CSV display one-based columns.

## Models

- **SAT / PySAT Glucose 3:** Boolean variable `x[r,c]` means a queen occupies cell `(r,c)`. Each row and column has exactly one queen. Each diagonal has at most one. The CNF builder offers `pairwise`, `sequential`, `binary`, `commander`, and `product` at-most-one encodings. At-least-one is one clause per row/column.
- **CP-SAT / OR-Tools:** one integer column variable per row; the columns, `column + row`, and `column - row` are each all-different.
- **CPLEX CP / CP Optimizer:** the same integer-variable/all-different CP model, using IBM's `docplex.cp` and a local `cpoptimizer.exe` runtime.
- **CPLEX MIP and Gurobi:** binary cell variables, row/column sums equal to one, diagonal sums at most one.

The CP and MIP models express the same feasible boards but use different variable types and constraints. Comparisons should discuss this modeling difference. The task is *feasibility*, not optimization, so there is no objective function.

Every returned board is checked independently by `validate_solution`. Status values are `SAT`, `UNSAT`, `TIMEOUT`, `UNAVAILABLE`, and `ERROR`; in particular, a timeout is never called unsatisfiable.

## Setup on Windows

Use the project folder as the terminal's current directory. One option is an isolated Python environment:

```powershell
py -3.11 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

The equivalent Conda option is:

```powershell
conda env create -f environment.yml
conda activate nqueens-btl1
```

Use **one** environment for all runs. In VS Code, choose that environment through **Python: Select Interpreter**. This folder's existing `.vscode/settings.json` prefers Conda; if using `.venv`, select its `Scripts/python.exe` manually.

For Gurobi and CPLEX MIP Python bindings:

```powershell
python -m pip install -r requirements-optional.txt
```

The optional bindings do not supply a Gurobi license. `docplex.cp` also needs IBM's separate CP Optimizer executable (`cpoptimizer.exe`). If these are absent, the corresponding command reports `UNAVAILABLE`; no comparison result is fabricated.

## Solve a board

The examples below use the `.venv` interpreter. With an activated Conda environment, replace it with `python`.

```powershell
.\.venv\Scripts\python.exe -m nqueens solve 8 --method sat --encoding sequential
.\.venv\Scripts\python.exe -m nqueens solve 8 --method cp-sat
.\.venv\Scripts\python.exe -m nqueens solve 8 --method cplex-mip
```

`N=2` and `N=3` must return `UNSAT`; `N=1` and every `N>=4` have a solution.

## Tests and experiments

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
.\.venv\Scripts\python.exe -m nqueens info
.\.venv\Scripts\python.exe -m nqueens benchmark --sizes 4 8 16 32 64 --methods sat cp-sat cplex-mip cplex-cp gurobi --encodings sequential pairwise binary commander product --repeats 3 --time-limit 60 --output results/benchmark.csv
.\.venv\Scripts\python.exe -m nqueens summarize --input results/benchmark.csv --output results/summary.csv
```

The benchmark writes a row for each run and a companion `benchmark.metadata.json` with the runtime versions and settings. `summary.csv` reports median timing **only for completed SAT/UNSAT runs** and separate counts for timeouts and unavailable tools. `build_time_s` measures model construction; `solve_time_s` measures the solve call, including SAT child-process startup; `engine_time_s` isolates SAT engine loading/solving inside that child process. `total_time_s` is build plus solve. SAT runs in a separate process because native PySAT interruption can exceed the requested limit on Windows; the process is terminated at the limit. Model-building time is measured separately and is not subject to the solver's time limit. All methods use one search worker/thread where the API supports it.

Start with small `N`, verify every status and board, then increase the sizes that fit your hardware. Record actual machine specifications, package versions, and any solver license limits in the report. Treat the included runs as development checks until you run the final benchmark protocol.

## Report mapping

The assignment asks for a scientific-paper-style LaTeX report using `\documentclass[a4paper,fleqn]{cas-sc}`. Suggested sections: Introduction; Problem Definition; SAT Encoding; MIP/CP Models; Experimental Setup; Results and Discussion; Conclusion; References; Data Availability. In Data Availability, link to a repository containing this code and the final benchmark CSV and metadata. The supplied example PDF is a writing reference, not benchmark data for N-Queens.

## Source files

- `nqueens/core.py`: problem rules and independent validation.
- `nqueens/sat.py`: CNF creation and five AMO encodings.
- `nqueens/alternatives.py`: CP-SAT, Gurobi, CPLEX MIP, CPLEX CP.
- `nqueens/__main__.py`: CLI and benchmark runner.
- `nqueens/summary.py`: aggregate benchmark CSV.
- `tests/test_nqueens.py`: solver and encoding correctness tests.

## API references

- PySAT solver API: https://pysathq.github.io/docs/html/api/solvers.html
- OR-Tools N-Queens: https://developers.google.com/optimization/cp/queens
- Gurobi Python model API: https://docs.gurobi.com/projects/optimizer/en/current/reference/python/model.html
- IBM CP N-Queens example: https://ibmdecisionoptimization.github.io/docplex-doc/cp/basic.n_queen.py.html
