import importlib
import io
import unittest
from contextlib import redirect_stdout
from unittest.mock import patch


class DiagnoseScoreDiffTest(unittest.TestCase):
    def test_import_has_no_live_fetch_side_effect_and_main_compares_patched_results(self):
        module = importlib.import_module("scripts.diagnose_score_diff")

        with patch.object(module, "load_report_daily_kline") as load_kline:
            self.assertTrue(callable(module.main))
            load_kline.assert_not_called()

        daily = [{"close": 100}]
        parts = {
            "price": 100,
            "change": 0,
            "ma5": 99,
            "ma20": 95,
            "closes": [95, 96, 97, 98, 100],
            "volumes": [1000, 1000, 1000, 1000, 1000],
        }

        def fake_strategy(_price, _change, _ma5, _ma20, _closes, _volumes):
            return {"decision": "WAIT", "confidence_score": 50, "heat_state": "NORMAL"}

        output = io.StringIO()
        with patch.object(module, "load_report_daily_kline", side_effect=[(daily, "test", None), (daily, "test", None)]), \
             patch.object(module, "_report_daily_parts", return_value=parts), \
             patch.object(module.analysis, "strategy", side_effect=fake_strategy), \
             redirect_stdout(output):
            self.assertEqual(module.main(["2344", "3481"]), 0)

        text = output.getvalue()
        self.assertIn("2344", text)
        self.assertIn("3481", text)
        self.assertIn("差异对比", text)


if __name__ == "__main__":
    unittest.main()
