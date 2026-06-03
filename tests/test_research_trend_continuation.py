import unittest
from datetime import date, timedelta
from types import SimpleNamespace

from scripts import research_trend_continuation as research


def _trading_dates(start, count):
    current = start
    days = []
    while len(days) < count:
        if current.weekday() < 5:
            days.append(current.isoformat())
        current += timedelta(days=1)
    return days


def _sample_rows():
    rows = []
    dates = _trading_dates(date(2026, 1, 5), 45)
    for idx, trade_date in enumerate(dates):
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
        rows.append(
            {
                "stock_id": "3231",
                "trade_date": trade_date,
                "open": close - 0.2,
                "high": high,
                "low": low,
                "close": close,
                "volume": volume,
            }
        )
    return rows


class ResearchTrendContinuationTest(unittest.TestCase):
    def test_pullback_continuation_fixture_is_classified_and_summarized(self):
        bars = research.normalize_bars(_sample_rows())
        events = research.collect_events(bars)
        pullback_events = events[("pullback_continuation", None)]

        self.assertTrue(pullback_events)
        self.assertEqual(pullback_events[0]["stock_id"], "3231")

        summaries = research.summarize_events(events, min_sample=1)
        pullback = next(row for row in summaries if row["group"] == "pullback_continuation")
        self.assertGreater(pullback["sample_count"], 0)
        self.assertIn(pullback["conclusion"], ["positive", "negative"])
        rendered = research.render_report(research.build_report(summaries, len(bars), min_sample=1))
        self.assertIn("research_trend_continuation", rendered)
        self.assertIn("pullback_continuation", rendered)
        self.assertIn("extended_spike", rendered)

    def test_missing_credentials_blocks_without_synthetic_fallback(self):
        with self.assertRaises(research.ResearchBlocked) as ctx:
            research.resolve_read_credentials(env={}, config_module=SimpleNamespace())

        self.assertEqual(ctx.exception.reason, "missing-credentials")
        blocked = research.blocked_report(ctx.exception.reason, ctx.exception.detail)
        self.assertTrue(blocked["no_synthetic_data"])
        self.assertIn("status: blocked", research.render_report(blocked))

    def test_missing_required_column_blocks(self):
        rows = _sample_rows()
        rows[0].pop("low")

        with self.assertRaises(research.ResearchBlocked) as ctx:
            research.normalize_bars(rows)

        self.assertEqual(ctx.exception.reason, "missing-column")

    def test_fetch_daily_price_uses_only_select_order_range_execute(self):
        calls = []

        class Query:
            def select(self, columns):
                calls.append(("select", columns))
                return self

            def order(self, column):
                calls.append(("order", column))
                return self

            def range(self, start, end):
                calls.append(("range", start, end))
                return self

            def execute(self):
                calls.append(("execute",))
                return SimpleNamespace(data=_sample_rows()[:2])

        class Client:
            def table(self, name):
                calls.append(("table", name))
                return Query()

        rows = research.fetch_daily_price_rows(Client(), page_size=1000, max_rows=1000)
        self.assertEqual(len(rows), 2)
        self.assertNotIn("insert", str(calls).lower())
        self.assertNotIn("upsert", str(calls).lower())
        self.assertNotIn("delete", str(calls).lower())

    def test_report_includes_universe_per_symbol_and_aggregate_threshold(self):
        rows = _sample_rows()
        bars = research.normalize_bars(rows)
        events = research.collect_events(bars)
        summaries = research.summarize_events(events, min_sample=1)
        per_symbol = research.summarize_pullback_by_symbol(bars, events)

        report = research.build_report(
            summaries,
            len(rows),
            min_sample=1,
            universe=["3231"],
            date_range={"start": "2026-01-01", "end": "2026-03-31"},
            per_symbol=per_symbol,
        )

        self.assertEqual(report["source"], "daily_price")
        self.assertEqual(report["universe_symbols"], ["3231"])
        self.assertEqual(report["universe_count"], 1)
        self.assertEqual(report["per_symbol"][0]["symbol"], "3231")
        self.assertGreater(report["per_symbol"][0]["hit_count"], 0)
        self.assertEqual(
            report["aggregate"]["total_hit_count"],
            report["per_symbol"][0]["hit_count"],
        )
        self.assertTrue(report["aggregate"]["meets_min_sample_count"])
        rendered = research.render_report(report)
        self.assertIn("total_hit_count:", rendered)
        self.assertIn("per_symbol:", rendered)

    def test_watchlist_source_must_resolve_to_12_by_default(self):
        self.assertEqual(len(research.resolve_watchlist_symbols()), 12)


if __name__ == "__main__":
    unittest.main()
