import unittest

from core.watchlist import STOCKS, WATCHLIST_CODES
from scripts.dry_run_replay import DEFAULT_WATCHLIST


class WatchlistAlignmentTest(unittest.TestCase):
    def test_shared_watchlist_has_12_configured_stocks(self):
        self.assertEqual(len(STOCKS), 12)

    def test_backfill_default_watchlist_matches_generator(self):
        self.assertEqual(DEFAULT_WATCHLIST, WATCHLIST_CODES)
        self.assertEqual(set(DEFAULT_WATCHLIST), set(STOCKS.values()))


if __name__ == "__main__":
    unittest.main()
