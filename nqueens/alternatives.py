"""Các mô hình giải chính xác (Exact Solvers) để so sánh với SAT."""

from __future__ import annotations

from time import perf_counter

from .core import SolveResult, check_size, diagonal_groups


def _check(n: int, time_limit: float) -> None:
    check_size(n)
    if time_limit <= 0:
        raise ValueError("Giới hạn thời gian (time_limit) phải là số dương")


def solve_cp_sat(n: int, time_limit: float = 60.0) -> SolveResult:
    """Giải bài toán N-Queens bằng CP-SAT (Google OR-Tools)."""
    _check(n, time_limit)
    result = SolveResult(n, "cp-sat", "ERROR")
    try:
        from ortools.sat.python import cp_model
    except ImportError:
        result.status = "UNAVAILABLE"
        result.details = "Chưa cài đặt ortools trong môi trường Python hiện tại"
        return result

    started = perf_counter()
    model = cp_model.CpModel()

    queens = [model.new_int_var(0, n - 1, f"queen_{r}") for r in range(n)]
    model.add_all_different(queens)
    model.add_all_different([queens[r] + r for r in range(n)])
    model.add_all_different([queens[r] - r for r in range(n)])

    result.build_time_s = perf_counter() - started
    result.variables = n
    result.constraints = 3

    started = perf_counter()
    try:
        solver = cp_model.CpSolver()
        solver.parameters.max_time_in_seconds = time_limit
        solver.parameters.num_search_workers = 1
        status = solver.solve(model)

        if status in (cp_model.OPTIMAL, cp_model.FEASIBLE):
            result.status = "SAT"
            result.columns = [int(solver.value(queen)) for queen in queens]
        elif status == cp_model.INFEASIBLE:
            result.status = "UNSAT"
        elif status == cp_model.UNKNOWN:
            result.status = "TIMEOUT"
        else:
            result.details = solver.status_name(status)
    except Exception as exc:
        result.details = f"{type(exc).__name__}: {exc}"

    result.solve_time_s = perf_counter() - started
    result.engine_time_s = result.solve_time_s
    return result


def solve_gurobi(n: int, time_limit: float = 60.0) -> SolveResult:
    """Giải bài toán N-Queens bằng Gurobi (Quy hoạch nguyên tuyến tính - MIP/ILP)."""
    _check(n, time_limit)
    result = SolveResult(n, "gurobi", "ERROR")
    try:
        import gurobipy as gp
    except ImportError:
        result.status = "UNAVAILABLE"
        result.details = "Chưa cài gurobipy hoặc chưa cấu hình license Gurobi hợp lệ"
        return result

    started = perf_counter()
    try:
        model = gp.Model("nqueens")
        model.Params.OutputFlag = 0
        model.Params.Threads = 1
        model.Params.TimeLimit = time_limit

        x = model.addVars(n, n, vtype=gp.GRB.BINARY, name="x")

        for r in range(n):
            model.addConstr(gp.quicksum(x[r, c] for c in range(n)) == 1)

        for c in range(n):
            model.addConstr(gp.quicksum(x[r, c] for r in range(n)) == 1)

        for cells in diagonal_groups(n):
            model.addConstr(gp.quicksum(x[r, c] for r, c in cells) <= 1)

        model.update()
        result.variables = model.NumVars
        result.constraints = model.NumConstrs
        result.build_time_s = perf_counter() - started

        started = perf_counter()
        model.optimize()

        if model.SolCount > 0:
            result.status = "SAT"
            result.columns = [next(c for c in range(n) if x[r, c].X > 0.5) for r in range(n)]
        elif model.Status == gp.GRB.INFEASIBLE:
            result.status = "UNSAT"
        elif model.Status == gp.GRB.TIME_LIMIT:
            result.status = "TIMEOUT"
        else:
            result.details = f"Gurobi status {model.Status}"

        result.solve_time_s = perf_counter() - started
        result.engine_time_s = result.solve_time_s
        model.dispose()
    except Exception as exc:
        result.details = f"{type(exc).__name__}: {exc}"
        if "license" in str(exc).lower():
            result.status = "UNAVAILABLE"
    return result


