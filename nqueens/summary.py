"""Aggregate successful benchmark runs without hiding failures/timeouts."""

from __future__ import annotations

import csv
from collections import Counter, defaultdict
from pathlib import Path
from statistics import median


def summarize_csv(source: Path, destination: Path) -> int:
    with source.open(encoding="utf-8-sig", newline="") as file:
        rows = list(csv.DictReader(file))
    grouped = defaultdict(list)
    for row in rows:
        grouped[(int(row["n"]), row["method"], row["encoding"])].append(row)
    destination.parent.mkdir(parents=True, exist_ok=True)
    fields = ["n", "method", "encoding", "runs", "sat", "unsat", "timeout", "unavailable",
              "error", "median_build_s", "median_solve_s", "median_engine_s", "median_total_s"]
    with destination.open("w", encoding="utf-8-sig", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=fields)
        writer.writeheader()
        for (n, method, encoding), group in sorted(grouped.items()):
            counts = Counter(row["status"] for row in group)
            completed = [row for row in group if row["status"] in ("SAT", "UNSAT")]
            engine_values = [float(row["engine_time_s"]) for row in completed
                             if row.get("engine_time_s") not in (None, "")]
            writer.writerow({
                "n": n, "method": method, "encoding": encoding, "runs": len(group),
                "sat": counts["SAT"], "unsat": counts["UNSAT"],
                "timeout": counts["TIMEOUT"], "unavailable": counts["UNAVAILABLE"],
                "error": counts["ERROR"],
                "median_build_s": median(float(r["build_time_s"]) for r in completed) if completed else "",
                "median_solve_s": median(float(r["solve_time_s"]) for r in completed) if completed else "",
                "median_engine_s": median(engine_values) if engine_values else "",
                "median_total_s": median(float(r["total_time_s"]) for r in completed) if completed else "",
            })
    return len(grouped)
