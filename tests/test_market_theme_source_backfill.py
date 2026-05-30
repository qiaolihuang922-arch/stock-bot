import unittest

from scripts.backfill_market_theme_sources import (
    MARKET_INDEX,
    build_confirmed_rows,
    build_index_rows,
    build_market_breadth,
    build_member_rows,
    build_source_payloads,
)


class MarketThemeSourceBackfillTest(unittest.TestCase):
    def test_build_index_rows_uses_only_official_twse_index_names(self):
        rows = build_index_rows(
            [
                {
                    "日期": "1150529",
                    "指數": "發行量加權股價指數",
                    "收盤指數": "44,732.94",
                    "漲跌": "+",
                    "漲跌點數": "1,096.50",
                    "漲跌百分比": "2.51",
                },
                {
                    "日期": "1150529",
                    "指數": "半導體類指數",
                    "收盤指數": "1,530.59",
                    "漲跌": "+",
                    "漲跌點數": "32.22",
                    "漲跌百分比": "2.15",
                },
                {
                    "日期": "1150529",
                    "指數": "非本輪來源",
                    "收盤指數": "1",
                    "漲跌百分比": "1",
                },
            ],
            trade_date="2026-05-29",
            as_of="2026-05-29T06:00:00+00:00",
        )

        self.assertEqual(len(rows), 2)
        self.assertEqual(rows[0]["index_scope"], "market")
        self.assertIsNone(rows[0]["sector_theme_key"])
        self.assertEqual(rows[1]["index_scope"], "sector_theme")
        self.assertEqual(rows[1]["sector_theme_key"], "twse_semiconductor")
        self.assertEqual(rows[1]["source_family"], "market_data")
        self.assertEqual(rows[1]["index_method"], "external_index")

    def test_build_market_breadth_uses_official_twse_breadth(self):
        breadth = build_market_breadth(
            [
                {
                    "出表日期": "1150529",
                    "類型": "股票",
                    "上漲": "805",
                    "下跌": "202",
                    "持平": "69",
                    "漲停": "42",
                    "跌停": "0",
                }
            ],
            trade_date="2026-05-29",
        )

        self.assertEqual(breadth["denominator"], 1076)
        self.assertEqual(breadth["up_count"], 805)
        self.assertEqual(breadth["up_ratio"], round(805 / 1076, 4))

    def test_build_member_rows_uses_twse_company_profile_industry(self):
        rows = build_member_rows(
            [
                {"公司代號": "2303", "公司簡稱": "聯電", "產業別": "24"},
                {"公司代號": "3231", "公司簡稱": "緯創", "產業別": "25"},
                {"公司代號": "9999", "公司簡稱": "非觀察", "產業別": "24"},
            ],
            watchlist_codes={"2303", "3231"},
            as_of="2026-05-29T06:00:00+00:00",
        )

        self.assertEqual(len(rows), 2)
        self.assertEqual({row["source_family"] for row in rows}, {"market_data"})
        self.assertEqual(
            {row["sector_theme_key"] for row in rows},
            {"twse_semiconductor", "twse_computer_peripheral"},
        )

    def test_build_confirmed_rows_from_official_index_and_breadth(self):
        index_rows = build_index_rows(
            [
                {"日期": "1150529", "指數": "發行量加權股價指數", "收盤指數": "44732.94", "漲跌百分比": "2.51"},
                {"日期": "1150529", "指數": "電子工業類指數", "收盤指數": "2928.42", "漲跌百分比": "2.62"},
            ],
            trade_date="2026-05-29",
            as_of="2026-05-29T06:00:00+00:00",
        )
        breadth = build_market_breadth(
            [{"出表日期": "1150529", "類型": "股票", "上漲": "805", "下跌": "202", "持平": "69"}],
            trade_date="2026-05-29",
        )

        confirmed = build_confirmed_rows(index_rows, breadth, as_of="2026-05-29T06:00:00+00:00")

        self.assertEqual(len(confirmed), 1)
        row = confirmed[0]
        self.assertEqual(row["market_index"], MARKET_INDEX)
        self.assertEqual(row["source_family"], "market_data")
        self.assertEqual(row["source_name"], "twse_openapi_mi_index")
        self.assertEqual(row["freshness"], "fresh")
        self.assertEqual(row["sector_theme_key"], "twse_electronics")
        self.assertEqual(row["metadata"]["source_quality"], "official_twse_openapi")
        self.assertTrue(row["metadata"]["external_market_index"])

    def test_build_source_payloads_blocks_without_official_index_rows(self):
        payloads = build_source_payloads([], [], [], trade_date="2026-05-29")

        self.assertEqual(payloads["status"], "blocked")
        self.assertEqual(payloads["index_rows"], [])
        self.assertEqual(payloads["confirmed_rows"], [])


if __name__ == "__main__":
    unittest.main()
