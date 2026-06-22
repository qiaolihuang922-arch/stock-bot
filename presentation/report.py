"""Telegram presentation assembly.

This module assembles already-prepared report data into Telegram messages. It
does not import storage clients or evidence writers; core.generator owns data
preparation and passes the formatter helpers needed for compatibility.
"""

SHOW_DATA_BASIS = False


def _float_or_none(value):
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _is_today_action_phase(report_phase):
    return report_phase in (None, "盤前", "盤中")


def _today_trigger_label(report_phase):
    return "盤前觀察" if report_phase == "盤前" else "盤中觸發"


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

    if _is_today_action_phase(report_phase):
        lines.append(deps["source_summary_text"](results_map))

    lines.append(f"原因：{reason_line}")
    lines.append(f"風險：{'；'.join(risk_parts)}")

    lines.extend([
        *deps["market_execution_bridge_lines"](
            holding_items,
            watch_items,
            market_mode,
            market_summary,
            report_context=report_context,
        ),
        *deps["format_cross_day_tracking_summary"](watch_items, report_context=report_context, market_mode=market_mode),
        *deps["format_strong_prepare_summary"](watch_items, market_mode),
        *deps["format_market_theme_summary_lines"](
            report_context.get("market_theme_evidence") or deps["market_theme_summary_evidence"](results_map, market_summary)
        ),
        f"📌 持倉：{holding_names}",
    ])

    if _is_today_action_phase(report_phase):
        execution_lines = deps["format_execution_checklist"](
            holding_items, watch_items, report_phase=report_phase, market_mode=market_mode, report_context=report_context
        )
        execution_lines = [line for line in execution_lines if line != "無新增下單"]
        if execution_lines:
            heading = "今日盤中風控建議" if report_phase == "盤中" else "今日盤前風控計畫"
            lines.extend(["", heading])
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
    executed_lines = deps["format_executed_checklist"](holding_items, watch_items)
    if executed_lines:
        lines.extend(["", "已執行（不重複下單）"])
        lines.extend(executed_lines)

    lines.extend(["", "持倉風控檢查"])
    lines.extend(deps["format_holding_control_checklist"](holding_items, report_phase=report_phase))

    if not _is_today_action_phase(report_phase):
        new_entry_lines = deps["format_new_entry_suggestions"](
            watch_items, report_phase=report_phase, market_mode=market_mode, report_context=report_context
        )
        if new_entry_lines:
            lines.extend(["", "新倉建議"])
            lines.extend(new_entry_lines)

    unheld_funnel_text = deps["format_unheld_funnel"](watch_items, market_mode=market_mode, report_context=report_context)
    if unheld_funnel_text:
        lines.extend(["", "未持倉狀態：", unheld_funnel_text])

    lines.extend(deps["format_backtest_groups"](watch_items, report_context=report_context))

    rejected_line = deps["rejected_trace_line"](watch_items, market_mode=market_mode, report_context=report_context)
    if rejected_line:
        lines.append(rejected_line)

    strategy_evidence_text = _strategy_evidence_text(strategy_evidence_summary)
    if strategy_evidence_text:
        lines.extend(["", strategy_evidence_text])

    lines = [_readable_rr_terms(line) for line in lines]
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
        stock_result.get("heat_state") == "EXTREME"
        or stock_result.get("trade_state") == "AVOID"
        or stock_result.get("price_behavior") == "LIMIT_LOCK"
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
    if stock_result.get("_volume_ratio_from_data"):
        for key in ["volume_ratio", "volume_ratio_10", "volume_ratio_20"]:
            try:
                value = stock_result.get(key)
            except AttributeError:
                value = None
            try:
                if value is not None and float(value) >= 1.1:
                    return False
            except (TypeError, ValueError):
                continue
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
    if funnel_state == "可準備":
        return score_text
    reason = _hidden_score_reason(rr_text, funnel_state, state)
    if reason == "RR不足":
        return "不適用（風險報酬不足）｜原因：風險報酬不足，等待修復"
    if reason == "等回測":
        return "不適用（等回測）｜原因：等待前高/突破區回測承接"
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


def _volume_window_text(data):
    v10 = _gate_value_text((data or {}).get("volume_ratio_10") or (data or {}).get("volume_ratio"))
    v20 = _gate_value_text((data or {}).get("volume_ratio_20"))
    if v10 and v20:
        return f"V10 {v10}x / V20 {v20}x"
    if v10:
        return f"V10 {v10}x"
    return None


def _volume_window_gap_text(data):
    volume_text = _volume_window_text(data)
    if not volume_text:
        return None
    try:
        v10 = float((data or {}).get("volume_ratio_10") or (data or {}).get("volume_ratio") or 0)
        v20_raw = (data or {}).get("volume_ratio_20")
        v20 = float(v20_raw) if v20_raw is not None else v10
    except (TypeError, ValueError):
        return f"{volume_text}待確認"
    return f"{volume_text}{'偏弱' if min(v10, v20) < 0.8 else '達標'}"


def _rr_gap_summary(stock_result, reason=None, funnel_state=None):
    rr_text = _gate_value_text((stock_result or {}).get("rr"))
    if not rr_text:
        return None
    try:
        rr_value = float(rr_text)
    except (TypeError, ValueError):
        return f"風險報酬 {rr_text}"
    if rr_value < 1.5:
        return None
    if (stock_result or {}).get("rr_context") == "actionable":
        return f"風險報酬 {rr_text}達標"
    return _potential_reward_text(rr_text, reason=reason, funnel_state=funnel_state, stock_result=stock_result)


def _potential_reward_text(rr_text, reason=None, funnel_state=None, stock_result=None):
    if not rr_text:
        return "潛在報酬：待確認，買點未成立"
    reason_text = str(reason or "")
    state_text = str(funnel_state or "")
    stock_result = stock_result or {}
    phase = str(stock_result.get("structure_phase") or "")
    behavior = str(stock_result.get("price_behavior") or "")
    if "急彈" in reason_text or state_text == "等回測":
        suffix = "但尚未回測確認"
    elif "反彈力道不足" in reason_text or state_text == "淘汰" or phase == "WEAK_REBOUND" or behavior == "WEAK_REBOUND":
        suffix = "但反彈未轉強"
    elif "進場品質" in reason_text or state_text == "等型態":
        suffix = "但型態/品質未過"
    elif "距觸發" in reason_text or state_text == "等接近":
        suffix = "但距離買點太遠"
    elif "開盤" in reason_text or state_text == "可準備":
        suffix = "但需開盤確認"
    else:
        suffix = "但買點未成立"
    return f"潛在報酬：好（{rr_text}倍），{suffix}"


def _entry_setup_summary(data, dist, stock_result, reason=None, funnel_state=None):
    parts = []
    retest_text = _retest_zone_text(data)
    if retest_text:
        parts.append(retest_text)
    volume_text = _volume_window_gap_text(data)
    if volume_text:
        parts.append(volume_text)
    rr_text = _rr_gap_summary(stock_result, reason=reason, funnel_state=funnel_state)
    if rr_text:
        parts.append(rr_text)
    return parts


def _retest_zone_text(data):
    low = _gate_value_text((data or {}).get("retest_zone_low"))
    high = _gate_value_text((data or {}).get("retest_zone_high"))
    if low and high:
        try:
            price = float((data or {}).get("price"))
            if price < float(low):
                return f"突破區 {low}~{high}（現價未站回）"
        except (TypeError, ValueError):
            pass
        return f"回測區 {low}~{high}"
    return "回測前高/突破區"


def _breakout_trigger_zone_text(data):
    low = _gate_value_text((data or {}).get("retest_zone_low"))
    high = _gate_value_text((data or {}).get("retest_zone_high"))
    if low and high:
        return f"突破區 {low}~{high}"
    if low:
        return f"突破區 {low} 附近"
    return "突破區/回測支撐"


def _retest_unlock_text(data):
    low = _gate_value_text((data or {}).get("retest_zone_low"))
    high = _gate_value_text((data or {}).get("retest_zone_high"))
    if low and high:
        try:
            price = float((data or {}).get("price"))
            if price < float(low):
                return f"先站回突破區 {low}~{high}，再回測不破"
        except (TypeError, ValueError):
            pass
        return f"回測區 {low}~{high}不破"
    return "回測前高/突破區不破"


def _recent_rebound_close_text(data):
    points = (
        ((data or {}).get("cross_day_context") or {})
        .get("recent_daily_price_points")
        or []
    )
    closes = []
    for point in points:
        if (point or {}).get("source") != "daily_price":
            continue
        try:
            closes.append(float(point.get("close")))
        except (AttributeError, TypeError, ValueError):
            continue
    if closes:
        close = _gate_value_text(closes[-1])
        return f"最近反彈收盤 {close} 附近"
    return "最近反彈收盤"


def _retest_anchor_value_from_text(retest_text):
    text = str(retest_text or "")
    marker = "最近反彈收盤"
    if marker not in text:
        return None
    tail = text.split(marker, 1)[1].strip()
    if tail.startswith("："):
        tail = tail[1:].strip()
    token = tail.split(" ", 1)[0].split("附近", 1)[0].split("；", 1)[0]
    return _float_or_none(token)


def _rebound_retest_basis_line(data, retest_text):
    anchor = str(retest_text or "").replace(" 附近不破", "").strip()
    anchor_value = _retest_anchor_value_from_text(retest_text)
    current_value = _float_or_none((data or {}).get("price"))
    if anchor_value is None or current_value is None:
        return f"回測基準：{anchor}；等待回測確認"

    tolerance = anchor_value * 0.005
    if current_value < anchor_value - tolerance:
        return f"回測基準：{anchor}；已跌破，等待重新站回或形成新支撐"
    if current_value <= anchor_value + tolerance:
        return f"回測基準：{anchor}；回測中，觀察能否守住"
    return f"回測基準：{anchor}；尚未回測"


