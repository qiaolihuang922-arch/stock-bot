import unittest
from unittest.mock import patch

import app


class RenderFreshnessPreflightTest(unittest.TestCase):
    def test_freshness_failure_warns_but_still_dispatches_and_marks_sent_after_success(self):
        client = app.app.test_client()
        calls = []

        class Response:
            status_code = 204
            text = ""

        def sent(tag):
            calls.append("sent")
            return False

        def mark(tag):
            calls.append("mark")

        def dispatch(*args, **kwargs):
            calls.append("dispatch")
            return Response()

        with patch.object(app, "run_market_theme_freshness_preflight", return_value=2), patch.object(
            app,
            "already_sent",
            sent,
        ), patch.object(
            app,
            "mark_sent",
            mark,
        ), patch.object(
            app.requests,
            "post",
            dispatch,
        ), patch.dict(
            app.os.environ,
            {"GITHUB_TOKEN": "token"},
            clear=False,
        ):
            response = client.get("/?test=1")

        self.assertEqual(response.status_code, 200)
        text = response.get_data(as_text=True)
        self.assertIn("✅ 測試", text)
        self.assertIn("freshness warning 2", text)
        self.assertEqual(calls, ["sent", "dispatch", "mark"])

    def test_freshness_success_runs_before_workflow_dispatch(self):
        client = app.app.test_client()
        calls = []

        class Response:
            status_code = 204
            text = ""

        def freshness():
            calls.append("freshness")
            return 0

        def sent(tag):
            calls.append("sent")
            return False

        def mark(tag):
            calls.append("mark")

        def dispatch(*args, **kwargs):
            calls.append("dispatch")
            return Response()

        with patch.object(app, "run_market_theme_freshness_preflight", freshness), patch.object(
            app,
            "already_sent",
            sent,
        ), patch.object(
            app,
            "mark_sent",
            mark,
        ), patch.object(
            app.requests,
            "post",
            dispatch,
        ), patch.dict(
            app.os.environ,
            {"GITHUB_TOKEN": "token"},
            clear=False,
        ):
            response = client.get("/?test=1")

        self.assertEqual(response.status_code, 200)
        self.assertIn("✅ 測試", response.get_data(as_text=True))
        self.assertEqual(calls, ["freshness", "sent", "dispatch", "mark"])

    def test_workflow_dispatch_failure_does_not_mark_sent(self):
        client = app.app.test_client()
        calls = []

        class Response:
            status_code = 500
            text = "boom"

        with patch.object(app, "run_market_theme_freshness_preflight", return_value=0), patch.object(
            app,
            "already_sent",
            lambda tag: False,
        ), patch.object(
            app,
            "mark_sent",
            side_effect=AssertionError("failed dispatch must not mark sent"),
        ), patch.object(
            app.requests,
            "post",
            side_effect=lambda *args, **kwargs: calls.append("dispatch") or Response(),
        ), patch.dict(
            app.os.environ,
            {"GITHUB_TOKEN": "token"},
            clear=False,
        ):
            response = client.get("/?test=1")

        self.assertEqual(response.status_code, 200)
        self.assertIn("GitHub錯誤 500", response.get_data(as_text=True))
        self.assertEqual(calls, ["dispatch"])


if __name__ == "__main__":
    unittest.main()
