STATE_LABELS = {
    "UNTRACKED": "未追蹤",
    "WATCH": "觀察",
    "WAIT_DATA": "等資料",
    "WAIT_MARKET": "等市場",
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

NEXT_EVENT_LABELS = {
    "ADD_TO_WATCHLIST": "加入追蹤",
    "SETUP_FORMED": "出現 setup",
    "DATA_RESTORED": "資料恢復",
    "MARKET_STRENGTH_CONFIRMED": "市場轉強",
    "VOLUME_CONFIRMED": "量能確認",
    "PULLBACK_CONFIRMED": "回測確認",
    "RR_REPAIRED": "RR修復",
    "COOLDOWN_FINISHED": "冷卻完成",
    "OPEN_CONFIRMATION": "開盤確認",
    "SUBMIT_ORDER": "送單前確認",
}

ACTION_BY_STATE = {
    "WATCH": "WATCH",
    "WAIT_DATA": "WAIT",
    "WAIT_MARKET": "WAIT",
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

UNHELD_STATE_META = {
    "UNTRACKED": {
        "phase": "DISCOVERY",
        "is_actionable": False,
        "is_terminal": False,
        "next_required_event": "ADD_TO_WATCHLIST",
    },
    "WATCH": {
        "phase": "WATCHLIST",
        "is_actionable": False,
        "is_terminal": False,
        "next_required_event": "SETUP_FORMED",
    },
    "WAIT_DATA": {
        "phase": "DATA_GATE",
        "is_actionable": False,
        "is_terminal": False,
        "next_required_event": "DATA_RESTORED",
    },
    "WAIT_MARKET": {
        "phase": "MARKET_GATE",
        "is_actionable": False,
        "is_terminal": False,
        "next_required_event": "MARKET_STRENGTH_CONFIRMED",
    },
    "WAIT_VOLUME": {
        "phase": "ENTRY_GATE",
        "is_actionable": False,
        "is_terminal": False,
        "next_required_event": "VOLUME_CONFIRMED",
    },
    "WAIT_PULLBACK": {
        "phase": "ENTRY_GATE",
        "is_actionable": False,
        "is_terminal": False,
        "next_required_event": "PULLBACK_CONFIRMED",
    },
    "WAIT_RR": {
        "phase": "RISK_REWARD_GATE",
        "is_actionable": False,
        "is_terminal": False,
        "next_required_event": "RR_REPAIRED",
    },
    "WAIT_COOLDOWN": {
        "phase": "COOLDOWN_GATE",
        "is_actionable": False,
        "is_terminal": False,
        "next_required_event": "HEAT_COOLDOWN_CONFIRMED",
    },
    "READY": {
        "phase": "ARMED",
        "is_actionable": False,
        "is_terminal": False,
        "next_required_event": "OPEN_CONFIRMATION",
    },
    "BUYABLE": {
        "phase": "ACTIONABLE",
        "is_actionable": True,
        "is_terminal": False,
        "next_required_event": "SUBMIT_ORDER",
    },
    "BLOCKED": {
        "phase": "BLOCKED",
        "is_actionable": False,
        "is_terminal": False,
        "next_required_event": "BLOCKER_CLEARED",
    },
}

UNHELD_TRANSITION_TABLE = {
    "UNKNOWN": {
        "DATA_GATE_FAILED": "WAIT_DATA",
        "MARKET_GATE_FAILED": "WAIT_MARKET",
        "VOLUME_GATE_FAILED": "WAIT_VOLUME",
        "PULLBACK_GATE_FAILED": "WAIT_PULLBACK",
        "RR_GATE_FAILED": "WAIT_RR",
        "COOLDOWN_GATE_FAILED": "WAIT_COOLDOWN",
        "SETUP_READY": "READY",
        "BUY_SIGNAL_CONFIRMED": "BUYABLE",
        "HARD_BLOCKED": "BLOCKED",
        "WATCHLIST_RETAINED": "WATCH",
    },
    "WATCH": {
        "DATA_GATE_FAILED": "WAIT_DATA",
        "MARKET_GATE_FAILED": "WAIT_MARKET",
        "VOLUME_GATE_FAILED": "WAIT_VOLUME",
        "PULLBACK_GATE_FAILED": "WAIT_PULLBACK",
        "RR_GATE_FAILED": "WAIT_RR",
        "COOLDOWN_GATE_FAILED": "WAIT_COOLDOWN",
        "SETUP_READY": "READY",
        "BUY_SIGNAL_CONFIRMED": "BUYABLE",
        "HARD_BLOCKED": "BLOCKED",
        "WATCHLIST_RETAINED": "WATCH",
    },
    "WAIT_DATA": {
        "DATA_GATE_FAILED": "WAIT_DATA",
        "MARKET_GATE_FAILED": "WAIT_MARKET",
        "VOLUME_GATE_FAILED": "WAIT_VOLUME",
        "PULLBACK_GATE_FAILED": "WAIT_PULLBACK",
        "RR_GATE_FAILED": "WAIT_RR",
        "COOLDOWN_GATE_FAILED": "WAIT_COOLDOWN",
        "SETUP_READY": "READY",
        "BUY_SIGNAL_CONFIRMED": "BUYABLE",
        "HARD_BLOCKED": "BLOCKED",
        "WATCHLIST_RETAINED": "WATCH",
    },
    "WAIT_MARKET": {
        "DATA_GATE_FAILED": "WAIT_DATA",
        "MARKET_GATE_FAILED": "WAIT_MARKET",
        "VOLUME_GATE_FAILED": "WAIT_VOLUME",
        "PULLBACK_GATE_FAILED": "WAIT_PULLBACK",
        "RR_GATE_FAILED": "WAIT_RR",
        "COOLDOWN_GATE_FAILED": "WAIT_COOLDOWN",
        "SETUP_READY": "READY",
        "BUY_SIGNAL_CONFIRMED": "BUYABLE",
        "HARD_BLOCKED": "BLOCKED",
        "WATCHLIST_RETAINED": "WATCH",
    },
    "WAIT_VOLUME": {
        "DATA_GATE_FAILED": "WAIT_DATA",
        "MARKET_GATE_FAILED": "WAIT_MARKET",
        "VOLUME_GATE_FAILED": "WAIT_VOLUME",
        "PULLBACK_GATE_FAILED": "WAIT_PULLBACK",
        "RR_GATE_FAILED": "WAIT_RR",
        "COOLDOWN_GATE_FAILED": "WAIT_COOLDOWN",
        "SETUP_READY": "READY",
        "BUY_SIGNAL_CONFIRMED": "BUYABLE",
        "HARD_BLOCKED": "BLOCKED",
        "WATCHLIST_RETAINED": "WATCH",
    },
    "WAIT_PULLBACK": {
        "DATA_GATE_FAILED": "WAIT_DATA",
        "MARKET_GATE_FAILED": "WAIT_MARKET",
        "VOLUME_GATE_FAILED": "WAIT_VOLUME",
        "PULLBACK_GATE_FAILED": "WAIT_PULLBACK",
        "RR_GATE_FAILED": "WAIT_RR",
        "COOLDOWN_GATE_FAILED": "WAIT_COOLDOWN",
        "SETUP_READY": "READY",
        "BUY_SIGNAL_CONFIRMED": "BUYABLE",
        "HARD_BLOCKED": "BLOCKED",
        "WATCHLIST_RETAINED": "WATCH",
    },
    "WAIT_RR": {
        "DATA_GATE_FAILED": "WAIT_DATA",
        "MARKET_GATE_FAILED": "WAIT_MARKET",
        "VOLUME_GATE_FAILED": "WAIT_VOLUME",
        "PULLBACK_GATE_FAILED": "WAIT_PULLBACK",
        "RR_GATE_FAILED": "WAIT_RR",
        "COOLDOWN_GATE_FAILED": "WAIT_COOLDOWN",
        "SETUP_READY": "READY",
        "BUY_SIGNAL_CONFIRMED": "BUYABLE",
        "HARD_BLOCKED": "BLOCKED",
        "WATCHLIST_RETAINED": "WATCH",
    },
    "WAIT_COOLDOWN": {
        "DATA_GATE_FAILED": "WAIT_DATA",
        "MARKET_GATE_FAILED": "WAIT_MARKET",
        "VOLUME_GATE_FAILED": "WAIT_VOLUME",
        "PULLBACK_GATE_FAILED": "WAIT_PULLBACK",
        "RR_GATE_FAILED": "WAIT_RR",
        "COOLDOWN_GATE_FAILED": "WAIT_COOLDOWN",
        "SETUP_READY": "READY",
        "BUY_SIGNAL_CONFIRMED": "BUYABLE",
        "HARD_BLOCKED": "BLOCKED",
        "WATCHLIST_RETAINED": "WATCH",
    },
    "READY": {
        "DATA_GATE_FAILED": "WAIT_DATA",
        "MARKET_GATE_FAILED": "WAIT_MARKET",
        "VOLUME_GATE_FAILED": "WAIT_VOLUME",
        "PULLBACK_GATE_FAILED": "WAIT_PULLBACK",
        "RR_GATE_FAILED": "WAIT_RR",
        "COOLDOWN_GATE_FAILED": "WAIT_COOLDOWN",
        "SETUP_READY": "READY",
        "BUY_SIGNAL_CONFIRMED": "BUYABLE",
        "HARD_BLOCKED": "BLOCKED",
        "WATCHLIST_RETAINED": "WATCH",
    },
    "BUYABLE": {
        "DATA_GATE_FAILED": "WAIT_DATA",
        "MARKET_GATE_FAILED": "WAIT_MARKET",
        "VOLUME_GATE_FAILED": "WAIT_VOLUME",
        "PULLBACK_GATE_FAILED": "WAIT_PULLBACK",
        "RR_GATE_FAILED": "WAIT_RR",
        "COOLDOWN_GATE_FAILED": "WAIT_COOLDOWN",
        "SETUP_READY": "READY",
        "BUY_SIGNAL_CONFIRMED": "BUYABLE",
        "HARD_BLOCKED": "BLOCKED",
        "WATCHLIST_RETAINED": "WATCH",
    },
    "BLOCKED": {
        "DATA_GATE_FAILED": "WAIT_DATA",
        "MARKET_GATE_FAILED": "WAIT_MARKET",
        "VOLUME_GATE_FAILED": "WAIT_VOLUME",
        "PULLBACK_GATE_FAILED": "WAIT_PULLBACK",
        "RR_GATE_FAILED": "WAIT_RR",
        "COOLDOWN_GATE_FAILED": "WAIT_COOLDOWN",
        "SETUP_READY": "READY",
        "BUY_SIGNAL_CONFIRMED": "BUYABLE",
        "HARD_BLOCKED": "BLOCKED",
        "WATCHLIST_RETAINED": "WATCH",
    },
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


def _source_blocker(source_status):
    if source_status in {"missing-source", "source-error", "insufficient-data", "unresolved-conflict"}:
        return {
            "missing-source": "DATA_MISSING",
            "source-error": "DATA_SOURCE_ERROR",
            "insufficient-data": "DATA_INSUFFICIENT",
            "unresolved-conflict": "DATA_CONFLICT",
        }.get(source_status, "DATA_GATE")
    return None


def _unheld_guard_snapshot(data, source_status=None):
    result = (data or {}).get("result") or {}
    guards = []
    source_blocker = _source_blocker(source_status)
    if source_blocker:
        guards.append(source_blocker)
    if result.get("market_grade") in {"D", "E"} or result.get("market_state") in {"weak", "bear"}:
        guards.append("MARKET_WEAK")
    if result.get("volume_state") == "WEAK" or result.get("trade_state") == "NO_VOLUME":
        guards.append("VOLUME_WEAK")
    rr = _as_float(result.get("rr"))
    if rr is None:
        guards.append("RR_MISSING")
    elif rr < 1.5:
        guards.append("RR_BELOW_MIN")
    if result.get("heat_state") in {"HOT", "EXTREME"} or result.get("trade_state") in {"EXTENDED", "AVOID"}:
        guards.append("HEAT_NOT_COOL")
    if result.get("structure_phase") in {"FAILED_BREAKOUT", "WEAK_REBOUND", "DISTRIBUTION"}:
        guards.append("STRUCTURE_FAILED")
    distance = _as_float(result.get("breakout_distance") or result.get("distance_to_breakout"))
    if distance is not None and distance > 4:
        guards.append("TOO_FAR_FROM_TRIGGER")
    quality = result.get("entry_quality")
    if quality and quality not in {"A+", "A", "B"}:
        guards.append("ENTRY_QUALITY_LOW")
    return list(dict.fromkeys(guards))


def _transition_event_for_state(state, *, source_status=None):
    if _source_blocker(source_status) and state in {"BUYABLE", "READY", "BLOCKED"}:
        return "DATA_GATE_FAILED"
    return {
        "UNTRACKED": "NOT_IN_WATCHLIST",
        "WATCH": "WATCHLIST_RETAINED",
        "WAIT_DATA": "DATA_GATE_FAILED",
        "WAIT_MARKET": "MARKET_GATE_FAILED",
        "WAIT_VOLUME": "VOLUME_GATE_FAILED",
        "WAIT_PULLBACK": "PULLBACK_GATE_FAILED",
        "WAIT_RR": "RR_GATE_FAILED",
        "WAIT_COOLDOWN": "COOLDOWN_GATE_FAILED",
        "READY": "SETUP_READY",
        "BUYABLE": "BUY_SIGNAL_CONFIRMED",
        "BLOCKED": "HARD_BLOCKED",
    }.get(state, "STATE_EVALUATED")


def _initial_unheld_target_state(data, *, funnel_state=None, watch_state=None):
    result = (data or {}).get("result") or {}
    if funnel_state in UNHELD_FUNNEL_STATE_MAP:
        return UNHELD_FUNNEL_STATE_MAP[funnel_state], f"未持倉漏斗：{funnel_state}"
    if watch_state in WATCH_STATE_MAP:
        return WATCH_STATE_MAP[watch_state], f"觀察狀態：{watch_state}"
    if result.get("decision") == "BUY":
        return "BUYABLE", "策略買點成立"
    if result.get("decision") == "FAIL":
        return "BLOCKED", "策略條件失敗"
    return "WATCH", "未達可買，保留觀察"


def _unheld_event_from_target(target_state, *, source_status=None, guards=None):
    if _source_blocker(source_status) and target_state in {"BUYABLE", "READY"}:
        return "DATA_GATE_FAILED"
    guard_set = set(guards or [])
    if target_state == "WATCH":
        if "VOLUME_WEAK" in guard_set:
            return "VOLUME_GATE_FAILED"
        if "HEAT_NOT_COOL" in guard_set:
            return "COOLDOWN_GATE_FAILED"
        if "RR_BELOW_MIN" in guard_set or "RR_MISSING" in guard_set:
            return "RR_GATE_FAILED"
        if "TOO_FAR_FROM_TRIGGER" in guard_set:
            return "PULLBACK_GATE_FAILED"
        if "MARKET_WEAK" in guard_set:
            return "MARKET_GATE_FAILED"
        if _source_blocker(source_status):
            return "DATA_GATE_FAILED"
    return _transition_event_for_state(target_state, source_status=source_status)


def _apply_unheld_transition(previous_state, event):
    origin = previous_state or "UNKNOWN"
    transitions = UNHELD_TRANSITION_TABLE.get(origin) or UNHELD_TRANSITION_TABLE["UNKNOWN"]
    if event in transitions:
        return {
            "from": origin,
            "event": event,
            "to": transitions[event],
            "allowed": True,
            "table": "UNHELD_TRANSITION_TABLE",
        }
    return {
        "from": origin,
        "event": event,
        "to": "BLOCKED",
        "allowed": False,
        "table": "UNHELD_TRANSITION_TABLE",
    }


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
    target_state, reason = _initial_unheld_target_state(
        data,
        funnel_state=funnel_state,
        watch_state=watch_state,
    )

    if target_state == "BUYABLE" and result.get("decision_type") == "trend_continuation":
        reason = "趨勢延續買點成立"

    guards = _unheld_guard_snapshot(data, source_status)
    event = _unheld_event_from_target(target_state, source_status=source_status, guards=guards)
    transition_result = _apply_unheld_transition(_previous_state(data), event)
    state = transition_result["to"]
    if event == "DATA_GATE_FAILED" and target_state in {"BUYABLE", "READY"}:
        reason = "資料來源不足，停止新倉行動"

    action = ACTION_BY_STATE.get(state, "WATCH")
    meta = UNHELD_STATE_META.get(state, UNHELD_STATE_META["WATCH"])
    source_blocker = _source_blocker(source_status)
    blocked_by = []
    if source_blocker:
        blocked_by.append(source_blocker)
    if state == "WAIT_VOLUME":
        blocked_by.append("VOLUME_WEAK")
    elif state == "WAIT_PULLBACK":
        blocked_by.append("PULLBACK_NOT_CONFIRMED")
    elif state == "WAIT_RR":
        blocked_by.append("RR_BELOW_MIN")
    elif state == "WAIT_COOLDOWN":
        blocked_by.append("HEAT_NOT_COOL")
    elif state == "BLOCKED" and not blocked_by:
        blocked_by.extend(
            guard for guard in guards
            if guard in {"STRUCTURE_FAILED", "MARKET_WEAK", "DATA_CONFLICT"}
        )
    blocked_by = list(dict.fromkeys(blocked_by))
    return {
        "schema_version": "v21.0",
        "stock_name": name,
        "stock_code": str((data or {}).get("stock_code") or ""),
        "scope": "unheld",
        "state": state,
        "state_label": STATE_LABELS[state],
        "phase": meta["phase"],
        "action": action,
        "action_label": ACTION_LABELS[action],
        "is_actionable": meta["is_actionable"],
        "is_terminal": meta["is_terminal"],
        "previous_state": _previous_state(data),
        "transition": f"{transition_result['from']}->{state}",
        "transition_event": event,
        "transition_from": transition_result["from"],
        "transition_to": state,
        "allowed_transition": transition_result["allowed"],
        "transition_table": transition_result["table"],
        "target_state": target_state,
        "reason": reason,
        "trigger": trigger,
        "next_required_event": meta["next_required_event"],
        "guards": guards,
        "blocked_by": blocked_by,
        "requires_order_lifecycle": False,
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
    if machine_state.get("scope") == "unheld":
        next_event = machine_state.get("next_required_event")
        next_label = NEXT_EVENT_LABELS.get(next_event)
        if next_label:
            prefix = "下一步" if machine_state.get("is_actionable") else "還差"
            parts.append(f"{prefix}：{next_label}")
        return "｜".join(parts)
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
            "phase": state.get("phase"),
            "action": state.get("action"),
            "is_actionable": state.get("is_actionable"),
            "is_terminal": state.get("is_terminal"),
            "previous_state": state.get("previous_state"),
            "transition": state.get("transition"),
            "transition_event": state.get("transition_event"),
            "transition_from": state.get("transition_from"),
            "transition_to": state.get("transition_to"),
            "allowed_transition": state.get("allowed_transition"),
            "transition_table": state.get("transition_table"),
            "target_state": state.get("target_state"),
            "reason": state.get("reason"),
            "trigger": state.get("trigger"),
            "next_required_event": state.get("next_required_event"),
            "guards": state.get("guards") or [],
            "blocked_by": state.get("blocked_by") or [],
            "requires_order_lifecycle": state.get("requires_order_lifecycle", False),
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
