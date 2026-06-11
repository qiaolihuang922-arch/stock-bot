"""Telegram presentation assembly.

This module assembles already-prepared report data into Telegram messages. It
does not import storage clients or evidence writers; core.generator owns data
preparation and passes the formatter helpers needed for compatibility.
"""

SHOW_DATA_BASIS = False


def formatTelegramSummary(
    results_map,
    best,
    score,
    market_summary,
    now,
    *,
    version,
    deps,
    position_warning=None,
    daily_write_warning=None,
    strategy_evidence_summary=None,
    report_phase=None,
    report_context=None,
):
    if report_phase is None:
        report_phase = deps["get_market_phase"]()
    if report_context is None:
        report_context = deps["build_report_context"](
            results_map,
            market_summary,
            now,
            strategy_evidence_summary=strategy_evidence_summary,
            report_phase=report_phase,
            position_warning=position_warning,
        )

    holding_items = [
        (name, data)
        for name, data in deps["ordered_result_items"](results_map)
        if data.get("holding")
    ]
    holding_items = deps["sort_position_summary"](holding_items)
    watch_items = [
        (name, data)
        for name, data in deps["ordered_result_items"](results_map)
        if not data.get("holding")
    ]
    market_mode, risk_level = deps["derive_market_state"](watch_items)

    lines = [
        f"【{now.strftime('%m/%d')} {report_phase}｜{version}】",
        f"報告日：{report_context['report_context'].get('as_of_date')}｜資料交易日：{report_context['report_context'].get('trade_date')}",
        f"Source：{report_context.get('source_status_text')}",
    ]

    if position_warning:
        lines.append(f"⚠ {position_warning}，持倉狀態不可信")

    if daily_write_warning:
        lines.append(f"⚠ {daily_write_warning}")

    holding_names = "、".join(name for name, _data in holding_items) or "無"
    conclusion_text = deps["today_conclusion_text"](
        holding_items,
        watch_items,
        market_mode,
        risk_level,
        report_phase=report_phase,
        report_context=report_context,
    )
    new_entry_items = deps["new_entry_suggestion_items"](
        watch_items,
        market_mode=market_mode,
        report_context=report_context,
    )
    reason_line = _summary_reason_line(
        holding_items,
        watch_items,
        new_entry_items,
        market_mode,
        report_phase,
        report_context,
        deps,
    )
    risk_parts = []
    if holding_items:
        risk_parts.append("持倉：hard_stop 永不豁免，跌破警戒 / 停損依風控處理")
    if new_entry_items:
        risk_parts.append("新倉：尚未買入，不列入交易執行，分批且不追價")
    if not risk_parts:
        risk_parts.append(deps["compact_risk_text"](results_map))
    lines.append(f"市場/結論：{market_mode}｜{risk_level}；{conclusion_text}")

    if report_phase == "盤中":
        lines.append(deps["source_summary_text"](results_map))

    lines.append(f"原因：{reason_line}")
    lines.append(f"風險：{'；'.join(risk_parts)}")

    lines.extend([
        *deps["market_execution_bridge_lines"](holding_items, watch_items, market_mode, market_summary),
        *deps["format_cross_day_tracking_summary"](watch_items, report_context=report_context, market_mode=market_mode),
        *deps["format_strong_prepare_summary"](watch_items, market_mode),
        *deps["format_market_theme_summary_lines"](
            report_context.get("market_theme_evidence") or deps["market_theme_summary_evidence"](results_map, market_summary)
        ),
        f"📌 持倉：{holding_names}",
    ])

    if report_phase == "盤中":
        execution_lines = deps["format_execution_checklist"](
            holding_items, watch_items, report_phase=report_phase, market_mode=market_mode, report_context=report_context
        )
        execution_lines = [line for line in execution_lines if line != "無新增下單"]
        if execution_lines:
            lines.extend(["", "今日盤中風控建議"])
            lines.extend(execution_lines)
        new_entry_lines = deps["format_new_entry_suggestions"](
            watch_items, report_phase=report_phase, market_mode=market_mode, report_context=report_context
        )
        if new_entry_lines:
            lines.extend(["", "新倉建議"])
            lines.extend(new_entry_lines)
        unheld_non_execution_lines = deps["format_unheld_non_execution_lines"](
            watch_items, report_phase=report_phase, market_mode=market_mode, report_context=report_context
        )
        if unheld_non_execution_lines:
            lines.extend(unheld_non_execution_lines)
    else:
        lines.extend(["", "今日交易"])
        lines.append("新增交易建議：無")

    executed_lines = deps["format_executed_checklist"](holding_items, watch_items)
    if executed_lines:
        lines.extend(["", "已執行（不重複下單）"])
        lines.extend(executed_lines)

    lines.extend(["", "持倉風控檢查"])
    lines.extend(deps["format_holding_control_checklist"](holding_items, report_phase=report_phase))

    if report_phase != "盤中":
        plan_count = len(deps["pending_trade_items"](
            holding_items, watch_items, market_mode=market_mode, report_context=report_context
        ))
        if plan_count:
            lines.extend(["", f"明日計畫 {plan_count}"])
            lines.extend(deps["format_execution_checklist"](
                holding_items, watch_items, report_phase=report_phase, market_mode=market_mode, report_context=report_context
            ))
        new_entry_lines = deps["format_new_entry_suggestions"](
            watch_items, report_phase=report_phase, market_mode=market_mode, report_context=report_context
        )
        if new_entry_lines:
            lines.extend(["", "新倉建議"])
            lines.extend(new_entry_lines)
        unheld_non_execution_lines = deps["format_unheld_non_execution_lines"](
            watch_items, report_phase=report_phase, market_mode=market_mode, report_context=report_context
        )
        if unheld_non_execution_lines:
            lines.extend(unheld_non_execution_lines)

    unheld_funnel_text = deps["format_unheld_funnel"](watch_items, market_mode=market_mode, report_context=report_context)
    if unheld_funnel_text:
        lines.extend(["", "未持倉狀態：", unheld_funnel_text])

    lines.extend(deps["format_backtest_groups"](watch_items, report_context=report_context))

    lines.extend(["", deps["detail_index_text"](
        holding_items, watch_items, report_phase=report_phase, market_mode=market_mode, report_context=report_context
    )])

    rejected_line = deps["rejected_trace_line"](watch_items, market_mode=market_mode, report_context=report_context)
    if rejected_line:
        lines.append(rejected_line)

    strategy_evidence_text = _strategy_evidence_text(strategy_evidence_summary)
    if strategy_evidence_text:
        lines.extend(["", strategy_evidence_text])

    return "\n".join(lines)


def _report_phase(report_context):
    return (report_context or {}).get("report_context", {}).get("report_phase")


def _strategy_evidence_text(strategy_evidence_summary):
    if isinstance(strategy_evidence_summary, dict):
        return strategy_evidence_summary.get("rendered_text") or strategy_evidence_summary.get("text")
    return strategy_evidence_summary


def _summary_reason_line(holding_items, watch_items, new_entry_items, market_mode, report_phase, report_context, deps):
    if holding_items and not new_entry_items:
        return "持倉多數依風控處理，新倉無有效進場。"
    if holding_items and new_entry_items:
        return "持倉依風控處理，新倉僅列可行動候選。"
    if new_entry_items:
        return "持倉無需處理，新倉僅列可行動候選。"
    return deps["today_reason_text"](
        watch_items,
        market_mode,
        report_phase=report_phase,
        report_context=report_context,
    )


def _is_unavailable_history_line(line):
    if not line:
        return True
    return (
        line in {"回測：-", "歷史：-"}
        or "回測：不可用" in line
        or "歷史：不可用" in line
        or "樣本不足" in line
    )


def _card_history_line(data, report_context, deps, dedupe_setup_key=False):
    strategy_line = deps["_strategy_sample_unavailable_card_line"](report_context)
    if strategy_line:
        return None
    line = deps["compact_backtest_line"](data.get("backtest_context"))
    if _is_unavailable_history_line(line):
        return None
    return line


def _afterhours_card_text(line, report_context):
    if _report_phase(report_context) not in {"盤後", "收盤"} or line is None:
        return line
    replacements = {
        "盤中留意": "盤後觀察",
        "盤中觸發": "明日開盤前確認",
        "盤中可追": "等待下一交易日訊號",
        "即時進場": "等待下一交易日訊號",
        "盤中先觀察": "明日觀察是否守住警戒",
        "盤中觀察修復狀況": "明日確認是否修復",
    }
    text = line
    for old, new in replacements.items():
        text = text.replace(old, new)
    return text


def _strategy_sample_status_line(report_context, deps):
    strategy = deps["_field_by_key"](report_context, "evidence.strategy_sample")
    status = strategy.get("source_status", "missing-source")
    reason_by_status = {
        "missing-source": "來源缺失",
        "insufficient-data": "樣本不足",
        "source-error": "來源讀取異常",
    }
    reason = reason_by_status.get(status)
    if reason:
        return f"策略樣本：本次不可用（原因：{reason}），單檔卡片不重複列示。"
    return "策略樣本：來源可驗證，只作輔助參考，不新增買點。"


def _holding_execution_memory_status(report_context, name, deps):
    if not report_context:
        return "available"
    position_status = deps["_stock_field"](report_context, name, "position").get("source_status", "missing-source")
    ledger_status = deps["_stock_field"](report_context, name, "execution_memory").get("source_status", "missing-source")
    statuses = [position_status, ledger_status]
    if all(status == "available" for status in statuses):
        return "available"
    if "unresolved-conflict" in statuses:
        return "unresolved-conflict"
    if "source-error" in statuses:
        return "source-error"
    if "missing-source" in statuses:
        return "missing-source"
    return "insufficient-data"


def _score_source_status(report_context, name, deps):
    if not report_context:
        return "available"
    return deps["_stock_field"](report_context, name, "score").get("source_status", "missing-source")


def _score_source_available(report_context, name, deps):
    return _score_source_status(report_context, name, deps) in {"available", "derived"}