def _daily_price_points(data):
    context = ((data or {}).get("cross_day_context") or {})
    sources = context.get("source_of_truth") or []
    if isinstance(sources, str):
        sources = [sources]
    if "daily_price" not in sources:
        return []
    points = []
    for point in context.get("recent_daily_price_points") or []:
        if (point or {}).get("source") != "daily_price":
            continue
        try:
            close = float(point.get("close"))
        except (AttributeError, TypeError, ValueError):
            continue
        normalized = {"close": close}
        for key in ["open", "high", "low", "volume"]:
            try:
                raw_value = point.get(key)
                if raw_value is not None:
                    normalized[key] = float(raw_value)
            except (AttributeError, TypeError, ValueError):
                pass
        points.append(normalized)
    return points


def _low_repair_anchor_text(data):
    points = _daily_price_points(data)
    if len(points) < 4:
        return "DB 日線不足，先不判斷低位修復"
    closes = [point["close"] for point in points]
    lows = [point.get("low", point["close"]) for point in points]
    recent_lows = lows[-5:] if len(lows) >= 5 else lows
    support = min(recent_lows)
    parts = [f"近期支撐 {_gate_value_text(support)}"]
    if len(closes) >= 5:
        ma5 = sum(closes[-5:]) / 5
        parts.append(f"5日均 {_gate_value_text(ma5)}")
    volume_values = [point.get("volume") for point in points if point.get("volume") is not None]
    if len(volume_values) >= 5:
        avg_volume = sum(volume_values[-5:]) / 5
        latest_volume = volume_values[-1]
        if avg_volume:
            parts.append(f"量能 {_gate_value_text(latest_volume / avg_volume)}x")
    return "｜".join(parts)


def _low_repair_progress_text(data):
    status = (data or {}).get("low_repair_status")
    if isinstance(status, dict) and status.get("ready"):
        met = status.get("met") or ["支撐未破", "站上5日均", "量能有效", "風險報酬達標"]
        return "已滿足 " + "、".join(met)
    points = _daily_price_points(data)
    if len(points) < 4:
        return "還差 DB日線補齊"
    stock_result = (data or {}).get("result") or {}
    closes = [point["close"] for point in points]
    lows = [point.get("low", point["close"]) for point in points]
    support = min((lows[-5:] if len(lows) >= 5 else lows))
    latest_price = _float_or_none((data or {}).get("price"))
    latest_close = latest_price if latest_price is not None else closes[-1]
    met = []
    missing = []

    if latest_close >= support:
        met.append("支撐未破")
    else:
        missing.append(f"守回支撐 {_gate_value_text(support)}")

    if len(closes) >= 5:
        ma5 = sum(closes[-5:]) / 5
        if latest_close >= ma5:
            met.append("站上5日均")
        else:
            missing.append(f"站回5日均 {_gate_value_text(ma5)}")
    else:
        missing.append("5日均資料補齊")

    volume_values = [point.get("volume") for point in points if point.get("volume") is not None]
    if len(volume_values) >= 5:
        avg_volume = sum(volume_values[-5:]) / 5
        latest_volume = volume_values[-1]
        volume_ratio = latest_volume / avg_volume if avg_volume else None
        if volume_ratio is not None and volume_ratio >= 1:
            met.append(f"量能有效 {_gate_value_text(volume_ratio)}x")
        elif volume_ratio is not None:
            missing.append(f"量能轉強（目前 {_gate_value_text(volume_ratio)}x）")
        else:
            missing.append("量能資料補齊")
    else:
        missing.append("量能資料補齊")

    try:
        rr_value = float(stock_result.get("rr"))
    except (TypeError, ValueError):
        rr_value = None
    if rr_value is not None and rr_value >= 1.5:
        met.append("風險報酬達標")
    elif rr_value is not None:
        missing.append(f"風險報酬 {_gate_value_text(rr_value)}→1.5")
    else:
        missing.append("風險報酬資料補齊")

    parts = []
    if met:
        parts.append("已滿足 " + "、".join(met))
    if missing:
        parts.append("還差 " + "、".join(missing))
    return "；".join(parts) if parts else "等待低位修復確認"


def _low_repair_unlock_text(data):
    return "近期支撐不破 + 站回5日均 + 量能轉強 + 風險報酬>=1.5"


def _repair_retest_gap_text(data):
    return f"等待回測{_recent_rebound_close_text(data)}不破"


def _repair_retest_unlock_text(data):
    return f"回測{_recent_rebound_close_text(data)}不破"


def _volume_wait_gap_text(data, target=0.8):
    ratio = _float_or_none((data or {}).get("volume_ratio"))
    if ratio is None:
        ratio = _float_or_none(((data or {}).get("result") or {}).get("volume_ratio"))
    if ratio is None:
        return "量能資料補齊後再評估"
    return f"目前量能 {_gate_value_text(ratio)}x，需至少 {_gate_value_text(target)}x"


def _overheat_chase_reason(data, fallback="短線過熱，先等冷卻"):
    stock_result = (data or {}).get("result") or {}
    change = _float_or_none((data or {}).get("change"))
    behavior = str(stock_result.get("price_behavior") or "")
    if behavior in {"LIMIT_LOCK", "LIMIT_REBOUND"} or (change is not None and change >= 9.0):
        return "漲停/過熱，不追價"
    return fallback


def _limit_chase_display_kind(data, blockers=None):
    stock_result = (data or {}).get("result") or {}
    blockers = set(blockers or stock_result.get("blockers") or [])
    if (
        stock_result.get("decision") == "FAIL"
        or stock_result.get("structure_phase") == "FAILED_BREAKOUT"
        or "突破失敗" in blockers
    ):
        return None
    behavior = str(stock_result.get("price_behavior") or "")
    change = _float_or_none((data or {}).get("change"))
    if behavior == "LIMIT_LOCK" or "漲停不追" in blockers or (change is not None and change >= 9.0):
        return "lock"
    if behavior == "LIMIT_REBOUND" or "漲停反彈待確認" in blockers:
        return "rebound"
    return None


def _strategy_source_title_label(source_status):
    return {
        "source-error": "策略樣本來源異常",
        "unresolved-conflict": "策略樣本來源衝突",
        "missing-source": "策略樣本證據不足",
        "insufficient-data": "策略樣本證據不足",
    }.get(source_status, "策略樣本證據不足")


def _decision_source_title_label(source_status):
    return (
        "資料來源缺失"
        if source_status in {"missing-source", "insufficient-data"}
        else "資料來源異常"
    )


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
    if rr is not None and rr >= 1.5 and stock_result.get("rr_context") == "actionable" and "RR" not in primary:
        basis.append("風險報酬達標")
    elif rr is not None and rr >= 1.5 and "RR" not in primary:
        potential = _potential_reward_text(_gate_value_text(rr), reason=primary_reason, funnel_state=(data or {}).get("funnel_state"), stock_result=stock_result)
        basis.append(potential.replace("潛在報酬：好", "潛在報酬好"))
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


def _strategy_granular_basis_line(funnel_state, primary_reason, basis):
    if not basis:
        return None
    if funnel_state == "可準備" or primary_reason == "開盤確認未完成":
        return f"依據：{basis}"
    if primary_reason in {"熱度 Lv.3", "過熱觀察"} or funnel_state == "等冷卻":
        return f"補充：{basis}，但熱度未降溫"
    if primary_reason == "急彈未回測" or funnel_state == "等回測":
        return f"補充：{basis}，但回測未確認"
    if primary_reason == "RR不足" or funnel_state == "等RR修復":
        return f"補充：{basis}，但RR未達標"
    if primary_reason == "進場品質不足" or funnel_state == "等型態":
        return f"補充：{basis}，但型態/品質未過"
    return f"補充：{basis}"


def _decision_first_reason_text(reason):
    mapping = {
        "RR不足": "風險報酬還不夠",
        "距觸發太遠": "尚未接近突破區",
        "未站回突破區": "尚未站回突破區",
        "熱度 Lv.3": "漲停/過熱，不追價",
        "過熱觀察": "短線過熱，先等冷卻",
        "急彈未回測": "急彈後還沒回測確認",
        "進場品質不足": "型態/品質還沒過",
        "反彈力道不足": "反彈還沒轉強",
        "漲跌停鎖定": "漲跌停鎖定，不追價",
        "開盤確認未完成": "盤後訊號需開盤確認",
        "量能不足": "量能還沒補上",
        "樣本不足": "策略樣本不足",
        "資料來源缺失": "資料來源缺失",
        "市場背景": "市場背景未轉強",
        "市場弱": "市場仍弱",
    }
    return mapping.get(str(reason or ""), str(reason or "條件未完成"))


