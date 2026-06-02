"""Telegram presentation assembly.

This module assembles already-prepared report data into Telegram messages. It
does not import storage clients or evidence writers; core.generator owns data
preparation and passes the formatter helpers needed for compatibility.
"""


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
    lines.extend([
        f"📊 市場：{market_mode}｜{risk_level}",
    ])

    if report_phase == "盤中":
        lines.append(deps["source_summary_text"](results_map))

    lines.extend([
        f"🧭 今日結論：{deps['today_conclusion_text'](holding_items, watch_items, market_mode, risk_level, report_phase=report_phase, report_context=report_context)}",
        f"🧭 原因：{deps['today_reason_text'](watch_items, market_mode, report_phase=report_phase, report_context=report_context)}",
    ])

    lines.extend([
        *deps["market_execution_bridge_lines"](holding_items, watch_items, market_mode, market_summary),
        *deps["format_cross_day_tracking_summary"](watch_items),
        *deps["format_strong_prepare_summary"](watch_items, market_mode),
        *deps["format_market_theme_summary_lines"](
            report_context.get("market_theme_evidence") or deps["market_theme_summary_evidence"](results_map, market_summary)
        ),
        f"🔥 最強：{deps['best_stock_text'](results_map, best, score, report_context=report_context)}",
        f"🚨 風險：{deps['compact_risk_text'](results_map)}",
        f"📌 持倉：{holding_names}",
    ])

    if report_phase == "盤中":
        execution_lines = deps["format_execution_checklist"](
            holding_items, watch_items, report_phase=report_phase, market_mode=market_mode, report_context=report_context
        )
        execution_lines = [line for line in execution_lines if line != "無新增下單"]
        if execution_lines:
            lines.extend(["", "✅ 今日盤中交易執行"])
            lines.extend(execution_lines)
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

    unheld_funnel_text = deps["format_unheld_funnel"](watch_items, market_mode=market_mode, report_context=report_context)
    if unheld_funnel_text:
        lines.extend(["", "未持倉漏斗（非執行）：", unheld_funnel_text])

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


def _afterhours_card_text(line, report_context):
    if _report_phase(report_context) != "盤後" or line is None:
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


def _score_gated_market_line(report_context, name, stock_result, dist, deps):
    if _score_source_available(report_context, name, deps):
        market_text = deps["plain_label"](deps["compact_market_line"](stock_result, dist))
        if ("弱勢" in market_text or "遠離突破" in market_text) and "極強" in market_text:
            market_text = market_text.replace("極強", "待確認")
        return f"盤面：{market_text}"
    return "盤面：強弱證據不足｜待確認"


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
    rr_line = "數據：新倉 RR：不適用（既有持倉）" if decision and not is_add_context else f"數據：RR {rr_text}"
    score_text = _score_data_text(report_context, name, data, deps)

    lines = [
        f"【{deps['stock_title'](name, data)}】📌 {summary_action}｜{deps['signed_pct'](deps['stock_pnl'](data))}",
        execution_line,
        f"風控：{deps['holding_risk_text'](decision)}",
        _score_gated_market_line(report_context, name, stock_result, dist, deps),
        deps["today_buy_holding_context_line"](data) if _report_phase(report_context) == "盤後" else None,
        f"決策：{decision_line}",
        f"條件：{condition_line}",
        f"下一步：{next_step}",
        deps["_source_status_line"](report_context, name, holding=True) if report_context else None,
        f"{rr_line}｜{score_text}｜V {data.get('volume_ratio', '-')}x",
        (
            None
            if _report_phase(report_context) == "盤後" and deps["_strategy_sample_unavailable"](report_context)
            else deps["_strategy_sample_unavailable_card_line"](report_context) or deps["compact_backtest_line"](data.get("backtest_context"))
        ),
        deps["price_change_line"](data.get("price"), data.get("change")),
    ]
    lines = [line for line in lines if line is not None]
    lines = [_afterhours_card_text(line, report_context) for line in lines]

    if reason_line:
        lines.insert(6, f"原因：{reason_line}")
    history_line = deps["cross_day_detail_line"](data)
    if history_line:
        lines.insert(-1, history_line)

    return "\n".join(lines)


