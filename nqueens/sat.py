"""Mã hóa bài toán N-Queens sang dạng SAT (CNF) và giải bằng SAT Solver."""

import math
from multiprocessing import get_context
from queue import Empty
from time import perf_counter

from .core import SolveResult, check_size, diagonal_groups

ENCODINGS = ("pairwise", "sequential", "binary", "commander", "product")

SOLVER_ALIASES = {
    "g3": "g3",
    "glucose3": "g3",
    "g4": "g4",
    "glucose4": "g4",
    "cd": "cd153",
    "cd153": "cd153",
    "cadical": "cd153",
    "m22": "m22",
    "minisat": "m22",
    "minisat22": "m22",
}


class CNFBuilder:
    """Lớp xây dựng công thức CNF cho bài toán N-Queens."""

    def __init__(self, n: int):
        self.n = n
        self.next_id = n * n + 1
        self.clauses = []

    def cell(self, row: int, col: int) -> int:
        return row * self.n + col + 1

    def auxiliary(self) -> int:
        var_id = self.next_id
        self.next_id += 1
        return var_id

    def add(self, *literals: int) -> None:
        self.clauses.append(list(literals))

    def _encode_pairwise(self, literals: list[int]) -> None:
        k = len(literals)
        for i in range(k):
            for j in range(i + 1, k):
                self.add(-literals[i], -literals[j])

    def _encode_sequential(self, literals: list[int]) -> None:
        k = len(literals)
        s = [self.auxiliary() for _ in range(k - 1)]

        self.add(-literals[0], s[0])
        for i in range(1, k - 1):
            lit = literals[i]
            prev_s = s[i - 1]
            curr_s = s[i]
            self.add(-lit, curr_s)
            self.add(-prev_s, curr_s)
            self.add(-lit, -prev_s)
        self.add(-literals[-1], -s[-1])

    def _encode_binary(self, literals: list[int]) -> None:
        k = len(literals)
        num_bits = math.ceil(math.log2(k))
        if num_bits == 0:
            return

        bits = [self.auxiliary() for _ in range(num_bits)]

        for index in range(k):
            lit = literals[index]
            for bit_pos in range(num_bits):
                bit_var = bits[bit_pos]
                bit_val = (index >> bit_pos) % 2
                if bit_val == 1:
                    self.add(-lit, bit_var)
                else:
                    self.add(-lit, -bit_var)

    def _encode_commander(self, literals: list[int]) -> None:
        k = len(literals)
        if k <= 3:
            self._encode_pairwise(literals)
            return

        commanders = []
        for i in range(0, k, 3):
            group = literals[i : i + 3]
            cmd = self.auxiliary()
            commanders.append(cmd)
            self._encode_pairwise(group)
            for lit in group:
                self.add(-lit, cmd)

        self.at_most_one(commanders, "commander")

    def _encode_product(self, literals: list[int]) -> None:
        k = len(literals)
        p = int(math.ceil(math.sqrt(k)))
        q = int(math.ceil(k / p))

        row_flags = [self.auxiliary() for _ in range(p)]
        col_flags = [self.auxiliary() for _ in range(q)]

        for index in range(k):
            lit = literals[index]
            r = index // q
            c = index % q
            self.add(-lit, row_flags[r])
            self.add(-lit, col_flags[c])

        self._encode_pairwise(row_flags)
        self._encode_pairwise(col_flags)

    def at_most_one(self, literals: list[int], encoding: str) -> None:
        if len(literals) < 2:
            return

        if encoding == "pairwise":
            self._encode_pairwise(literals)
        elif encoding == "sequential":
            self._encode_sequential(literals)
        elif encoding == "binary":
            self._encode_binary(literals)
        elif encoding == "commander":
            self._encode_commander(literals)
        elif encoding == "product":
            self._encode_product(literals)
        else:
            raise ValueError(f"Không hỗ trợ kiểu mã hóa: {encoding}")

    def exactly_one(self, literals: list[int], encoding: str) -> None:
        self.clauses.append(list(literals))
        self.at_most_one(literals, encoding)


def build_cnf(n: int, encoding: str = "sequential") -> CNFBuilder:
    check_size(n)
    if encoding not in ENCODINGS:
        raise ValueError(f"Encoding phải là một trong các giá trị: {', '.join(ENCODINGS)}")

    cnf = CNFBuilder(n)

    for row in range(n):
        row_cells = [cnf.cell(row, col) for col in range(n)]
        cnf.exactly_one(row_cells, encoding)

    for col in range(n):
        col_cells = [cnf.cell(row, col) for row in range(n)]
        cnf.exactly_one(col_cells, encoding)

    for diagonal in diagonal_groups(n):
        diag_cells = [cnf.cell(row, col) for row, col in diagonal]
        cnf.at_most_one(diag_cells, encoding)

    return cnf


def _solver_worker(clauses: list[list[int]], n: int, solver_key: str, output_queue) -> None:
    try:
        from pysat.solvers import Solver

        start_time = perf_counter()
        with Solver(name=solver_key, bootstrap_with=clauses) as solver:
            is_sat = solver.solve()
            solve_time = perf_counter() - start_time

            if is_sat:
                model = solver.get_model()
                true_vars = {var for var in model if var > 0}

                columns = []
                for row in range(n):
                    for col in range(n):
                        cell_id = row * n + col + 1
                        if cell_id in true_vars:
                            columns.append(col)
                            break

                output_queue.put(("SAT", columns, "", solve_time))
            else:
                output_queue.put(("UNSAT", None, "", solve_time))
    except Exception as exc:
        output_queue.put(("ERROR", None, f"{type(exc).__name__}: {exc}", 0.0))


def solve_sat(n: int, encoding: str = "sequential", time_limit: float = 60.0, solver_name: str = "g3") -> SolveResult:
    check_size(n)
    if time_limit <= 0:
        raise ValueError("time_limit phải là số dương")

    solver_key = SOLVER_ALIASES.get(solver_name.lower(), solver_name)

    start_build = perf_counter()
    cnf = build_cnf(n, encoding)
    build_time = perf_counter() - start_build

    result = SolveResult(
        n=n,
        method="sat",
        status="ERROR",
        build_time_s=build_time,
        variables=cnf.next_id - 1,
        constraints=len(cnf.clauses),
        encoding=encoding,
    )

    try:
        import pysat.solvers  # noqa: F401
    except ImportError:
        result.status = "UNAVAILABLE"
        result.details = "Chưa cài đặt thư viện python-sat"
        return result

    context = get_context("spawn")
    queue = context.Queue()
    worker = context.Process(target=_solver_worker, args=(cnf.clauses, n, solver_key, queue))
    worker.daemon = True

    start_solve = perf_counter()
    try:
        worker.start()
        worker.join(time_limit)

        if worker.is_alive():
            worker.terminate()
            worker.join(1)
            if worker.is_alive():
                worker.kill()
                worker.join()
            result.status = "TIMEOUT"
        else:
            try:
                status, columns, details, engine_time = queue.get(timeout=1)
                result.status = status
                result.columns = columns
                result.details = details
                result.engine_time_s = engine_time
            except Empty:
                result.details = "Tiến trình kết thúc mà không trả về kết quả"
    except Exception as exc:
        result.status = "ERROR"
        result.details = f"{type(exc).__name__}: {exc}"
    finally:
        result.solve_time_s = perf_counter() - start_solve
        queue.close()

    return result