def _compact_gap_text(text):
    text = str(text or "").strip()
    if not text:
        return text
    if text.startswith("RR ") and "｜需>=1.5｜差" in text:
        rr_value = text.split("｜", 1)[0].replace("RR ", "").strip()
        tail = text.split("｜差", 1)
        gap_value = tail[1].split("｜", 1)[0].strip() if len(tail) > 1 else None
        rest = tail[1].split("｜", 1)[1] if len(tail) > 1 and "｜" in tail[1] else ""
        base = f"風險報酬 {rr_value}→1.5"
        if gap_value:
            base += f"（差{gap_value}）"
        text = base + (f"｜{rest}" if rest else "")
    replacements = [
        ("需>=1.5", "目標1.5"),
        ("進場品質 ", "品質 "),
        ("｜需B以上", "→B以上"),
        (" 未達B", "→B以上"),
        ("→B以上", "→B 以上"),
        ("需B以上", "需 B 以上"),
        ("（setup未成立）", "僅參考"),
        ("突破區需<=5%", "買點區<=5%"),
        ("突破買點區需<=5%", "買點區<=5%"),
        ("若走趨勢延續/回測承接，需另見有效setup", "另等趨勢延續/回測承接買點型態"),
        ("另等趨勢延續/回測承接setup", "另等趨勢延續/回測承接買點型態"),
        ("setup", "買點型態"),
        ("急彈追價區，尚未回測", "急彈後先等回測"),
        ("需降至 Lv.1/觀察以下", "降到 Lv.1/觀察以下"),
        ("需解除鎖定後重新評估", "解除鎖定後再評估"),
        ("需放量轉強後重新評估", "放量轉強後再評估"),
        ("需量能回升後重新評估", "量能回升後再評估"),
        ("需更多有效策略樣本確認", "補足有效策略樣本"),
        ("需補齊有效行情 / 策略來源", "補齊行情/策略來源"),
    ]
    for old, new in replacements:
        text = text.replace(old, new)
    text = text.replace("（現價未站回）", "")
    text = text.replace("RR ", "風險報酬 ")
    parts = []
    for part in text.split("｜"):
        part = part.strip()
        if not part:
            continue
        if part.startswith("突破區 "):
            part = "站回" + part
        elif part.startswith("回測區 "):
            part = part + "不破"
        elif part.startswith("理論風險報酬 ") or part.startswith("理論RR "):
            value = part.replace("理論風險報酬 ", "").replace("理論RR ", "").replace("僅參考", "").strip()
            part = _potential_reward_text(value)
        elif part.startswith("V10 ") and ("偏弱" in part or "達標" in part):
            label = "量能偏弱" if "偏弱" in part else "量能達標"
            raw = part.replace("偏弱", "").replace("達標", "").replace("V10", "10日量").replace("V20", "20日量")
            part = f"{label}（{raw}）"
        elif part.startswith("風險報酬 ") and "目標1.5" in part:
            part = part.replace("｜", " ")
        parts.append(part)
    return "；".join(dict.fromkeys(parts))


def _quality_wait_gap_text(quality, reason=None, funnel_state=None):
    quality = str(quality or "").strip()
    if not quality:
        return None
    if quality in {"A+", "A", "B"}:
        return None
    if reason in {"急彈未回測", "反彈力道不足", "漲跌停鎖定"} or funnel_state in {"等回測", "隔日確認"}:
        return "買點品質：回測 / 轉強後重評"
    if funnel_state == "等冷卻":
        return "買點品質：降溫後重評"
    return f"買點品質未過（目前 {quality}，需B以上）"


def _compact_unlock_text(text):
    text = str(text or "").strip()
    if not text:
        return text
    replacements = [
        ("解除主 blocker 後重新評估", "主條件解除後重新評估"),
        ("風險報酬比修復到 >=1.5", "風險報酬 >= 1.5"),
        ("接近觸發區，或另出現趨勢延續/回測承接setup後再評估", "接近觸發區，或出現趨勢延續/回測承接買點型態"),
        ("回測不破且非追高時重新評估", "回測不破 + 非追高"),
        ("重新形成突破、回測或趨勢延續 setup", "重新形成突破/回測/趨勢延續買點型態"),
        ("setup", "買點型態"),
        ("品質B以上", "買點品質 B 以上"),
        ("品質 B 以上", "買點品質 B 以上"),
        ("風險報酬>=1.5", "風險報酬 >= 1.5"),
        ("明日開盤後仍守突破區 / 不追價", "開盤後守突破區 + 不追價"),
        ("降溫後重新評估", "降溫後重新評估"),
        ("量能回升後重新評估", "量能回升後重新評估"),
        ("補齊有效策略樣本後重新評估", "補齊有效策略樣本後重新評估"),
        ("補齊有效行情 / 策略來源後重新評估", "補齊行情/策略來源後重新評估"),
    ]
    for old, new in replacements:
        text = text.replace(old, new)
    text = text.replace("買點買點品質", "買點品質")
    text = text.replace(" + ", " + ")
    return text


def _readable_evidence_lines(reason, gap, unlock=None, basis=None, funnel_state=None):
    lines = [
        f"不能買：{_decision_first_reason_text(reason)}",
        f"還差：{_compact_gap_text(gap)}",
    ]
    if unlock:
        lines.append(f"可買條件：{_compact_unlock_text(unlock)}")
    if basis:
        basis_line = _strategy_granular_basis_line(funnel_state, reason, basis)
        if basis_line and basis_line.startswith("依據："):
            lines.append(basis_line)
    lines = [_readable_rr_terms(line) for line in lines]
    return "\n".join(lines)


def _readable_rr_terms(text):
    if text is None:
        return None
    text = str(text)
    replacements = [
        ("等RR修復", "等風險報酬"),
        ("等RR達標", "等風險報酬達標"),
        ("等待RR修復", "等待風險報酬修復"),
        ("RR修復", "風險報酬修復"),
        ("RR不足", "風險報酬不足"),
        ("RR不可用", "風險報酬不可用"),
        ("RR達標", "風險報酬達標"),
        ("理論RR", "潛在報酬"),
        ("理論風險報酬", "潛在報酬"),
        ("RR：", "風險報酬："),
        ("RR >=", "風險報酬 >="),
        ("RR>=", "風險報酬>="),
        ("RR ", "風險報酬 "),
        ("等RR", "等風險報酬"),
        ("風險報酬>=", "風險報酬 >="),
        ("風險報酬 >=1.5", "風險報酬 >= 1.5"),
        ("品質B以上", "品質 B 以上"),
    ]
    for old, new in replacements:
        text = text.replace(old, new)
    if "】" not in text:
        strategy_replacements = [
            ("買點 setup", "買點型態"),
            ("setup", "買點型態"),
            ("出現 買點型態", "出現買點型態"),
            ("重新形成 買點型態", "重新形成買點型態"),
            ("重新形成買點 買點型態", "重新形成買點型態"),
        ]
        for old, new in strategy_replacements:
            text = text.replace(old, new)
    return text


def _entry_contract(reason, gap, unlock=None, *, basis=None):
    lines = _readable_evidence_lines(reason, gap, unlock, basis=basis)
    contract = {"reason": None, "gap": None, "unlock": None, "extras": []}
    for line in lines.splitlines():
        if line.startswith("不能買："):
            contract["reason"] = _strip_line_prefix(line, ["不能買："])
        elif line.startswith("還差："):
            contract["gap"] = _strip_line_prefix(line, ["還差："])
        elif line.startswith("可買條件："):
            contract["unlock"] = _strip_line_prefix(line, ["可買條件："])
        else:
            contract["extras"].append(line)
    return contract


def _entry_contract_text(contract):
    if not contract:
        return None
    lines = []
    reason = contract.get("reason")
    gap = contract.get("gap")
    unlock = contract.get("unlock")
    if reason:
        lines.append(f"不能買：{reason}")
    if gap:
        lines.append(f"還差：{gap}")
    if unlock:
        lines.append(f"可買條件：{unlock}")
    lines.extend(contract.get("extras") or [])
    return "\n".join(lines) if lines else None


