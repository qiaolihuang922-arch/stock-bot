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

    if report_context.get("source_status_summary", {}).get("funnel") not in {"derived", "available"}:
        lines.append("🧭 新倉：無有效進場。")

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
        lines.extend(["", "✅ 今日盤中交易執行"])
        lines.extend(deps["format_execution_checklist"](
            holding_items, watch_items, report_phase=report_phase, market_mode=market_mode, report_context=report_context
        ))
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

    lines.extend(["", "未持倉漏斗（非執行）："])
    lines.append(deps["format_unheld_funnel"](watch_items, market_mode=market_mode, report_context=report_context))

    lines.extend(["", deps["detail_index_text"](
        holding_items, watch_items, report_phase=report_phase, market_mode=market_mode, report_context=report_context
    )])

    rejected_line = deps["rejected_trace_line"](watch_items, market_mode=market_mode, report_context=report_context)
    if rejected_line:
        lines.append(rejected_line)

    if strategy_evidence_summary:
        lines.extend(["", strategy_evidence_summary])

    return "\n".join(lines)


def _report_phase(report_context):
    return (report_context or {}).get("report_context", {}).get("report_phase")


def _afterhours_card_text(line, report_context):
    if _report_phase(report_context) != "盤後" or line is None:
        return line
    replacements = {
        "盤中留意": "盤後觀察",
        "盤中觸發": "明日開盤前確認",
        "盤中可追": "等待下一交易日訊號",
        "即時進場": "等待下一交易日訊號",
        "盤中先觀察": "收盤後風控觀察",
        "盤中觀察修復狀況": "收盤後觀察修復狀況",
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


def formatTelegramPositionCard(name, data, *, deps, report_context=None):
    holding = data["holding"]
    decision = deps["ensure_holding_decision"](name, data)
    stock_result = data["result"]
    today_text = deps["holding_today_trade_text"](data, decision) or "無"
    dist = deps["card_breakout_distance"](data)
    decision_line, condition_line = deps["holding_detail_decision_lines"](name, data)
    reason_line = deps["holding_reason_line"](name, data)
    next_step = deps["holding_next_step_line"](name, data)
    rr_text = deps["rr_display_text"](stock_result, holding=True)
    add_levels = {"ADD_10", "ADD_20", "ADD_30"}
    is_add_context = bool(decision and decision.get("level") in add_levels and decision.get("allow_add") is not False)
    rr_line = "數據：新倉 RR：不適用（既有持倉）" if decision and not is_add_context else f"數據：RR {rr_text}"

    lines = [
        f"【{deps['stock_title'](name, data)}】📌 {deps['position_summary_action'](name, data)}｜{deps['signed_pct'](deps['stock_pnl'](data))}",
        f"倉位：{holding['shares']}股｜均價 {deps['price_text'](holding.get('avg_price'))}｜今日 {today_text}",
        f"風控：{deps['holding_risk_text'](decision)}",
        f"盤面：{deps['plain_label'](deps['compact_market_line'](stock_result, dist))}",
        f"決策：{decision_line}",
        f"條件：{condition_line}",
        f"下一步：{next_step}",
        deps["_source_status_line"](report_context, name, holding=True) if report_context else None,
        f"{rr_line}｜S {data.get('structure_score', '-')}/5｜V {data.get('volume_ratio', '-')}x",
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
    source_status = deps["_stock_decision_source_status"](report_context, name)
    source_eligible = source_status == "available"
    valid_entry = deps["is_valid_entry"](stock_result) and source_eligible
    title_label = "買點成立" if valid_entry else (blockers[0] if blockers else deps["final_label"](stock_result))
    state = deps["tomorrow_watch_state"](name, data)
    funnel_state = deps["unheld_funnel_state"](name, data, market_mode=market_mode, report_context=report_context)
    prepare_label, prepare_action = deps["strong_prepare_bucket"](data)
    if deps["is_valid_entry"](stock_result) and not source_eligible:
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
        title_action = "可準備"
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
    if deps["is_valid_entry"](stock_result) and not source_eligible:
        buy_line = f"買點：不可買，source {source_status}"
        data_line = "數據：RR 不可用｜S 不可用｜V 不可用"
        price_line = "價格：不可用（source missing）"
    elif valid_entry and report_phase not in (None, "盤中"):
        buy_line = "買點：盤後追蹤｜開盤後確認｜不追價"
        data_line = f"數據：RR {rr_text}｜S {data.get('structure_score', '-')}/5｜V {data.get('volume_ratio', '-')}x"
        price_line = deps["price_change_line"](data.get("price"), data.get("change"))
    elif valid_entry and detail_size_text != raw_size_text:
        buy_line = f"買點：可買｜{detail_size_text}｜分批，不追價"
        data_line = f"數據：RR {rr_text}｜S {data.get('structure_score', '-')}/5｜V {data.get('volume_ratio', '-')}x"
        price_line = deps["price_change_line"](data.get("price"), data.get("change"))
    elif valid_entry:
        buy_line = f"買點：可買｜建議 {raw_size_text}｜{wait_text}"
        data_line = f"數據：RR {rr_text}｜S {data.get('structure_score', '-')}/5｜V {data.get('volume_ratio', '-')}x"
        price_line = deps["price_change_line"](data.get("price"), data.get("change"))
    elif funnel_state == "可準備" and prepare_action:
        buy_line = f"買點：{prepare_action}"
        data_line = f"數據：RR {rr_text}｜S {data.get('structure_score', '-')}/5｜V {data.get('volume_ratio', '-')}x"
        price_line = deps["price_change_line"](data.get("price"), data.get("change"))
    elif funnel_state == "等回測":
        buy_line = "買點：不買，等回測"
        data_line = f"數據：RR {rr_text}｜S {data.get('structure_score', '-')}/5｜V {data.get('volume_ratio', '-')}x"
        price_line = deps["price_change_line"](data.get("price"), data.get("change"))
    elif funnel_state == "淘汰":
        buy_line = f"買點：不可買，{wait_text}"
        data_line = f"數據：RR {rr_text}｜S {data.get('structure_score', '-')}/5｜V {data.get('volume_ratio', '-')}x"
        price_line = deps["price_change_line"](data.get("price"), data.get("change"))
    else:
        buy_line = f"買點：不買，{wait_text}"
        data_line = f"數據：RR {rr_text}｜S {data.get('structure_score', '-')}/5｜V {data.get('volume_ratio', '-')}x"
        price_line = deps["price_change_line"](data.get("price"), data.get("change"))
    trigger_label = "盤中觸發" if report_phase == "盤中" else "明日觸發"
    tomorrow_line = f"{trigger_label}：{deps['tomorrow_trigger_text'](state, data)}"
    reason_line = (
        f"原因：price/OHLCV/RR source {source_status}，不作新倉決策"
        if deps["is_valid_entry"](stock_result) and not source_eligible
        else deps["rejected_transition_reason_line"](stock_result) if funnel_state == "淘汰" else None
    )
    lines = [
        f"【{deps['stock_title'](name, data)}】{title_icon} {title_action}｜{title_label}",
        f"盤面：{deps['plain_label'](deps['compact_market_line'](stock_result, dist))}",
        buy_line,
    ]

    if reason_line:
        lines.append(reason_line)

    lines.extend([
        tomorrow_line,
        deps["_source_status_line"](report_context, name, holding=False) if report_context else None,
        data_line,
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
    return "新倉：無有效進場。"


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


def _afterhours_brief_lines(holding_items, watch_items, report_context, deps, market_mode=None, summary_message=None):
    funnel = deps["build_unheld_funnel"](watch_items, market_mode=market_mode, report_context=report_context) if watch_items else {"可買": []}
    actionable = len(funnel.get("可買") or [])
    has_holding = bool(holding_items)
    if actionable:
        conclusion = f"結論：新倉候選 {actionable} 檔需明日開盤前確認；既有持倉以收盤後風控觀察為主。"
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
        _strategy_sample_status_line(report_context, deps),
        f"明日前確認：{'；'.join(checks[:3])}。",
    ]
    for source_line in (summary_message or "").splitlines():
        if source_line.startswith("⚠ ") and "每日快照未寫入" in source_line:
            lines.append(f"資料寫入：{source_line[2:]}，明日前確認補寫狀態。")
            break
    return lines


def _market_theme_data_basis_line(report_context, deps):
    evidence = report_context.get("market_theme_evidence") or {}
    field = deps["_field_by_key"](report_context, "evidence.market_theme")
    status = field.get("source_status") or deps["_manifest_status"](evidence.get("source_status"))
    trend = evidence.get("evidence_trend") or {}
    trend_parts = []
    if trend.get("observed_days"):
        trend_parts.append(f"近 {trend.get('observed_days')} 個交易證據日")
    if trend.get("recent_supporting_days") is not None:
        trend_parts.append(f"近期 {trend.get('recent_supporting_days')} 日支持")
    trend_text = "，".join(trend_parts) if trend_parts else "近幾個交易證據日"

    if evidence.get("confirmed") and status == "available":
        return (
            f"市場 / 題材背景：{trend_text}仍支持目前背景觀察，可靠度中等；"
            "這只用來理解環境，不等於買點。"
        )
    if status in {"missing-source", "source-error", "insufficient-data"}:
        return (
            "市場 / 題材背景：近幾個交易證據日不足以形成可靠背景，"
            "只作觀察，不作買點。"
        )
    return f"市場 / 題材背景：{trend_text}只作背景觀察，可靠度有限，不等於買點。"


def _strategy_sample_data_basis_line(report_context, deps):
    if _report_phase(report_context) == "盤後":
        return None
    strategy = deps["_field_by_key"](report_context, "evidence.strategy_sample")
    status = strategy.get("source_status", "missing-source")
    if status in {"missing-source", "source-error", "insufficient-data"}:
        return "策略樣本：本輪缺少可驗證樣本，可靠度低，未納入買賣判斷。"
    return "策略樣本：樣本來源可驗證，只作輔助參考，不新增買點。"


def _position_candidate_data_basis_line(report_context):
    statuses = report_context.get("source_status_summary") or {}
    position_status = statuses.get("position", "missing-source")
    candidate_status = statuses.get("funnel", "missing-source")
    position_ready = position_status == "available"
    candidate_ready = candidate_status in {"available", "derived"}

    if position_ready and candidate_ready:
        return (
            "持倉 / 價格 / 候選資料：持倉與價格資料可支持風控檢查；"
            "候選資料可支持分類，缺資料的標的會保守處理，不作有效進場。"
        )
    if position_ready:
        return (
            "持倉 / 價格 / 候選資料：持倉與價格資料可支持風控檢查；"
            "候選資料不足，本輪不給缺資料標的進場結論。"
        )
    return (
        "持倉 / 價格 / 候選資料：部分持倉或候選資料不足，只能支持有限風控檢查；"
        "缺資料標的本輪不給進場結論。"
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

    if _report_phase(report_context) != "盤後":
        strategy = deps["_field_by_key"](report_context, "evidence.strategy_sample")
        strategy_status = strategy.get("source_status", "missing-source")
        if strategy_status == "missing-source":
            lines.append("策略樣本：缺少可驗證來源，本次不納入買賣判斷。")
        elif strategy_status == "insufficient-data":
            lines.append("策略樣本：樣本不足，本次不納入買賣判斷。")
        elif strategy_status == "source-error":
            lines.append("策略樣本：來源讀取異常，本次不納入買賣判斷。")

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
        lines.append("執行記憶：資料不足，涉及已賣、停利或剩餘股數時採保守顯示。")
    elif has_conflict:
        lines.append("執行記憶：紀錄仍有待釐清的差異，未確認部分不輸出確定結論。")

    position_status = statuses.get("position")
    if position_status in {"missing-source", "source-error"}:
        lines.append("持倉來源：讀取不足，持倉風控只保留可確認資訊。")

    candidate_status = statuses.get("funnel")
    if candidate_status in {"missing-source", "source-error", "insufficient-data", "unresolved-conflict"}:
        lines.append("未持倉候選：來源不足或有疑義的標的不輸出有效進場。")

    lines.append("持倉 RR：既有持倉若不是加碼情境，只顯示新倉 RR 不適用。")
    return lines


def _decision_brief_lines(summary_message, version):
    noisy_prefixes = (
        "報告日：",
        "Source：",
        "證據日期：",
        "來源：",
        "趨勢：",
    )
    noisy_contains = (
        "latest_trade_date",
        "lookback_range",
        "source_of_truth",
        "db_table",
        "missing-source",
        "source-missing",
        "source-error",
        "insufficient-data",
        "unavailable",
        "fail-closed",
        "production",
        "runtime",
    )
    lines = []
    skip_strategy_evidence = False
    for line in (summary_message or "").splitlines():
        if line.startswith("📊 策略證據 v20.0"):
            skip_strategy_evidence = True
            continue
        if skip_strategy_evidence:
            if line == "":
                skip_strategy_evidence = False
            continue
        if line.startswith("【") and f"｜{version}】" in line:
            continue
        if any(line.startswith(prefix) for prefix in noisy_prefixes):
            continue
        if any(term in line for term in noisy_contains):
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
):
    if _report_phase(report_context) == "盤後":
        decision_lines = _afterhours_brief_lines(
            holding_items,
            watch_items,
            report_context,
            deps,
            market_mode=market_mode,
            summary_message=summary_message,
        )
    else:
        decision_lines = _decision_brief_lines(summary_message, version)
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
        _position_candidate_data_basis_line(report_context),
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
    evidence_message = deps["format_brief_data_evidence_message"](
        report_context,
        holding_items,
        [
            (name, data)
            for name, data in ordered_items
            if not data.get("holding")
        ],
        market_mode=market_mode,
        summary_message=summary_message,
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
