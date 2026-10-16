"""Mã hóa bài toán N-Queens sang dạng SAT (CNF) và giải bằng SAT Solver (Glucose 3).

Mục tiêu chính:
1. Tạo các biến mệnh đề cho bàn cờ N x N.
2. Thiết lập ràng buộc ALO (At-Least-One) và AMO (At-Most-One).
3. Cài đặt 5 kỹ thuật mã hóa AMO phổ biến (Pairwise, Sequential, Binary, Commander, Product)
   được tách thành các hàm riêng biệt, rõ ràng, dễ đọc.
4. Gọi SAT Solver giải bài toán và trích xuất vị trí quân hậu.
"""

from __future__ import annotations

import math
from itertools import combinations
from multiprocessing import get_context
from queue import Empty
from time import perf_counter

from .core import SolveResult, check_size, diagonal_groups

# Danh sách 5 kỹ thuật mã hóa At-Most-One (AMO)
ENCODINGS = ("pairwise", "sequential", "binary", "commander", "product")


class CNFBuilder:
    """Lớp hỗ trợ xây dựng tập mệnh đề CNF (Conjunctive Normal Form).

    - Quản lý danh sách các mệnh đề (clauses).
    - Quản lý ID của các biến logic.
    - Cung cấp các phương thức mã hóa ràng buộc AMO và Exactly-One.
    """

    def __init__(self, n: int):
        self.n = n
        # Ô cờ ban đầu được đánh số từ 1 đến n*n.
        # Biến phụ sinh thêm (auxiliary) sẽ bắt đầu từ n*n + 1 trở đi.
        self.next_id = n * n + 1
        self.clauses: list[list[int]] = []

    def cell(self, row: int, col: int) -> int:
        """Trả về ID biến logic đại diện cho ô (row, col) trên bàn cờ.

        Quy ước 1-indexed: Ô (0, 0) là 1, ô (0, 1) là 2, ..., ô (n-1, n-1) là n*n.
        """
        return row * self.n + col + 1

    def auxiliary(self) -> int:
        """Cấp phát 1 ID biến phụ mới duy nhất (không trùng lặp)."""
        var_id = self.next_id
        self.next_id += 1
        return var_id

    def add(self, *literals: int) -> None:
        """Thêm một mệnh đề (phép HOẶC giữa các literal) vào danh sách clauses.

        Ví dụ: self.add(-1, 2) tương đương mệnh đề (NOT x1 OR x2).
        """
        self.clauses.append(list(literals))

    # =========================================================================
    # 5 PHƯƠNG PHÁP MÃ HÓA AT-MOST-ONE (AMO - Tối đa 1 biến là True)
    # =========================================================================

    def _encode_pairwise(self, literals: list[int]) -> None:
        """1. Mã hóa theo cặp (Pairwise / Binomial Encoding).

        - Ý tưởng: Xét mọi cặp (x_i, x_j), không được phép cả 2 cùng True:
          NOT (x_i AND x_j)  <=>  (NOT x_i OR NOT x_j)
        - Số biến phụ: 0.
        - Số mệnh đề: k * (k - 1) / 2 = O(k^2).
        """
        for a, b in combinations(literals, 2):
            self.add(-a, -b)

    def _encode_sequential(self, literals: list[int]) -> None:
        """2. Mã hóa bộ đếm tuần tự (Sequential Counter - Carsten Sinz, 2005).

        - Ý tưởng: Dùng chuỗi biến phụ s[0], s[1], ..., s[k-2] để tích lũy.
          s[i] = True nghĩa là: "Đã có ít nhất 1 quân hậu xuất hiện ở vị trí <= i".
        - Số biến phụ: k - 1 = O(k).
        - Số mệnh đề: 3k - 4 = O(k).
        """
        k = len(literals)
        # Tạo k - 1 biến phụ đóng vai trò bộ tích lũy
        counters = [self.auxiliary() for _ in range(k - 1)]

        # Bước 1: Phần tử đầu tiên x[0]
        # Nếu x[0] = True -> bật cờ tích lũy s[0]
        self.add(-literals[0], counters[0])

        # Bước 2: Các phần tử ở giữa x[1] đến x[k - 2]
        for i in range(1, k - 1):
            curr_lit = literals[i]
            prev_s = counters[i - 1]
            curr_s = counters[i]

            # Nếu x[i] = True -> bật cờ tích lũy s[i]
            self.add(-curr_lit, curr_s)
            # Kế thừa: Nếu bước trước đã có hậu (s[i-1] = True) -> s[i] cũng phải True
            self.add(-prev_s, curr_s)
            # Điều kiện cấm: Nếu bước trước đã có hậu (s[i-1] = True) -> x[i] PHẢI là False
            self.add(-curr_lit, -prev_s)

        # Bước 3: Phần tử cuối cùng x[k - 1]
        # Nếu bước trước đã có hậu (s[k-2] = True) -> x[k-1] PHẢI là False
        self.add(-literals[-1], -counters[-1])

    def _encode_binary(self, literals: list[int]) -> None:
        """3. Mã hóa nhị phân (Binary / Bitwise Encoding).

        - Ý tưởng: Đánh số thứ tự các biến từ 0 đến k-1.
          Dùng m = ceil(log2(k)) biến phụ b[0], b[1], ... đại diện cho các bit nhị phân.
          Nếu biến x[index] là True -> ép các bit b nhận đúng mã nhị phân của 'index'.
          Hai biến khác nhau sẽ ép các bit nhận giá trị đối nghịch nhau (mâu thuẫn),
          do đó không bao giờ có 2 biến cùng là True được.
        - Số biến phụ: ceil(log2(k)) = O(log k).
        - Số mệnh đề: k * ceil(log2(k)) = O(k * log k).
        """
        k = len(literals)
        num_bits = (k - 1).bit_length()  # Số lượng bit cần thiết (tương đương ceil(log2(k)))
        bits = [self.auxiliary() for _ in range(num_bits)]

        for index, literal in enumerate(literals):
            for bit_pos in range(num_bits):
                bit_var = bits[bit_pos]
                # Kiểm tra bit thứ bit_pos của số 'index' là 1 hay 0
                is_bit_set = (index >> bit_pos) & 1

                if is_bit_set:
                    # Nếu bit là 1: literal True -> bit_var phải là True: (NOT literal OR bit_var)
                    self.add(-literal, bit_var)
                else:
                    # Nếu bit là 0: literal True -> bit_var phải là False: (NOT literal OR NOT bit_var)
                    self.add(-literal, -bit_var)

    def _encode_commander(self, literals: list[int]) -> None:
        """4. Mã hóa biến chỉ huy (Commander Variable Encoding).

        - Ý tưởng: Chia tập k biến thành các nhóm nhỏ (mỗi nhóm tối đa 3 biến).
          Mỗi nhóm tạo 1 biến chỉ huy (commander).
          + Trong từng nhóm: Tối đa 1 biến là True.
          + Nếu có 1 biến trong nhóm là True -> biến commander của nhóm đó phải True.
          + Giữa các commander: Gọi đệ quy để đảm bảo tối đa 1 commander là True.
        - Số biến phụ: O(k).
        - Số mệnh đề: O(k).
        """
        if len(literals) <= 3:
            self._encode_pairwise(literals)
            return

        commanders = []
        group_size = 3

        for start in range(0, len(literals), group_size):
            group = literals[start : start + group_size]
            commander = self.auxiliary()
            commanders.append(commander)

            # Ràng buộc 1: Trong nội bộ nhóm, tối đa 1 biến là True
            self._encode_pairwise(group)

            # Ràng buộc 2: Nếu bất kỳ biến nào trong nhóm True -> commander phải True
            for lit in group:
                self.add(-lit, commander)

        # Ràng buộc 3: Giữa các biến chỉ huy, tối đa 1 biến được là True (đệ quy)
        self.at_most_one(commanders, "commander")

    def _encode_product(self, literals: list[int]) -> None:
        """5. Mã hóa ma trận tích (Product Encoding - Jingchao Chen, 2010).

        - Ý tưởng: Xếp các biến vào lưới 2 chiều kích thước rows x cols (xấp xỉ sqrt(k)).
          + Tạo 'rows' biến phụ đại diện cho hàng.
          + Tạo 'cols' biến phụ đại diện cho cột.
          + Biến thứ 'index' nằm tại tọa độ (row_idx, col_idx).
            Nếu biến này True -> cả cờ hàng và cờ cột tương ứng phải True.
          + Dùng Pairwise để cấm trùng hàng và cấm trùng cột.
        - Số biến phụ: 2 * sqrt(k) = O(sqrt(k)).
        - Số mệnh đề: O(k).
        """
        k = len(literals)
        rows = max(2, int(math.isqrt(k)))
        cols = math.ceil(k / rows)

        row_flags = [self.auxiliary() for _ in range(rows)]
        col_flags = [self.auxiliary() for _ in range(cols)]

        for index, literal in enumerate(literals):
            r = index // cols
            c = index % cols
            # Nếu literal True -> hàng r phải True và cột c phải True
            self.add(-literal, row_flags[r])
            self.add(-literal, col_flags[c])

        # Tối đa 1 cờ hàng là True, tối đa 1 cờ cột là True
        self._encode_pairwise(row_flags)
        self._encode_pairwise(col_flags)

    # =========================================================================
    # RÀNG BUỘC CARDINALITY TỔNG QUÁT
    # =========================================================================

    def at_most_one(self, literals: list[int], encoding: str) -> None:
        """Điều hướng mã hóa At-Most-One (AMO) sang hàm xử lý tương ứng."""
        if len(literals) < 2:
            return

        handlers = {
            "pairwise": self._encode_pairwise,
            "sequential": self._encode_sequential,
            "binary": self._encode_binary,
            "commander": self._encode_commander,
            "product": self._encode_product,
        }

        if encoding not in handlers:
            raise ValueError(f"Kiểu mã hóa không hợp lệ: {encoding}. Chọn từ: {list(handlers.keys())}")

        handlers[encoding](literals)

    def exactly_one(self, literals: list[int], encoding: str) -> None:
        """Mã hóa ràng buộc Exactly-One (Có đúng 1 biến là True).

        Exactly-One = At-Least-One (ALO) AND At-Most-One (AMO).
        """
        # 1. ALO: Có ít nhất 1 biến True -> (x1 OR x2 OR ... OR xk)
        self.clauses.append(literals.copy())
        # 2. AMO: Có tối đa 1 biến True -> Dùng phương pháp encoding được chọn
        self.at_most_one(literals, encoding)


