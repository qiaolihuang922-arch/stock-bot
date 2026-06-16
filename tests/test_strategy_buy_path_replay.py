from datetime import date

from scripts.audit_strategy_buy_path_replay import summarize, transition_after_state


def test_transition_after_wait_retest_counts_next_states():
    events = [
        {"stock_id": "3481", "stock_name": "群創", "trade_date": "2026-06-01", "funnel_state": "等回測", "primary_blocker": "連漲修復待回測", "close": 50},
        {"stock_id": "3481", "stock_name": "群創", "trade_date": "2026-06-02", "funnel_state": "可買", "primary_blocker": "可買", "close": 51},
        {"stock_id": "2337", "stock_name": "旺宏", "trade_date": "2026-06-01", "funnel_state": "等回測", "primary_blocker": "連漲修復待回測", "close": 150},
        {"stock_id": "2337", "stock_name": "旺宏", "trade_date": "2026-06-02", "funnel_state": "等量能", "primary_blocker": "量能不足", "close": 149},
    ]

    result = transition_after_state(events, "等回測")

    assert result["next_state_counts"] == {"可買": 1, "等量能": 1}
    assert result["examples"][0]["from_state"] == "等回測"


def test_summary_marks_deadlock_and_false_negative_without_db_writes():
    events = [
        {
            "stock_id": "3481",
            "stock_name": "群創",
            "trade_date": "2026-06-01",
            "funnel_state": "等回測",
            "snapshot_is_tradeable": True,
            "primary_blocker": "回測未確認",
            "close": 50,
        },
        {
            "stock_id": "3481",
            "stock_name": "群創",
            "trade_date": "2026-06-02",
            "funnel_state": "等量能",
            "snapshot_is_tradeable": False,
            "primary_blocker": "量能不足",
            "close": 49,
        },
    ]
    rows_by_stock = {
        "3481": [
            {"trade_date": date(2026, 6, 1)},
            {"trade_date": date(2026, 6, 2)},
        ]
    }

    artifact = summarize(events, rows_by_stock, date(2026, 6, 1), date(2026, 6, 2), "v21.1")

    assert artifact["read_only"] is True
    assert artifact["db_write"] is False
    assert artifact["schema_change"] is False
    assert artifact["live_telegram"] is False
    assert artifact["diagnosis"]["deadlock_suspected"] is True
    assert artifact["diagnosis"]["funnel_blocks_snapshot_tradeable"] is True
    assert artifact["totals"]["snapshot_tradeable_blocked_by_funnel_days"] == 1
