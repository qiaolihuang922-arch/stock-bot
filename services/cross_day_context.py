from datetime import datetime

try:
    import pytz
except ImportError:
    pytz = None

from core.watchlist import STOCKS
from services.strategy_evidence import stable_watch_category, reject_family


tz = pytz.timezone("Asia/Taipei") if pytz else None

ACTION_ALIASES = {
    "BUY": "buy",
    "買": "buy",
    "買入": "buy",
    "HOLD": "hold",
    "續抱": "hold",
    "OBSERVE": "observe",
    "觀察": "observe",
    "REDUCE": "reduce",
    "減碼": "reduce",
    "TAKE_PROFIT": "take_profit",
    "停利": "take_profit",
    "STOP": "stop_loss",
    "STOP_LOSS": "stop_loss",
    "停損": "stop_loss",
}

PERSISTENT_SOURCE_TABLES = {
    "positions",
    "position_events",
    "daily_signal_snapshot",
    "signal_runs",
    "signal_items",
    "signal_outcomes",
    "strategy_feature_snapshots",
    "strategy_outcome_metrics",
    "strategy_classification_audit",
}


def empty_cross_day_context(symbol, status="missing-source", sources=None):
    return {
        "symbol": symbol,
        "source_status": status,
        "source_of_truth": sources or [],
        "previous_state": "unknown",
        "previous_action": "unknown",
        "previous_action_date": None,
        "consecutive_observe_days": 0,
        "repair_status": "unknown",
        "failure_status": "unknown",
        "historical_evidence_weight": 0,
        "weight_reason": [],
        "dedupe_guard": "unknown" if status != "ready" else "none",
        "same_run_guard": None,
        "same_run_action": None,
        "same_run_action_date": None,
        "same_run_source": None,
        "allowed_effects": [
            "sort_priority",
            "summary_wording",
            "prepare_promotion",
            "duplicate_action_suppression",
            "risk_note",
        ],
        "forbidden_effects": [
            "cannot_flip_to_buy_alone",
            "cannot_override_hard_stop",
            "cannot_fake_execution",
            "cannot_confirm_market_evidence",
            "cannot_use_same_run_as_cross_day_memory",
        ],
    }


def stock_code_for_name(name, data=None):
    data = data or {}
    return str(data.get("stock_code") or STOCKS.get(name) or name)


def _fetch_rows(client, table, fields, limit):
    return (
        client.table(table)
        .select(fields)
        .order("trade_date", desc=True)
        .limit(limit)
        .execute()
        .data
        or []
    )


def _fetch_event_rows(client, limit):
    return (
        client.table("position_events")
        .select("stock_code,stock_name,event_date,action_label,shares_delta,created_at")
        .order("event_date", desc=True)
        .limit(limit)
        .execute()
        .data
        or []
    )


def _today_string(now=None):
    now = now or (datetime.now(tz) if tz else datetime.now())
    return now.date().isoformat() if hasattr(now, "date") else str(now)


def _state_from_feature(row):
    category = row.get("watch_category")
    family = row.get("reject_family")
    if category == "可買":
        return "buyable"
    if category == "持倉":
        return "holding"
    if category in ["可準備", "等回測", "RR不足", "追價風險"]:
        return "prepare"
    if category in ["等量能"]:
        return "observe"
    if category in ["淘汰", "弱勢淘汰"] or family in ["弱勢", "突破失敗"]:
        return "eliminated"
    if category:
        return "observe"
    return "unknown"


def _state_from_snapshot(row):
    if not row:
        return "unknown"
    action = row.get("action")
    if row.get("position_state") == "holding":
        return "holding"
    if row.get("is_tradeable"):
        return "buyable"
    if action == "BUY":
        return "buyable"
    if action == "FAIL":
        return "eliminated"
    return "observe" if row else "unknown"


