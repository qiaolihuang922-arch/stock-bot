import runpy
import unittest
from unittest.mock import patch


class MainDeliveryGuardTest(unittest.TestCase):
    def test_failed_telegram_send_does_not_mark_sent(self):
        with patch("core.utils.sent_tag_exists", return_value=False), \
             patch("core.utils.mark_sent", side_effect=AssertionError("failed send must not mark sent")), \
             patch("core.generator.generate_report", return_value=(["msg"], None)), \
             patch("services.notifier.send_many", return_value=False):
            with self.assertRaises(SystemExit):
                runpy.run_module("main", run_name="__main__")

    def test_successful_telegram_send_marks_sent_after_send(self):
        calls = []

        def send_many(_messages, reply_markup=None):
            calls.append("send")
            return True

        def mark_sent(_tag):
            calls.append("mark")

        with patch("core.utils.sent_tag_exists", return_value=False), \
             patch("core.utils.mark_sent", side_effect=mark_sent), \
             patch("core.generator.generate_report", return_value=(["msg"], None)), \
             patch("services.notifier.send_many", side_effect=send_many):
            runpy.run_module("main", run_name="__main__")

        self.assertEqual(calls, ["send", "mark"])


if __name__ == "__main__":
    unittest.main()
