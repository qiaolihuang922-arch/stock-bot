import unittest
from datetime import date

from services.stock_api import parse_twse_date, parse_twse_number


class StockApiHistoryTest(unittest.TestCase):
    def test_parse_twse_roc_date(self):
        self.assertEqual(parse_twse_date("115/05/22"), date(2026, 5, 22))

    def test_parse_twse_western_date(self):
        self.assertEqual(parse_twse_date("2026/05/22"), date(2026, 5, 22))

    def test_parse_twse_number(self):
        self.assertEqual(parse_twse_number("1,234,567"), 1234567.0)
        self.assertIsNone(parse_twse_number("--"))


if __name__ == "__main__":
    unittest.main()
