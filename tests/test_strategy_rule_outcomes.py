from datetime import date

from scripts.audit_strategy_rule_outcomes import (
    attach_outcomes,
    group_outcomes,
    summarize_rule_outcomes,
)


def _rows(values):
    return [
        {"trade_date": date(2026, 6, idx + 1), "close": value, "volume": 1000}
        for idx, value in enumerate(values)
    ]


def test_attach_outcomes_uses_forward_daily_price_without_writes():
    events = [{
        "stock_id": "2337",
        "trade_date": "2026-06-01",
        "close": 100,
        "funnel_state": "可買",
        "primary_blocker": "可買",
    }]

    enriched = attach_outcomes(events, {"2337": _rows([100, 103, 101, 106, 110, 108, 112, 115, 113, 118, 120])})

    assert enriched[0]["outcomes"]["1d"]["return_pct"] == 3.0
    assert enriched[0]["outcomes"]["3d"]["return_pct"] == 6.0
    assert enriched[0]["outcomes"]["10d"]["return_pct"] == 20.0
    assert enriched[0]["outcomes"]["3d"]["max_adverse_pct"] == 1.0


def test_group_outcomes_flags_blocker_that_later_runs_up():
    events = []
    for idx in range(20):
        events.append({
            "funnel_state": "等回測",
            "primary_blocker": "量能不足",
            "outcomes": {
                "5d": {
                    "status": "ready",
                    "return_pct": 3,
                    "max_favorable_pct": 5,
                    "max_adverse_pct": -1,
                }
            },
        })

    grouped = group_outcomes(events, "primary_blocker")

    assert grouped["量能不足"]["5d"]["win_rate_pct"] == 100.0
    assert grouped["量能不足"]["verdict"]["verdict"] == "audit_needed_maybe_too_strict"


def test_summary_artifact_is_readonly_and_collects_flags():
    events = []
    for idx in range(20):
        events.append({
            "stock_id": "2337",
            "stock_name": "旺宏",
            "trade_date": "2026-06-01",
            "close": 100,
            "funnel_state": "等量能",
            "primary_blocker": "量能不足",
            "decision_type": "wait_breakout_confirm",
            "entry_quality": "C",
            "volume_state": "WEAK",
            "heat_state": "NORMAL",
        })
    rows_by_stock = {"2337": _rows([100, 101, 102, 103, 104, 105, 106, 107, 108, 109, 110])}

    artifact = summarize_rule_outcomes(events, rows_by_stock, date(2026, 6, 1), date(2026, 6, 10), "v21.1")

    assert artifact["read_only"] is True
    assert artifact["db_write"] is False
    assert artifact["schema_change"] is False
    assert artifact["live_telegram"] is False
    assert artifact["by_funnel_state"]["等量能"]["sample"] == 20
    assert artifact["flags"]