def formatTelegramUnheldCard(name, data, *, deps, report_phase=None, market_mode=None, report_context=None):
    stock_result = data["result"]
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
    funnel_state = deps["unheld_funnel_state"](name, data, market_mode=market_mode, report_context=report_context)
    prepare_label, prepare_action = deps["strong_prepare_bucket"](data)
    if deps["is_valid_entry"](stock_result) and strategy_source_blocked:
        title_label = "策略樣本證據不足" if strategy_source_status != "source-error" else "策略樣本來源異常"
    elif deps["is_valid_entry"](stock_result) and not source_eligible:
        title_label = "source missing" if source_status in {"missing-source", "insufficient-data"} else source_status
    elif state == "弱勢淘汰":
        title_label = deps["rejected_primary_reason"](stock_result)
    elif funnel_state == "可準備" and prepare_label:
        title_label = prepare_label

    if valid_entry:
        title_icon = "🟢"
        if report_phase not in (None, "盤中"):
            title_action = f"明日追蹤｜{deps['unheld_entry_size_detail_text'](stock_result)}"
        else:
            title_action = f"可買｜{deps['unheld_entry_size_detail_text'](stock_result)}"
    elif deps["is_valid_entry"](stock_result) and not source_eligible:
        title_icon = "⛔"
        title_action = "不可行動"
    elif funnel_state == "可準備":
        title_icon = "👀"
        title_action = deps["unheld_non_actionable_prepare_label"](data)
    elif state in ["等冷卻", "等回測"]:
        title_icon = "⏳"
        title_action = state
    elif state in ["等RR修復", "等量能", "隔日確認"]:
        title_icon = "👀"
        title_action = state
    elif state == "弱勢淘汰":
        title_icon = "⛔"
        title_action = "淘汰"
    else:
        title_icon = "⛔"
        title_action = "不買"

    rr_text = deps["rr_display_text"](stock_result, holding=False)
    wait_text = deps["unheld_entry_wait_text"](stock_result, state, funnel_state)
    detail_size_text = deps["unheld_entry_size_detail_text"](stock_result)
    raw_size_text = deps["entry_size_text"](stock_result)
    score_text = _score_data_text(report_context, name, data, deps)
    if deps["is_valid_entry"](stock_result) and strategy_source_blocked:
        strategy_reason = {
            "missing-source": "策略樣本來源缺失",
            "insufficient-data": "策略樣本樣本不足",
            "source-error": "策略樣本來源讀取異常",
        }.get(strategy_source_status, "策略樣本不可用")
        buy_line = f"買點：不可買，{strategy_reason}"
        data_line = f"數據：RR {rr_text}｜S 證據不足｜V {data.get('volume_ratio', '-')}x"
        price_line = deps["price_change_line"](data.get("price"), data.get("change"))
    elif deps["is_valid_entry"](stock_result) and not source_eligible:
        buy_line = f"買點：不可買，source {source_status}"
        data_line = "數據：RR 不可用｜S 不可用｜V 不可用"
        price_line = "價格：不可用（source missing）"
    elif valid_entry and report_phase not in (None, "盤中"):
        buy_line = "買點：盤後追蹤｜開盤後確認｜不追價"
        data_line = f"數據：RR {rr_text}｜{score_text}｜V {data.get('volume_ratio', '-')}x"
        price_line = deps["price_change_line"](data.get("price"), data.get("change"))
    elif valid_entry and detail_size_text != raw_size_text:
        buy_line = f"買點：可買｜{detail_size_text}｜分批，不追價"
        data_line = f"數據：RR {rr_text}｜{score_text}｜V {data.get('volume_ratio', '-')}x"
        price_line = deps["price_change_line"](data.get("price"), data.get("change"))
    elif valid_entry:
        buy_line = f"買點：可買｜建議 {raw_size_text}｜{wait_text}"
        data_line = f"數據：RR {rr_text}｜{score_text}｜V {data.get('volume_ratio', '-')}x"
        price_line = deps["price_change_line"](data.get("price"), data.get("change"))
    elif funnel_state == "可準備" and prepare_action:
        buy_line = f"買點：{prepare_action}"
        data_line = f"數據：RR {rr_text}｜{score_text}｜V {data.get('volume_ratio', '-')}x"
        price_line = deps["price_change_line"](data.get("price"), data.get("change"))
    elif funnel_state == "等回測":
        buy_line = "買點：不買，等回測"
        data_line = f"數據：RR {rr_text}｜{score_text}｜V {data.get('volume_ratio', '-')}x"
        price_line = deps["price_change_line"](data.get("price"), data.get("change"))
    elif funnel_state == "淘汰":
        buy_line = f"買點：不可買，{wait_text}"
        data_line = f"數據：RR {rr_text}｜{score_text}｜V {data.get('volume_ratio', '-')}x"
        price_line = deps["price_change_line"](data.get("price"), data.get("change"))
    else:
        buy_line = f"買點：不買，{wait_text}"
        data_line = f"數據：RR {rr_text}｜{score_text}｜V {data.get('volume_ratio', '-')}x"
        price_line = deps["price_change_line"](data.get("price"), data.get("change"))
    trigger_label = "盤中觸發" if report_phase == "盤中" else "明日觸發"
    if deps["is_valid_entry"](stock_result) and strategy_source_blocked:
        tomorrow_line = f"{trigger_label}：無有效進場，先補策略樣本證據"
    else:
        tomorrow_line = f"{trigger_label}：{deps['tomorrow_trigger_text'](state, data)}"
    reason_line = (
        (
            "原因：策略樣本不可用，高置信 S 分數 / 強弱分類暫不採用"
            if strategy_source_blocked
            else f"原因：price/OHLCV/RR source {source_status}，不作新倉決策"
        )
        if deps["is_valid_entry"](stock_result) and not source_eligible
        else deps["rejected_transition_reason_line"](stock_result) if funnel_state == "淘汰" else None
    )
    low_volume_limit_up_risk = deps["low_volume_limit_up_risk_text"](data)
    lines = [
        f"【{deps['stock_title'](name, data)}】{title_icon} {title_action}｜{title_label}",
        (
            "盤面：證據不足｜待確認"
            if strategy_source_blocked
            else _score_gated_market_line(report_context, name, stock_result, dist, deps)
        ),
        buy_line,
    ]

    if reason_line:
        lines.append(reason_line)

    lines.extend([
        tomorrow_line,
        None if _report_phase(report_context) == "盤後" else (
            deps["_source_status_line"](report_context, name, holding=False) if report_context else None
        ),
        data_line,
        low_volume_limit_up_risk,
        (
            None
            if _report_phase(report_context) == "盤後" and deps["_strategy_sample_unavailable"](report_context)
            else deps["_strategy_sample_unavailable_card_line"](report_context) or deps["compact_backtest_line"](data.get("backtest_context"))
        ),
        price_line,
    ])
    lines = [line for line in lines if line is not None]
    lines = [_afterhours_card_text(line, report_context) for line in lines]
    history_line = deps["cross_day_detail_line"](data)
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
    actionable = len(funnel["可買"])
    if actionable:
        return f"新倉：可行動候選 {actionable} 檔，以第二則卡片為準。"
    return "新倉：目前沒有可行動候選。"


