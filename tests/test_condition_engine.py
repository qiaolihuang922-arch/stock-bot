import unittest

from core.condition_engine import condition_engine, summarize_conditions
from core.signal_snapshot import _reason_labels


class ConditionEngineTest(unittest.TestCase):
    def test_wait_breakout_low_rr_keeps_rr_gap_until_breakout_threshold(self):
        result = {
            "decision": "WAIT",
            "decision_type": "wait_breakout_low_rr",
            "rr": 1.2,
            "market_grade": "A",
            "structure_state": "STRONG",
            "trend": "UP",
            "volume_state": "EXPANSION",
            "risk": 0.03,
        }

        conditions = condition_engine(result)
        gaps = summarize_conditions(conditions, result["decision"])

        self.assertEqual(result["decision"], "WAIT")
        self.assertFalse(conditions["rr"])
        self.assertTrue(gaps)
        self.assertIn("rr", gaps)
        self.assertIn("RR不足", _reason_labels(result))


if __name__ == "__main__":
    unittest.main()