def _score_data_text(report_context, name, data, deps):
    if _score_source_available(report_context, name, deps):
        return f"S {data.get('structure_score', '-')}/5"
    status = _score_source_status(report_context, name, deps)
    if status in {"insufficient-data", "missing-source", "insufficient", "missing"}:
        return "S 證據不足"
    return "S 不可用"


def _is_heat_blocked(stock_result):
    return (
        stock_result.get("heat_state") in {"HOT", "EXTREME"}
        or stock_result.get("trade_state") in {"EXTENDED", "AVOID"}
        or stock_result.get("price_behavior") in {"LIMIT_LOCK", "LIMIT_REBOUND"}
        or str(stock_result.get("extended_level") or "") in {"3", "4", "5"}
    )


def _is_risk_blocked(stock_result, data):
    decision = stock_result.get("_holding_decision") or (data or {}).get("holding_decision") or {}
    decision_text = f"{decision.get('action') or ''} {decision.get('level') or ''} {decision.get('note') or ''}"
    return (
        stock_result.get("decision") == "FAIL"
        or stock_result.get("structure_phase") in {"FAILED_BREAKOUT", "WEAK", "DISTRIBUTION", "WEAK_REBOUND"}
        or stock_result.get("price_behavior") == "WEAK_REBOUND"
        or (data or {}).get("funnel_state") == "淘汰"
        or stock_result.get("funnel_state") == "淘汰"
        or any(token in decision_text for token in ["減碼", "停損", "硬風控", "結構弱"])
    )


def _is_volume_blocked(stock_result, data):
    text = " ".join(
        str(value or "")
        for value in [
            stock_result.get("trade_state"),
            stock_result.get("volume_state"),
            stock_result.get("wait_reason"),
            stock_result.get("reason"),
            stock_result.get("reject_family"),
            (data or {}).get("funnel_state"),
        ]
    )
    return (
        stock_result.get("trade_state") == "NO_VOLUME"
        or "量能不足" in text
        or "NO_VOLUME" in text
    )


def _evidence_unavailable_text(stock_result, data):
    if _is_risk_blocked(stock_result, data):
        return "風控不適用"
    if _is_heat_blocked(stock_result):
        return "過熱不適用"
    if _is_volume_blocked(stock_result, data):
        return "量能不適用"
    return "資料不足"


def _hidden_score_reason(rr_text, funnel_state, state):
    for value in [rr_text or "", funnel_state or "", state or ""]:
        text = str(value)
        if "量能不足" in text:
            return "量能不足"
        if "過熱" in text or "等冷卻" in text or "不可追高" in text:
            return "過熱"
        if "不可行動" in text or "淘汰" in text:
            return "不可行動"
        if "弱勢" in text:
            return "弱勢"
        if "RR" in text or "RR修復" in text or "不足" in text:
            return "RR不足"
        if "回測" in text:
            return "等回測"
    return funnel_state or state or "不可行動"


def _unheld_score_text_for_state(score_text, rr_text, valid_entry, funnel_state, state, stock_result=None, data=None):
    if valid_entry or funnel_state in {"趨勢延續", "隔日確認"} or state == "隔日確認":
        return score_text
    if (
        data
        and _report_phase((data or {}).get("report_context")) == "盤後"
        and stock_result
        and stock_result.get("decision") == "BUY"
        and funnel_state == "可準備"
    ):
        return "不適用（盤後待確認）｜原因：盤後待確認，需開盤後重新確認"
    reason = _hidden_score_reason(rr_text, funnel_state, state)
    if reason == "RR不足":
        return "不適用（RR不足）｜原因：RR不足，等待RR修復"
    evidence_text = _evidence_unavailable_text(stock_result or {}, data or {})
    return f"不適用（{reason}）｜證據：{evidence_text}"


def _gate_value_text(value):
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    if number.is_integer():
        return str(int(number))
    return f"{number:.2f}".rstrip("0").rstrip(".")


def _gate_gap_text(value, threshold):
    try:
        gap = float(threshold) - float(value)
    except (TypeError, ValueError):
        return None
    if gap < 0:
        gap = 0
    return _gate_value_text(gap)


def _display_entry_distance_policy(stock_result):
    stock_result = stock_result or {}
    decision_type = stock_result.get("decision_type")
    phase = stock_result.get("structure_phase")
    behavior = stock_result.get("price_behavior")
    entry_profile = stock_result.get("entry_profile")
    entry_stage = stock_result.get("entry_stage")
    breakout_state = stock_result.get("breakout_state")
    trend = stock_result.get("trend")
    structure = stock_result.get("structure_state")
    try:
        distance = float(stock_result.get("breakout_distance"))
    except (TypeError, ValueError):
        distance = None

    if decision_type in {"trend_continuation", "trend_observation"}:
        return {"label": "趨勢延續", "max_pct": None, "hard_gate": False, "unlock": "回踩站回且不追高加碼"}
    if entry_stage == "PULLBACK_RECLAIM" or entry_profile == "BUY_RECLAIM_CONFIRM":
        return {"label": "回測承接", "max_pct": None, "hard_gate": False, "unlock": "回測不破且量價轉強"}
    if phase in {"SHAKEOUT", "HEALTHY_PULLBACK"} or behavior == "LOW_VOLUME_PULLBACK":
        return {"label": "回測承接", "max_pct": None, "hard_gate": False, "unlock": "回測不破且量價轉強"}
    if decision_type in {"breakout", "wait_breakout_confirm", "wait_breakout_low_rr"} or breakout_state == "BREAKOUT":
        return {"label": "突破買點區", "max_pct": 5.0, "hard_gate": True, "unlock": "回到買點區內，或轉為回測承接 setup"}
    if (
        decision_type in {"pre_breakout", "wait_pre_breakout", "wait_pre_breakout_low_rr"}
        or phase in {"BREAKOUT_NEAR", "READY_BREAKOUT"}
        or breakout_state == "READY"
        or (distance is not None and 0 <= distance <= 5)
    ):
        return {"label": "突破買點區", "max_pct": 5.0, "hard_gate": True, "unlock": "接近突破買點區後重評，或另出現回測承接 setup"}
    if phase == "BASE" and trend == "UP" and structure in {"STRONG", "NORMAL"}:
        return {"label": "底部轉強觀察區", "max_pct": 8.0, "hard_gate": True, "unlock": "站穩支撐且風險報酬達標"}
    return {"label": "有效 setup", "max_pct": None, "hard_gate": False, "unlock": "重新形成突破、回測或趨勢延續 setup"}


def _supporting_basis_text(data, primary_reason):
    stock_result = (data or {}).get("result") or {}
    basis = []
    primary = str(primary_reason or "")
    try:
        rr = float(stock_result.get("rr"))
    except (TypeError, ValueError):
        rr = None
    if rr is not None and rr >= 1.5 and "RR" not in primary:
        basis.append("RR 達標")
    try:
        volume = float((data or {}).get("volume_ratio"))
    except (TypeError, ValueError):
        volume = None
    if volume is not None and volume >= 1:
        basis.append("量能達標")
    backtest = (data or {}).get("backtest_context") or {}
    if backtest:
        basis.append("回測僅輔助")
    return "；".join(dict.fromkeys(basis))


