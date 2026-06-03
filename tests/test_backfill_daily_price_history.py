import unittest
from datetime import date
from types import SimpleNamespace

from scripts import backfill_daily_price_history as backfill


def _rows(symbol="3231"):
    return [
        {
            "stock_id": symbol,
            "trade_date": date(2026, 6, 1),
            "open": 10.0,
            "high": 11.0,
            "low": 9.5,
            "close": 10.5,
            "volume": 1000,
            "source": "twse",
        },
        {
            "stock_id": symbol,
            "trade_date": date(2026, 6, 2),
            "open": 10.5,
            "high": 11.5,
            "low": 10.0,
            "close": 11.0,
            "volume": 1200,
            "source": "twse",
        },
    ]


class FakeQuery:
    def __init__(self, client, table_name):
        self.client = client
        self.table_name = table_name

    def select(self, columns):
        self.client.calls.append((self.table_name, "select", columns))
        return self

    def in_(self, column, values):
        self.client.calls.append((self.table_name, "in", column, tuple(values)))
        return self

    def gte(self, column, value):
        self.client.calls.append((self.table_name, "gte", column, value))
        return self

    def lte(self, column, value):
        self.client.calls.append((self.table_name, "lte", column, value))
        return self

    def upsert(self, rows, on_conflict=None):
        self.client.calls.append((self.table_name, "upsert", len(rows), on_conflict))
        self.client.upserted.extend(rows)
        return self

    def execute(self):
        self.client.calls.append((self.table_name, "execute"))
        return SimpleNamespace(data=self.client.existing_rows)


class FakeClient:
    def __init__(self, existing_rows=None):
        self.calls = []
        self.existing_rows = existing_rows or []
        self.upserted = []

    def table(self, table_name):
        self.calls.append(("table", table_name))
        return FakeQuery(self, table_name)


class BackfillDailyPriceHistoryTest(unittest.TestCase):
    def test_dry_run_plans_rows_without_write(self):
        args = backfill.parse_args([
            "--dry-run",
            "--symbols",
            "3231",
            "--start",
            "2026-06-01",
            "--end",
            "2026-06-02",
        ])

        report, exit_code = backfill.build_report(
            args,
            market_loader=lambda symbol, start, end: _rows(symbol),
        )

        self.assertEqual(exit_code, 0)
        self.assertEqual(report["mode"], "dry-run")
        self.assertEqual(report["result"], "no-write")
        self.assertEqual(report["universe_symbols"], ["3231"])
        self.assertEqual(report["per_symbol"][0]["planned_rows"], 2)
        self.assertEqual(report["per_symbol"][0]["rows_to_write"], 2)
        self.assertFalse(report["live_write"])

    def test_symbols_limits_universe_and_skip_existing(self):
        client = FakeClient(existing_rows=[{"stock_id": "3231", "trade_date": "2026-06-01"}])
        args = backfill.parse_args([
            "--dry-run",
            "--symbols",
            "3231,2421",
            "--start",
            "2026-06-01",
            "--end",
            "2026-06-02",
            "--skip-existing",
        ])

        report, exit_code = backfill.build_report(
            args,
            client=client,
            market_loader=lambda symbol, start, end: _rows(symbol),
        )

        self.assertEqual(exit_code, 0)
        self.assertEqual(report["universe_symbols"], ["3231", "2421"])
        by_symbol = {row["symbol"]: row for row in report["per_symbol"]}
        self.assertEqual(by_symbol["3231"]["existing_rows"], 1)
        self.assertEqual(by_symbol["3231"]["rows_to_write"], 1)
        self.assertEqual(by_symbol["2421"]["rows_to_write"], 2)

    def test_write_uses_approved_daily_price_upsert_and_read_after_write(self):
        client = FakeClient()
        args = backfill.parse_args([
            "--write",
            "--confirm-write",
            "--read-after-write",
            "--symbols",
            "3231",
            "--start",
            "2026-06-01",
            "--end",
            "2026-06-02",
        ])

        def loader(symbol, start, end):
            rows = _rows(symbol)
            client.existing_rows = [
                {"stock_id": row["stock_id"], "trade_date": row["trade_date"].isoformat()}
                for row in rows
            ]
            return rows

        report, exit_code = backfill.build_report(args, client=client, market_loader=loader)

        self.assertEqual(exit_code, 0)
        self.assertEqual(report["result"], "write-complete")
        self.assertIn(
            ("daily_price", "upsert", 2, "stock_id,trade_date"),
            client.calls,
        )
        self.assertEqual(report["read_after_write"]["status"], "ok")
        self.assertNotIn("daily_signal_snapshot", str(client.calls))

    def test_missing_credentials_blocks_when_write_needs_client(self):
        with self.assertRaises(backfill.BackfillBlocked) as ctx:
            backfill.build_supabase_client(env={}, config_module=SimpleNamespace())

        self.assertEqual(ctx.exception.reason, "missing-credentials")

    def test_market_source_error_blocks_without_write(self):
        args = backfill.parse_args([
            "--dry-run",
            "--symbols",
            "3231",
            "--start",
            "2026-06-01",
            "--end",
            "2026-06-02",
        ])

        report, exit_code = backfill.build_report(
            args,
            market_loader=lambda symbol, start, end: [],
        )

        self.assertEqual(exit_code, 2)
        self.assertEqual(report["status"], "blocked")
        self.assertEqual(report["fail_closed_reason"], "source-error")
        self.assertFalse(report["live_write"])


if __name__ == "__main__":
    unittest.main()
