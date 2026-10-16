"""Shared problem definition and independent solution validation."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Iterable


def check_size(n: int) -> None:
    if not isinstance(n, int) or isinstance(n, bool) or n < 1:
        raise ValueError("N must be a positive integer")


def diagonal_groups(n: int) -> list[list[tuple[int, int]]]:
    """Return both families of diagonals with at least two cells."""
    check_size(n)
    groups: list[list[tuple[int, int]]] = []
    for difference in range(-(n - 1), n):
        cells = [(r, r - difference) for r in range(n) if 0 <= r - difference < n]
        if len(cells) > 1:
            groups.append(cells)
    for total in range(2 * n - 1):
        cells = [(r, total - r) for r in range(n) if 0 <= total - r < n]
        if len(cells) > 1:
            groups.append(cells)
    return groups


def validate_solution(n: int, columns: Iterable[int]) -> bool:
    """Columns are zero-based; item r gives the queen's column in row r."""
    check_size(n)
    values = list(columns)
    if len(values) != n or any(not isinstance(c, int) or isinstance(c, bool) or not 0 <= c < n for c in values):
        return False
    return (
        len(set(values)) == n
        and len({r - c for r, c in enumerate(values)}) == n
        and len({r + c for r, c in enumerate(values)}) == n
    )


def board_text(columns: Iterable[int]) -> str:
    values = list(columns)
    return "\n".join(" ".join("Q" if c == queen else "." for c in range(len(values))) for queen in values)


@dataclass
class SolveResult:
    n: int
    method: str
    status: str
    columns: list[int] | None = None
    build_time_s: float = 0.0
    solve_time_s: float = 0.0
    engine_time_s: float | None = None
    variables: int | None = None
    constraints: int | None = None
    encoding: str = ""
    details: str = ""
    extra: dict = field(default_factory=dict)

    @property
    def valid(self) -> bool | None:
        return validate_solution(self.n, self.columns) if self.columns is not None else None

    @property
    def total_time_s(self) -> float:
        return self.build_time_s + self.solve_time_s

    def record(self) -> dict:
        data = asdict(self)
        data["valid"] = self.valid
        data["total_time_s"] = self.total_time_s
        data["columns"] = "" if self.columns is None else " ".join(str(c + 1) for c in self.columns)
        data["extra"] = str(self.extra)
        return data