def build_cnf(n: int, encoding: str = "sequential") -> CNFBuilder:
    """Xây dựng toàn bộ hệ thống mệnh đề CNF cho bàn cờ N x N.

    Bao gồm 3 nhóm ràng buộc:
    1. Mỗi hàng có đúng 1 quân hậu (Exactly-One).
    2. Mỗi cột có đúng 1 quân hậu (Exactly-One).
    3. Mỗi đường chéo (chính và phụ) có tối đa 1 quân hậu (At-Most-One).
    """
    check_size(n)
    if encoding not in ENCODINGS:
        raise ValueError(f"Encoding phải là một trong các giá trị: {', '.join(ENCODINGS)}")

    cnf = CNFBuilder(n)

    # 1. Ràng buộc theo từng hàng
    for row in range(n):
        row_cells = [cnf.cell(row, col) for col in range(n)]
        cnf.exactly_one(row_cells, encoding)

    # 2. Ràng buộc theo từng cột
    for col in range(n):
        col_cells = [cnf.cell(row, col) for row in range(n)]
        cnf.exactly_one(col_cells, encoding)

    # 3. Ràng buộc theo từng đường chéo
    for diagonal in diagonal_groups(n):
        diag_cells = [cnf.cell(row, col) for row, col in diagonal]
        cnf.at_most_one(diag_cells, encoding)

    return cnf


