"""Run `python -m nqueens --help` for the project commands."""

from __future__ import annotations

import argparse
import csv
import json
import platform
import sys
from importlib import metadata
from pathlib import Path

from .alternatives import solve_cp_sat, solve_cplex_cp, solve_cplex_mip, solve_gurobi
from .core import SolveResult, board_text
from .sat import ENCODINGS, solve_sat
from .summary import summarize_csv

METHODS = ("sat", "cp-sat", "cplex-mip", "cplex-cp", "gurobi")


AVAILABLE_SAT_SOLVERS = ("g3", "g4", "cd153", "m22", "cadical", "glucose3", "glucose4", "minisat")


def run_method(n: int, method: str, encoding: str, time_limit: float, solver_name: str = "g3") -> SolveResult:
    functions = {
        "sat": lambda: solve_sat(n, encoding, time_limit, solver_name),
        "cp-sat": lambda: solve_cp_sat(n, time_limit),
        "cplex-mip": lambda: solve_cplex_mip(n, time_limit),
        "cplex-cp": lambda: solve_cplex_cp(n, time_limit),
        "gurobi": lambda: solve_gurobi(n, time_limit),
    }
    result = functions[method]()
    if result.status == "SAT" and result.valid is not True:
        result.status = "ERROR"
        result.details = "Solver returned a board that failed independent validation"
    return result


def versions() -> dict[str, str]:
    data = {"python": sys.version.split()[0], "platform": platform.platform()}
    for package in ("python-sat", "ortools", "gurobipy", "docplex", "cplex"):
        try:
            data[package] = metadata.version(package)
        except metadata.PackageNotFoundError:
            data[package] = "not installed"
    return data


def main() -> int:
    parser = argparse.ArgumentParser(description="Exact N-Queens models for Assignment 1")
    sub = parser.add_subparsers(dest="command", required=True)
    solve = sub.add_parser("solve", help="Solve one board and print the answer")
    solve.add_argument("n", type=int)
    solve.add_argument("--method", choices=METHODS, default="sat")
    solve.add_argument("--encoding", choices=ENCODINGS, default="sequential")
    solve.add_argument("--solver", default="g3", help="SAT solver name (g3, g4, cd153/cadical, m22/minisat)")
    solve.add_argument("--time-limit", type=float, default=60.0)

    bench = sub.add_parser("benchmark", help="Run a reproducible comparison and write CSV")
    bench.add_argument("--sizes", type=int, nargs="+", default=[1, 2, 3, 4, 8, 16, 32])
    bench.add_argument("--methods", choices=METHODS, nargs="+", default=list(METHODS))
    bench.add_argument("--encodings", choices=ENCODINGS, nargs="+", default=["sequential"])
    bench.add_argument("--solver", default="g3", help="SAT solver name (g3, g4, cd153, m22)")
    bench.add_argument("--repeats", type=int, default=3)
    bench.add_argument("--time-limit", type=float, default=60.0)
    bench.add_argument("--output", type=Path, default=Path("results/benchmark.csv"))
    summary = sub.add_parser("summarize", help="Write median timings and status counts from benchmark CSV")
    summary.add_argument("--input", type=Path, default=Path("results/benchmark.csv"))
    summary.add_argument("--output", type=Path, default=Path("results/summary.csv"))
    sub.add_parser("info", help="Print Python, platform, and package versions")
    args = parser.parse_args()

    if args.command == "info":
        print(json.dumps(versions(), indent=2, ensure_ascii=False))
        return 0
    if args.command == "summarize":
        count = summarize_csv(args.input, args.output)
        print(f"Saved {count} groups to {args.output}")
        return 0
    if args.command == "solve":
        result = run_method(args.n, args.method, args.encoding, args.time_limit, getattr(args, "solver", "g3"))
        print(json.dumps(result.record(), indent=2, ensure_ascii=False))
        if result.columns is not None:
            print("\n" + board_text(result.columns))
        return 0 if result.status in ("SAT", "UNSAT") else 1

    if args.repeats < 1 or any(n < 1 for n in args.sizes) or args.time_limit <= 0:
        parser.error("Sizes, repeats, and time limit must be positive")
    args.output.parent.mkdir(parents=True, exist_ok=True)
    records = []
    solver_name = getattr(args, "solver", "g3")
    for n in args.sizes:
        for method in args.methods:
            encodings = args.encodings if method == "sat" else [""]
            for encoding in encodings:
                for repeat in range(1, args.repeats + 1):
                    result = run_method(n, method, encoding, args.time_limit, solver_name)
                    row = {"repeat": repeat, "sat_solver": solver_name if method == "sat" else "", **result.record()}
                    records.append(row)
                    info_enc = f"{encoding}({solver_name})" if method == "sat" else method
                    print(f"N={n:<4} {method:<10} {info_enc:<18} run={repeat} "
                          f"{result.status:<11} total={result.total_time_s:.4f}s")
                    if result.status == "UNAVAILABLE":
                        break  # Do not repeat a missing dependency or license.
    with args.output.open("w", encoding="utf-8-sig", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=list(records[0]))
        writer.writeheader()
        writer.writerows(records)
    metadata_path = args.output.with_suffix(".metadata.json")
    metadata_path.write_text(json.dumps({"versions": versions(), "sizes": args.sizes,
                                         "methods": args.methods, "encodings": args.encodings,
                                         "solver": solver_name,
                                         "repeats": args.repeats, "time_limit_s": args.time_limit},
                                        indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"Saved {len(records)} rows to {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
