"""Telegram presentation assembly.

This module assembles already-prepared report data into Telegram messages. It
does not import storage clients or evidence writers; core.generator owns data
preparation and passes the formatter helpers needed for compatibility.
"""


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
