"""Các mô hình giải chính xác (Exact Solvers) để so sánh với SAT.

Bao gồm:
- CP-SAT (Google OR-Tools): Lập trình ràng buộc (Constraint Programming - CP)
- Gurobi: Quy hoạch tuyến tính nguyên/hỗn hợp (ILP / MIP)
- CPLEX MIP: Quy hoạch nguyên dùng IBM ILOG CPLEX
- CPLEX CP: Lập trình ràng buộc dùng IBM CP Optimizer (docplex.cp)

Các module thư viện chỉ được import cục bộ trong từng hàm để việc thiếu một solver
(hoặc thiếu license) không làm ảnh hưởng đến các solver khác hay phương pháp SAT.
"""

from __future__ import annotations

from time import perf_counter

from .core import SolveResult, check_size, diagonal_groups


def _check(n: int, time_limit: float) -> None:
    """Kiểm tra tính hợp lệ của kích thước n và thời gian giới hạn."""
    check_size(n)
    if time_limit <= 0:
        raise ValueError("Giới hạn thời gian (time_limit) phải là số dương")


def solve_cp_sat(n: int, time_limit: float = 60.0) -> SolveResult:
    """Giải bài toán N-Queens bằng CP-SAT (Google OR-Tools).

    Mô hình hóa theo Constraint Programming (CP):
    - Biến: n biến số nguyên queens[r] thuộc đoạn [0, n - 1], đại diện cho chỉ số cột
      của quân hậu tại hàng r.
    - Ràng buộc:
      1. queens[r] khác nhau đôi một (AllDifferent) -> Mỗi cột có tối đa 1 hậu.
      2. queens[r] + r khác nhau đôi một (AllDifferent) -> Không cùng đường chéo phụ.
      3. queens[r] - r khác nhau đôi một (AllDifferent) -> Không cùng đường chéo chính.
    """
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

    # Tạo n biến nguyên: queens[r] là cột của quân hậu tại hàng r (giá trị từ 0 đến n-1)
    queens = [model.new_int_var(0, n - 1, f"queen_{r}") for r in range(n)]

    # Ràng buộc 1: Không có hai quân hậu nào cùng một cột
    model.add_all_different(queens)

    # Ràng buộc 2: Không có hai quân hậu nào cùng đường chéo phụ (cột + hàng khác nhau đôi một)
    model.add_all_different([queens[r] + r for r in range(n)])

    # Ràng buộc 3: Không có hai quân hậu nào cùng đường chéo chính (cột - hàng khác nhau đôi một)
    model.add_all_different([queens[r] - r for r in range(n)])

    result.build_time_s = perf_counter() - started
    result.variables = n
    result.constraints = 3  # 3 ràng buộc AllDifferent toàn cục

    started = perf_counter()
    try:
        solver = cp_model.CpSolver()
        solver.parameters.max_time_in_seconds = time_limit
        solver.parameters.num_search_workers = 1  # Dùng 1 luồng để so sánh công bằng về CPU time
        status = solver.solve(model)

        if status in (cp_model.OPTIMAL, cp_model.FEASIBLE):
            result.status = "SAT"
            # Lấy vị trí cột đã gán cho từng hàng
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
    """Giải bài toán N-Queens bằng Gurobi (Quy hoạch nguyên tuyến tính - MIP/ILP).

    Mô hình hóa theo MIP:
    - Biến: n x n biến nhị phân x[r, c] thuộc {0, 1}.
      x[r, c] = 1 nếu ô (r, c) có quân hậu, ngược lại = 0.
    - Ràng buộc:
      1. Tổng x[r, c] theo mỗi hàng r bằng 1 (mỗi hàng đúng 1 hậu).
      2. Tổng x[r, c] theo mỗi cột c bằng 1 (mỗi cột đúng 1 hậu).
      3. Tổng x[r, c] trên mỗi đường chéo <= 1 (mỗi đường chéo tối đa 1 hậu).
    """
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
        model.Params.OutputFlag = 0       # Tắt log stdout màn hình
        model.Params.Threads = 1          # 1 luồng để đối chuẩn công bằng
        model.Params.TimeLimit = time_limit

        # Tạo ma trận n x n biến nhị phân
        x = model.addVars(n, n, vtype=gp.GRB.BINARY, name="x")

        # Ràng buộc 1: Mỗi hàng có đúng 1 quân hậu
        for r in range(n):
            model.addConstr(gp.quicksum(x[r, c] for c in range(n)) == 1)

        # Ràng buộc 2: Mỗi cột có đúng 1 quân hậu
        for c in range(n):
            model.addConstr(gp.quicksum(x[r, c] for r in range(n)) == 1)

        # Ràng buộc 3: Mỗi đường chéo chính và phụ có tối đa 1 quân hậu
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
            # Tìm cột c có x[r, c] == 1 cho từng hàng r
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
    """Giải bài toán N-Queens bằng CPLEX MIP (IBM ILOG CPLEX qua docplex.mp).

    Mô hình hóa tương tự Gurobi:
    - Biến nhị phân x[r, c] thuộc {0, 1} cho từng ô cờ.
    - Ràng buộc tổng hàng = 1, tổng cột = 1, tổng đường chéo <= 1.
    """
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
        model.context.cplex_parameters.threads = 1  # 1 luồng
        x = model.binary_var_matrix(range(n), range(n), name="x")

        # Ràng buộc hàng: mỗi hàng đúng 1 quân hậu
        for r in range(n):
            model.add_constraint(model.sum(x[r, c] for c in range(n)) == 1)

        # Ràng buộc cột: mỗi cột đúng 1 quân hậu
        for c in range(n):
            model.add_constraint(model.sum(x[r, c] for r in range(n)) == 1)

        # Ràng buộc đường chéo: mỗi đường chéo tối đa 1 quân hậu
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
        # Xử lý trường hợp vượt quá giới hạn bản Community Edition (1000 biến) hoặc thiếu license
        if any(term in message for term in ("no cplex runtime", "license", "limits exceeded", "promotional version")):
            result.status = "UNAVAILABLE"
    return result


def solve_cplex_cp(n: int, time_limit: float = 60.0) -> SolveResult:
    """Giải bài toán N-Queens bằng CPLEX CP Optimizer (docplex.cp).

    Mô hình hóa theo Constraint Programming với biến chỉ số cột:
    - n biến số nguyên queens[r] thuộc đoạn [0, n - 1].
    - Ràng buộc AllDifferent cho:
      1. Các cột: queens
      2. Đường chéo phụ: queens[r] + r
      3. Đường chéo chính: queens[r] - r
    """
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

        # Ràng buộc AllDifferent không cho trùng cột và trùng đường chéo
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
