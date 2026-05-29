import unittest
from unittest.mock import call, patch

from services import notifier


class NotifierSendManyTest(unittest.TestCase):
    def test_reply_markup_attaches_to_last_message(self):
        reply_markup = {"inline_keyboard": [[{"text": "設定", "callback_data": "noop"}]]}

        with patch.object(notifier, "send", return_value=True) as mock_send, \
             patch.object(notifier.time, "sleep"):
            ok = notifier.send_many(["持倉詳情", "未持倉詳情", "總覽摘要"], reply_markup=reply_markup)

        self.assertTrue(ok)
        self.assertEqual(
            mock_send.call_args_list,
            [
                call("持倉詳情", reply_markup=None),
                call("未持倉詳情", reply_markup=None),
                call("總覽摘要", reply_markup=reply_markup),
            ],
        )

    def test_send_many_preserves_formatter_version_header_on_last_message(self):
        summary = "【05/28 盤中｜v20.3.0】\n今日新倉：無有效進場"

        with patch.object(notifier, "send", return_value=True) as mock_send, \
             patch.object(notifier.time, "sleep"):
            ok = notifier.send_many(["持倉詳情", "未持倉詳情", summary])

        self.assertTrue(ok)
        self.assertEqual(mock_send.call_args_list[-1], call(summary, reply_markup=None))
        self.assertIn("【05/28 盤中｜v20.3.0】", mock_send.call_args_list[-1].args[0])

    def test_reply_markup_stays_on_single_string_message(self):
        reply_markup = {"inline_keyboard": [[{"text": "設定", "callback_data": "noop"}]]}

        with patch.object(notifier, "send", return_value=True) as mock_send:
            ok = notifier.send_many("總覽摘要", reply_markup=reply_markup)

        self.assertTrue(ok)
        mock_send.assert_called_once_with("總覽摘要", reply_markup=reply_markup)


if __name__ == "__main__":
    unittest.main()