def _unheld_buy_gap_line(data, dist, blockers, valid_entry, funnel_state, source_status, strategy_source_blocked, title_label=None):
    stock_result = data.get("result") or {}
    is_actionable = valid_entry or funnel_state == "趨勢延續"
    post_market_prepare = (
        _report_phase((data or {}).get("report_context")) == "盤後"
        and stock_result.get("decision") == "BUY"
        and not is_actionable
        and funnel_state == "可準備"
    )
    if is_actionable:
        return None

    def evidence_lines(reason, gap, unlock=None, basis=None):
        lines = [f"卡關主因：{reason}", f"量化差距：{gap}"]
        if unlock:
            lines.append(f"解鎖：{unlock}")
        basis = basis if basis is not None else _supporting_basis_text(data, reason)
        if basis:
            lines.append(f"依據：{basis}")
        return "\n".join(lines)

    gates = []
    source_gates = []
    if strategy_source_blocked:
        source_gates.append(("樣本不足", "需更多有效策略樣本確認"))
    source_blocked = source_status in {"missing-source", "insufficient-data", "source-error", "unresolved-conflict"}
    if source_blocked and not strategy_source_blocked:
        source_gates.append(("資料來源缺失", "需補齊有效行情 / 策略來源"))
    blocker_text = "、".join(str(item) for item in blockers)
    phase = stock_result.get("structure_phase")
    title_text = str(title_label or "")
    market_background = "市場弱" in title_text or "市場弱" in blocker_text
    if "量能不足" in title_text:
        gates.append(("量能不足", "需量能回升後重新評估"))
    elif "量能不足" in blocker_text:
        gates.append(("量能不足", "需量能回升後重新評估"))
    if "突破失敗" in blocker_text or phase == "FAILED_BREAKOUT":
        distance_text = _gate_value_text(dist)
        gap = "需重新站回突破區"
        policy = _display_entry_distance_policy(stock_result)
        max_pct = policy.get("max_pct") or 5.0
        policy_label = policy["label"] if policy.get("hard_gate") else "突破買點區"
        if distance_text and float(distance_text) > max_pct:
            distance_gap = _gate_value_text(float(distance_text) - max_pct)
            gap = f"距突破區 {distance_text}%｜{policy_label}需<={_gate_value_text(max_pct)}%｜差{distance_gap}%"
        return evidence_lines("未站回突破區", gap, "重新站回突破區後再評估", basis="")
    if post_market_prepare:
        return evidence_lines(
            "開盤確認未完成",
            "盤後待開盤確認",
            "明日開盤後仍守突破區 / 不追價",
        )

    behavior = stock_result.get("price_behavior")
    if behavior in {"LIMIT_LOCK", "LIMIT_REBOUND"} or "漲停" in blocker_text or "不可追高" in blocker_text:
        gates.append(("漲跌停鎖定", "需解除鎖定後重新評估"))
    if behavior == "WEAK_REBOUND" or phase == "WEAK_REBOUND" or "弱反彈" in blocker_text:
        gates.append(("反彈力道不足", "需放量轉強後重新評估"))

    heat = stock_result.get("heat_state")
    if heat == "EXTREME":
        return evidence_lines("熱度 Lv.3", "熱度 Lv.3｜需降至 Lv.1/觀察以下", "降溫後重新評估")
    if heat == "HOT" or "過熱" in blocker_text:
        return evidence_lines("過熱觀察", "熱度 Lv.2｜需降至 Lv.1/觀察以下", "降溫後重新評估")

    rr_text = _gate_value_text(stock_result.get("rr"))
    if not is_actionable and rr_text and ("RR不足" in blocker_text or float(rr_text) < 1.5):
        rr_gap = f"RR {rr_text}｜需>=1.5｜差{_gate_gap_text(rr_text, 1.5)}"
        gates.append(("RR不足", rr_gap))

    distance_text = _gate_value_text(dist)
    policy = _display_entry_distance_policy(stock_result)
    max_pct = policy.get("max_pct")
    if distance_text and policy.get("hard_gate") and max_pct is not None and float(distance_text) > max_pct:
        distance_gap = _gate_value_text(float(distance_text) - max_pct)
        distance_gap_text = (
            f"距突破 {distance_text}%｜{policy['label']}需<={_gate_value_text(max_pct)}%｜另等趨勢延續/回測承接setup"
            if funnel_state == "等接近"
            else f"距突破 {distance_text}%｜{policy['label']}需<={_gate_value_text(max_pct)}%｜差{distance_gap}%｜若走趨勢延續/回測承接，需另見有效setup"
        )
        gates.append((
            "距觸發太遠",
            distance_gap_text,
        ))

    quality = stock_result.get("entry_quality")
    if funnel_state != "等接近" and not is_actionable and quality and quality not in {"A+", "A", "B"}:
        gates.append(("進場品質不足", f"進場品質 {quality}｜需B以上"))

    if not gates:
        gates.extend(source_gates)
    if funnel_state != "等接近" and market_background and gates and gates[0][0] != "市場弱":
        gates.append(("市場背景", "市場轉強後才評估執行"))

    if not gates and post_market_prepare:
        gates.append(("盤後待確認", "需開盤後重新確認"))
    elif not gates and funnel_state == "可準備":
        gates.append(("買點尚未成立", "需觸發後重新評估"))
    elif not gates and funnel_state == "等回測":
        gates.append(("回測未確認", "需回測不破後重新評估"))
    elif not gates and funnel_state == "等RR修復":
        gates.append(("RR不足", "RR 不可用｜需>=1.5"))
    elif not gates and funnel_state == "等量能":
        gates.append(("量能不足", "需量能回升後重新評估"))
    elif not gates and funnel_state == "隔日確認":
        gates.append(("隔日確認", "需轉強後重新評估"))
    elif not gates and funnel_state == "淘汰":
        gates.append(("重新轉強", "需確認後重新評估"))
    if not gates:
        if blockers:
            gates.append((str(blockers[0]), "需解除後重新評估"))
        else:
            gates.append(("資料來源缺失", "需補齊有效行情 / 策略來源"))

    primary_reason, primary_gap = gates[0]
    extra_gaps = []
    for reason, gap in gates[1:3]:
        if reason != primary_reason:
            extra_gaps.append(gap)
    if extra_gaps:
        primary_gap = f"{primary_gap}｜" + "｜".join(extra_gaps)
    unlock = {
        "RR不足": "風險報酬比修復到 >=1.5",
        "距觸發太遠": "接近觸發區，或另出現趨勢延續/回測承接setup後再評估",
        "市場背景": "市場轉強後再評估",
        "漲跌停鎖定": "解除鎖定後重新評估",
        "反彈力道不足": "放量轉強後重新評估",
        "市場弱": "市場轉強後重新評估",
        "量能不足": "量能回升後重新評估",
        "樣本不足": "補齊有效策略樣本後重新評估",
        "資料來源缺失": "補齊有效行情 / 策略來源後重新評估",
    }.get(primary_reason, "解除主 blocker 後重新評估")
    basis = "" if funnel_state == "等接近" else None
    return evidence_lines(primary_reason, primary_gap, unlock, basis=basis)


def _stock_decision_judgment(report_context, name):
    judgments = (report_context or {}).get("stock_judgments") or {}
    judgment = judgments.get(name)
    if judgment:
        return judgment
    field = None
    for item in (report_context or {}).get("evidence_manifest") or []:
        if item.get("field_name") == f"stock.{name}.decision_judgment":
            field = item
            break
    value = (field or {}).get("value") or {}
    return value if isinstance(value, dict) else {}


def _decision_reason_text(report_context, name):
    judgment = _stock_decision_judgment(report_context, name)
    if not judgment:
        return None
    def visible_blocker(item):
        return {
            "unresolved RR不足": "RR不足",
            "overheat / EXTREME": "過熱未降溫",
            "failed breakout": "突破失敗",
            "漲跌停 / 追高 hard gate": "漲跌停鎖定 / 不追高",
            "volume hard gate": "量能不足",
            "hard stop / holding risk": "跌破停損線",
            "holding hard risk": "跌破警戒或結構轉弱",
            "conflicting evidence": "證據衝突",
            "missing-source": "資料來源缺失",
            "source-error": "資料來源異常",
            "insufficient-data": "資料不足",
        }.get(str(item), str(item))

    def visible_progress(item):
        text = str(item)
        return {
            "既有買點與倉位規則通過": "買點成立，倉位規則通過",
            "trend_continuation 同源證據達標，仍限小倉契約": "趨勢延續同源證據達標，仍限小倉",
            "來源可追溯，現狀維持 可準備": "維持可準備，不升格可買",
            "來源可追溯，現狀維持 等RR修復": "維持等 RR 修復",
            "來源可追溯，現狀維持 等冷卻": "維持等冷卻",
            "來源可追溯，現狀維持 淘汰": "維持不可行動",
            "既有持倉依持倉 / ledger / 價格來源判斷，不列新倉 eligibility": "",
        }.get(text, text.replace("技術 setup ", "技術條件").replace("技術 setup", "技術條件"))

    blockers = [
        visible_blocker(item)
        for item in judgment.get("blocking_reasons") or []
        if str(item) != "DB/live restriction: evidence cannot authorize DB write/live Telegram delivery"
    ]
    progress = [
        text for text in (visible_progress(item) for item in judgment.get("progress_reasons") or [])
        if text
    ]
    if judgment.get("eligibility_state") == "prepare":
        progress = [
            text for text in progress
            if "買點成立" not in text and "倉位規則通過" not in text
        ]
    if _report_phase(report_context) != "盤中":
        progress = [
            text for text in progress
            if "買點成立" not in text and "倉位規則通過" not in text
        ]
    status = judgment.get("evidence_status")
    status_text = {
        "missing": "資料來源缺失，停止新倉",
        "source_error": "資料來源異常，停止新倉",
        "conflicting": "證據衝突，停止新倉",
        "insufficient": "資料不足，停止新倉",
    }.get(status)
    if blockers:
        is_holding = any(".position" in str(ref) for ref in judgment.get("evidence_refs") or [])
        if not status_text:
            return "風險依據：卡關 " + "、".join(blockers[:2]) if is_holding else None
        prefix = "風險依據" if is_holding else "決策依據"
        parts = [part for part in [status_text, "卡關 " + "、".join(blockers[:2])] if part]
        return f"{prefix}：" + "；".join(parts)
    if progress:
        return "依據：" + "；".join(progress[:2])
    if status_text:
        return f"決策依據：{status_text}"
    return None


def _append_decision_reason(existing_line, report_context, name, *, default_prefix="理由"):
    reason = _decision_reason_text(report_context, name)
    if not reason:
        return existing_line
    if existing_line:
        existing_line = existing_line.replace("技術 setup ", "技術條件").replace("技術 setup", "技術條件")
    if not existing_line:
        if "：" in reason:
            return reason
        return f"{default_prefix}：{reason}"
    reason_body = reason.split("：", 1)[1] if "：" in reason else reason
    if reason_body and reason_body in existing_line:
        return existing_line
    if reason in existing_line:
        return existing_line
    return f"{existing_line.rstrip('。；')}；{reason}"


def _percent_distance(current, target):
    try:
        current_value = float(current)
        target_value = float(target)
    except (TypeError, ValueError):
        return None
    if target_value <= 0:
        return None
    return _gate_value_text(abs(current_value - target_value) / target_value * 100)


def _holding_visible_risk_reason(data, decision):
    if not decision:
        return None
    level = decision.get("level")
    price = (data or {}).get("price")
    hard_stop = decision.get("hard_stop_price")
    warning = decision.get("warning_price")
    if level == "STOP_100":
        distance = _percent_distance(price, hard_stop)
        if distance:
            return f"跌破停損線 {distance}%，避免虧損擴大"
        return "跌破停損線，避免虧損擴大"
    if level in {"REDUCE_25", "REDUCE_50"} or str(decision.get("action") or "").startswith("硬風控"):
        stop_distance = _percent_distance(price, hard_stop)
        warning_distance = _percent_distance(price, warning)
        distances = []
        if warning_distance:
            distances.append(f"距警戒線 {warning_distance}%")
        if stop_distance:
            distances.append(f"距停損線 {stop_distance}%")
        prefix = "，".join(distances)
        return f"{prefix}，結構轉弱" if prefix else "跌破警戒或結構轉弱"
    return None


def _weak_buy_backtest_line(name, data, deps, include_all=False):
    line = deps["compact_backtest_line"]((data or {}).get("backtest_context"))
    if not line or line == "回測：-":
        return None
    weak_tokens = ["偏弱", "無明顯優勢", "樣本不足", "不可用", "判讀不足"]
    if not include_all and not any(token in line for token in weak_tokens):
        return None
    body = line.replace("回測：", "", 1)
    return f"回測（{name}）：{body}；回測僅輔助，分批小倉、不追價"