def _unheld_entry_contract(data, dist, blockers, valid_entry, funnel_state, source_status, strategy_source_blocked, title_label=None):
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

    def contract(reason, gap, unlock=None, basis=None):
        basis = basis if basis is not None else _supporting_basis_text(data, reason)
        return _entry_contract(reason, gap, unlock, basis=basis)

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
        gates.append(("量能不足", _volume_wait_gap_text(data)))
    elif "量能不足" in blocker_text:
        gates.append(("量能不足", _volume_wait_gap_text(data)))
    if "突破失敗" in blocker_text or phase == "FAILED_BREAKOUT":
        return contract("未站回突破區", "尚未站回突破區", "重新站回突破區後再評估", basis="")
    if post_market_prepare:
        return contract(
            "開盤確認未完成",
            "盤後待開盤確認",
            "明日開盤後仍守突破區 / 不追價",
        )
    if funnel_state == "等資料" and source_gates:
        primary_reason, primary_gap = source_gates[0]
        unlock = {
            "樣本不足": "補齊有效策略樣本後重新評估",
            "資料來源缺失": "補齊有效行情 / 策略來源後重新評估",
        }.get(primary_reason, "資料恢復後重新評估")
        return contract(primary_reason, primary_gap, unlock, basis="")

    behavior = stock_result.get("price_behavior")
    multi_day_rebound_wait = bool(data.get("multi_day_rebound_wait") or stock_result.get("multi_day_rebound_wait"))
    if multi_day_rebound_wait:
        retest_text = _repair_retest_gap_text(data)
        unlock_text = _repair_retest_unlock_text(data)
        return contract(
            "連漲修復待回測",
            retest_text,
            f"{unlock_text} + 非追高 + 量能有效",
            basis="",
        )
    evidence_reason = str((data or {}).get("evidence_adjustment_reason") or "")
    if funnel_state == "可準備" and "低位修復" in evidence_reason:
        return {
            "reason": "低位修復條件成立；盤後不追價",
            "gap": _low_repair_anchor_text(data),
            "unlock": "明日開盤不追高 + 守支撐/5日均 + 量能不失控",
            "extras": [f"條件：{_low_repair_progress_text(data)}"],
        }
    if funnel_state == "等低位修復":
        return {
            "reason": "突破買點太遠，改看低位修復",
            "gap": _low_repair_anchor_text(data),
            "unlock": _low_repair_unlock_text(data),
            "extras": [f"條件：{_low_repair_progress_text(data)}"],
        }
    limit_display_kind = _limit_chase_display_kind(data, blockers)
    if limit_display_kind:
        if limit_display_kind == "rebound":
            return contract(
                "漲停反彈，隔日確認",
                "解除鎖定後，看回測是否守住",
                "開板/降溫 + 回測不破 + 非追高",
                basis="",
            )
        return contract(
            "漲停/過熱，不追價",
            "解除鎖定後，看開板回測是否守住",
            "開板/降溫 + 回測不破 + 非追高",
            basis="",
        )
    if "急彈待回測" in blocker_text:
        retest_text = _retest_zone_text(data)
        unlock_text = _retest_unlock_text(data)
        return contract(
            "急彈未回測",
            retest_text,
            f"{unlock_text} + 非漲停追價 + 量能有效",
            basis="",
        )
    if behavior == "WEAK_REBOUND" or phase == "WEAK_REBOUND" or "弱反彈" in blocker_text:
        gates.append(("反彈力道不足", "需放量轉強後重新評估"))

    heat = stock_result.get("heat_state")
    if heat == "EXTREME":
        return contract(
            _overheat_chase_reason(data),
            "熱度 Lv.3｜需降至 Lv.1/觀察以下",
            "降到 Lv.1/觀察以下 + 回測不破 + 非漲停追價",
        )
    if heat == "HOT" or "過熱" in blocker_text:
        return contract(
            _overheat_chase_reason(data),
            "熱度 Lv.2｜需降至 Lv.1/觀察以下",
            "降到 Lv.1/觀察以下 + 回測不破",
        )

    rr_text = _gate_value_text(stock_result.get("rr"))
    if not is_actionable and rr_text and ("RR不足" in blocker_text or float(rr_text) < 1.5):
        rr_gap = f"RR {rr_text}｜需>=1.5｜差{_gate_gap_text(rr_text, 1.5)}"
        gates.append(("RR不足", rr_gap))

    distance_text = _gate_value_text(dist)
    policy = _display_entry_distance_policy(stock_result)
    max_pct = policy.get("max_pct")
    if funnel_state == "等接近":
        zone_text = _breakout_trigger_zone_text(data)
        distance_gap_text = (
            f"距突破 {distance_text}%，尚未接近{zone_text}"
            if distance_text
            else f"尚未接近{zone_text}"
        )
        gates.append(("距觸發太遠", distance_gap_text))
    if funnel_state != "等接近" and distance_text and policy.get("hard_gate") and max_pct is not None and float(distance_text) > max_pct:
        distance_gap_text = (
            f"尚未接近{_breakout_trigger_zone_text(data)}"
            if funnel_state == "等接近"
            else "尚未形成有效買點型態"
        )
        gates.append((
            "距觸發太遠",
            distance_gap_text,
        ))

    quality = stock_result.get("entry_quality")
    if funnel_state != "等接近" and not is_actionable and quality and quality not in {"A+", "A", "B"}:
        setup_text = _quality_wait_gap_text(quality, reason="進場品質不足", funnel_state=funnel_state)
        gates.append(("進場品質不足", setup_text))

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
        gates.append(("RR不足", "風險報酬不可用｜需>=1.5"))
    elif not gates and funnel_state == "等量能":
        gates.append(("量能不足", _volume_wait_gap_text(data)))
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
        "距觸發太遠": f"接近{_breakout_trigger_zone_text(data)}，或出現趨勢延續/回測承接setup",
        "市場背景": "市場轉強後再評估",
        "漲跌停鎖定": "解除鎖定後重新評估",
        "反彈力道不足": "放量轉強 + 品質B以上 + 風險報酬>=1.5",
        "急彈未回測": "回測不破且非追高時重新評估",
        "市場弱": "市場轉強後重新評估",
        "量能不足": "量能 >= 0.8x 且非追高時重新評估",
        "進場品質不足": "重新形成 setup + 品質B以上 + 量能有效 + 風險報酬>=1.5",
        "過熱觀察": "降溫到 Lv.1/觀察以下 + 回測不破",
        "熱度 Lv.3": "降溫到 Lv.1/觀察以下 + 回測不破 + 非漲停追價",
        "樣本不足": "補齊有效策略樣本後重新評估",
        "資料來源缺失": "補齊有效行情 / 策略來源後重新評估",
    }.get(primary_reason, "解除主 blocker 後重新評估")
    basis = "" if funnel_state == "等接近" else None
    return contract(primary_reason, primary_gap, unlock, basis=basis)


def _unheld_buy_gap_line(data, dist, blockers, valid_entry, funnel_state, source_status, strategy_source_blocked, title_label=None):
    return _entry_contract_text(
        _unheld_entry_contract(
            data,
            dist,
            blockers,
            valid_entry,
            funnel_state,
            source_status,
            strategy_source_blocked,
            title_label=title_label,
        )
    )


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
            "來源可追溯，現狀維持 等RR修復": "維持等風險報酬修復",
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
    if not _is_today_action_phase(_report_phase(report_context)):
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


def _stock_result_with_data_overrides(data):
    data = data or {}
    stock_result = dict(data.get("result") or {})
    for key in [
        "volume_ratio",
        "volume_ratio_10",
        "volume_ratio_20",
        "breakout_distance",
        "distance_to_breakout",
    ]:
        if stock_result.get(key) is None and data.get(key) is not None:
            stock_result[key] = data.get(key)
            if key.startswith("volume_ratio"):
                stock_result["_volume_ratio_from_data"] = True
    return stock_result


def _recent_price_transition(data):
    points = _daily_price_points(data)
    if len(points) < 2:
        return {}
    try:
        latest_close = float(points[-1]["close"])
        previous_close = float(points[-2]["close"])
        current = float((data or {}).get("price"))
    except (KeyError, TypeError, ValueError):
        return {}
    if latest_close == 0 or previous_close == 0:
        return {}
    previous_change_pct = (latest_close / previous_close - 1) * 100
    current_change_pct = (current / latest_close - 1) * 100
    eps = 0.15
    if previous_change_pct > eps and current_change_pct < -eps:
        pattern = "UP_THEN_DOWN"
    elif previous_change_pct < -eps and current_change_pct > eps:
        pattern = "DOWN_THEN_UP"
    elif previous_change_pct > eps and current_change_pct > eps:
        pattern = "CONTINUOUS_UP"
    elif previous_change_pct < -eps and current_change_pct < -eps:
        pattern = "CONTINUOUS_DOWN"
    else:
        pattern = "FLAT"
    return {
        "pattern": pattern,
        "previous_change_pct": previous_change_pct,
        "current_change_pct": current_change_pct,
    }


def _adjust_market_text_by_recent_price_transition(market_text, data):
    transition = _recent_price_transition(data)
    pattern = transition.get("pattern")
    if pattern == "UP_THEN_DOWN":
        if "趨勢延續" in market_text:
            market_text = market_text.replace("趨勢延續", "反彈回測", 1)
        if "極強" in market_text:
            market_text = market_text.replace("極強", "待確認", 1)
    elif pattern == "CONTINUOUS_DOWN":
        if "極強" in market_text:
            market_text = market_text.replace("極強", "待確認", 1)
        if "洗盤回測" in market_text:
            market_text = market_text.replace("洗盤回測", "回踩轉弱", 1)
    return market_text


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
    stock_result = _stock_result_with_data_overrides(data)
    if _score_source_available(report_context, name, deps):
        market_text = deps["plain_label"](deps["compact_market_line"](stock_result, dist))
        market_text = _strip_breakout_position_segment(market_text)
        market_text = _adjust_market_text_by_recent_price_transition(market_text, data)
        if ("弱勢" in market_text or "遠離突破" in market_text) and "極強" in market_text:
            market_text = market_text.replace("極強", "待確認")
        if _is_low_volume_consolidation(report_context, data, stock_result):
            market_text = market_text.replace("極強", "縮量觀察")
            market_text = market_text.replace("｜待確認", "｜縮量觀察")
            if "縮量" not in market_text:
                market_text = f"{market_text}｜縮量觀察"
        return f"盤面：{market_text}"
    return "盤面：強弱證據不足｜待確認"


def _strip_line_prefix(text, prefixes):
    text = str(text or "").strip()
    for prefix in prefixes:
        if text.startswith(prefix):
            return text[len(prefix):].strip()
    return text


