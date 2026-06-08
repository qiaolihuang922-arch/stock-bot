STATE_LABELS = {
    "UNTRACKED": "未追蹤",
    "WATCH": "觀察",
    "WAIT_VOLUME": "等量能",
    "WAIT_PULLBACK": "等回測",
    "WAIT_RR": "等RR修復",
    "WAIT_COOLDOWN": "等冷卻",
    "READY": "可準備",
    "BUYABLE": "可買",
    "ENTERED_TODAY": "今日進場",
    "HOLD": "續抱",
    "REDUCE": "減碼",
    "TAKE_PROFIT": "停利",
    "STOP_LOSS": "停損",
    "CLOSED": "結案",
    "BLOCKED": "不可行動",
}

ACTION_LABELS = {
    "NONE": "不動作",
    "WATCH": "追蹤",
    "WAIT": "等待",
    "PREPARE": "準備",
    "BUY": "買入候選",
    "HOLD": "續抱",
    "REDUCE": "減碼",
    "TAKE_PROFIT": "停利",
    "STOP_LOSS": "停損",
    "BLOCK": "停止行動",
}

ACTION_BY_STATE = {
    "WATCH": "WATCH",
    "WAIT_VOLUME": "WAIT",
    "WAIT_PULLBACK": "WAIT",
    "WAIT_RR": "WAIT",
    "WAIT_COOLDOWN": "WAIT",
    "READY": "PREPARE",
    "BUYABLE": "BUY",
    "ENTERED_TODAY": "HOLD",
    "HOLD": "HOLD",
    "REDUCE": "REDUCE",
    "TAKE_PROFIT": "TAKE_PROFIT",
    "STOP_LOSS": "STOP_LOSS",
    "CLOSED": "NONE",
    "BLOCKED": "BLOCK",
}

UNHELD_FUNNEL_STATE_MAP = {
    "可買": "BUYABLE",
    "趨勢延續": "BUYABLE",
    "可準備": "READY",
    "等量能": "WAIT_VOLUME",
    "等回測": "WAIT_PULLBACK",
    "等RR修復": "WAIT_RR",
    "等冷卻": "WAIT_COOLDOWN",
    "隔日確認": "WATCH",
    "淘汰": "BLOCKED",
    "弱勢淘汰": "BLOCKED",
}

WATCH_STATE_MAP = {
    "可買": "BUYABLE",
    "等量能": "WAIT_VOLUME",
    "等回測": "WAIT_PULLBACK",
    "等RR修復": "WAIT_RR",
    "等冷卻": "WAIT_COOLDOWN",
    "隔日確認": "WATCH",
    "弱勢淘汰": "BLOCKED",
    "淘汰": "BLOCKED",
}

POSITION_ACTION_STATE_MAP = {
    "停損": "STOP_LOSS",
    "硬風控減碼": "REDUCE",
    "增量減碼": "REDUCE",
    "減碼": "REDUCE",
    "第二段停利": "TAKE_PROFIT",
    "第二段停利剩餘建議": "TAKE_PROFIT",
    "停利": "TAKE_PROFIT",
    "停利記憶不足": "BLOCKED",
    "新倉風控觀察": "ENTERED_TODAY",
    "風控觀察": "HOLD",
    "核心風控觀察": "HOLD",
    "洗盤警戒": "HOLD",
    "洗盤續抱": "HOLD",
    "減碼後觀察": "HOLD",
    "停利後觀察": "HOLD",
    "停利後核心倉": "HOLD",
    "核心續抱": "HOLD",
    "續抱觀察": "HOLD",
    "續抱": "HOLD",
}


def _as_float(value):
    try:
        if value in [None, ""]:
            return None
        return float(value)
    except (TypeError, ValueError):
        return None


def _previous_state(data):
    context = (data or {}).get("cross_day_context") or {}
    value = context.get("previous_state")
    if not value or value == "unknown":
        return None
    return str(value)


def _risk_flags(data):
    result = (data or {}).get("result") or {}
    flags = []
    if result.get("decision") == "FAIL":
        flags.append("decision_FAIL")
    if result.get("structure_phase") in {"FAILED_BREAKOUT", "WEAK_REBOUND", "DISTRIBUTION"}:
        flags.append(str(result.get("structure_phase")))
    if result.get("price_behavior") == "WEAK_REBOUND":
        flags.append("WEAK_REBOUND")
    if result.get("trade_state") in {"AVOID", "EXTENDED", "NO_VOLUME", "LATE_ENTRY"}:
        flags.append(str(result.get("trade_state")))
    rr = _as_float(result.get("rr"))
    if rr is not None and rr < 1:
        flags.append("RR_LT_1")
    return flags