def _confidence_data_text(report_context, name, data, deps):
    stock_result = data.get("result") or {}
    if "final_confidence" not in stock_result or "technical_confidence" not in stock_result:
        return _score_data_text(report_context, name, data, deps)

    try:
        final = min(100, round(float(stock_result.get("final_confidence") or 0)))
        technical = round(float(stock_result.get("technical_confidence") or 0))
    except (TypeError, ValueError):
        return _score_data_text(report_context, name, data, deps)

    evidence_score = stock_result.get("evidence_score")
    status = stock_result.get("evidence_status") or "unavailable"
    if evidence_score is None or status == "unavailable":
        return f"綜合 {final}｜技術 {technical}｜證據：{_evidence_unavailable_text(stock_result, data)}"

    try:
        pct = round((float(stock_result.get("evidence_modifier") or 1.0) - 1.0) * 100)
    except (TypeError, ValueError):
        pct = 0
    if technical < 10 or final == technical:
        return f"綜合 {final}｜技術 {technical}｜證據：微幅（{status}）"
    if status == "partial" and pct == 0:
        return f"綜合 {final}｜技術 {technical}｜證據：partial｜僅輔助參考"
    sign = "+" if pct >= 0 else ""
    return f"綜合 {final}｜技術 {technical}｜證據 {sign}{pct}%（{status}）"


def _low_volume_ratio(data):
    try:
        return float((data or {}).get("volume_ratio"))
    except (TypeError, ValueError):
        return None


def _is_low_volume_consolidation(report_context, data, stock_result):
    if _report_phase(report_context) != "盤後":
        return False
    ratio = _low_volume_ratio(data)
    if ratio is None or ratio >= 0.8:
        return False
    return (
        stock_result.get("volume_price_state") == "COILING"
        or stock_result.get("structure_phase") == "BASE"
        or stock_result.get("lifecycle") == "BASE"
    )


def _score_gated_market_line(report_context, name, data, dist, deps):
    stock_result = data.get("result") or {}
    if _score_source_available(report_context, name, deps):
        market_text = deps["plain_label"](deps["compact_market_line"](stock_result, dist))
        if ("弱勢" in market_text or "遠離突破" in market_text) and "極強" in market_text:
            market_text = market_text.replace("極強", "待確認")
        if _is_low_volume_consolidation(report_context, data, stock_result):
            market_text = market_text.replace("極強", "縮量觀察")
            market_text = market_text.replace("｜待確認", "｜縮量觀察")
            if "縮量" not in market_text:
                market_text = f"{market_text}｜縮量觀察"
        return f"盤面：{market_text}"
    return "盤面：強弱證據不足｜待確認"


def _unheld_rr_text(stock_result, funnel_state, valid_entry, deps):
    weak_structure = (
        stock_result.get("decision") in {"NO_TRADE", "FAIL"}
        or stock_result.get("structure_phase") in {"FAILED_BREAKOUT", "WEAK", "DISTRIBUTION", "WEAK_REBOUND"}
        or stock_result.get("price_behavior") == "WEAK_REBOUND"
        or stock_result.get("market_grade") == "D"
    )
    if not valid_entry and (funnel_state == "淘汰" or weak_structure):
        return "-（不可行動）"
    if funnel_state == "等冷卻" or deps["should_show_overheat_rr_blocker"](stock_result, holding=False):
        return "-（過熱）"
    return deps["rr_display_text"](stock_result, holding=False)


def formatTelegramPositionCard(name, data, *, deps, report_context=None):
    holding = data["holding"]
    decision = deps["ensure_holding_decision"](name, data)
    summary_action = deps["position_summary_action"](name, data)
    stock_result = data["result"]
    today_text = deps["holding_today_trade_text"](data, decision) or "無"
    execution_status = _holding_execution_memory_status(report_context, name, deps)
    execution_ready = execution_status == "available"
    execution_line = (
        f"倉位：{holding['shares']}股｜均價 {deps['price_text'](holding.get('avg_price'))}｜今日 {today_text}"
        if execution_ready
        else "今日執行：執行記憶不足，暫不顯示精確執行欄位"
    )
    dist = deps["card_breakout_distance"](data)
    decision_line, condition_line = deps["holding_detail_decision_lines"](name, data)
    reason_line = deps["holding_reason_line"](name, data)
    next_step = deps["holding_next_step_line"](name, data)
    rr_text = deps["rr_display_text"](stock_result, holding=True)
    add_levels = {"ADD_10", "ADD_20", "ADD_30"}
    is_add_context = bool(
        decision
        and decision.get("level") in add_levels
        and decision.get("allow_add") is not False
        and summary_action != "新倉風控觀察"
    )
    score_text = _confidence_data_text(report_context, name, data, deps)
    data_line = (
        f"數據：不適用（既有持倉）｜V {data.get('volume_ratio', '-')}x"
        if decision and not is_add_context
        else f"數據：RR {rr_text}｜{score_text}｜V {data.get('volume_ratio', '-')}x"
    )

    is_afterhours = _report_phase(report_context) in {"盤後", "收盤"}
    hide_low_signal_detail = (
        summary_action in {"停損", "減碼", "停利"}
        or (decision and decision.get("level") in {"HARD_STOP", "STOP", "REDUCE_50", "TAKE_PROFIT"})
    )
    lines = [
        f"【{deps['stock_title'](name, data)}】📌 {summary_action}｜{deps['signed_pct'](deps['stock_pnl'](data))}",
        deps["trade_state_machine_line"](data),
        execution_line,
        f"風控：{deps['holding_risk_text'](decision)}",
        _score_gated_market_line(report_context, name, data, dist, deps),
        deps["today_buy_holding_context_line"](data) if _report_phase(report_context) == "盤後" else None,
        f"決策：{decision_line}",
        None if is_afterhours or hide_low_signal_detail else f"條件：{condition_line}",
        f"下一步：{next_step}",
        deps["_source_status_line"](report_context, name, holding=True) if report_context else None,
        None if is_afterhours or hide_low_signal_detail else data_line,
        _card_history_line(data, report_context, deps),
        deps["price_change_line"](data.get("price"), data.get("change")),
    ]
    lines = [line for line in lines if line is not None]
    lines = [_afterhours_card_text(line, report_context) for line in lines]

    risk_reason = _holding_visible_risk_reason(data, decision)
    if risk_reason and reason_line:
        reason_line = f"原因：{reason_line}；風險依據：{risk_reason}"
    elif risk_reason:
        reason_line = f"原因：{risk_reason}"
    else:
        reason_line = _append_decision_reason(
            f"原因：{reason_line}" if reason_line else None,
            report_context,
            name,
            default_prefix="原因",
        )
    if reason_line:
        lines.insert(6, reason_line)
    history_line = None if is_afterhours else deps["cross_day_detail_line"](data)
    if history_line:
        lines.insert(-1, history_line)

    return "\n".join(lines)


