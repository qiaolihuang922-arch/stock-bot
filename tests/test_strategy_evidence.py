import unittest
from datetime import datetime

from services import strategy_evidence


def result(**overrides):
    base = {
        "decision": "WAIT",
        "action": 0,
        "rr": 0.5,
        "market_grade": "B",
        "structure_state": "NORMAL",
        "structure_phase": "BREAKOUT_CONFIRM",
        "price_behavior": "NORMAL",
        "volume_state": "NORMAL",
        "heat_state": "NORMAL",
        "trade_state": "LATE_ENTRY",
        "strength": 5,
        "confidence_score": 64,
        "breakout_distance": 1.2,
    }
    base.update(overrides)
    return base


class StrategyEvidenceTest(unittest.TestCase):
    def test_feature_snapshot_uses_stable_taxonomy_without_changing_decision(self):
        data = {
            "stock_code": "2421",
            "price": 120,
            "change": 1.2,
            "closes": [100, 101, 102, 103, 104, 105, 106, 107, 108, 109, 110],
            "volumes": [1000] * 11,
            "result": result(decision="BUY", action=0.1, rr=2.0, trade_state="WAIT"),
        }

        row = strategy_evidence.feature_from_result("2421", "2026-05-26", "v20.0", data)

        self.assertEqual(row["watch_category"], "可買")
        self.assertEqual(row["reject_family"], "可買")
        self.assertEqual(data["result"]["decision"], "BUY")
        self.assertEqual(data["result"]["action"], 0.1)

    def test_build_payloads_blocks_incomplete_watchlist(self):
        payload = strategy_evidence.build_strategy_evidence_payloads(
            "v20.0",
            "收盤",
            {
                "建準": {
                    "stock_code": "2421",
                    "price": 120,
                    "change": 1.2,
                    "result": result(),
                    "closes": [100] * 20,
                    "volumes": [1000] * 20,
                }
            },
            datetime(2026, 5, 26, 13, 30),
            expected_stock_ids=["2421", "2337"],
        )

        self.assertFalse(payload["recorded"])
        self.assertEqual(payload["reason"], "incomplete_watchlist")
        self.assertEqual(payload["feature_rows"], [])

    def test_outcome_metrics_are_deterministic(self):
        feature_rows = [
            {
                "stock_id": "2421",
                "trade_date": "2026-05-01",
                "strategy_version": "v20.0",
                "watch_category": "RR不足",
                "reject_family": "RR不足",
                "price": 100,
            }
        ]
        price_rows = [
            {"stock_id": "2421", "trade_date": "2026-05-01", "open": 100, "high": 101, "low": 99, "close": 100, "volume": 1000},
            {"stock_id": "2421", "trade_date": "2026-05-02", "open": 101, "high": 104, "low": 98, "close": 103, "volume": 1000},
            {"stock_id": "2421", "trade_date": "2026-05-03", "open": 103, "high": 106, "low": 102, "close": 105, "volume": 1000},
            {"stock_id": "2222", "trade_date": "2026-05-01", "open": 100, "high": 100, "low": 100, "close": 100, "volume": 1000},
            {"stock_id": "2222", "trade_date": "2026-05-02", "open": 100, "high": 101, "low": 99, "close": 101, "volume": 1000},
            {"stock_id": "2222", "trade_date": "2026-05-03", "open": 101, "high": 102, "low": 100, "close": 102, "volume": 1000},
        ]

        rows = strategy_evidence.calculate_outcome_metrics(feature_rows, price_rows, horizons=[2])

        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["close_return_pct"], 5.0)
        self.assertEqual(rows[0]["max_favorable_excursion_pct"], 6.0)
        self.assertEqual(rows[0]["max_adverse_excursion_pct"], -2.0)
        self.assertEqual(rows[0]["best_entry_gap_pct"], -2.0)
        self.assertEqual(rows[0]["outcome_label"], "win")
        self.assertAlmostEqual(rows[0]["relative_return_pct"], 1.5)

    def test_classification_report_marks_low_sample(self):
        feature_rows = [
            {
                "stock_id": f"24{i}",
                "trade_date": "2026-05-01",
                "strategy_version": "v20.0",
                "watch_category": "RR不足",
                "reject_family": "RR不足",
            }
            for i in range(3)
        ]
        outcome_rows = [
            {
                "stock_id": f"24{i}",
                "trade_date": "2026-05-01",
                "strategy_version": "v20.0",
                "horizon_days": 3,
                "close_return_pct": 1,
                "max_favorable_excursion_pct": 2,
                "max_adverse_excursion_pct": -1,
            }
            for i in range(3)
        ]

        report = strategy_evidence.build_classification_report(feature_rows, outcome_rows, min_sample=10)
        text = strategy_evidence.format_strategy_evidence_summary(report)

        self.assertIn("RR不足｜樣本 3｜樣本不足，不判讀", text)

    def test_classification_report_separates_3d_win_rate_and_5d_mfe(self):
        feature_rows = [
            {
                "stock_id": f"24{i}",
                "trade_date": "2026-05-01",
                "strategy_version": "v20.0",
                "watch_category": "RR不足",
                "reject_family": "RR不足",
            }
            for i in range(10)
        ]
        outcome_rows = []
        for i in range(10):
            outcome_rows.append({
                "stock_id": f"24{i}",
                "trade_date": "2026-05-01",
                "strategy_version": "v20.0",
                "horizon_days": 3,
                "close_return_pct": 1 if i < 6 else -1,
                "max_favorable_excursion_pct": 2,
                "max_adverse_excursion_pct": -1,
            })
            outcome_rows.append({
                "stock_id": f"24{i}",
                "trade_date": "2026-05-01",
                "strategy_version": "v20.0",
                "horizon_days": 5,
                "close_return_pct": 2,
                "max_favorable_excursion_pct": 8,
                "max_adverse_excursion_pct": -2,
            })

        report = strategy_evidence.build_classification_report(feature_rows, outcome_rows, min_sample=10)
        text = strategy_evidence.format_strategy_evidence_summary(report)

        self.assertEqual(report["RR不足"]["win_rate"], 60)
        self.assertEqual(report["RR不足"]["mfe_horizon"], 5)
        self.assertIn("RR不足｜樣本 10｜3日勝率 60%｜5日MFE中位 +8.0%｜漏失 10", text)

    def test_audit_flags_high_momentum_weak_rebound(self):
        data = {
            "stock_code": "2337",
            "price": 160,
            "change": 5.2,
            "closes": [100, 101, 102, 103, 104, 120, 130, 140, 150, 160],
            "volumes": [1000] * 10,
            "result": result(
                rr=2.0,
                market_grade="D",
                structure_phase="WEAK_REBOUND",
                price_behavior="WEAK_REBOUND",
                trade_state="WAIT",
            ),
        }

        feature = strategy_evidence.feature_from_result("2337", "2026-05-26", "v20.0", data)
        audits = strategy_evidence.build_audit_rows([feature])

        self.assertEqual(len(audits), 1)
        self.assertIn("高波動", audits[0]["suggested_audit_category"])
        self.assertEqual(audits[0]["review_status"], "open")


if __name__ == "__main__":
    unittest.main()
