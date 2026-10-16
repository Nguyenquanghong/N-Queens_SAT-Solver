"""Correctness checks for the problem and every SAT encoding."""

import itertools
import unittest

from nqueens.__main__ import run_method
from nqueens.core import diagonal_groups, validate_solution
from nqueens.sat import CNFBuilder, ENCODINGS


class CoreTests(unittest.TestCase):
    def test_known_board(self):
        self.assertTrue(validate_solution(4, [1, 3, 0, 2]))
        self.assertFalse(validate_solution(4, [0, 1, 2, 3]))
        self.assertFalse(validate_solution(4, [1, 1, 0, 2]))

    def test_diagonals(self):
        self.assertEqual(len(diagonal_groups(4)), 10)
        self.assertIn([(0, 0), (1, 1), (2, 2), (3, 3)], diagonal_groups(4))


class SatTests(unittest.TestCase):
    def test_amo_truth_table(self):
        from pysat.solvers import Solver

        for encoding, size in itertools.product(ENCODINGS, range(2, 7)):
            with self.subTest(encoding=encoding, size=size):
                builder = CNFBuilder(1)
                variables = list(range(1, size + 1))
                builder.next_id = size + 1
                builder.at_most_one(variables, encoding)
                with Solver(name="g3", bootstrap_with=builder.clauses) as solver:
                    for subset_size in range(size + 1):
                        for true_vars in itertools.combinations(variables, subset_size):
                            true_set = set(true_vars)
                            assignment = [v if v in true_set else -v for v in variables]
                            self.assertEqual(solver.solve(assumptions=assignment), subset_size <= 1)

    def test_small_boards(self):
        expected = {1: "SAT", 2: "UNSAT", 3: "UNSAT", 4: "SAT", 5: "SAT", 8: "SAT"}
        for encoding in ENCODINGS:
            for n, status in expected.items():
                with self.subTest(encoding=encoding, n=n):
                    result = run_method(n, "sat", encoding, 10)
                    self.assertEqual(result.status, status, result.details)
                    if status == "SAT":
                        self.assertTrue(result.valid)

    def test_cp_sat_cross_check(self):
        for n in range(1, 9):
            with self.subTest(n=n):
                result = run_method(n, "cp-sat", "", 10)
                self.assertEqual(result.status, "UNSAT" if n in (2, 3) else "SAT", result.details)
                if result.status == "SAT":
                    self.assertTrue(result.valid)

    def test_cplex_mip_cross_check_when_available(self):
        for n in (1, 2, 3, 4, 8):
            with self.subTest(n=n):
                result = run_method(n, "cplex-mip", "", 10)
                if result.status == "UNAVAILABLE":
                    self.skipTest(result.details)
                self.assertEqual(result.status, "UNSAT" if n in (2, 3) else "SAT", result.details)
                if result.status == "SAT":
                    self.assertTrue(result.valid)


if __name__ == "__main__":
    unittest.main()