def _today_state(data):
    if data.get("holding"):
        return "holding"
    category = stable_watch_category(data.get("result") or {}, holding=False)
    if category == "可買":
        return "buyable"
    if category in ["追價風險", "等回測", "RR不足"]:
        return "prepare"
    if category in ["弱勢淘汰"]:
        return "eliminated"
    return "observe"


def _is_observe_state(state):
    return state in ["observe", "prepare", "eliminated"]


def _repair_status(previous_state, today_state, data):
    result = data.get("result") or {}
    family = reject_family(result, stable_watch_category(result, holding=bool(data.get("holding"))))

    if previous_state == "unknown":
        return "unknown", "unknown"
    if today_state == "eliminated":
        return "failed", "invalidated"
    if previous_state == "eliminated" and today_state in ["prepare", "observe"]:
        return "improving", "cooling"
    if previous_state in ["observe", "prepare"] and today_state in ["prepare", "buyable"]:
        return "repaired", "still_valid"
    if family in ["弱勢", "量能不足"]:
        return "deteriorating", "cooling"
    return "unchanged", "still_valid"


def _action_from_text(text):
    raw = str(text or "").upper()
    for token, action in ACTION_ALIASES.items():
        if token.upper() in raw:
            return action
    return "unknown"


def _latest_event_action(rows, today=None):
    if not rows:
        return "unknown", None, "none"
    row = rows[0]
    action = _action_from_text(row.get("action_label"))
    date = row.get("event_date")
    if action == "unknown":
        try:
            delta = float(row.get("shares_delta") or 0)
        except (TypeError, ValueError):
            delta = 0
        if delta > 0:
            action = "buy"
        elif delta < 0:
            action = "reduce"
    guard = "none"
    if date and today and str(date) == str(today):
        guard = "same_day_executed"
    elif action == "buy":
        guard = "new_position_guard"
    elif action == "take_profit":
        guard = "prior_take_profit_completed"
    elif action == "reduce":
        guard = "prior_reduce_completed"
    return action, date, guard


def _today_event_guard(today_events):
    today_events = today_events or {}
    if today_events.get("bought_shares", 0) > 0:
        return "same_day_executed", "buy"
    if today_events.get("sold_shares", 0) > 0:
        labels = " ".join(str(item) for item in today_events.get("labels") or [])
        action = _action_from_text(labels)
        if action == "take_profit":
            return "same_day_executed", "take_profit"
        return "same_day_executed", "reduce"
    return None, None


def _evidence_weight(outcome_rows):
    if not outcome_rows:
        return 0, []
    weight = 0
    reasons = []
    for row in outcome_rows[:8]:
        try:
            close_return = float(row.get("close_return_pct") or 0)
            mfe = float(row.get("max_favorable_excursion_pct") or 0)
            mae = float(row.get("max_adverse_excursion_pct") or 0)
        except (TypeError, ValueError):
            continue
        if mfe >= 5 or close_return >= 3:
            weight += 1
        elif close_return <= -3 or mae <= -5:
            weight -= 1
    if weight > 0:
        reasons.append("歷史同類後續偏正")
    elif weight < 0:
        reasons.append("歷史同類後續偏弱")
    return max(-2, min(2, weight)), reasons[:3]