def _entry_check_lines(buy_line, buy_gap_line, *, funnel_state=None, data=None):
    buy_text = str(buy_line or "").strip()
    if isinstance(buy_gap_line, dict):
        reason = buy_gap_line.get("reason")
        gap = buy_gap_line.get("gap")
        unlock = buy_gap_line.get("unlock")
        extras = list(buy_gap_line.get("extras") or [])
        entry_text = _strip_line_prefix(buy_text, ["買點："])
        entry_parts = []
        if entry_text:
            entry_parts.append(entry_text)
        if reason and reason not in entry_text:
            entry_parts.append(f"原因：{reason}")
        lines = []
        if str(gap or "").startswith("熱度"):
            lines = []
            if reason:
                lines.append(f"狀態：{reason}")
            wait = str(gap or "").strip()
            if "；" in wait:
                wait = wait.split("；", 1)[0]
            if unlock:
                unlock = unlock.replace("降到 Lv.1/觀察以下", "降溫到 Lv.1")
                wait = f"{wait}；有效買點：{unlock}" if wait else f"有效買點：{unlock}"
            if wait:
                lines.append(f"等待：{wait}")
            return lines

        if reason and ("漲停" in str(reason) or "鎖定" in str(reason)):
            lines = [f"狀態：{reason}"]
            if gap:
                lines.append(f"等待：{gap}")
            if unlock:
                lines.append(f"有效買點：{unlock}")
            return lines

        if funnel_state == "等接近":
            zone = None
            gap_text = str(gap or "")
            if "尚未接近" in gap_text:
                zone = gap_text.split("尚未接近", 1)[1].strip()
            entry_line = "進場：不買"
            if zone:
                entry_line += f"｜尚未接近{zone}"
            wait_text = gap_text
            if zone:
                wait_text = wait_text.replace(f"，尚未接近{zone}", "").replace(f"；尚未接近{zone}", "")
            wait_text = wait_text.strip("；， ")
            if wait_text:
                wait_text += "；"
            wait_text += "有效買點只看：接近突破區 / 回測承接型態"
            return [entry_line, f"等待：{wait_text}"]

        if funnel_state == "等冷卻":
            lines = []
            if reason:
                lines.append(f"狀態：{reason}")
            wait = str(gap or "").strip()
            if "；" in wait:
                wait = wait.split("；", 1)[0]
            if unlock:
                unlock = unlock.replace("降到 Lv.1/觀察以下", "降溫到 Lv.1")
                wait = f"{wait}；有效買點：{unlock}" if wait else f"有效買點：{unlock}"
            if wait:
                lines.append(f"等待：{wait}")
            return lines

        if funnel_state == "等回測":
            lines = []
            if reason:
                lines.append(f"狀態：{reason}")
            retest = str(gap or "").strip()
            waiting_retest = retest.startswith("等待回測")
            if retest.startswith("等待回測"):
                retest = retest.replace("等待回測", "", 1)
            if retest:
                if waiting_retest and retest.startswith("最近反彈收盤"):
                    lines.append(_rebound_retest_basis_line(data, retest))
                else:
                    lines.append(f"回測：{retest}")
            if unlock:
                if waiting_retest and retest and unlock.startswith(f"回測{retest}"):
                    unlock = unlock.replace(f"回測{retest}", "回踩不破", 1)
                elif retest and unlock.startswith(f"回測{retest}"):
                    unlock = unlock.replace(f"回測{retest}", "不破", 1)
                elif retest and unlock.startswith(f"{retest}"):
                    unlock = unlock.replace(f"{retest}", "不破", 1)
                lines.append(f"有效買點：{unlock}")
            return lines

        if funnel_state == "可準備" and reason and "低位修復" in str(reason):
            lines = [f"狀態：{reason}"]
            if gap:
                lines.append(f"觀察：{gap}")
            lines.extend(extras)
            if unlock:
                lines.append(f"可買：{unlock}")
            return lines

        if funnel_state == "等低位修復":
            lines = []
            if reason:
                lines.append(f"路線：{reason}")
            if gap:
                lines.append(f"觀察：{gap}")
            lines.extend(extras)
            if unlock:
                lines.append(f"有效買點：{unlock}")
            return lines

        if funnel_state == "等型態":
            lines = []
            if reason:
                lines.append(f"狀態：{reason}")
            wait = str(gap or "").strip()
            if wait:
                lines.append(f"等待：{wait}")
            if unlock:
                lines.append(f"有效買點：{unlock}")
            return lines

        if entry_parts:
            lines.append("進場：" + "｜".join(dict.fromkeys(entry_parts)))
        if gap:
            lines.append(f"缺口：{gap}")
        if unlock:
            lines.append(f"可買：{unlock}")
        lines.extend(extras)
        return lines

    gap_lines = [
        str(line).strip()
        for line in str(buy_gap_line or "").splitlines()
        if str(line).strip()
    ]
    if not gap_lines:
        return [buy_text] if buy_text else []

    reason = None
    gap = None
    unlock = None
    extras = []
    for line in gap_lines:
        if line.startswith("不能買："):
            reason = _strip_line_prefix(line, ["不能買："])
        elif line.startswith("還差："):
            gap = _strip_line_prefix(line, ["還差："])
        elif line.startswith("可買條件："):
            unlock = _strip_line_prefix(line, ["可買條件："])
        else:
            extras.append(line)

    entry_text = _strip_line_prefix(buy_text, ["買點："])
    entry_parts = []
    if entry_text:
        entry_parts.append(entry_text)
    if reason and reason not in entry_text:
        entry_parts.append(f"原因：{reason}")

    lines = []
    if str(gap or "").startswith("熱度"):
        lines = []
        if reason:
            lines.append(f"狀態：{reason}")
        wait = str(gap or "").strip()
        if "；" in wait:
            wait = wait.split("；", 1)[0]
        if unlock:
            unlock = unlock.replace("降到 Lv.1/觀察以下", "降溫到 Lv.1")
            wait = f"{wait}；有效買點：{unlock}" if wait else f"有效買點：{unlock}"
        if wait:
            lines.append(f"等待：{wait}")
        return lines

    if funnel_state == "等接近":
        zone = None
        gap_text = str(gap or "")
        if "尚未接近" in gap_text:
            zone = gap_text.split("尚未接近", 1)[1].strip()
        entry_line = "進場：不買"
        if zone:
            entry_line += f"｜尚未接近{zone}"
        wait_text = gap_text
        if zone:
            wait_text = wait_text.replace(f"，尚未接近{zone}", "").replace(f"；尚未接近{zone}", "")
        wait_text = wait_text.strip("；， ")
        if wait_text:
            wait_text += "；"
        wait_text += "有效買點只看：接近突破區 / 回測承接型態"
        return [entry_line, f"等待：{wait_text}"]

    if funnel_state == "等冷卻":
        lines = []
        if reason:
            lines.append(f"狀態：{reason}")
        wait = str(gap or "").strip()
        if "；" in wait:
            wait = wait.split("；", 1)[0]
        if unlock:
            unlock = unlock.replace("降到 Lv.1/觀察以下", "降溫到 Lv.1")
            wait = f"{wait}；有效買點：{unlock}" if wait else f"有效買點：{unlock}"
        if wait:
            lines.append(f"等待：{wait}")
        return lines

    if funnel_state == "等回測":
        lines = []
        if reason:
            lines.append(f"狀態：{reason}")
        retest = str(gap or "").strip()
        waiting_retest = retest.startswith("等待回測")
        if retest.startswith("等待回測"):
            retest = retest.replace("等待回測", "", 1)
        if retest:
            if waiting_retest and retest.startswith("最近反彈收盤"):
                lines.append(_rebound_retest_basis_line(data, retest))
            else:
                lines.append(f"回測：{retest}")
        if unlock:
            if waiting_retest and retest and unlock.startswith(f"回測{retest}"):
                unlock = unlock.replace(f"回測{retest}", "回踩不破", 1)
            elif retest and unlock.startswith(f"回測{retest}"):
                unlock = unlock.replace(f"回測{retest}", "不破", 1)
            elif retest and unlock.startswith(f"{retest}"):
                unlock = unlock.replace(f"{retest}", "不破", 1)
            lines.append(f"有效買點：{unlock}")
        return lines

    if funnel_state == "等低位修復":
        lines = []
        if reason:
            lines.append(f"路線：{reason}")
        if gap:
            lines.append(f"觀察：{gap}")
        lines.extend(extras)
        if unlock:
            lines.append(f"有效買點：{unlock}")
        return lines

    if funnel_state == "等型態":
        lines = []
        if reason:
            lines.append(f"狀態：{reason}")
        wait = str(gap or "").strip()
        if wait:
            lines.append(f"等待：{wait}")
        if unlock:
            lines.append(f"有效買點：{unlock}")
        return lines

    if entry_parts:
        lines.append("進場：" + "｜".join(dict.fromkeys(entry_parts)))
    if gap:
        lines.append(f"缺口：{gap}")
    if unlock:
        lines.append(f"可買：{unlock}")
    lines.extend(extras)
    return lines


def _compact_unheld_trade_state_line(line, *, valid_entry=False, post_market_prepare=False, data_source_blocked=False, funnel_state=None):
    if not line:
        return None
    if valid_entry or post_market_prepare:
        return line
    if data_source_blocked:
        return None
    if funnel_state in {"可準備", "等冷卻", "等回測", "等型態", "等接近", "等低位修復", "等RR修復", "淘汰"}:
        return None
    return line


def _compact_unheld_history_line(line, *, funnel_state=None):
    if not line:
        return None
    text = str(line)
    if "修復中" in text or "權重 +" in text:
        return line
    if funnel_state in {"淘汰", "等資料"} and (
        "前次 eliminated" in text
        or "前次 failed" in text
        or "已買" in text
        or "已賣" in text
        or "停損" in text
    ):
        return line
    return None


def _strip_breakout_position_segment(market_text):
    if not market_text:
        return market_text
    breakout_labels = (
        "已突破，位於突破區上方",
        "臨界突破",
        "接近突破",
        "遠離突破",
    )
    parts = [
        part for part in str(market_text).split("｜")
        if not any(label in part for label in breakout_labels)
    ]
    return "｜".join(parts) if parts else market_text


def _breakout_distance_label(dist):
    try:
        value = float(dist)
    except (TypeError, ValueError):
        return None
    if value < 0:
        return "已突破"
    if value < 1:
        return "臨界突破"
    if value <= 5:
        return "接近突破"
    return "遠離突破"


