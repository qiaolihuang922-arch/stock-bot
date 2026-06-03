import json
import tempfile
import unittest
from datetime import datetime
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from core import generator
from presentation import report as presentation_report
from scripts import monitor_trend_continuation as monitor
from scripts import research_trend_continuation as research
from services.analysis import (
    TREND_CONTINUATION_DEFAULT_EVIDENCE,
    detect_trend_continuation_setup,
    strategy,
)


AVAILABLE_STRATEGY_EVIDENCE = {
    "rendered_text": "策略樣本：來源可驗證｜樣本 30｜classification backtest source 可用",
    "structured_status": {
        "status": "available",
        "source": "daily_signal_snapshot",
        "row_count": 30,
        "as_of": "2026-06-02",
        "missing_fields": [],
        "completeness": "complete",
    },
}


def trend_continuation_rows():
    rows = []
    for idx in range(26):
        close = 100 + idx
        volume = 1000
        low = close - 0.5
        high = close + 1.0
        if idx == 24:
            close = 121
            low = 119.2
            volume = 600
        if idx == 25:
            close = 124
            low = 122.8
            high = 125
            volume = 1400
        rows.append({
            "stock_id": "3231",
            "trade_date": f"2026-02-{idx + 1:02d}",
            "open": close - 0.2,
            "high": high,
            "low": low,
            "close": close,
            "volume": volume,
        })
    return rows


def extended_spike_rows():
    rows = []
    for idx in range(26):
        close = 100 + idx * 0.2
        if idx == 25:
            close = 130
        rows.append({
            "stock_id": "3231",
            "trade_date": f"2026-03-{idx + 1:02d}",
            "open": close - 0.2,
            "high": close + 1,
            "low": close - 0.5,
            "close": close,
            "volume": 1800 if idx == 25 else 1000,
        })
    return rows


def strategy_from_rows(rows, evidence=TREND_CONTINUATION_DEFAULT_EVIDENCE):
    closes = [row["close"] for row in rows]
    volumes = [row["volume"] for row in rows]
    price = closes[-1]
    previous = closes[-2]
    return strategy(
        price,
        (price - previous) / previous * 100,
        sum(closes[-5:]) / 5,
        sum(closes[-20:]) / 20,
        closes,
        volumes,
        ohlcv_bars=rows,
        trend_continuation_evidence=evidence,
        stock_id="3231",
    )


def trend_payload():
    rows = trend_continuation_rows()
    closes = [row["close"] for row in rows]
    volumes = [row["volume"] for row in rows]
    price = closes[-1]
    previous = closes[-2]
    return {
        "result": strategy_from_rows(rows),
        "price": price,
        "change": (price - previous) / previous * 100,
        "price_source": "realtime",
        "daily_source": "yahoo",
        "stock_code": "3231",
        "ma5": sum(closes[-5:]) / 5,
        "ma20": sum(closes[-20:]) / 20,
        "closes": closes,
        "volumes": volumes,
        "volume_ratio": round(volumes[-1] / (sum(volumes[-10:]) / 10), 2),
        "ohlcv": rows[-1],
        "holding": None,
    }


def summary_message(messages):
    return next(message for message in messages if "🧾" in message and generator.VERSION in message)


def unheld_message(messages):
    return next(message for message in messages if "【未持倉標的】" in message)


class FakeQuery:
    def __init__(self, rows):
        self.rows = rows

    def select(self, *_args, **_kwargs):
        return self

    def eq(self, *_args, **_kwargs):
        return self

    def lte(self, *_args, **_kwargs):
        return self

    def order(self, *_args, **_kwargs):
        return self

    def limit(self, *_args, **_kwargs):
        return self

    def execute(self):
        return SimpleNamespace(data=self.rows)


class FakeMonitorClient:
    def __init__(self, tables):
        self.tables = tables

    def table(self, name):
        return FakeQuery(self.tables.get(name, []))