def formatTelegramUnheldCard(name, data, *, deps, report_phase=None, market_mode=None, report_context=None):
    stock_result = data["result"]
    effective_report_phase = report_phase or _report_phase(report_context)
    dist = deps["card_breakout_distance"](data)
    blockers = deps["entry_blockers"](stock_result)
    stock_source_status = deps["_stock_decision_source_status"](report_context, name)
    strategy_source_status = deps["_strategy_sample_decision_source_status"](report_context)
    source_status = deps["_unheld_decision_source_status"](report_context, name)
    stock_source_eligible = stock_source_status == "available"
    strategy_source_eligible = strategy_source_status == "available"
    strategy_source_blocked = stock_source_eligible and not strategy_source_eligible
    source_eligible = source_status == "available"
    valid_entry = deps["is_valid_entry"](stock_result) and source_eligible
    title_label = "買點成立" if valid_entry else (blockers[0] if blockers else deps["final_label"](stock_result))
    state = deps["tomorrow_watch_state"](name, data)
    data_source_display_blocked = strategy_source_blocked and state == "等資料"
    funnel_state = deps["unheld_funnel_state"](name, data, market_mode=market_mode, report_context=report_context)
    prepare_label, prepare_action = deps["strong_prepare_bucket"](data)
    post_market_prepare = (
        source_eligible
        and deps["post_market_unheld_buy_requires_open_confirmation"](data, report_context=report_context)
    )
    data_with_context = dict(data)
    data_with_context["report_context"] = report_context
    if valid_entry and funnel_state not in ["可買", "趨勢延續"]:
        valid_entry = False
        title_label = (
            "前態待確認"
            if funnel_state == "淘汰" and data.get("evidence_adjustment_reason")
            else deps["rejected_primary_reason"](stock_result)
            if funnel_state == "淘汰"
            else (blockers[0] if blockers else deps["final_label"](stock_result))
        )
    if not valid_entry and funnel_state in ["等冷卻", "等市場", "等接近", "等型態", "等回測", "等RR修復", "等量能", "等資料", "隔日確認", "淘汰"]:
        state = funnel_state
    if data_source_display_blocked:
        title_label = "資料不足"
    elif deps["is_valid_entry"](stock_result) and strategy_source_blocked:
        title_label = {
            "source-error": "策略樣本來源異常",
            "unresolved-conflict": "策略樣本來源衝突",
        }.get(strategy_source_status, "策略樣本證據不足")
    elif deps["is_valid_entry"](stock_result) and not source_eligible:
        title_label = "資料來源缺失" if source_status in {"missing-source", "insufficient-data"} else "資料來源異常"
    elif (state == "弱勢淘汰" or funnel_state == "淘汰") and not data.get("evidence_adjustment_reason"):
        title_label = deps["rejected_primary_reason"](stock_result)
    elif post_market_prepare:
        title_label = "開盤後確認"
    elif funnel_state == "可準備" and prepare_label:
        title_label = prepare_label

    if valid_entry:
        title_icon = "🟢"
        if funnel_state == "趨勢延續":
            title_action = "趨勢延續買入"
            title_label = "小倉"
        elif report_phase not in (None, "盤中"):
            title_action = f"明日追蹤｜{deps['unheld_entry_size_detail_text'](stock_result)}"
        else:
            title_action = f"可買｜{deps['unheld_entry_size_detail_text'](stock_result)}"
    elif deps["is_valid_entry"](stock_result) and not source_eligible:
        title_icon = "⛔"
        title_action = "不可行動"
    elif post_market_prepare:
        title_icon = "🟡"
        title_action = "明日準備｜不可買"
    elif data_source_display_blocked:
        title_icon = "⏳"
        title_action = "等資料"
    elif funnel_state == "可準備":
        title_icon = "👀"
        title_action = "可準備" if data.get("evidence_adjustment_reason") else deps["unheld_non_actionable_prepare_label"](data)
    elif state in ["等冷卻", "等市場", "等接近", "等型態", "等回測", "等資料"]:
        title_icon = "⏳"
        title_action = state
    elif state in ["等RR修復", "等量能", "隔日確認"]:
        title_icon = "👀"
        title_action = state
    elif funnel_state == "淘汰" and data.get("evidence_adjustment_reason"):
        title_icon = "⛔"
        title_action = "不買"
    elif state in ["弱勢淘汰", "淘汰"]:
        title_icon = "⛔"
        title_action = "淘汰"
    else:
        title_icon = "⛔"
        title_action = "不買"

    rr_text = _unheld_rr_text(stock_result, funnel_state, valid_entry, deps)
    wait_text = deps["unheld_entry_wait_text"](stock_result, state, funnel_state)
    detail_size_text = deps["unheld_entry_size_detail_text"](stock_result)
    raw_size_text = deps["entry_size_text"](stock_result)
    score_text = _confidence_data_text(report_context, name, data, deps)
    rr_data_text = f"RR：{rr_text}" if rr_text == "-（不可行動）" else f"RR {rr_text}"
    display_score_text = _unheld_score_text_for_state(
        score_text,
        rr_text,
        valid_entry,
        funnel_state,
        state,
        stock_result=stock_result,
        data=data_with_context,
    )
    if deps["is_valid_entry"](stock_result) and strategy_source_blocked:
        strategy_reason = {
            "missing-source": "策略樣本來源缺失",
            "insufficient-data": "策略樣本樣本不足",
            "source-error": "策略樣本來源讀取異常",
            "unresolved-conflict": "策略樣本來源衝突",
        }.get(strategy_source_status, "策略樣本不可用")
        buy_line = f"買點：不可買，{strategy_reason}"
        data_line = f"數據：{rr_data_text}｜S 證據不足｜V {data.get('volume_ratio', '-')}x"
        price_line = deps["price_change_line"](data.get("price"), data.get("change"))
    elif deps["is_valid_entry"](stock_result) and not source_eligible:
        source_reason = (
            "資料來源缺失"
            if source_status in {"missing-source", "insufficient-data"}
            else "資料來源異常"
        )
        buy_line = f"買點：不可買，{source_reason}"
        data_line = "數據：RR 不可用｜S 不可用｜V 不可用"
        price_line = f"價格：不可用（{source_reason}）"
    elif valid_entry and funnel_state == "趨勢延續":
        buy_line = "買點：趨勢延續買入｜小倉 <=15%｜回測 55% 勝 / +2.26%"
        data_line = f"數據：{rr_data_text}｜{score_text}｜V {data.get('volume_ratio', '-')}x"
        price_line = deps["price_change_line"](data.get("price"), data.get("change"))
    elif valid_entry and report_phase not in (None, "盤中"):
        buy_line = "買點：盤後追蹤｜開盤後確認｜不追價"
        data_line = f"數據：{rr_data_text}｜{score_text}｜V {data.get('volume_ratio', '-')}x"
        price_line = deps["price_change_line"](data.get("price"), data.get("change"))
    elif post_market_prepare:
        buy_line = "買點：明日準備｜不可下單"
        data_line = f"數據：{rr_data_text}｜{display_score_text}｜V {data.get('volume_ratio', '-')}x"
        price_line = deps["price_change_line"](data.get("price"), data.get("change"))
    elif valid_entry and detail_size_text != raw_size_text:
        buy_line = f"買點：可買｜{detail_size_text}｜分批，不追價"
        data_line = f"數據：{rr_data_text}｜{score_text}｜V {data.get('volume_ratio', '-')}x"
        price_line = deps["price_change_line"](data.get("price"), data.get("change"))
    elif valid_entry:
        buy_line = f"買點：可買｜建議 {raw_size_text}｜{wait_text}"
        data_line = f"數據：{rr_data_text}｜{score_text}｜V {data.get('volume_ratio', '-')}x"
        price_line = deps["price_change_line"](data.get("price"), data.get("change"))
    elif data_source_display_blocked:
        buy_line = "買點：不買，等資料恢復"
        data_line = f"數據：{rr_data_text}｜{display_score_text}｜V {data.get('volume_ratio', '-')}x"
        price_line = deps["price_change_line"](data.get("price"), data.get("change"))
    elif funnel_state == "可準備" and prepare_action:
        buy_line = f"買點：{prepare_action}"
        data_line = f"數據：{rr_data_text}｜{display_score_text}｜V {data.get('volume_ratio', '-')}x"
        price_line = deps["price_change_line"](data.get("price"), data.get("change"))
    elif funnel_state == "等回測":
        buy_line = "買點：不買，等回測"
        data_line = f"數據：{rr_data_text}｜{display_score_text}｜V {data.get('volume_ratio', '-')}x"
        price_line = deps["price_change_line"](data.get("price"), data.get("change"))
    elif funnel_state == "等接近":
        buy_line = "買點：不買，等接近觸發區"
        data_line = f"數據：{rr_data_text}｜{display_score_text}｜V {data.get('volume_ratio', '-')}x"
        price_line = deps["price_change_line"](data.get("price"), data.get("change"))
    elif funnel_state == "淘汰":
        buy_line = f"買點：不可買，{wait_text}"
        data_line = f"數據：{rr_data_text}｜{display_score_text}｜V {data.get('volume_ratio', '-')}x"
        price_line = deps["price_change_line"](data.get("price"), data.get("change"))
    else:
        buy_line = f"買點：不買，{wait_text}"
        data_line = f"數據：{rr_data_text}｜{display_score_text}｜V {data.get('volume_ratio', '-')}x"
        price_line = deps["price_change_line"](data.get("price"), data.get("change"))
    trigger_label = "盤中觸發" if report_phase == "盤中" else "明日觸發"
    if valid_entry and funnel_state == "趨勢延續":
        tomorrow_line = f"{trigger_label}：回踩站回日，小倉執行；不追高加碼"
    elif data_source_display_blocked:
        tomorrow_line = f"{trigger_label}：無有效進場，先補策略樣本證據"
    elif deps["is_valid_entry"](stock_result) and strategy_source_blocked:
        tomorrow_line = f"{trigger_label}：無有效進場，先補策略樣本證據"
    else:
        tomorrow_line = f"{trigger_label}：{deps['tomorrow_trigger_text'](state, data)}"
    reason_line = (
        "依據：回測 55% 勝 / +2.26%，回踩站回 ma5/ma10 後放量確認"
        if valid_entry and funnel_state == "趨勢延續"
        else
        (
            "原因：策略樣本不可用，高置信 S 分數 / 強弱分類暫不採用"
            if strategy_source_blocked
            else "原因：資料來源缺失，不作新倉決策"
        )
        if deps["is_valid_entry"](stock_result) and not source_eligible
        else "原因：資料來源缺失，停止新倉"
        if data_source_display_blocked
        else f"理由：{data.get('evidence_adjustment_reason')}" if data.get("evidence_adjustment_reason") else deps["rejected_transition_reason_line"](stock_result) if funnel_state == "淘汰" else None
    )
    show_source_decision_reason = (
        bool(reason_line)
        or valid_entry
        or state in ["弱勢淘汰", "淘汰"]
        or (deps["is_valid_entry"](stock_result) and not source_eligible)
    )
    if show_source_decision_reason:
        reason_line = _append_decision_reason(reason_line, report_context, name)
    trend_control_lines = []
    if valid_entry and funnel_state == "趨勢延續":
        trend_control_lines = [
            "倉位：<=15%",
            "止損：回踩低點下方；形態失效即出",
            "持有：對齊 5 日 edge，5 日內未續漲或跌破回踩低點即了結",
        ]
    low_volume_limit_up_risk = deps["low_volume_limit_up_risk_text"](data)
    buy_gap_line = _unheld_buy_gap_line(
        data_with_context,
        dist,
        blockers,
        valid_entry,
        funnel_state,
        source_status,
        strategy_source_blocked,
        title_label=title_label,
    )
    compact_wait_card = (
        not valid_entry
        and not strategy_source_blocked
        and source_eligible
        and (
            funnel_state in {"等接近", "等型態", "淘汰"}
            or state in {"等資料", "不可行動"}
        )
    )
    is_afterhours = effective_report_phase in {"盤後", "收盤"}
    is_afterhours_rejected = is_afterhours and funnel_state == "淘汰" and not valid_entry
    market_line = None if is_afterhours_rejected else (
        "盤面：證據不足｜待確認"
        if strategy_source_blocked
        else _score_gated_market_line(report_context, name, data, dist, deps)
    )
    if compact_wait_card and market_line == "盤面：證據不足｜待確認":
        market_line = None
    trade_state_line = deps["trade_state_machine_line"](data)
    if (
        (compact_wait_card and funnel_state == "淘汰")
        or (funnel_state == "淘汰" and "交易狀態：等資料" in str(trade_state_line))
    ):
        trade_state_line = None
    lines = [
        f"【{deps['stock_title'](name, data)}】{title_icon} {title_action}｜{title_label}",
        trade_state_line,
        market_line,
        buy_line,
        buy_gap_line,
    ]

    weak_buy_backtest_line = _weak_buy_backtest_line(
        name,
        data,
        deps,
        include_all=post_market_prepare,
    ) if (valid_entry or post_market_prepare) else None
    if weak_buy_backtest_line:
        lines.append(weak_buy_backtest_line)

    if reason_line and not (is_afterhours_rejected or compact_wait_card):
        lines.append(reason_line)

    lines.extend(trend_control_lines)

    lines.extend([
        tomorrow_line,
        None if is_afterhours else (
            deps["_source_status_line"](report_context, name, holding=False) if report_context else None
        ),
        None if (is_afterhours_rejected or compact_wait_card) else data_line,
        low_volume_limit_up_risk,
        price_line,
    ])
    lines = [line for line in lines if line is not None]
    lines = [_afterhours_card_text(line, report_context) for line in lines]
    history_line = None if is_afterhours else deps["cross_day_detail_line"](data)
    if history_line:
        lines.insert(-1, history_line)

    return "\n".join(lines)