def solve_cplex_mip(n: int, time_limit: float = 60.0) -> SolveResult:
    """Giải bài toán N-Queens bằng CPLEX MIP (IBM ILOG CPLEX qua docplex.mp)."""
    _check(n, time_limit)
    result = SolveResult(n, "cplex-mip", "ERROR")
    try:
        from docplex.mp.model import Model
    except ImportError:
        result.status = "UNAVAILABLE"
        result.details = "Chưa cài docplex hoặc bộ runtime CPLEX trên máy"
        return result

    started = perf_counter()
    try:
        model = Model(name="nqueens")
        model.time_limit = time_limit
        model.context.cplex_parameters.threads = 1
        x = model.binary_var_matrix(range(n), range(n), name="x")

        for r in range(n):
            model.add_constraint(model.sum(x[r, c] for c in range(n)) == 1)

        for c in range(n):
            model.add_constraint(model.sum(x[r, c] for r in range(n)) == 1)

        for cells in diagonal_groups(n):
            model.add_constraint(model.sum(x[r, c] for r, c in cells) <= 1)

        result.variables = model.number_of_variables
        result.constraints = model.number_of_constraints
        result.build_time_s = perf_counter() - started

        started = perf_counter()
        solution = model.solve(log_output=False)

        if solution is not None:
            result.status = "SAT"
            result.columns = [next(c for c in range(n) if solution.get_value(x[r, c]) > 0.5)
                              for r in range(n)]
        else:
            status = str(model.solve_details.status).lower()
            if "infeasible" in status:
                result.status = "UNSAT"
            elif "time" in status or "abort" in status:
                result.status = "TIMEOUT"
            else:
                result.details = f"CPLEX status: {status}"

        result.solve_time_s = perf_counter() - started
        result.engine_time_s = result.solve_time_s
        model.end()
    except Exception as exc:
        result.details = f"{type(exc).__name__}: {exc}"
        message = str(exc).lower()
        if any(term in message for term in ("no cplex runtime", "license", "limits exceeded", "promotional version")):
            result.status = "UNAVAILABLE"
    return result


def solve_cplex_cp(n: int, time_limit: float = 60.0) -> SolveResult:
    """Giải bài toán N-Queens bằng CPLEX CP Optimizer (docplex.cp)."""
    _check(n, time_limit)
    result = SolveResult(n, "cplex-cp", "ERROR")
    try:
        from docplex.cp.model import CpoModel
    except ImportError:
        result.status = "UNAVAILABLE"
        result.details = "Chưa cài docplex và bộ thực thi IBM CP Optimizer (cpoptimizer.exe)"
        return result

    started = perf_counter()
    try:
        model = CpoModel(name="nqueens")
        queens = model.integer_var_list(n, 0, n - 1, "queen")

        model.add(model.all_diff(queens))
        model.add(model.all_diff([queens[r] + r for r in range(n)]))
        model.add(model.all_diff([queens[r] - r for r in range(n)]))

        result.variables = n
        result.constraints = 3
        result.build_time_s = perf_counter() - started

        started = perf_counter()
        solution = model.solve(TimeLimit=time_limit, Workers=1, LogVerbosity="Quiet")

        if solution.is_solution():
            result.status = "SAT"
            result.columns = [int(solution.get_value(queen)) for queen in queens]
        else:
            status = str(solution.get_solve_status()).lower()
            if "infeasible" in status:
                result.status = "UNSAT"
            elif "unknown" in status or "limit" in status:
                result.status = "TIMEOUT"
            else:
                result.details = f"CP Optimizer status: {status}"

        result.solve_time_s = perf_counter() - started
        result.engine_time_s = result.solve_time_s
    except Exception as exc:
        result.details = f"{type(exc).__name__}: {exc}"
        if "cpoptimizer" in str(exc).lower() or "license" in str(exc).lower():
            result.status = "UNAVAILABLE"
    return result