class TrendContinuationValidationTest(unittest.TestCase):
    def test_positive_pullback_continuation_strategy_report_and_research_parity(self):
        rows = trend_continuation_rows()
        bars = research.normalize_bars(rows)
        metrics = {index: research._series_metrics(bars, index) for index in range(len(bars))}
        research_match = research.pullback_continuation_match(bars, len(bars) - 1, metrics)
        production_match = detect_trend_continuation_setup(rows)

        result = strategy_from_rows(rows)
        messages = generator.formatTelegramMessages(
            {"緯創": trend_payload()},
            "",
            "緯創",
            90,
            {"trade_date": "2026-06-03"},
            datetime(2026, 6, 3, 10, 0),
            strategy_evidence_summary=AVAILABLE_STRATEGY_EVIDENCE,
            report_phase="盤中",
        )
        rendered = "\n\n".join(messages)

        self.assertTrue(research_match)
        self.assertEqual(production_match["trigger_date"], research_match["trigger_date"])
        self.assertEqual(result["decision_type"], "trend_continuation")
        self.assertEqual(result["decision"], "BUY")
        self.assertLessEqual(result["position"], 0.15)
        self.assertEqual(result["position_label"], "小倉")
        self.assertIn("趨勢延續", rendered)
        self.assertIn("小倉", rendered)

    def test_extended_spike_without_pullback_does_not_buy(self):
        result = strategy_from_rows(extended_spike_rows())

        self.assertNotEqual(result.get("decision_type"), "trend_continuation")
        self.assertFalse(
            result.get("decision") == "BUY"
            and result.get("decision_type") == "trend_continuation"
        )

    def test_negative_evidence_does_not_buy(self):
        result = strategy_from_rows(
            trend_continuation_rows(),
            evidence={
                "sample_n": 232,
                "win_rate_5d": 54.9,
                "avg_return_5d": -0.1,
                "polarity": "negative",
                "meets_min_sample": True,
                "source": "daily_price",
            },
        )

        self.assertEqual(result["decision"], "WAIT")
        self.assertEqual(result["decision_type"], "trend_observation")
        self.assertEqual(result["wait_reason"], "WAIT_TREND_CONTINUATION_EVIDENCE")

    def test_data_basis_hidden_but_report_context_manifest_statuses_remain(self):
        payload = trend_payload()
        with patch.object(presentation_report, "SHOW_DATA_BASIS", False):
            messages = generator.formatTelegramMessages(
                {"緯創": payload},
                "",
                "緯創",
                90,
                {"trade_date": "2026-06-03"},
                datetime(2026, 6, 3, 10, 0),
                strategy_evidence_summary=AVAILABLE_STRATEGY_EVIDENCE,
                report_phase="盤中",
            )
        context = generator.build_report_context(
            {"緯創": payload},
            {"trade_date": "2026-06-03"},
            datetime(2026, 6, 3, 10, 0),
            strategy_evidence_summary=AVAILABLE_STRATEGY_EVIDENCE,
            report_phase="盤中",
        )

        self.assertNotIn("資料依據", summary_message(messages))
        self.assertTrue(context["manifest"])
        self.assertTrue(context["source_status"])
        self.assertTrue(context["evidence_status"])

    def test_show_data_basis_true_restores_visible_text(self):
        payload = trend_payload()
        payload["price_source"] = "runtime-cache"
        with patch.object(presentation_report, "SHOW_DATA_BASIS", True):
            messages = generator.formatTelegramMessages(
                {"緯創": payload},
                "",
                "緯創",
                90,
                {"trade_date": "2026-06-03"},
                datetime(2026, 6, 3, 10, 0),
                strategy_evidence_summary=AVAILABLE_STRATEGY_EVIDENCE,
                report_phase="盤中",
            )

        self.assertIn("資料依據", summary_message(messages))

    def test_unheld_backtest_line_dedupes_same_setup_key_only(self):
        first = trend_payload()
        second = trend_payload()
        third = trend_payload()
        for payload, code, setup_key in [
            (first, "3231", "trend_continuation"),
            (second, "2421", "trend_continuation"),
            (third, "3035", "breakout_confirm"),
        ]:
            payload["stock_code"] = code
            payload["backtest_context"] = {
                "setup_key": setup_key,
                "setup": setup_key,
                "sample": 35,
                "win_rate": 60,
                "avg_return": 1.2,
            }
            payload["result"]["setup_key"] = setup_key

        messages = generator.formatTelegramMessages(
            {"緯創": first, "建準": second, "智原": third},
            "",
            "緯創",
            90,
            {"trade_date": "2026-06-03"},
            datetime(2026, 6, 3, 10, 0),
            strategy_evidence_summary=AVAILABLE_STRATEGY_EVIDENCE,
            report_phase="盤中",
        )
        unheld = unheld_message(messages)
        summary = summary_message(messages)

        self.assertNotIn("回測：樣本35", unheld)
        self.assertEqual(summary.count("回測分組"), 1)
        self.assertIn("樣本35｜參考度高｜3日勝率60%｜相對+1.2%｜略優：", summary)
        for name in ["緯創", "建準", "智原"]:
            self.assertIn(name, summary)

    def test_monitor_outputs_readonly_json_and_fail_closed_without_outcomes(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            artifact = Path(tmpdir) / "trend.json"
            artifact.write_text(json.dumps({
                "groups": [{
                    "group": "pullback_continuation",
                    "win_rate_5d": 0.5517,
                    "avg_return_5d": 0.0226,
                    "sample_count": 232,
                }]
            }), encoding="utf-8")
            args = monitor.parse_args([
                "--artifact", str(artifact),
                "--trade-date", "2026-06-03",
                "--alert-after-trades", "3",
            ])
            client = FakeMonitorClient({
                "daily_signal_snapshot": [{
                    "stock_id": "3231",
                    "trade_date": "2026-06-03",
                    "version": generator.VERSION,
                    "action": "BUY",
                    "decision_type": "trend_continuation",
                }],
                "signal_outcomes": [],
            })

            output = monitor.run_monitor(args, client=client)

        self.assertEqual(output["status"], "insufficient-data")
        self.assertEqual(output["source"], "production-read-only")
        self.assertEqual(output["setup_key"], "trend_continuation")
        self.assertEqual(output["live_hit_count"], 1)
        self.assertEqual(output["evaluated_trade_count"], 0)
        self.assertEqual(output["backtest_win_rate_5d"], 0.5517)
        self.assertFalse(output["alert"])


if __name__ == "__main__":
    unittest.main()