def _brief_holding_line(holding_items, deps):
    if not holding_items:
        return "持倉：無持倉。"

    blocked = [
        name for name, data in holding_items
        if deps["position_summary_action"](name, data) in {"停利記憶不足", "停利記憶待確認"}
    ]
    if blocked:
        return f"持倉：{'、'.join(blocked)} 先補交易執行記憶；其餘依第一則風控卡處理。"

    return "持倉：依第一則既有卡片處理，不新增第二個主行動。"


def _brief_new_position_line(watch_items, report_context, deps, market_mode=None):
    funnel = deps["build_unheld_funnel"](watch_items, market_mode=market_mode, report_context=report_context) if watch_items else {"可買": []}
    actionable = len(funnel.get("可買") or []) + len(funnel.get("趨勢延續") or [])
    if actionable:
        return f"新倉：可行動候選 {actionable} 檔，以第二則卡片為準。"
    prepare_count = len(funnel.get("可準備") or []) if funnel else 0
    if prepare_count:
        return f"新倉：無有效進場；可準備 {prepare_count} 檔需明日開盤後確認，未確認前不可下單。"
    return "新倉：目前沒有可行動候選。"


def _today_buy_holding_names(holding_items, deps):
    return [
        name for name, data in holding_items
        if deps["is_today_buy_holding"](data)
    ]


def _today_buy_risk_names(holding_items, deps):
    return [
        name for name, data in holding_items
        if deps["is_today_buy_holding"](data)
        and deps["position_summary_action"](name, data) in {"停損", "減碼", "硬風控減碼"}
    ]


def _brief_background_line(report_context, deps):
    market = deps["_field_by_key"](report_context, "evidence.market_theme")
    strategy = deps["_field_by_key"](report_context, "evidence.strategy_sample")
    strategy_status = strategy.get("source_status", "missing-source")
    market_text = (
        "市場/題材背景只用來理解環境，不構成買點"
        if market.get("source_status") == "available"
        else "市場/題材背景可靠度不足，只作觀察"
    )
    if strategy_status in {"missing-source", "source-error", "insufficient-data"}:
        return f"背景：{market_text}；策略樣本本輪不採用。"
    return f"背景：{market_text}；策略樣本只作輔助，不新增進場理由。"


def _compact_market_overview_line(holding_items, watch_items, report_context, deps, market_mode=None):
    if market_mode is None:
        market_mode, risk_level = deps["derive_market_state"](watch_items)
    else:
        _mode, risk_level = deps["derive_market_state"](watch_items)
    funnel = deps["build_unheld_funnel"](watch_items, market_mode=market_mode, report_context=report_context) if watch_items else {}
    pending_count = len(deps["pending_trade_items"](
        holding_items,
        watch_items,
        market_mode=market_mode,
        report_context=report_context,
    ))
    pending_count += len(deps["executed_trade_items"](
        holding_items,
        watch_items,
        market_mode=market_mode,
        report_context=report_context,
    ))
    new_entry_count = len(deps["new_entry_suggestion_items"](
        watch_items,
        market_mode=market_mode,
        report_context=report_context,
    ))
    today_new_entry_count = len(_today_buy_holding_names(holding_items, deps))
    today_buy_risk_count = len(_today_buy_risk_names(holding_items, deps))
    executed_actions = deps["executed_trade_items"](
        holding_items,
        watch_items,
        market_mode=market_mode,
        report_context=report_context,
    )
    pending_actions = deps["pending_trade_items"](
        holding_items,
        watch_items,
        market_mode=market_mode,
        report_context=report_context,
    )
    action_labels = []
    for item in [*pending_actions, *executed_actions]:
        state = item.get("state") if isinstance(item, dict) else None
        line = item.get("line", "") if isinstance(item, dict) else ""
        if state == "已執行":
            if "停利" in line:
                state = "停利"
            elif "減碼" in line:
                state = "減碼"
            elif "停損" in line:
                state = "停損"
        if state and state not in action_labels:
            action_labels.append(state)
    action_suffix = f"（{'/'.join(action_labels[:3])}）" if action_labels else ""
    actionable_count = len(funnel.get("可買") or []) if funnel else 0
    trend_count = len(funnel.get("趨勢延續") or []) if funnel else 0
    prepare_counts = deps["unheld_prepare_bucket_counts"](
        watch_items,
        funnel=funnel,
        market_mode=market_mode,
        report_context=report_context,
    ) if funnel else {}
    tracking_only_count = deps["unheld_tracking_only_count"](funnel) if funnel else 0
    rejected_count = len(funnel.get("淘汰") or []) if funnel else 0
    unheld_count = sum(len(items) for items in funnel.values()) if funnel else len(watch_items)
    unheld_parts = []
    if actionable_count:
        unheld_parts.append(f"可買{actionable_count}")
    if trend_count:
        unheld_parts.append(f"趨勢延續{trend_count}")
    unheld_parts.extend(
        f"{label}{count}"
        for label, count in deps["_prepare_count_parts"](prepare_counts)
    )
    if rejected_count == unheld_count and unheld_count:
        unheld_parts.append("全部不可行動")
    else:
        if tracking_only_count:
            unheld_parts.append(f"僅追蹤{tracking_only_count}")
        if rejected_count:
            unheld_parts.append(f"淘汰{rejected_count}")
    if today_new_entry_count:
        today_observe_count = max(today_new_entry_count - today_buy_risk_count, 0)
        today_parts = []
        if today_buy_risk_count:
            today_parts.append(f"已風控 {today_buy_risk_count}")
        if today_observe_count:
            today_parts.append(f"觀察 {today_observe_count}")
        today_entry_text = f"今日買入紀錄 {today_new_entry_count}"
        if today_parts:
            today_entry_text += f"（{'/'.join(today_parts)}）"
    else:
        today_entry_text = f"今日新建倉 {today_new_entry_count}"
    parts = [
        f"市場：{market_mode} {risk_level}",
        f"執行動作 {pending_count}{action_suffix}",
        today_entry_text,
        f"持倉風控 {len(holding_items)}",
        f"未持倉 {unheld_count}（{'/'.join(unheld_parts)}）",
    ]
    if new_entry_count:
        parts.insert(2, f"新倉建議 {new_entry_count}")
    if trend_count:
        parts.insert(3, f"趨勢延續買入 {trend_count} 檔小倉")
    return "｜".join(parts)