def evaluate_position_state(name, data, *, summary_action=None, trigger=None):
    summary_action = summary_action or "續抱"
    state = POSITION_ACTION_STATE_MAP.get(summary_action, "HOLD")
    action = ACTION_BY_STATE.get(state, "HOLD")
    reason = summary_action
    if state == "ENTERED_TODAY":
        reason = "今日買入後先進入風控觀察"
    elif state == "BLOCKED":
        reason = "執行記憶不足，停止輸出可執行賣出股數"
    elif state in {"REDUCE", "TAKE_PROFIT", "STOP_LOSS"}:
        reason = f"持倉主行動：{summary_action}"

    return {
        "schema_version": "v21.0",
        "stock_name": name,
        "stock_code": str((data or {}).get("stock_code") or ""),
        "scope": "holding",
        "state": state,
        "state_label": STATE_LABELS[state],
        "action": action,
        "action_label": ACTION_LABELS[action],
        "previous_state": _previous_state(data),
        "transition": f"{_previous_state(data) or 'UNKNOWN'}->{state}",
        "reason": reason,
        "trigger": trigger,
        "source": "derived-readonly",
        "db_write": False,
        "schema_change": False,
        "risk_flags": _risk_flags(data),
    }


def evaluate_unheld_state(
    name,
    data,
    *,
    funnel_state=None,
    watch_state=None,
    trigger=None,
    source_status=None,
):
    result = (data or {}).get("result") or {}
    if funnel_state in UNHELD_FUNNEL_STATE_MAP:
        state = UNHELD_FUNNEL_STATE_MAP[funnel_state]
        reason = f"未持倉漏斗：{funnel_state}"
    elif watch_state in WATCH_STATE_MAP:
        state = WATCH_STATE_MAP[watch_state]
        reason = f"觀察狀態：{watch_state}"
    elif result.get("decision") == "BUY":
        state = "BUYABLE"
        reason = "策略買點成立"
    elif result.get("decision") == "FAIL":
        state = "BLOCKED"
        reason = "策略條件失敗"
    else:
        state = "WATCH"
        reason = "未達可買，保留觀察"

    if state == "BUYABLE" and result.get("decision_type") == "trend_continuation":
        reason = "趨勢延續買點成立"

    if (
        state in {"BUYABLE", "READY"}
        and source_status in {"missing-source", "source-error", "insufficient-data", "unresolved-conflict"}
    ):
        state = "BLOCKED"
        reason = "資料來源不足，停止新倉行動"

    action = ACTION_BY_STATE.get(state, "WATCH")
    return {
        "schema_version": "v21.0",
        "stock_name": name,
        "stock_code": str((data or {}).get("stock_code") or ""),
        "scope": "unheld",
        "state": state,
        "state_label": STATE_LABELS[state],
        "action": action,
        "action_label": ACTION_LABELS[action],
        "previous_state": _previous_state(data),
        "transition": f"{_previous_state(data) or 'UNKNOWN'}->{state}",
        "reason": reason,
        "trigger": trigger,
        "source": "derived-readonly",
        "db_write": False,
        "schema_change": False,
        "risk_flags": _risk_flags(data),
    }


def visible_state_line(machine_state):
    if not machine_state:
        return None
    parts = [
        f"交易狀態：{machine_state.get('state_label')}",
        f"動作：{machine_state.get('action_label')}",
    ]
    trigger = machine_state.get("trigger")
    if trigger:
        parts.append(f"觸發：{trigger}")
    return "｜".join(parts)


def build_state_artifact(results_map):
    items = []
    for name, data in (results_map or {}).items():
        state = (data or {}).get("trade_state_machine")
        if not state:
            continue
        items.append({
            "stock_name": name,
            "stock_code": state.get("stock_code"),
            "scope": state.get("scope"),
            "state": state.get("state"),
            "action": state.get("action"),
            "previous_state": state.get("previous_state"),
            "transition": state.get("transition"),
            "reason": state.get("reason"),
            "trigger": state.get("trigger"),
            "source": state.get("source"),
            "db_write": False,
            "schema_change": False,
        })
    return {
        "artifact_id": "trade_state_machine_v21",
        "schema_version": "v21.0",
        "source": "derived-readonly",
        "db_write": False,
        "schema_change": False,
        "items": items,
    }
