BLOCKING_REASONS = [
    "RR不足",
    "量能不足",
    "過熱 Lv.3",
    "不追高",
    "市場弱"
]

BLOCKING_PATTERNS = [
    "LOCK_LIMIT",
    "LIMIT_REBOUND",
    "WEAK_REBOUND",
    "FAILED_BREAKOUT",
    "SHAKEOUT"
]


def _has_reason(row, text):
    return text in (row.get("reasons") or [])


def validate_snapshots(rows):
    errors = []
    by_date = {}

    for idx, row in enumerate(rows, 1):
        label = f"{row.get('trade_date')} {row.get('stock_id')} row#{idx}"
        reasons = row.get("reasons") or []
        pattern = row.get("pattern")
        action = row.get("action")
        rr = row.get("rr")
        heat = row.get("heat_level") or 0
        is_tradeable = bool(row.get("is_tradeable"))
        is_best = bool(row.get("is_best_candidate"))

        by_date.setdefault(row.get("trade_date"), []).append(row)

        if is_tradeable:
            if action != "BUY":
                errors.append(f"{label}: is_tradeable=True but action={action}")

            for reason in BLOCKING_REASONS:
                if reason in reasons:
                    errors.append(f"{label}: is_tradeable=True but reason={reason}")

            if pattern in BLOCKING_PATTERNS:
                errors.append(f"{label}: is_tradeable=True but pattern={pattern}")

            if rr is None or rr < 1:
                errors.append(f"{label}: is_tradeable=True but rr={rr}")

            if heat >= 2:
                errors.append(f"{label}: is_tradeable=True but heat_level={heat}")

        if is_best:
            if not is_tradeable:
                errors.append(f"{label}: best candidate is not tradeable")
            if action != "BUY":
                errors.append(f"{label}: best candidate action is {action}")
            if rr is None or rr < 1:
                errors.append(f"{label}: best candidate rr={rr}")
            if heat >= 2:
                errors.append(f"{label}: best candidate heat_level={heat}")

        if action == "NO_TRADE" and is_tradeable:
            errors.append(f"{label}: NO_TRADE marked tradeable")

        if pattern == "LOCK_LIMIT" and is_tradeable:
            errors.append(f"{label}: limit-up lock marked tradeable")

        if pattern == "WEAK_REBOUND" and is_tradeable:
            errors.append(f"{label}: weak rebound marked tradeable")

        if pattern == "FAILED_BREAKOUT" and not _has_reason(row, "突破失敗"):
            errors.append(f"{label}: failed breakout missing reason")

    for trade_date, daily in by_date.items():
        best_count = sum(1 for row in daily if row.get("is_best_candidate"))

        if best_count > 1:
            errors.append(f"{trade_date}: more than one best candidate ({best_count})")

    # 中文註釋：v19.0 replay / backfill 前先檢查策略快照一致性，避免錯誤訊號批量入庫。
    return errors