def _afterhours_brief_lines(holding_items, watch_items, report_context, deps, market_mode=None, daily_write_warning=None):
    funnel = deps["build_unheld_funnel"](watch_items, market_mode=market_mode, report_context=report_context) if watch_items else {"可買": []}
    actionable = len(funnel.get("可買") or []) + len(funnel.get("趨勢延續") or [])
    prepare_count = len(funnel.get("可準備") or [])
    has_holding = bool(holding_items)
    today_buy_names = _today_buy_holding_names(holding_items, deps)
    today_buy_risk_names = _today_buy_risk_names(holding_items, deps)
    today_buy_risk_count = len(today_buy_risk_names)
    today_buy_observe_count = max(len(today_buy_names) - today_buy_risk_count, 0)
    all_today_buys_are_risk = bool(today_buy_names) and today_buy_risk_count == len(today_buy_names)
    mixed_today_buy_risk = bool(today_buy_names) and 0 < today_buy_risk_count < len(today_buy_names)
    if actionable and today_buy_names:
        if all_today_buys_are_risk:
            conclusion = f"結論：今日買入紀錄 {len(today_buy_names)} 檔，已全部轉入風控/停損減碼；新增有效進場 {actionable} 檔需明日開盤前確認。"
        elif mixed_today_buy_risk:
            conclusion = f"結論：今日買入紀錄 {len(today_buy_names)} 檔（已風控 {today_buy_risk_count}/觀察 {today_buy_observe_count}）；新增有效進場 {actionable} 檔需明日開盤前確認。"
        else:
            conclusion = f"結論：今日交易已建立新倉 {len(today_buy_names)} 檔；新增有效進場 {actionable} 檔需明日開盤前確認。"
    elif actionable:
        conclusion = f"結論：新倉候選 {actionable} 檔需明日開盤前確認；既有持倉以收盤後風控觀察為主。"
    elif today_buy_names:
        if all_today_buys_are_risk:
            conclusion = f"結論：今日買入紀錄 {len(today_buy_names)} 檔，已全部轉入風控/停損減碼；新增有效進場：無。"
        elif mixed_today_buy_risk:
            conclusion = f"結論：今日買入紀錄 {len(today_buy_names)} 檔（已風控 {today_buy_risk_count}/觀察 {today_buy_observe_count}）；新增有效進場：無。"
        else:
            conclusion = f"結論：今日交易已建立新倉 {len(today_buy_names)} 檔；新增有效進場：無。"
    elif has_holding:
        conclusion = "結論：今日無有效新倉；既有持倉以收盤後風控觀察為主。"
    else:
        conclusion = "結論：今日無有效新倉；未持倉標的等待下一交易日訊號。"

    checks = []
    if holding_items:
        checks.append("觀察持倉是否跌破警戒")
    if actionable:
        checks.append("新倉候選需開盤後重新確認有效進場")
    elif prepare_count:
        checks.append("可準備候選需明日開盤後確認，未確認前不可下單")
    elif watch_items:
        checks.append("未持倉標的重新等待有效進場")
    if not checks:
        checks.append("等下一交易日資料更新")

    lines = [
        "📌 盤後簡報",
        _compact_market_overview_line(holding_items, watch_items, report_context, deps, market_mode=market_mode),
        conclusion,
    ]
    if today_buy_names:
        if all_today_buys_are_risk:
            today_trade_line = f"今日買入紀錄後風控：{len(today_buy_names)} 檔（{'、'.join(today_buy_names)}）"
        elif mixed_today_buy_risk:
            today_trade_line = f"今日買入狀態：已風控 {today_buy_risk_count}/觀察 {today_buy_observe_count}（{'、'.join(today_buy_names)}）"
        else:
            today_trade_line = f"今日交易：已建立新倉 {len(today_buy_names)} 檔（{'、'.join(today_buy_names)}）"
        lines.extend([
            today_trade_line,
            f"新增有效進場：{actionable} 檔需明日開盤前確認" if actionable else "新增有效進場：無",
        ])
        if prepare_count:
            lines.append(f"可準備：{prepare_count} 檔需明日開盤後確認，未確認前不可下單")
    elif actionable:
        lines.append(f"新增有效進場：{actionable} 檔需明日開盤前確認")
        if prepare_count:
            lines.append(f"可準備：{prepare_count} 檔需明日開盤後確認，未確認前不可下單")
    elif prepare_count:
        lines.extend([
            "新倉：無有效進場",
            f"可準備：{prepare_count} 檔需明日開盤後確認，未確認前不可下單",
            "新增有效進場：無",
        ])
    elif not actionable:
        lines.append("新增有效進場：無")
    lines.append(f"明日前確認：{'；'.join(checks[:3])}。")
    if holding_items:
        lines.extend([
            "",
            "持倉風控檢查",
            *deps["format_holding_control_checklist"](holding_items, report_phase="盤後"),
        ])
    new_entry_lines = deps["format_new_entry_suggestions"](
        watch_items, report_phase="盤後", market_mode=market_mode, report_context=report_context
    )
    if new_entry_lines:
        lines.extend(["", "新倉建議", *new_entry_lines])
    unheld_funnel_text = deps["format_unheld_funnel"](watch_items, market_mode=market_mode, report_context=report_context)
    if unheld_funnel_text:
        lines.extend(["", "未持倉狀態：", unheld_funnel_text])
    lines.extend(deps["format_backtest_groups"](watch_items, report_context=report_context))
    if daily_write_warning:
        lines.append(f"資料寫入：{daily_write_warning}，明日前確認補寫狀態。")
    return lines


def _market_theme_data_basis_line(report_context, deps):
    evidence = report_context.get("market_theme_evidence") or {}
    field = deps["_field_by_key"](report_context, "evidence.market_theme")
    status = field.get("source_status") or deps["_manifest_status"](evidence.get("source_status"))
    trend = evidence.get("evidence_trend") or {}
    trend_parts = []
    if trend.get("observed_days"):
        trend_parts.append(f"近 {trend.get('observed_days')} 個交易日短期背景")
    if trend.get("recent_supporting_days") is not None:
        trend_parts.append(f"近期 {trend.get('recent_supporting_days')} 日支持")
    trend_text = "，".join(trend_parts) if trend_parts else "短期背景資料"

    observed_days = trend.get("observed_days") or 0
    supporting_days = trend.get("recent_supporting_days")
    support_streak = trend.get("support_streak_days") or 0
    if status != "available" or observed_days < 5:
        reliability = "資料不足"
    elif observed_days >= 15 and (supporting_days or 0) >= 3 and support_streak >= 2:
        reliability = "可靠度較高"
    elif observed_days >= 10 and (supporting_days or 0) >= 2:
        reliability = "可靠度有限"
    else:
        reliability = "可靠度不足以判定"

    if reliability == "資料不足":
        return "市場 / 題材背景：短期背景資料不足，僅供觀察。"
    if evidence.get("confirmed") and status == "available":
        return (
            f"市場 / 題材背景：{trend_text}仍支持目前背景觀察，{reliability}；"
            "這只用來理解環境，不等於買點。"
        )
    if status in {"missing-source", "source-error", "insufficient-data"}:
        return "市場 / 題材背景：短期背景資料不足，僅供觀察。"
    return f"市場 / 題材背景：{trend_text}只作背景觀察，可靠度有限，不等於買點。"


def _strategy_sample_data_basis_line(report_context, deps):
    strategy = deps["_field_by_key"](report_context, "evidence.strategy_sample")
    status = strategy.get("source_status", "missing-source")
    report_results = report_context.get("results_map") or {}
    has_trend_continuation_buy = any(
        ((data.get("result") or {}).get("decision_type") == "trend_continuation")
        and ((data.get("result") or {}).get("decision") == "BUY")
        for data in report_results.values()
        if isinstance(data, dict)
    )
    if status == "missing-source":
        return "策略樣本：缺少可驗證來源，本次不納入買賣判斷。"
    if status == "insufficient-data":
        return "策略樣本：樣本不足，本次不納入買賣判斷。"
    if status == "source-error":
        return "策略樣本：來源讀取異常，本次不納入買賣判斷。"
    if has_trend_continuation_buy:
        return "策略樣本：trend_continuation 同源證據達標，僅此例外支持回踩站回小倉買入。"
    return "策略樣本：樣本來源可驗證，只作輔助參考，不新增買點。"


def _position_candidate_data_basis_line(report_context, holding_items=None, watch_items=None, deps=None, market_mode=None):
    statuses = report_context.get("source_status_summary") or {}
    position_status = statuses.get("position", "missing-source")
    candidate_status = statuses.get("funnel", "missing-source")
    position_ready = position_status == "available"
    candidate_ready = candidate_status in {"available", "derived"}
    holding_count = len(holding_items or [])
    watch_count = len(watch_items or [])
    funnel_text = ""
    trend_count = 0
    if deps and watch_items:
        funnel = deps["build_unheld_funnel"](watch_items, market_mode=market_mode, report_context=report_context)
        prepare_counts = deps["unheld_prepare_bucket_counts"](
            watch_items,
            funnel=funnel,
            market_mode=market_mode,
            report_context=report_context,
        )
        buy_count = len(funnel.get("可買") or [])
        trend_count = len(funnel.get("趨勢延續") or [])
        prepare_count = len(funnel.get("可準備") or [])
        prepare_text = deps["unheld_prepare_funnel_text"](prepare_counts) or "不可追高觀察 0"
        tracking_count = deps["unheld_tracking_only_count"](funnel)
        rejected_count = len(funnel.get("淘汰") or [])
        trend_text = f"趨勢延續 {trend_count}、" if trend_count else ""
        funnel_text = (
            f"未持倉 {watch_count} 檔已分類：可買 {buy_count}、"
            f"{trend_text}{prepare_text}、僅追蹤 {tracking_count}、淘汰 {rejected_count}；"
        )
    elif watch_count:
        funnel_text = f"未持倉 {watch_count} 檔已分類；"

    position_text = (
        f"持倉與價格資料可支持風控檢查（持倉 {holding_count} 檔）；"
        if holding_count
        else "持倉與價格資料可支持風控檢查；"
    )

    if trend_count:
        return (
            f"持倉 / 價格 / 候選資料：{position_text}{funnel_text}"
            "trend_continuation 同源證據達標者支持小倉進場，其餘未持倉資料只支持分類觀察。"
        )

    if position_ready and candidate_ready:
        return (
            f"持倉 / 價格 / 候選資料：{position_text}{funnel_text}"
            "未持倉資料只支持分類觀察，不支持直接進場。"
        )
    if position_ready:
        return (
            f"持倉 / 價格 / 候選資料：{position_text}"
            "未持倉資料不足時只支持分類觀察，不支持直接進場。"
        )
    return (
        "持倉 / 價格 / 候選資料：部分持倉或候選資料不足，只能支持有限風控檢查；"
        "未持倉資料只支持分類觀察，不支持直接進場。"
    )


def _layer_status(report_context, layer):
    slots = [
        field for field in report_context.get("evidence_manifest") or []
        if field.get("layer") == layer
    ]
    if not slots:
        return "missing-source"
    statuses = {slot.get("status") for slot in slots}
    if "unresolved-conflict" in statuses:
        return "unresolved-conflict"
    if "source-error" in statuses:
        return "source-error"
    if "missing-source" in statuses:
        return "missing-source"
    if "insufficient-data" in statuses:
        return "insufficient-data"
    if statuses == {"not-used"}:
        return "not-used"
    return "available"


def _evidence_human_status_lines(report_context, deps):
    statuses = report_context.get("source_status_summary") or {}
    lines = []

    ledger_status = _layer_status(report_context, "ledger")
    conflict_status = _layer_status(report_context, "conflict")
    has_conflict = (
        ledger_status == "unresolved-conflict"
        or conflict_status == "unresolved-conflict"
        or any(
            field.get("conflict") not in [None, "", "none"]
            for field in report_context.get("evidence_manifest") or []
        )
    )
    if ledger_status == "insufficient-data":
        lines.append("執行記憶：資料不足，涉及已賣、停利、今日買賣或剩餘股數時採保守顯示，不補推已執行結論。")
    elif has_conflict:
        lines.append("執行記憶：紀錄仍有待釐清的差異，未確認部分不輸出確定結論。")
    elif ledger_status == "available" and _report_phase(report_context) == "盤後":
        lines.append("執行記憶：今日買賣、停利與剩餘股數依可驗證紀錄處理；無確認紀錄時不補推已執行結論。")

    position_status = statuses.get("position")
    if position_status in {"missing-source", "source-error"}:
        lines.append("持倉來源：讀取不足，持倉風控只保留可確認資訊。")

    candidate_status = statuses.get("funnel")
    if candidate_status in {"missing-source", "source-error", "insufficient-data", "unresolved-conflict"}:
        lines.append("未持倉候選：來源不足或有疑義的標的不輸出有效進場。")

    lines.append("持倉 RR：既有持倉若不是加碼情境，只顯示新倉 RR 不適用。持倉主行動以風控為準，避免把持倉誤讀成新買點。")
    return lines