# =============================================================================
# THỰC THI SOLVER VÀ QUẢN LÝ TIẾN TRÌNH CON
# =============================================================================

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


def _solver_worker(clauses: list[list[int]], n: int, solver_key: str, output_queue) -> None:
    """Hàm chạy trong tiến trình con (child process) để gọi SAT Solver.

    Việc tách tiến trình giúp Windows có thể ép ngắt an toàn khi bài toán bị quá giờ (timeout).
    """
    try:
        from pysat.solvers import Solver

        started = perf_counter()
        # Nạp tập mệnh đề vào SAT Solver được chỉ định
        with Solver(name=solver_key, bootstrap_with=clauses) as solver:
            satisfiable = solver.solve()
            solve_duration = perf_counter() - started

            if satisfiable:
                # Lấy tập hợp các biến có giá trị True (dương)
                model_true_vars = {val for val in solver.get_model() if val > 0}

                # Tìm vị trí cột của từng hàng (từ 0 đến n-1)
                columns = []
                for row in range(n):
                    col = next(c for c in range(n) if (row * n + c + 1) in model_true_vars)
                    columns.append(col)

                output_queue.put(("SAT", columns, "", solve_duration))
            else:
                output_queue.put(("UNSAT", None, "", solve_duration))
    except Exception as exc:
        output_queue.put(("ERROR", None, f"{type(exc).__name__}: {exc}", 0.0))


