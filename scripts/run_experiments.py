"""Comprehensive Benchmark Script for Assignment 1 - N-Queens:

1. Experiment 1: Compare 5 SAT Encodings (Pairwise, Sequential, Binary, Commander, Product)
   and CP-SAT (Google OR-Tools) across sizes N = 4, 8, 16, 32, 64, 128, 256.
2. Experiment 2: Compare 4 CDCL SAT Solvers (Glucose 3, Glucose 4, CaDiCaL, Minisat 2.2).
3. Export CSV results and generate scientific plots to report/figures/.
"""

import csv
import json
import os
import sys
from pathlib import Path

# Configure UTF-8 for console output on Windows
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

import matplotlib.pyplot as plt

# Add project root to sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from nqueens.sat import solve_sat, ENCODINGS
from nqueens.alternatives import solve_cp_sat


def run_encodings_experiment():
    print("=================================================================")
    print("EXPERIMENT 1: 5 SAT ENCODINGS AND CP-SAT BENCHMARK (LARGE N)")
    print("=================================================================")

    sizes = [4, 8, 16, 32, 64, 128, 256]
    encodings = ["pairwise", "sequential", "binary", "commander", "product"]
    time_limit = 45.0

    out_dir = PROJECT_ROOT / "results"
    out_dir.mkdir(parents=True, exist_ok=True)
    csv_path = out_dir / "benchmark_encodings.csv"
    if csv_path.exists():
        print(f"\n=> Loaded existing Experiment 1 results from: {csv_path}")
        with open(csv_path, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            loaded = []
            for row in reader:
                loaded.append({
                    "n": int(row["n"]),
                    "method": row["method"],
                    "encoding": row["encoding"],
                    "sat_solver": row["sat_solver"],
                    "status": row["status"],
                    "build_time_s": float(row["build_time_s"]) if row["build_time_s"] else None,
                    "solve_time_s": float(row["solve_time_s"]) if row["solve_time_s"] else None,
                    "total_time_s": float(row["total_time_s"]) if row["total_time_s"] else None,
                    "variables": int(row["variables"]) if row["variables"] else None,
                    "constraints": int(row["constraints"]) if row["constraints"] else None,
                })
            return loaded

    results = []
    for n in sizes:
        print(f"\n--- Testing Board Size N = {n} ---")

        # 1. Test 5 SAT Encodings (with Glucose 3)
        for enc in encodings:
            # Pairwise generates tens of millions of clauses at N >= 256, skipping safely
            if enc == "pairwise" and n >= 256:
                print(f"  [SAT] {enc:<12} N={n:<3}: Skipped (O(N^2) memory limit)")
                results.append({
                    "n": n, "method": "sat", "encoding": enc, "sat_solver": "glucose3",
                    "status": "MEM_LIMIT", "build_time_s": None, "solve_time_s": None,
                    "total_time_s": None, "variables": None, "constraints": None
                })
                continue

            print(f"  [SAT] Encoding: {enc:<12} ...", end=" ", flush=True)
            res = solve_sat(n=n, encoding=enc, time_limit=time_limit, solver_name="g3")
            print(f"[{res.status}] Build={res.build_time_s:.4f}s | Solve={res.solve_time_s:.4f}s | Clauses={res.constraints}")
            results.append({
                "n": n, "method": "sat", "encoding": enc, "sat_solver": "glucose3",
                "status": res.status, "build_time_s": res.build_time_s,
                "solve_time_s": res.solve_time_s, "total_time_s": res.total_time_s,
                "variables": res.variables, "constraints": res.constraints
            })

        # 2. Test CP-SAT (Google OR-Tools)
        print(f"  [CP-SAT] OR-Tools Solver   ...", end=" ", flush=True)
        cp_res = solve_cp_sat(n=n, time_limit=time_limit)
        print(f"[{cp_res.status}] Build={cp_res.build_time_s:.4f}s | Solve={cp_res.solve_time_s:.4f}s")
        results.append({
            "n": n, "method": "cp-sat", "encoding": "none", "sat_solver": "none",
            "status": cp_res.status, "build_time_s": cp_res.build_time_s,
            "solve_time_s": cp_res.solve_time_s, "total_time_s": cp_res.total_time_s,
            "variables": cp_res.variables, "constraints": cp_res.constraints
        })

    csv_path = out_dir / "benchmark_encodings.csv"
    with open(csv_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(results[0].keys()))
        writer.writeheader()
        writer.writerows(results)
    print(f"\n=> Experiment 1 results saved to: {csv_path}")
    return results


def run_solvers_experiment():
    print("\n=================================================================")
    print("EXPERIMENT 2: CDCL SAT SOLVERS COMPARISON (Glucose 3, 4, CaDiCaL, Minisat)")
    print("=================================================================")

    sizes = [16, 32, 64, 128, 256]
    solvers = [
        ("g3", "Glucose 3"),
        ("g4", "Glucose 4"),
        ("cd153", "CaDiCaL 1.5"),
        ("m22", "Minisat 2.2")
    ]
    encoding = "sequential"
    time_limit = 45.0

    results = []
    out_dir = PROJECT_ROOT / "results"

    for n in sizes:
        print(f"\n--- Comparing Solvers with N = {n} ---")
        for solver_key, solver_label in solvers:
            print(f"  [{solver_label:<14}] Solving ...", end=" ", flush=True)
            res = solve_sat(n=n, encoding=encoding, time_limit=time_limit, solver_name=solver_key)
            time_display = f"{res.engine_time_s:.4f}s" if res.engine_time_s is not None else f"{res.solve_time_s:.4f}s (wall)"
            print(f"[{res.status}] Engine Solve Time = {time_display}")
            results.append({
                "n": n, "solver_key": solver_key, "solver_name": solver_label,
                "encoding": encoding, "status": res.status,
                "build_time_s": res.build_time_s, "solve_time_s": res.solve_time_s,
                "engine_time_s": res.engine_time_s, "total_time_s": res.total_time_s,
                "variables": res.variables, "constraints": res.constraints
            })

    csv_path = out_dir / "benchmark_solvers.csv"
    with open(csv_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(results[0].keys()))
        writer.writeheader()
        writer.writerows(results)
    print(f"\n=> Experiment 2 results saved to: {csv_path}")
    return results


def plot_charts(enc_results, solver_results):
    print("\n=================================================================")
    print("GENERATING SCIENTIFIC CHARTS FOR PAPER (report/figures/)")
    print("=================================================================")

    fig_dir = PROJECT_ROOT / "report" / "figures"
    fig_dir.mkdir(parents=True, exist_ok=True)

    plt.style.use("seaborn-v0_8-whitegrid" if "seaborn-v0_8-whitegrid" in plt.style.available else "default")
    plt.rcParams["font.sans-serif"] = ["DejaVu Sans", "Arial"]
    plt.rcParams["axes.edgecolor"] = "#333333"
    plt.rcParams["axes.linewidth"] = 0.8

    # --- CHART 1: Number of Clauses vs Board Size N (Log scale) ---
    plt.figure(figsize=(8, 5))
    encodings = ["pairwise", "sequential", "binary", "commander", "product"]
    markers = {"pairwise": "o", "sequential": "s", "binary": "^", "commander": "D", "product": "v"}
    colors = {"pairwise": "#e74c3c", "sequential": "#2ecc71", "binary": "#3498db", "commander": "#9b59b6", "product": "#e67e22"}

    for enc in encodings:
        filtered = [r for r in enc_results if r["method"] == "sat" and r["encoding"] == enc and r["constraints"] is not None]
        ns = [r["n"] for r in filtered]
        clauses = [r["constraints"] for r in filtered]
        plt.plot(ns, clauses, marker=markers[enc], color=colors[enc], label=enc.capitalize(), linewidth=2, markersize=6)

    plt.yscale("log")
    plt.title("Comparison of Generated Clauses across AMO Encodings", fontsize=13, fontweight="bold", pad=12)
    plt.xlabel("Board Size N", fontsize=11, fontweight="bold")
    plt.ylabel("Number of Clauses (Log scale)", fontsize=11, fontweight="bold")
    plt.xticks([4, 8, 16, 32, 64, 128, 256], [str(x) for x in [4, 8, 16, 32, 64, 128, 256]])
    plt.legend(frameon=True, fontsize=10)
    plt.tight_layout()
    plt.savefig(fig_dir / "fig_clauses_encodings.png", dpi=300)
    plt.close()
    print("  + Saved fig_clauses_encodings.png")

    # --- CHART 2: Solve Time vs Board Size N across Encodings ---
    plt.figure(figsize=(8, 5))
    for enc in encodings:
        filtered = [r for r in enc_results if r["method"] == "sat" and r["encoding"] == enc and r["solve_time_s"] is not None and r["status"] == "SAT"]
        ns = [r["n"] for r in filtered]
        times = [r["solve_time_s"] for r in filtered]
        plt.plot(ns, times, marker=markers[enc], color=colors[enc], label=enc.capitalize(), linewidth=2, markersize=6)

    plt.yscale("log")
    plt.title("SAT Solving Time vs. Board Size N across Encodings", fontsize=13, fontweight="bold", pad=12)
    plt.xlabel("Board Size N", fontsize=11, fontweight="bold")
    plt.ylabel("Solve Time in Seconds (Log scale)", fontsize=11, fontweight="bold")
    plt.xticks([4, 8, 16, 32, 64, 128, 256], [str(x) for x in [4, 8, 16, 32, 64, 128, 256]])
    plt.legend(frameon=True, fontsize=10)
    plt.tight_layout()
    plt.savefig(fig_dir / "fig_solve_time_encodings.png", dpi=300)
    plt.close()
    print("  + Saved fig_solve_time_encodings.png")

    # --- CHART 3: SAT (Glucose 3 Sequential) vs CP-SAT (OR-Tools) ---
    plt.figure(figsize=(8, 5))
    sat_seq = [r for r in enc_results if r["method"] == "sat" and r["encoding"] == "sequential" and r["status"] == "SAT"]
    cpsat_data = [r for r in enc_results if r["method"] == "cp-sat" and r["status"] == "SAT"]

    plt.plot([r["n"] for r in sat_seq], [r["solve_time_s"] for r in sat_seq], marker="s", color="#2ecc71", label="SAT (Glucose 3 - Sequential)", linewidth=2.2, markersize=7)
    plt.plot([r["n"] for r in cpsat_data], [r["solve_time_s"] for r in cpsat_data], marker="o", color="#3498db", label="CP-SAT (Google OR-Tools)", linewidth=2.2, markersize=7)

    plt.yscale("log")
    plt.title("Runtime Scalability: SAT vs. CP-SAT (Constraint Programming)", fontsize=13, fontweight="bold", pad=12)
    plt.xlabel("Board Size N", fontsize=11, fontweight="bold")
    plt.ylabel("Solve Time in Seconds (Log scale)", fontsize=11, fontweight="bold")
    plt.xticks([4, 8, 16, 32, 64, 128, 256], [str(x) for x in [4, 8, 16, 32, 64, 128, 256]])
    plt.legend(frameon=True, fontsize=10)
    plt.tight_layout()
    plt.savefig(fig_dir / "fig_sat_vs_cpsat.png", dpi=300)
    plt.close()
    print("  + Saved fig_sat_vs_cpsat.png")

    # --- CHART 4: CDCL SAT Solvers Comparison ---
    plt.figure(figsize=(8, 5))
    solver_markers = {"Glucose 3": "o", "Glucose 4": "s", "CaDiCaL 1.5": "^", "Minisat 2.2": "D"}
    solver_colors = {"Glucose 3": "#1abc9c", "Glucose 4": "#3498db", "CaDiCaL 1.5": "#e74c3c", "Minisat 2.2": "#f39c12"}

    solv_names = ["Glucose 3", "Glucose 4", "CaDiCaL 1.5", "Minisat 2.2"]
    for s_name in solv_names:
        sub = [r for r in solver_results if r["solver_name"] == s_name and r["status"] == "SAT" and r["engine_time_s"] is not None]
        if sub:
            plt.plot([r["n"] for r in sub], [r["engine_time_s"] for r in sub],
                     marker=solver_markers[s_name], color=solver_colors[s_name],
                     label=s_name, linewidth=2, markersize=6)

    plt.yscale("log")
    plt.title("Performance Comparison across CDCL SAT Solvers (Sequential AMO)", fontsize=13, fontweight="bold", pad=12)
    plt.xlabel("Board Size N", fontsize=11, fontweight="bold")
    plt.ylabel("Engine Solve Time in Seconds (Log scale)", fontsize=11, fontweight="bold")
    plt.xticks([16, 32, 64, 128, 256], [str(x) for x in [16, 32, 64, 128, 256]])
    plt.legend(frameon=True, fontsize=10)
    plt.tight_layout()
    plt.savefig(fig_dir / "fig_sat_solvers.png", dpi=300)
    plt.close()
    print("  + Saved fig_sat_solvers.png")


if __name__ == "__main__":
    enc_results = run_encodings_experiment()
    solver_results = run_solvers_experiment()
    plot_charts(enc_results, solver_results)
    print("\n[COMPLETE] All experimental data and scientific figures are ready!")