def _decision_brief_lines(
    summary_message,
    version,
    excluded_summary_lines=None,
    excluded_summary_sections=None,
    excluded_summary_prefixes=None,
):
    excluded_summary_lines = set(excluded_summary_lines or [])
    excluded_summary_sections = set(excluded_summary_sections or [])
    excluded_summary_prefixes = tuple(excluded_summary_prefixes or ())
    lines = []
    skip_excluded_section = False
    for line in (summary_message or "").splitlines():
        if line in excluded_summary_sections:
            skip_excluded_section = True
            continue
        if skip_excluded_section:
            if line == "":
                skip_excluded_section = False
            continue
        if line in excluded_summary_lines:
            continue
        if excluded_summary_prefixes and line.startswith(excluded_summary_prefixes):
            continue
        if line.startswith("【") and f"｜{version}】" in line:
            continue
        lines.append(line)

    while lines and lines[0] == "":
        lines.pop(0)
    while lines and lines[-1] == "":
        lines.pop()
    return lines


def _status_is_abnormal(status):
    return status in {
        "missing-source",
        "source-error",
        "insufficient-data",
        "insufficient",
        "missing",
        "unresolved-conflict",
    }


def _has_abnormal_data_basis(report_context):
    report_results = (report_context or {}).get("results_map") or {}
    for data in report_results.values():
        if not isinstance(data, dict):
            continue
        stock_result = data.get("result") or {}
        if stock_result.get("decision_type") == "trend_continuation" and stock_result.get("decision") == "BUY":
            return True
    statuses = (report_context or {}).get("source_status_summary") or {}
    for key, status in statuses.items():
        if key == "position" and status == "not-applicable":
            continue
        if _status_is_abnormal(status):
            return True
    for field in (report_context or {}).get("evidence_manifest") or []:
        field_name = field.get("field_name") or ""
        status = field.get("source_status") or field.get("status")
        if field_name.startswith("source.") and _status_is_abnormal(status):
            return True
        if field.get("conflict") not in [None, "", "none"]:
            return True
    return False


def _data_basis_lines(report_context, holding_items, watch_items, deps, market_mode=None):
    if not _has_abnormal_data_basis(report_context):
        return []
    lines = [
        _market_theme_data_basis_line(report_context, deps),
        _strategy_sample_data_basis_line(report_context, deps),
        _position_candidate_data_basis_line(
            report_context,
            holding_items=holding_items,
            watch_items=watch_items,
            deps=deps,
            market_mode=market_mode,
        ),
        *_evidence_human_status_lines(report_context, deps),
    ]
    return [line for line in lines if line is not None]


def format_brief_data_evidence_message(
    report_context,
    holding_items,
    watch_items,
    *,
    version,
    deps,
    market_mode=None,
    summary_message=None,
    summary_excluded_lines=None,
    summary_excluded_prefixes=None,
    summary_excluded_sections=None,
    daily_write_warning=None,
):
    if _report_phase(report_context) == "盤後":
        decision_lines = _afterhours_brief_lines(
            holding_items,
            watch_items,
            report_context,
            deps,
            market_mode=market_mode,
            daily_write_warning=daily_write_warning,
        )
    else:
        decision_lines = _decision_brief_lines(
            summary_message,
            version,
            excluded_summary_lines=summary_excluded_lines,
            excluded_summary_prefixes=summary_excluded_prefixes,
            excluded_summary_sections=summary_excluded_sections,
        )
        brief_lines = [
            _compact_market_overview_line(holding_items, watch_items, report_context, deps, market_mode=market_mode),
            _brief_holding_line(holding_items, deps),
        ]
        if not deps["new_entry_suggestion_items"](
            watch_items,
            market_mode=market_mode,
            report_context=report_context,
        ):
            brief_lines.append("新倉：無有效進場")
        decision_lines = brief_lines + decision_lines

    data_basis_lines = []
    if SHOW_DATA_BASIS:
        data_basis_lines = _data_basis_lines(
            report_context,
            holding_items,
            watch_items,
            deps,
            market_mode=market_mode,
        )
    title = f"🧾 {version} 簡報＋資料依據" if data_basis_lines else f"🧾 {version} 簡報"
    lines = [
        title,
        "",
        "決策簡報",
        *decision_lines,
    ]
    if data_basis_lines:
        lines.extend(["", "資料依據", *data_basis_lines])
    return "\n".join(line for line in lines if line is not None)


def render_telegram_messages(
    results_map,
    full_msg,
    best,
    score,
    market_summary,
    now,
    *,
    version,
    deps,
    position_warning=None,
    include_detail=False,
    daily_write_warning=None,
    strategy_evidence_summary=None,
    report_phase=None,
    future_watch_message=None,
):
    ordered_items = deps["ordered_result_items"](results_map)
    if report_phase is None:
        report_phase = deps["get_market_phase"]()
    watch_items_for_mode = [
        (name, data)
        for name, data in ordered_items
        if not data.get("holding")
    ]
    market_mode, _risk_level = deps["derive_market_state"](watch_items_for_mode)
    report_context = deps["build_report_context"](
        results_map,
        market_summary,
        now,
        strategy_evidence_summary=strategy_evidence_summary,
        report_phase=report_phase,
        position_warning=position_warning,
    )
    deps["apply_trade_state_machine"](
        results_map,
        report_context=report_context,
        market_mode=market_mode,
    )
    holding_items = deps["sort_position_summary"]([
        (name, data)
        for name, data in ordered_items
        if data.get("holding")
    ])
    watch_items = [
        (name, data)
        for name, data in ordered_items
        if not data.get("holding")
    ]
    position_cards = [
        deps["formatTelegramPositionCard"](name, data, report_context=report_context)
        for name, data in holding_items
    ]
    unheld_cards = [
        deps["formatTelegramUnheldCard"](
            name,
            data,
            report_phase=report_phase,
            market_mode=market_mode,
            report_context=report_context,
        )
        for _index, (name, data) in deps["sort_watchlist_grouped"]([
            (name, data)
            for name, data in ordered_items
            if not data.get("holding")
        ])
    ]
    telegram_header = f"【{now.strftime('%m/%d')} {report_phase}｜{version}】"
    holdings_message = (
        f"{telegram_header}\n"
        "【持倉標的】\n\n"
        + ("\n\n".join(position_cards) if position_cards else "無持倉")
    )
    unheld_message = (
        f"{telegram_header}\n"
        "【未持倉標的】\n\n"
        + ("\n\n".join(unheld_cards) if unheld_cards else "無")
    )
    summary_message = deps["formatTelegramSummary"](
        results_map,
        best,
        score,
        market_summary,
        now,
        position_warning,
        daily_write_warning,
        strategy_evidence_summary,
        report_phase=report_phase,
        report_context=report_context,
    )
    summary_excluded_lines = {
        telegram_header,
        f"報告日：{report_context['report_context'].get('as_of_date')}｜資料交易日：{report_context['report_context'].get('trade_date')}",
        f"Source：{report_context.get('source_status_text')}",
        f"📌 持倉：{'、'.join(name for name, _data in holding_items) or '無'}",
    }
    summary_excluded_prefixes = (
        "市場/結論：",
        "背景：",
        "僅追蹤：",
    )
    if position_warning:
        summary_excluded_lines.add(f"⚠ {position_warning}，持倉狀態不可信")
    summary_excluded_lines.update(deps["format_market_theme_summary_lines"](
        report_context.get("market_theme_evidence") or deps["market_theme_summary_evidence"](results_map, market_summary)
    ))
    if any(
        data.get("price_source") == "runtime-cache" or data.get("daily_source") == "runtime-cache"
        for _name, data in ordered_items
    ):
        summary_excluded_lines.add(deps["source_summary_text"](results_map))
    technical_executed_names = {
        name
        for name, data in holding_items
        if data.get("cross_day_context")
    }
    if technical_executed_names:
        for executed_line in deps["format_executed_checklist"](holding_items, watch_items):
            if any(f". {name}｜" in executed_line for name in technical_executed_names):
                summary_excluded_lines.add(executed_line)
    blocked_holding_names = {
        name
        for name, data in holding_items
        if deps["position_summary_action"](name, data) in {"停利記憶不足", "停利記憶待確認"}
    }
    if blocked_holding_names:
        for control_line in deps["format_holding_control_checklist"](holding_items, report_phase=report_phase):
            if any(f". {name}｜" in control_line for name in blocked_holding_names):
                summary_excluded_lines.add(control_line)
    summary_excluded_sections = []
    strategy_evidence_text = _strategy_evidence_text(strategy_evidence_summary)
    if strategy_evidence_text:
        summary_excluded_sections.append(strategy_evidence_text.splitlines()[0])
    summary_excluded_sections.append("僅追蹤：")
    evidence_message = deps["format_brief_data_evidence_message"](
        report_context,
        holding_items,
        watch_items,
        market_mode=market_mode,
        summary_message=summary_message,
        summary_excluded_lines=summary_excluded_lines,
        summary_excluded_prefixes=summary_excluded_prefixes,
        summary_excluded_sections=summary_excluded_sections,
        daily_write_warning=daily_write_warning,
    )

    messages = [
        holdings_message,
        unheld_message,
        f"{telegram_header}\n{evidence_message}",
    ]
    if future_watch_message:
        messages.append(future_watch_message)

    if include_detail:
        for chunk in deps["format_details_backup_messages"](full_msg):
            messages.append(chunk)

    return messages