def _breakout_distance_line(dist, data=None, funnel_state=None, title_label=None):
    label = _breakout_distance_label(dist)
    if not label:
        return None
    stock_result = (data or {}).get("result") or {}
    blocker_text = " ".join(str(item) for item in (stock_result.get("blockers") or []))
    context_text = " ".join([
        str(funnel_state or ""),
        str(title_label or ""),
        str(stock_result.get("heat_state") or ""),
        str(stock_result.get("price_behavior") or ""),
        blocker_text,
    ])
    if label == "已突破" and any(token in context_text for token in ["HOT", "EXTREME", "LIMIT", "過熱", "漲停", "不可追高", "等冷卻"]):
        change = _float_or_none((data or {}).get("change"))
        behavior = str(stock_result.get("price_behavior") or "")
        limit_like = behavior in {"LIMIT_LOCK", "LIMIT_REBOUND"} or (change is not None and change >= 9.0)
        label = "已突破，但漲停/過熱不追" if limit_like else "已突破，但短線過熱不追"
    return f"距突破：{_gate_value_text(dist)}%｜{label}"


def _unheld_rr_text(stock_result, funnel_state, valid_entry, deps, state=None, title_label=None, blockers=None):
    blockers = set(blockers or stock_result.get("blockers") or [])
    title_text = str(title_label or "")
    try:
        rebound_change = float(stock_result.get("live_change", stock_result.get("change", 0)) or 0)
    except (TypeError, ValueError):
        rebound_change = 0
    if any(token in title_text for token in ["策略樣本", "資料來源"]):
        return "-（不可行動）"
    strong_rebound_wait = (
        "急彈待回測" in blockers
        or "急彈待回測" in title_text
        or (
            (funnel_state == "等回測" or state == "等回測")
            and stock_result.get("price_behavior") == "WEAK_REBOUND"
            and rebound_change >= 7.0
        )
    )
    if strong_rebound_wait:
        raw_rr_text = _gate_value_text(stock_result.get("rr"))
        return raw_rr_text or deps["rr_display_text"](stock_result, holding=False)
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


def _holding_warning_breach_text(data, decision):
    if not decision:
        return None
    price = _float_or_none((data or {}).get("price"))
    warning = _float_or_none(decision.get("warning_price"))
    hard_stop = _float_or_none(decision.get("hard_stop_price"))
    if price is None or warning is None:
        return None
    if hard_stop is not None and price <= hard_stop:
        return "已跌破停損，優先停損"
    if price < warning:
        return "已跌破警戒，未到停損"
    return None


def _holding_action_contract(summary_action, decision_line, reason_line, condition_line, next_step, *, data=None, decision=None):
    action = str(summary_action or "")
    decision_text = str(decision_line or "").strip()
    risk_text = str(reason_line or "").strip()
    if risk_text.startswith("原因："):
        risk_text = risk_text.replace("原因：", "", 1).strip()
    condition_text = str(condition_line or "").strip()
    next_text = str(next_step or "").strip()
    warning_breach = _holding_warning_breach_text(data, decision)
    if warning_breach and "未跌破風控" in risk_text:
        risk_text = warning_breach
    combined_text = " ".join([action, decision_text, risk_text, condition_text, next_text])

    if "停利記憶不足" in combined_text or "execution memory 不足" in combined_text:
        return {
            "action_label": "決策",
            "unlock_label": "可恢復",
            "entry": decision_text or "停利記憶不足，暫不輸出賣出股數",
            "reason": "execution memory 不足，fail closed 不輸出停利股數",
            "gap": "production execution memory 缺失或矛盾，fail closed",
            "unlock": "補齊 production execution memory 後再評估停利",
            "next": next_text or "先不輸出賣出股數，避免重複或錯誤停利",
        }

    if action == "停損":
        return {
            "action_label": "決策",
            "unlock_label": "再進場",
            "entry": decision_text or "停損 100%，硬停損觸發",
            "reason": risk_text or "跌破停損線，避免虧損擴大",
            "gap": "已跌破停損線",
            "unlock": "清出後重新等待買點，不急回補",
            "next": next_text or "清出後不急回補，等重新出現買點",
        }
    if action == "減碼":
        return {
            "action_label": "決策",
            "unlock_label": "可恢復",
            "entry": decision_text or "減碼，先降風險",
            "reason": risk_text or "結構轉弱或跌破快速風控",
            "gap": condition_text or "未重新站回關鍵區",
            "unlock": "重新站回關鍵區且量價修復後再評估",
            "next": next_text or "若無法重新站回突破區，繼續降低優先級",
        }
    if action == "停利":
        return {
            "action_label": "決策",
            "unlock_label": "可續抱",
            "entry": decision_text or "分批落袋",
            "reason": risk_text or "達到停利或過熱延伸",
            "gap": condition_text or "保留核心倉觀察",
            "unlock": "冷卻後再評估是否續攻",
            "next": next_text or "保留核心倉，等待冷卻後再評估",
        }
    if action == "洗盤續抱":
        return {
            "action_label": "決策",
            "unlock_label": "可續抱",
            "entry": decision_text or "續抱，不加碼",
            "reason": risk_text or "洗盤回測未跌破風控",
            "gap": condition_text or "守警戒價，等量價修復",
            "unlock": "守住警戒價 + 量價修復",
            "next": next_text or "守警戒價，等量價修復",
        }
    if action == "新倉風控觀察":
        return {
            "action_label": "決策",
            "unlock_label": "可續抱",
            "entry": decision_text or "續抱觀察，暫不加碼",
            "reason": risk_text or "今日剛進場，先看風控",
            "gap": condition_text or "守警戒價，跌破停損或轉弱優先風控",
            "unlock": "守住警戒且結構修復後再評估",
            "next": next_text or "明日觀察是否守住警戒，未修復再降級",
        }
    return {
        "action_label": "決策",
        "unlock_label": "可續抱",
        "entry": decision_text or "續抱，不加碼",
        "reason": risk_text or warning_breach or "未跌破風控，但尚未重新轉強",
        "gap": "跌破警戒後先看能否收復，跌破停損則優先風控" if warning_breach else (condition_text or "守警戒價，等量價修復"),
        "unlock": "守住警戒價 + 量價修復",
        "next": "收復警戒才恢復觀察；跌破停損優先風控" if warning_breach else (next_text or "觀察是否守住警戒，未修復再降級"),
    }


