import unittest
from unittest.mock import patch

import app


class RenderFreshnessPreflightTest(unittest.TestCase):
    def test_freshness_failure_blocks_dispatch_before_sent_tag(self):
        client = app.app.test_client()

        with patch.object(app, "run_market_theme_freshness_preflight", return_value=2), patch.object(
            app,
            "already_sent",
            side_effect=AssertionError("already_sent should not run on freshness failure"),
        ), patch.object(
            app.requests,
            "post",
            side_effect=AssertionError("workflow dispatch should not run on freshness failure"),
        ), patch.dict(
            app.os.environ,
            {"GITHUB_TOKEN": "token"},
            clear=False,
        ):
            response = client.get("/?test=1")

        self.assertEqual(response.status_code, 200)
        self.assertIn("freshness check failed 2", response.get_data(as_text=True))

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

        def dispatch(*args, **kwargs):
            calls.append("dispatch")
            return Response()

        with patch.object(app, "run_market_theme_freshness_preflight", freshness), patch.object(
            app,
            "already_sent",
            sent,
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
        self.assertEqual(calls, ["freshness", "sent", "dispatch"])


if __name__ == "__main__":
    unittest.main()