def solve_sat(n: int, encoding: str = "sequential", time_limit: float = 60.0, solver_name: str = "g3") -> SolveResult:
    """Hàm chính: Giải bài toán N-Queens bằng SAT Solver (mặc định Glucose 3, hỗ trợ Cadical, Minisat...)."""
    check_size(n)
    if time_limit <= 0:
        raise ValueError("Giới hạn thời gian (time_limit) phải là số dương")

    solver_key = SOLVER_ALIASES.get(solver_name.lower(), solver_name)

    # Bước 1: Xây dựng CNF và đo thời gian dựng mô hình
    build_start = perf_counter()
    cnf = build_cnf(n, encoding)
    build_time = perf_counter() - build_start

    # Khởi tạo kết quả ban đầu
    total_vars = cnf.next_id - 1
    total_clauses = len(cnf.clauses)
    result = SolveResult(
        n=n,
        method="sat",
        status="ERROR",
        build_time_s=build_time,
        variables=total_vars,
        constraints=total_clauses,
        encoding=encoding,
    )

    try:
        import pysat.solvers  # noqa: F401
    except ImportError:
        result.status = "UNAVAILABLE"
        result.details = "Chưa cài đặt thư viện python-sat"
        return result

    # Bước 2: Khởi chạy tiến trình con để giải với thời gian giới hạn time_limit
    context = get_context("spawn")
    output_queue = context.Queue()
    worker = context.Process(target=_solver_worker, args=(cnf.clauses, n, solver_key, output_queue))
    worker.daemon = True

    solve_start = perf_counter()
    try:
        worker.start()
        worker.join(time_limit)

        if worker.is_alive():
            # Quá thời gian quy định -> Dừng tiến trình
            worker.terminate()
            worker.join(1)
            if worker.is_alive():
                worker.kill()
                worker.join()
            result.status = "TIMEOUT"
        else:
            # Lấy kết quả từ Queue
            try:
                status, columns, details, engine_time = output_queue.get(timeout=1)
                result.status = status
                result.columns = columns
                result.details = details
                result.engine_time_s = engine_time
            except Empty:
                result.details = f"Tiến trình kết thúc với mã {worker.exitcode} mà không trả về kết quả"
    except Exception as exc:
        result.status = "ERROR"
        result.details = f"{type(exc).__name__}: {exc}"
    finally:
        result.solve_time_s = perf_counter() - solve_start
        output_queue.close()

    return result