def build_cross_day_contexts(results_map, client=None, today_position_events=None, now=None, limit=240):
    contexts = {
        name: empty_cross_day_context(stock_code_for_name(name, data))
        for name, data in (results_map or {}).items()
    }
    if not results_map:
        return contexts
    if client is None:
        return contexts

    errors = []
    rows_by_table = {}
    for table, fields in [
        ("daily_signal_snapshot", "stock_id,trade_date,version,action,is_tradeable,position_state,reasons"),
        ("strategy_feature_snapshots", "stock_id,trade_date,strategy_version,watch_category,reject_family"),
        ("strategy_outcome_metrics", "stock_id,trade_date,strategy_version,watch_category,reject_family,horizon_days,close_return_pct,max_favorable_excursion_pct,max_adverse_excursion_pct,outcome_label"),
        ("strategy_classification_audit", "stock_id,trade_date,strategy_version,suggested_audit_category,severity,review_status"),
    ]:
        try:
            rows_by_table[table] = _fetch_rows(client, table, fields, limit)
        except Exception as exc:
            rows_by_table[table] = []
            errors.append(f"{table}: {exc}")

    try:
        event_rows = _fetch_event_rows(client, limit)
        rows_by_table["position_events"] = event_rows
    except Exception as exc:
        rows_by_table["position_events"] = []
        errors.append(f"position_events: {exc}")

    today = _today_string(now)
    for name, data in results_map.items():
        symbol = stock_code_for_name(name, data)
        feature_rows = [
            row for row in rows_by_table.get("strategy_feature_snapshots", [])
            if str(row.get("stock_id")) == symbol and str(row.get("trade_date")) != today
        ]
        snapshot_rows = [
            row for row in rows_by_table.get("daily_signal_snapshot", [])
            if str(row.get("stock_id")) == symbol and str(row.get("trade_date")) != today
        ]
        outcome_rows = [
            row for row in rows_by_table.get("strategy_outcome_metrics", [])
            if str(row.get("stock_id")) == symbol
        ]
        event_rows = [
            row for row in rows_by_table.get("position_events", [])
            if str(row.get("stock_code")) == symbol or row.get("stock_name") == name
        ]
        latest_feature = feature_rows[0] if feature_rows else None
        latest_snapshot = snapshot_rows[0] if snapshot_rows else None
        previous_state = (
            _state_from_feature(latest_feature)
            if latest_feature
            else _state_from_snapshot(latest_snapshot)
        )
        today_state = _today_state(data)
        repair_status, failure_status = _repair_status(previous_state, today_state, data)
        observe_days = 0
        for row in feature_rows:
            state = _state_from_feature(row)
            if not _is_observe_state(state):
                break
            observe_days += 1
        if not observe_days and _is_observe_state(previous_state):
            observe_days = 1
        previous_action, previous_action_date, dedupe_guard = _latest_event_action(event_rows, today=today)
        today_guard, today_action = _today_event_guard((today_position_events or {}).get(name, {}))
        weight, reasons = _evidence_weight(outcome_rows)
        if repair_status in ["repaired", "improving"] and weight < 1:
            weight += 1
            reasons.append("前次狀態修復中")
        if repair_status in ["failed", "deteriorating"] and weight > -1:
            weight -= 1
            reasons.append("前次狀態轉弱")

        context_sources = []
        if latest_feature:
            context_sources.append("strategy_feature_snapshots")
        if latest_snapshot:
            context_sources.append("daily_signal_snapshot")
        if outcome_rows:
            context_sources.append("strategy_outcome_metrics")
        if event_rows:
            context_sources.append("position_events")
        context_sources = [
            source for source in context_sources
            if source in PERSISTENT_SOURCE_TABLES
        ]

        status = "ready" if context_sources else "insufficient-data"
        if errors:
            status = "source-error"
        if status != "ready":
            previous_state = "unknown"
            previous_action = "unknown"
            previous_action_date = None
            observe_days = 0
            repair_status = "unknown"
            failure_status = "unknown"
            weight = 0
            reasons = []
            dedupe_guard = "unknown"
        contexts[name] = {
            **empty_cross_day_context(symbol, status=status, sources=context_sources),
            "source_status": status,
            "source_errors": errors[:3],
            "previous_state": previous_state,
            "previous_action": previous_action,
            "previous_action_date": previous_action_date,
            "consecutive_observe_days": observe_days,
            "repair_status": repair_status,
            "failure_status": failure_status,
            "historical_evidence_weight": max(-2, min(2, weight)),
            "weight_reason": reasons[:3],
            "dedupe_guard": dedupe_guard,
            "same_run_guard": today_guard,
            "same_run_action": today_action,
            "same_run_action_date": today if today_guard else None,
            "same_run_source": "today_position_events" if today_guard else None,
        }

    return contexts
