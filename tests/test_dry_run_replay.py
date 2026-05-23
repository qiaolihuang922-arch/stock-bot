import unittest
from datetime import date

from scripts.dry_run_replay import build_replay_rows


class DryRunReplayTest(unittest.TestCase):
    def test_replay_outputs_requested_window_only(self):
        rows = build_replay_rows(
            ["3231", "2421"],
            date(2026, 5, 11),
            date(2026, 5, 15),
            "v19.0"
        )

        self.assertEqual(len(rows), 10)
        self.assertEqual({row["version"] for row in rows}, {"v19.0"})
        self.assertEqual(
            sorted({row["trade_date"] for row in rows}),
            [
                "2026-05-11",
                "2026-05-12",
                "2026-05-13",
                "2026-05-14",
                "2026-05-15"
            ]
        )

    def test_replay_marks_only_one_best_candidate_per_day(self):
        rows = build_replay_rows(
            ["3231", "2421", "3035"],
            date(2026, 5, 11),
            date(2026, 5, 13),
            "v19.0"
        )

        for trade_date in {row["trade_date"] for row in rows}:
            daily = [row for row in rows if row["trade_date"] == trade_date]
            self.assertLessEqual(
                sum(1 for row in daily if row["is_best_candidate"]),
                1
            )


if __name__ == "__main__":
    unittest.main()
