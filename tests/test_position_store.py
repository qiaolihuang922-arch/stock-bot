import unittest
from types import SimpleNamespace
from unittest.mock import patch

from services import position_store


class PositionStoreFailClosedTest(unittest.TestCase):
    def test_missing_supabase_config_returns_no_fallback_positions(self):
        with patch.object(position_store, "_client", return_value=None):
            positions = position_store.load_positions()

        self.assertEqual(positions, {})
        self.assertIn("missing-source", position_store.get_position_store_warning())

    def test_position_db_error_returns_no_fallback_positions(self):
        class FailingClient:
            def table(self, _name):
                raise RuntimeError("db unavailable")

        with patch.object(position_store, "_client", return_value=FailingClient()):
            positions = position_store.load_positions()

        self.assertEqual(positions, {})
        self.assertIn("source-error", position_store.get_position_store_warning())

    def test_empty_position_table_returns_unavailable_not_zero_share_defaults(self):
        class EmptyQuery:
            def select(self, _fields):
                return self

            def execute(self):
                return SimpleNamespace(data=[])

        class EmptyClient:
            def table(self, _name):
                return EmptyQuery()

        with patch.object(position_store, "_client", return_value=EmptyClient()):
            positions = position_store.load_positions()

        self.assertEqual(positions, {})
        self.assertIn("unavailable", position_store.get_position_store_warning())

    def test_position_events_db_error_returns_unavailable_not_zero_events(self):
        class FailingEventQuery:
            def select(self, _fields):
                return self

            def eq(self, *_args):
                return self

            def order(self, _field):
                return self

            def execute(self):
                raise RuntimeError("events unavailable")

        class FailingEventClient:
            def table(self, _name):
                return FailingEventQuery()

        with patch.object(position_store, "_client", return_value=FailingEventClient()):
            events = position_store.load_today_position_events()

        self.assertNotIn("英業達", events)
        self.assertFalse(events["available"])
        self.assertFalse(events["today_events_known"])
        self.assertIn("source-error", position_store.get_position_store_warning())

    def test_empty_position_events_query_is_real_zero_event_summary(self):
        class EmptyEventQuery:
            def select(self, _fields):
                return self

            def eq(self, *_args):
                return self

            def order(self, _field):
                return self

            def execute(self):
                return SimpleNamespace(data=[])

        class EmptyEventClient:
            def table(self, _name):
                return EmptyEventQuery()

        with patch.object(position_store, "_client", return_value=EmptyEventClient()):
            events = position_store.load_today_position_events()

        self.assertIn("英業達", events)
        self.assertTrue(events["英業達"]["available"])
        self.assertTrue(events["英業達"]["today_events_known"])
        self.assertEqual(events["英業達"]["event_count"], 0)


if __name__ == "__main__":
    unittest.main()