def _rr_data_prefix(stock_result, rr_text):
    if not rr_text or str(rr_text).startswith("-"):
        return "風險報酬"
    try:
        rr_value = float(rr_text)
    except (TypeError, ValueError):
        rr_value = None
    if rr_value is not None and rr_value < 1.5:
        return "風險報酬"
    if (stock_result or {}).get("rr_context") in {"blocked", "setup_pending", "theoretical"}:
        return "潛在報酬"
    return "風險報酬"


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
        else f"數據：風險報酬 {rr_text}｜{score_text}｜V {data.get('volume_ratio', '-')}x"
    )

    is_afterhours = _report_phase(report_context) in {"盤後", "收盤"}
    hide_low_signal_detail = (
        summary_action in {"停損", "減碼", "停利"}
        or (decision and decision.get("level") in {"HARD_STOP", "STOP", "REDUCE_50", "TAKE_PROFIT"})
    )
    lines = [
        f"【{deps['stock_title'](name, data)}】📌 {summary_action}｜{deps['signed_pct'](deps['stock_pnl'](data))}",
        execution_line,
        f"風控：{deps['holding_risk_text'](decision)}",
        _score_gated_market_line(report_context, name, data, dist, deps),
        _breakout_distance_line(dist, data=data),
        deps["today_buy_holding_context_line"](data) if _report_phase(report_context) == "盤後" else None,
        deps["_source_status_line"](report_context, name, holding=True) if report_context else None,
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
    contract = _holding_action_contract(
        summary_action,
        decision_line,
        reason_line,
        condition_line,
        next_step,
        data=data,
        decision=decision,
    )
    insert_at = 6
    gap_text = contract.get("gap")
    next_text = contract.get("next")
    if summary_action in {"停損", "減碼", "停利"}:
        handling_text = next_text or gap_text
    else:
        handling_text = gap_text or next_text
    contract_lines = [
        f"{contract['action_label']}：{contract['entry']}｜原因：{contract['reason']}",
        f"明日處理：{handling_text}",
    ]
    contract_lines = [_afterhours_card_text(line, report_context) for line in contract_lines]
    for offset, line in enumerate(contract_lines):
        lines.insert(insert_at + offset, line)
    lines.append(deps["price_change_line"](data.get("price"), data.get("change")))

    lines = [_readable_rr_terms(line) for line in lines]
    return "\n".join(lines)


def formatTelegramUnheldCard(name, data, *, deps, report_phase=None, market_mode=None, report_context=None):
    stock_result = _stock_result_with_data_overrides(data)
    data = dict(data)
    data["result"] = stock_result
    effective_report_phase = report_phase or _report_phase(report_context)
    dist = deps["card_breakout_distance"](data)
    blockers = deps["entry_blockers"](stock_result)
    limit_display_kind = _limit_chase_display_kind(data, blockers)
    stock_source_status = deps["_stock_decision_source_status"](report_context, name)
    strategy_source_status = deps["_strategy_sample_decision_source_status"](report_context)
    source_status = deps["_unheld_decision_source_status"](report_context, name)
    if not deps["_has_source_decision_context"](report_context):
        stock_source_status = "available"
        strategy_source_status = "available"
        source_status = "available"
    stock_source_eligible = stock_source_status == "available"
    strategy_source_eligible = strategy_source_status == "available"
    strategy_source_blocked = False
    source_eligible = stock_source_eligible
    valid_entry = deps["is_valid_entry"](stock_result) and source_eligible
    title_label = "買點成立" if valid_entry else (blockers[0] if blockers else deps["final_label"](stock_result))
    state = deps["tomorrow_watch_state"](name, data)
    funnel_state = deps["unheld_funnel_state"](name, data, market_mode=market_mode, report_context=report_context)
    low_repair_actionable = funnel_state == "可買" and bool(data.get("low_repair_intraday_buy_ready"))
    data_source_display_blocked = strategy_source_blocked and (state == "等資料" or funnel_state == "等資料")
    prepare_label, prepare_action = deps["strong_prepare_bucket"](data)
    post_market_prepare = (
        source_eligible
        and deps["post_market_unheld_buy_requires_open_confirmation"](data, report_context=report_context)
    )
    data_with_context = dict(data)
    data_with_context["report_context"] = report_context
    if low_repair_actionable:
        valid_entry = True
        title_label = "低位修復小倉"
    if valid_entry and funnel_state not in ["可買", "趨勢延續"]:
        valid_entry = False
        title_label = (
            "前態待確認"
            if funnel_state == "淘汰" and data.get("evidence_adjustment_reason")
            else deps["rejected_primary_reason"](stock_result)
            if funnel_state == "淘汰"
            else (blockers[0] if blockers else deps["final_label"](stock_result))
        )
    if not valid_entry and funnel_state in ["等冷卻", "等市場", "等接近", "等低位修復", "等型態", "等回測", "等RR修復", "等量能", "等資料", "隔日確認", "淘汰"]:
        state = funnel_state
    try:
        distance_value = float(str(dist).replace("%", "").strip()) if dist is not None else None
    except (TypeError, ValueError):
        distance_value = None
    if (
        not valid_entry
        and state == "等型態"
        and distance_value is not None
        and distance_value > 12
    ):
        if _daily_price_points(data):
            state = "等低位修復"
            funnel_state = "等低位修復"
        else:
            state = "等接近"
            funnel_state = "等接近"
    if not valid_entry and funnel_state == "等接近" and distance_value is not None and distance_value > 5:
        title_label = "遠離觸發"
    if data_source_display_blocked:
        title_label = _strategy_source_title_label(strategy_source_status)
    elif funnel_state == "等資料" and strategy_source_blocked:
        title_label = _strategy_source_title_label(strategy_source_status)
    elif funnel_state == "等資料":
        title_label = _decision_source_title_label(source_status)
    elif funnel_state == "等回測" and (data.get("multi_day_rebound_wait") or stock_result.get("multi_day_rebound_wait")):
        title_label = "反彈修復待回測"
    elif funnel_state == "等低位修復":
        title_label = "低位修復觀察"
    elif deps["is_valid_entry"](stock_result) and strategy_source_blocked:
        title_label = _strategy_source_title_label(strategy_source_status)
    elif deps["is_valid_entry"](stock_result) and not source_eligible:
        title_label = _decision_source_title_label(source_status)
    elif (state == "弱勢淘汰" or funnel_state == "淘汰") and not data.get("evidence_adjustment_reason"):
        title_label = deps["rejected_primary_reason"](stock_result)
    elif post_market_prepare:
        title_label = "開盤後確認"
    elif funnel_state == "可準備" and "低位修復" in str(data.get("evidence_adjustment_reason") or ""):
        title_label = "低位修復成立"
    elif funnel_state == "可準備" and prepare_label:
        title_label = prepare_label
    if title_label == "RR不足":
        title_label = "風險報酬不足"

    if valid_entry:
        title_icon = "🟢"
        if funnel_state == "趨勢延續":
            title_action = "趨勢延續買入"
            title_label = "小倉"
        elif low_repair_actionable:
            title_action = "可買｜小倉"
            title_label = "低位修復成立"
        elif not _is_today_action_phase(report_phase):
            title_action = f"明日追蹤｜{deps['unheld_entry_size_detail_text'](stock_result)}"
        else:
            title_action = f"可買｜{deps['unheld_entry_size_detail_text'](stock_result)}"
    elif limit_display_kind == "lock":
        title_icon = "⏳"
        title_action = "等回測"
        title_label = "漲停不追"
    elif limit_display_kind == "rebound":
        title_icon = "👀"
        title_action = "隔日確認"
        title_label = "漲停反彈待確認"
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
    elif state in ["等冷卻", "等市場", "等接近", "等低位修復", "等型態", "等回測", "等資料"]:
        title_icon = "⏳"
        title_action = state
    elif state in ["等RR修復", "等量能", "隔日確認"]:
        title_icon = "👀"
        title_action = "等風險報酬" if state == "等RR修復" else state
    elif funnel_state == "淘汰" and data.get("evidence_adjustment_reason"):
        title_icon = "⛔"
        title_action = "不買"
    elif state in ["弱勢淘汰", "淘汰"]:
        title_icon = "⛔"
        title_action = "淘汰"
    else:
        title_icon = "⛔"
        title_action = "不買"

    rr_text = _unheld_rr_text(
        stock_result,
        funnel_state,
        valid_entry,
        deps,
        state=state,
        title_label=title_label,
        blockers=blockers,
    )
    wait_text = deps["unheld_entry_wait_text"](stock_result, state, funnel_state)
    detail_size_text = deps["unheld_entry_size_detail_text"](stock_result)
    raw_size_text = deps["entry_size_text"](stock_result)
    score_text = _confidence_data_text(report_context, name, data, deps)
    rr_prefix = _rr_data_prefix(stock_result, rr_text)
    if rr_prefix == "潛在報酬":
        rr_data_text = _potential_reward_text(
            rr_text,
            reason=title_label,
            funnel_state=funnel_state,
            stock_result=stock_result,
        )
    else:
        rr_data_text = f"風險報酬：{rr_text}" if rr_text == "-（不可行動）" else f"{rr_prefix} {rr_text}"
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
        data_line = "數據：風險報酬不可用｜S 不可用｜V 不可用"
        price_line = f"價格：不可用（{source_reason}）"
    elif valid_entry and funnel_state == "趨勢延續":
        buy_line = "買點：趨勢延續買入｜小倉 <=15%｜回測 55% 勝 / +2.26%"
        data_line = f"數據：{rr_data_text}｜{score_text}｜V {data.get('volume_ratio', '-')}x"
        price_line = deps["price_change_line"](data.get("price"), data.get("change"))
    elif low_repair_actionable:
        buy_line = "買點：可買｜低位修復小倉｜守支撐/5日均，不追價"
        low_repair_status = data.get("low_repair_status") or {}
        low_repair_rr = _gate_value_text(low_repair_status.get("rr"))
        low_repair_volume = _gate_value_text(low_repair_status.get("volume_ratio") or data.get("volume_ratio"))
        data_line = f"數據：風險報酬 {low_repair_rr}｜低位修復條件成立｜V {low_repair_volume}x"
        price_line = deps["price_change_line"](data.get("price"), data.get("change"))
    elif valid_entry and not _is_today_action_phase(report_phase):
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
    elif funnel_state == "等資料":
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
    elif funnel_state == "等低位修復":
        buy_line = "買點：不買，等低位修復"
        data_line = f"數據：{rr_data_text}｜{display_score_text}｜V {data.get('volume_ratio', '-')}x"
        price_line = deps["price_change_line"](data.get("price"), data.get("change"))
    elif funnel_state == "等接近":
        buy_line = f"買點：不買，等接近{_breakout_trigger_zone_text(data)}"
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
    is_low_repair_prepare = (
        funnel_state == "可準備"
        and "低位修復" in str(data.get("evidence_adjustment_reason") or "")
    )
    trigger_label = _today_trigger_label(report_phase) if _is_today_action_phase(report_phase) else "明日觸發"
    if valid_entry and funnel_state == "趨勢延續":
        tomorrow_line = f"{trigger_label}：回踩站回日，小倉執行；不追高加碼"
    elif low_repair_actionable:
        tomorrow_line = f"{trigger_label}：守支撐/5日均 + 量能不失控，小倉試單"
    elif is_low_repair_prepare:
        tomorrow_line = f"{trigger_label}：開盤不追高；守支撐/5日均 + 量能不失控，小倉確認"
    elif limit_display_kind:
        tomorrow_line = f"{trigger_label}：開板/降溫後回測不破，且非追高"
    elif data_source_display_blocked:
        tomorrow_line = f"{trigger_label}：無有效進場，先補策略樣本證據"
    elif funnel_state == "等資料":
        tomorrow_line = f"{trigger_label}：資料恢復後再評估"
    elif deps["is_valid_entry"](stock_result) and strategy_source_blocked:
        tomorrow_line = f"{trigger_label}：無有效進場，先補策略樣本證據"
    elif funnel_state == "等接近":
        tomorrow_line = f"{trigger_label}：進入突破區附近，或形成回測承接型態再重評"
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
    if data_source_display_blocked or funnel_state == "等資料":
        reason_line = None
        data_line = None
    show_source_decision_reason = (
        bool(reason_line)
        or valid_entry
        or state in ["弱勢淘汰", "淘汰"]
        or (deps["is_valid_entry"](stock_result) and not source_eligible)
    )
    if show_source_decision_reason and not low_repair_actionable:
        reason_line = _append_decision_reason(reason_line, report_context, name)
    trend_control_lines = []
    if valid_entry and funnel_state == "趨勢延續":
        trend_control_lines = [
            "倉位：<=15%",
            "止損：回踩低點下方；形態失效即出",
            "持有：對齊 5 日 edge，5 日內未續漲或跌破回踩低點即了結",
        ]
    low_volume_limit_up_risk = deps["low_volume_limit_up_risk_text"](data)
    buy_gap_contract = _unheld_entry_contract(
        data_with_context,
        dist,
        blockers,
        valid_entry,
        funnel_state,
        source_status,
        strategy_source_blocked,
        title_label=title_label,
    )
    if is_low_repair_prepare:
        reason_line = None
        data_line = None
    if limit_display_kind:
        reason_line = None
        data_line = None
    compact_wait_card = (
        not valid_entry
        and not strategy_source_blocked
        and source_eligible
        and (
            funnel_state in {"等接近", "等低位修復", "等型態", "淘汰"}
            or state in {"等資料", "不可行動"}
        )
    )
    is_afterhours = effective_report_phase in {"盤後", "收盤"}
    is_afterhours_rejected = is_afterhours and funnel_state == "淘汰" and not valid_entry
    preserve_strategy_source_card = deps["is_valid_entry"](stock_result) and strategy_source_blocked
    if (
        not valid_entry
        and is_afterhours
        and not post_market_prepare
        and not preserve_strategy_source_card
        and funnel_state in {"等冷卻", "等接近", "等低位修復", "等型態", "等回測", "等RR修復", "隔日確認", "淘汰"}
        and data_line
        and ("不適用" in data_line or "風控不適用" in data_line)
    ):
        data_line = None
    if (
        not valid_entry
        and not post_market_prepare
        and funnel_state == "可準備"
        and data_line
        and "風控不適用" in data_line
        and "證據 +" not in data_line
        and "證據：資料不足" not in data_line
    ):
        data_line = None
    if (
        not valid_entry
        and not post_market_prepare
        and not data_source_display_blocked
        and "資料來源" not in str(title_label or "")
        and "策略樣本" not in str(title_label or "")
        and funnel_state in {"等冷卻", "等回測", "等型態", "等接近", "等低位修復", "等RR修復", "隔日確認", "淘汰"}
    ):
        data_line = None
    market_line = None if is_afterhours_rejected else (
        "盤面：證據不足｜待確認"
        if strategy_source_blocked
        else _score_gated_market_line(report_context, name, data, dist, deps)
    )
    if market_line == "盤面：證據不足｜待確認" and not valid_entry and not preserve_strategy_source_card:
        market_line = None
    if compact_wait_card and market_line == "盤面：證據不足｜待確認":
        market_line = None
    trade_state_line = deps["trade_state_machine_line"](data)
    if (
        (compact_wait_card and funnel_state == "淘汰")
        or (funnel_state == "淘汰" and "交易狀態：等資料" in str(trade_state_line))
    ):
        trade_state_line = None
    trade_state_line = _compact_unheld_trade_state_line(
        trade_state_line,
        valid_entry=valid_entry,
        post_market_prepare=post_market_prepare,
        data_source_blocked=data_source_display_blocked or (deps["is_valid_entry"](stock_result) and not source_eligible),
        funnel_state=funnel_state,
    )
    if low_repair_actionable:
        trade_state_line = "交易狀態：可買｜動作：小倉試單｜條件：守支撐/5日均，不追價"
    entry_check_lines = _entry_check_lines(buy_line, buy_gap_contract, funnel_state=funnel_state, data=data)
    lines = [
        f"【{deps['stock_title'](name, data)}】{title_icon} {title_action}｜{title_label}",
        trade_state_line,
        market_line,
        _breakout_distance_line(dist, data=data, funnel_state=funnel_state, title_label=title_label),
        *entry_check_lines,
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
    history_line = None if is_afterhours else _compact_unheld_history_line(
        deps["cross_day_detail_line"](data),
        funnel_state=funnel_state,
    )
    if history_line:
        lines.insert(-1, history_line)

    lines = [_readable_rr_terms(line) for line in lines]
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

    return None


def _brief_new_position_line(watch_items, report_context, deps, market_mode=None):
    funnel = deps["build_unheld_funnel"](watch_items, market_mode=market_mode, report_context=report_context) if watch_items else {"可買": []}
    actionable = len(funnel.get("可買") or []) + len(funnel.get("趨勢延續") or [])
    if actionable:
        return f"新倉：可行動候選 {actionable} 檔，以第二則卡片為準。"
    prepare_count = len(funnel.get("可準備") or []) if funnel else 0
    if prepare_count:
        return f"新倉：無有效進場；可準備 {prepare_count} 檔需明日開盤後確認，未確認前不可下單。"
    return "新倉：目前沒有可行動候選。"


def _unheld_strategy_group_check(funnel):
    if not funnel:
        return None
    labels = [
        ("等冷卻", "等冷卻"),
        ("等回測", "等回測"),
        ("等RR修復", "等風險報酬"),
        ("等型態", "等型態"),
        ("等接近", "等接近"),
        ("等低位修復", "等低位修復"),
        ("等量能", "等量能"),
        ("等市場", "等市場"),
        ("等資料", "等資料"),
        ("淘汰", "淘汰"),
    ]
    total = sum(len(funnel.get(key) or []) for key, _ in labels)
    if total == 0 or total > 8:
        return None
    if any(len(funnel.get(key) or []) > 3 for key, _ in labels):
        return None
    parts = []
    for key, label in labels:
        names = funnel.get(key) or []
        if names:
            parts.append(f"{'、'.join(names)}{label}")
    if not parts:
        return None
    return "未持倉：" + "；".join(parts)


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
        f"未持倉 {unheld_count}" + (f"（{'/'.join(unheld_parts)}）" if unheld_parts else ""),
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
            conclusion = f"結論：新倉候選 {actionable} 檔需確認；今日買入紀錄已轉風控。"
        elif mixed_today_buy_risk:
            conclusion = f"結論：新倉候選 {actionable} 檔需確認；今日買入紀錄已風控 {today_buy_risk_count}/觀察 {today_buy_observe_count}。"
        else:
            conclusion = f"結論：新倉候選 {actionable} 檔需確認；今日買入紀錄守警戒觀察。"
    elif actionable:
        conclusion = f"結論：新倉候選 {actionable} 檔，明日開盤前確認。"
    elif today_buy_names:
        if all_today_buys_are_risk:
            conclusion = "結論：新倉無有效進場；今日買入紀錄已轉風控。"
        elif mixed_today_buy_risk:
            conclusion = f"結論：新倉無有效進場；今日買入紀錄已風控 {today_buy_risk_count}/觀察 {today_buy_observe_count}。"
        else:
            conclusion = "結論：新倉無有效進場；今日買入紀錄守警戒觀察。"
    elif has_holding:
        conclusion = "結論：新倉無有效進場；持倉先看風控。"
    else:
        conclusion = "結論：新倉無有效進場；未持倉等觸發。"

    checks = []
    if holding_items:
        checks.append("觀察持倉是否跌破警戒")
    if actionable:
        checks.append("新倉候選需開盤後重新確認有效進場")
    elif prepare_count:
        checks.append("可準備候選需明日開盤後確認，未確認前不可下單")
    elif watch_items:
        checks.append(_unheld_strategy_group_check(funnel) or "未持倉標的重新等待有效進場")
    if not checks:
        checks.append("等下一交易日資料更新")

    plan_lines = []
    if today_buy_names:
        risk_text = f"{'、'.join(today_buy_risk_names)}減碼/停損優先" if today_buy_risk_names else None
        observe_names = [name for name in today_buy_names if name not in set(today_buy_risk_names)]
        observe_text = f"{'、'.join(observe_names)}守警戒觀察" if observe_names else None
        plan_lines.extend([text for text in [risk_text, observe_text] if text])
    if actionable:
        plan_lines.append(f"新倉候選 {actionable} 檔，明日開盤前重新確認")
    elif prepare_count:
        plan_lines.append(f"可準備 {prepare_count} 檔，開盤確認前不下單")
    unheld_check = _unheld_strategy_group_check(funnel) if watch_items else None
    if unheld_check:
        plan_lines.append(unheld_check)
    elif watch_items and not actionable and not prepare_count:
        plan_lines.append("未持倉僅追蹤，等觸發")
    if not plan_lines:
        plan_lines.extend(checks[:2])

    lines = [
        "📌 盤後簡報",
        conclusion,
        f"明日計畫：{'；'.join(plan_lines[:4])}。",
    ]
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
    if actionable or prepare_count:
        unheld_funnel_text = deps["format_unheld_funnel"](watch_items, market_mode=market_mode, report_context=report_context)
        if unheld_funnel_text:
            lines.extend(["", "未持倉狀態：", unheld_funnel_text])
    lines.extend(deps["format_backtest_groups"](watch_items, report_context=report_context))
    if daily_write_warning:
        lines.append(f"資料寫入：{daily_write_warning}，明日前確認補寫狀態。")
    lines = [_readable_rr_terms(line) for line in lines]
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

    lines.append("持倉風險報酬：既有持倉若不是加碼情境，只顯示新倉風險報酬不適用。持倉主行動以風控為準，避免把持倉誤讀成新買點。")
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
        "原因：",
        "風險：",
        "持倉：依第一則",
        "📎 詳情索引：",
    )
    if position_warning:
        summary_excluded_lines.add(f"⚠ {position_warning}，持倉狀態不可信")
    source_summary_line = deps["source_summary_text"](results_map)
    if "LAST_OHLCV" not in source_summary_line:
        summary_excluded_lines.add(source_summary_line)
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