def _today_buy_holding_names(holding_items, deps):
    return [
        name for name, data in holding_items
        if deps["is_today_buy_holding"](data)
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


def _afterhours_brief_lines(holding_items, watch_items, report_context, deps, market_mode=None, daily_write_warning=None):
    funnel = deps["build_unheld_funnel"](watch_items, market_mode=market_mode, report_context=report_context) if watch_items else {"可買": []}
    actionable = len(funnel.get("可買") or [])
    has_holding = bool(holding_items)
    today_buy_names = _today_buy_holding_names(holding_items, deps)
    if actionable and today_buy_names:
        conclusion = f"結論：今日交易已建立新倉 {len(today_buy_names)} 檔；新增有效進場 {actionable} 檔需明日開盤前確認。"
    elif actionable:
        conclusion = f"結論：新倉候選 {actionable} 檔需明日開盤前確認；既有持倉以收盤後風控觀察為主。"
    elif today_buy_names:
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
    elif watch_items:
        checks.append("未持倉標的重新等待有效進場")
    if not checks:
        checks.append("等下一交易日資料更新")

    lines = [
        "📌 盤後簡報",
        conclusion,
    ]
    if today_buy_names:
        lines.extend([
            f"今日交易：已建立新倉 {len(today_buy_names)} 檔（{'、'.join(today_buy_names)}）",
            f"新增有效進場：{actionable} 檔需明日開盤前確認" if actionable else "新增有效進場：無",
        ])
    elif not actionable:
        lines.append("新增有效進場：無")
    lines.extend([
        _strategy_sample_status_line(report_context, deps),
        f"明日前確認：{'；'.join(checks[:3])}。",
    ])
    if holding_items:
        lines.extend([
            "",
            "持倉風控檢查",
            *deps["format_holding_control_checklist"](holding_items, report_phase="盤後"),
        ])
    unheld_funnel_text = deps["format_unheld_funnel"](watch_items, market_mode=market_mode, report_context=report_context)
    if unheld_funnel_text:
        lines.extend(["", "未持倉漏斗（非執行）：", unheld_funnel_text])
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

    if evidence.get("confirmed") and status == "available":
        return (
            f"市場 / 題材背景：{trend_text}仍支持目前背景觀察，{reliability}；"
            "這只用來理解環境，不等於買點。"
        )
    if status in {"missing-source", "source-error", "insufficient-data"}:
        return (
            "市場 / 題材背景：短期背景資料不足以形成可靠背景，"
            "只作觀察，不作買點。"
        )
    return f"市場 / 題材背景：{trend_text}只作背景觀察，可靠度有限，不等於買點。"


def _strategy_sample_data_basis_line(report_context, deps):
    if _report_phase(report_context) == "盤後":
        return None
    strategy = deps["_field_by_key"](report_context, "evidence.strategy_sample")
    status = strategy.get("source_status", "missing-source")
    if status == "missing-source":
        return "策略樣本：缺少可驗證來源，本次不納入買賣判斷。"
    if status == "insufficient-data":
        return "策略樣本：樣本不足，本次不納入買賣判斷。"
    if status == "source-error":
        return "策略樣本：來源讀取異常，本次不納入買賣判斷。"
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
    if deps and watch_items:
        funnel = deps["build_unheld_funnel"](watch_items, market_mode=market_mode, report_context=report_context)
        buy_count = len(funnel.get("可買") or [])
        prepare_count = len(funnel.get("可準備") or [])
        tracking_count = deps["unheld_tracking_only_count"](funnel)
        rejected_count = len(funnel.get("淘汰") or [])
        funnel_text = (
            f"未持倉 {watch_count} 檔已分類：可買 {buy_count}、"
            f"不可追高觀察 {prepare_count}、僅追蹤 {tracking_count}、淘汰 {rejected_count}；"
        )
    elif watch_count:
        funnel_text = f"未持倉 {watch_count} 檔已分類；"

    position_text = (
        f"持倉與價格資料可支持風控檢查（持倉 {holding_count} 檔）；"
        if holding_count
        else "持倉與價格資料可支持風控檢查；"
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


def _decision_brief_lines(summary_message, version, excluded_summary_lines=None, excluded_summary_sections=None):
    excluded_summary_lines = set(excluded_summary_lines or [])
    excluded_summary_sections = set(excluded_summary_sections or [])
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
        if line.startswith("【") and f"｜{version}】" in line:
            continue
        lines.append(line)

    while lines and lines[0] == "":
        lines.pop(0)
    while lines and lines[-1] == "":
        lines.pop()
    return lines


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
            excluded_summary_sections=summary_excluded_sections,
        )
        brief_lines = [
            _brief_holding_line(holding_items, deps),
            _brief_new_position_line(watch_items, report_context, deps, market_mode=market_mode),
            _brief_background_line(report_context, deps),
        ]
        decision_lines = brief_lines + decision_lines

    lines = [
        f"🧾 {version} 簡報＋資料依據",
        "",
        "決策簡報",
        *decision_lines,
        "",
        "資料依據",
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
    }
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
    evidence_message = deps["format_brief_data_evidence_message"](
        report_context,
        holding_items,
        watch_items,
        market_mode=market_mode,
        summary_message=summary_message,
        summary_excluded_lines=summary_excluded_lines,
        summary_excluded_sections=summary_excluded_sections,
        daily_write_warning=daily_write_warning,
    )

    messages = [
        holdings_message,
        unheld_message,
        f"{telegram_header}\n{evidence_message}",
    ]

    if include_detail:
        for chunk in deps["format_details_backup_messages"](full_msg):
            messages.append(chunk)

    return messages
