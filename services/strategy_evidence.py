from datetime import datetime

try:
    import pytz
except ImportError:
    pytz = None

from core.watchlist import WATCHLIST_CODES, missing_watchlist_codes


tz = pytz.timezone("Asia/Taipei") if pytz else None
OUTCOME_HORIZONS = [1, 3, 5, 10]
REPORT_CATEGORIES = ["淘汰", "等回測", "RR不足"]
MIN_REPORT_SAMPLE = 10


def _num(value):
    try:
        if value in [None, "-"]:
            return None
        return float(value)
    except:
        return None


def _safe_round(value, digits=4):
    value = _num(value)
    if value is None:
        return None
    return round(value, digits)


def _avg(values):
    values = [item for item in values if item is not None]
    return sum(values) / len(values) if values else None


def _median(values):
    values = sorted(item for item in values if item is not None)
    if not values:
        return None
    mid = len(values) // 2
    if len(values) % 2:
        return values[mid]
    return (values[mid - 1] + values[mid]) / 2


def _pct(current, base):
    current = _num(current)
    base = _num(base)
    if current is None or not base:
        return None
    return (current - base) / base * 100


def _pct_change(values, days):
    if not values or len(values) <= days:
        return None
    return _pct(values[-1], values[-1 - days])


def _vol_ratio(values, days):
    if not values or len(values) < days:
        return None
    base = _avg([_num(item) for item in values[-days:]])
    latest = _num(values[-1])
    if latest is None or not base:
        return None
    return latest / base


def should_record_strategy_evidence(phase, now=None):
    now = now or (datetime.now(tz) if tz else datetime.now())
    if now.weekday() >= 5:
        return False
    after_close = now.hour > 13 or (now.hour == 13 and now.minute >= 20)
    return after_close and phase in ["收盤", "盤後"]


def stable_watch_category(result, holding=False):
    if holding:
        return "持倉"

    decision = result.get("decision")
    action = _num(result.get("action")) or 0
    rr = _num(result.get("rr"))
    phase = result.get("structure_phase")
    behavior = result.get("price_behavior")
    heat = result.get("heat_state")
    trade_state = result.get("trade_state")
    market = result.get("market_grade")
    dist = _num(result.get("breakout_distance"))
    volume_state = result.get("volume_state")

    if decision == "BUY" and action > 0:
        return "可買"

    if heat in ["HOT", "EXTREME"] or trade_state in ["AVOID", "EXTENDED"] or behavior in ["LIMIT_LOCK", "LIMIT_REBOUND"]:
        return "追價風險"

    if trade_state == "LATE_ENTRY" or (rr is not None and rr < 1):
        return "RR不足"

    if trade_state == "NO_VOLUME" or volume_state == "WEAK":
        return "等量能"

    if phase in ["WEAK_REBOUND", "WEAK"] or market == "D":
        return "弱勢淘汰"

    if dist is not None and dist > 4:
        return "等回測"

    return "等回測"


def reject_family(result, category=None):
    category = category or stable_watch_category(result)
    rr = _num(result.get("rr"))
    heat = result.get("heat_state")
    trade_state = result.get("trade_state")
    behavior = result.get("price_behavior")
    phase = result.get("structure_phase")
    market = result.get("market_grade")
    volume_state = result.get("volume_state")

    if category == "可買":
        return "可買"
    if category == "持倉":
        return "持倉"
    if heat in ["HOT", "EXTREME"] or trade_state in ["AVOID", "EXTENDED"] or behavior in ["LIMIT_LOCK", "LIMIT_REBOUND"]:
        return "追價風險"
    if trade_state == "LATE_ENTRY" or (rr is not None and rr < 1):
        return "RR不足"
    if trade_state == "NO_VOLUME" or volume_state == "WEAK":
        return "量能不足"
    if phase in ["WEAK_REBOUND", "WEAK"] or market == "D":
        return "弱勢"
    return "條件未齊"


def feature_from_result(stock_id, trade_date, version, data):
    result = data.get("result") or {}
    closes = data.get("closes") or []
    volumes = data.get("volumes") or []
    holding = bool(data.get("holding"))
    category = stable_watch_category(result, holding=holding)
    family = reject_family(result, category)
    blockers = result.get("reasons") or result.get("blockers") or []
    if not blockers:
        blockers = [family] if family not in ["可買", "持倉"] else []

    return {
        "stock_id": stock_id,
        "trade_date": trade_date,
        "strategy_version": version,
        "price": _safe_round(data.get("price"), 4),
        "change_pct": _safe_round(data.get("change"), 4),
        "chg_1d": _safe_round(_pct_change(closes, 1), 4),
        "chg_3d": _safe_round(_pct_change(closes, 3), 4),
        "chg_5d": _safe_round(_pct_change(closes, 5), 4),
        "chg_10d": _safe_round(_pct_change(closes, 10), 4),
        "vol_ratio_5": _safe_round(_vol_ratio(volumes, 5), 4),
        "vol_ratio_10": _safe_round(_vol_ratio(volumes, 10), 4),
        "breakout_distance": _safe_round(result.get("breakout_distance"), 4),
        "rr": _safe_round(result.get("rr"), 4),
        "score": _safe_round(result.get("strength"), 4),
        "confidence": _safe_round(result.get("confidence_score"), 4),
        "market_state": result.get("market_grade"),
        "trend": result.get("trend"),
        "structure_state": result.get("structure_state"),
        "structure_phase": result.get("structure_phase"),
        "volume_state": result.get("volume_state"),
        "heat_state": result.get("heat_state"),
        "trade_state": result.get("trade_state"),
        "decision": result.get("decision"),
        "action": _safe_round(result.get("action"), 4),
        "is_tradeable": bool(result.get("is_tradeable", False)),
        "is_best_candidate": bool(result.get("is_best_candidate", False)),
        "watch_category": category,
        "reject_family": family,
        "blockers": blockers,
        "raw_reason_summary": "、".join(str(item) for item in blockers[:5]),
        "audit_category": audit_category_for_feature(category, family, result, data)
    }


def market_bar_from_data(stock_id, trade_date, data):
    ohlcv = data.get("ohlcv") or {}
    required = ["open", "high", "low", "close", "volume"]
    if not all(_num(ohlcv.get(field)) is not None for field in required):
        return None
    return {
        "stock_id": stock_id,
        "trade_date": trade_date,
        "open": _safe_round(ohlcv.get("open"), 4),
        "high": _safe_round(ohlcv.get("high"), 4),
        "low": _safe_round(ohlcv.get("low"), 4),
        "close": _safe_round(ohlcv.get("close"), 4),
        "volume": _safe_round(ohlcv.get("volume"), 4),
        "turnover": _safe_round(ohlcv.get("turnover"), 4),
        "source": ohlcv.get("source", "daily_close")
    }


def build_strategy_evidence_payloads(version, phase, results_map, now=None, expected_stock_ids=None):
    now = now or (datetime.now(tz) if tz else datetime.now())
    if not should_record_strategy_evidence(phase, now):
        return {
            "recorded": False,
            "reason": "skip_phase",
            "market_rows": [],
            "feature_rows": [],
            "audit_rows": []
        }

    expected_stock_ids = expected_stock_ids or WATCHLIST_CODES
    missing = missing_watchlist_codes(results_map, expected_stock_ids)
    if missing:
        return {
            "recorded": False,
            "reason": "incomplete_watchlist",
            "missing_stock_ids": missing,
            "market_rows": [],
            "feature_rows": [],
            "audit_rows": []
        }

    trade_date = now.strftime("%Y-%m-%d")
    market_rows = []
    feature_rows = []

    for _name, data in results_map.items():
        stock_id = data.get("stock_code")
        if not stock_id:
            continue
        bar = market_bar_from_data(stock_id, trade_date, data)
        if bar:
            market_rows.append(bar)
        feature_rows.append(feature_from_result(stock_id, trade_date, version, data))

    return {
        "recorded": True,
        "reason": "ready",
        "market_rows": market_rows,
        "feature_rows": feature_rows,
        "audit_rows": build_audit_rows(feature_rows)
    }


def feature_from_signal_row(row):
    result = {
        "decision": row.get("action"),
        "rr": row.get("rr"),
        "market_grade": row.get("market_state"),
        "structure_state": row.get("structure_state"),
        "structure_phase": row.get("pattern"),
        "volume_state": None,
        "heat_state": "EXTREME" if (row.get("heat_level") or 0) >= 3 else ("HOT" if (row.get("heat_level") or 0) >= 2 else "NORMAL"),
        "trade_state": "LATE_ENTRY" if "RR不足" in (row.get("reasons") or []) else "WAIT",
        "breakout_distance": None,
        "strength": row.get("score"),
        "action": 0
    }
    category = stable_watch_category(result)
    if row.get("is_tradeable"):
        category = "可買"
    family = reject_family(result, category)
    return {
        "stock_id": row.get("stock_id"),
        "trade_date": row.get("trade_date"),
        "strategy_version": row.get("version"),
        "price": _safe_round(row.get("close"), 4),
        "change_pct": None,
        "chg_1d": None,
        "chg_3d": None,
        "chg_5d": None,
        "chg_10d": None,
        "vol_ratio_5": None,
        "vol_ratio_10": _safe_round(row.get("volume_ratio"), 4),
        "breakout_distance": None,
        "rr": _safe_round(row.get("rr"), 4),
        "score": _safe_round(row.get("score"), 4),
        "confidence": None,
        "market_state": row.get("market_state"),
        "trend": None,
        "structure_state": row.get("structure_state"),
        "structure_phase": row.get("pattern"),
        "volume_state": None,
        "heat_state": result.get("heat_state"),
        "trade_state": result.get("trade_state"),
        "decision": row.get("action"),
        "action": 0,
        "is_tradeable": bool(row.get("is_tradeable")),
        "is_best_candidate": bool(row.get("is_best_candidate")),
        "watch_category": category,
        "reject_family": family,
        "blockers": row.get("reasons") or [],
        "raw_reason_summary": "、".join(str(item) for item in (row.get("reasons") or [])[:5]),
        "audit_category": None
    }


def market_rows_from_price_rows(price_rows, source="backfill"):
    rows = []
    for row in price_rows:
        close = _num(row.get("close"))
        volume = _num(row.get("volume"))
        if close is None or volume is None:
            continue
        open_price = _num(row.get("open"))
        high = _num(row.get("high"))
        low = _num(row.get("low"))
        rows.append({
            "stock_id": row.get("stock_id"),
            "trade_date": row.get("trade_date"),
            "open": _safe_round(open_price if open_price is not None else close, 4),
            "high": _safe_round(high if high is not None else close, 4),
            "low": _safe_round(low if low is not None else close, 4),
            "close": _safe_round(close, 4),
            "volume": _safe_round(volume, 4),
            "turnover": _safe_round(row.get("turnover"), 4),
            "source": row.get("source") or source
        })
    return rows


def feature_rows_from_signal_rows(signal_rows):
    return [feature_from_signal_row(row) for row in signal_rows]


def price_lookup(price_rows):
    lookup = {}
    for row in price_rows:
        stock_id = row.get("stock_id")
        trade_date = str(row.get("trade_date"))
        if not stock_id or not trade_date:
            continue
        lookup.setdefault(stock_id, {})[trade_date] = row
    return lookup


def sorted_dates(rows):
    return sorted({str(row.get("trade_date")) for row in rows if row.get("trade_date")})


def _future_window(lookup, stock_id, trade_date, horizon_days):
    dates = sorted(lookup.get(stock_id, {}))
    if trade_date not in dates:
        return None
    start = dates.index(trade_date)
    end = start + horizon_days
    if end >= len(dates):
        return None
    return [lookup[stock_id][date] for date in dates[start + 1:end + 1]]


def _market_return(price_rows, trade_date, horizon_days):
    lookup = price_lookup(price_rows)
    returns = []
    for stock_id, rows in lookup.items():
        start = rows.get(trade_date)
        window = _future_window(lookup, stock_id, trade_date, horizon_days)
        if not start or not window:
            continue
        returns.append(_pct(window[-1].get("close"), start.get("close")))
    return _avg(returns)


def outcome_label(close_return, mfe, mae):
    if close_return is None:
        return "pending"
    if close_return >= 3:
        return "win"
    if close_return <= -3:
        return "loss"
    if mfe is not None and mfe >= 5 and close_return < 1:
        return "whipsaw"
    if mfe is not None and mfe >= 3:
        return "late_win"
    if mae is not None and mae <= -5:
        return "risk"
    return "flat"


def calculate_outcome_metrics(feature_rows, price_rows, horizons=None):
    horizons = horizons or OUTCOME_HORIZONS
    lookup = price_lookup(price_rows)
    rows = []

    for feature in feature_rows:
        stock_id = feature.get("stock_id")
        trade_date = str(feature.get("trade_date"))
        start = lookup.get(stock_id, {}).get(trade_date)
        if not start:
            continue
        start_close = _num(start.get("close") or feature.get("price"))
        if not start_close:
            continue

        for horizon in horizons:
            window = _future_window(lookup, stock_id, trade_date, horizon)
            if not window:
                continue
            horizon_close = _num(window[-1].get("close"))
            highs = [_num(row.get("high") or row.get("close")) for row in window]
            lows = [_num(row.get("low") or row.get("close")) for row in window]
            close_return = _pct(horizon_close, start_close)
            mfe = _pct(max(item for item in highs if item is not None), start_close) if any(item is not None for item in highs) else None
            mae = _pct(min(item for item in lows if item is not None), start_close) if any(item is not None for item in lows) else None
            market_return = _market_return(price_rows, trade_date, horizon)

            rows.append({
                "stock_id": stock_id,
                "trade_date": trade_date,
                "strategy_version": feature.get("strategy_version"),
                "watch_category": feature.get("watch_category"),
                "reject_family": feature.get("reject_family"),
                "horizon_days": horizon,
                "close_return_pct": _safe_round(close_return, 4),
                "relative_return_pct": _safe_round(close_return - market_return, 4) if market_return is not None and close_return is not None else None,
                "max_favorable_excursion_pct": _safe_round(mfe, 4),
                "max_adverse_excursion_pct": _safe_round(mae, 4),
                "hit_breakout_after_signal": bool(mfe is not None and mfe >= 3),
                "hit_stop_like_drawdown": bool(mae is not None and mae <= -5),
                "best_entry_gap_pct": _safe_round(mae, 4),
                "outcome_label": outcome_label(close_return, mfe, mae)
            })

    return rows


def _setup_key_from_feature(feature):
    return feature.get("reject_family") or feature.get("watch_category")


def _score_from_setup_metrics(win_rate, median_mfe, median_mae):
    if win_rate is None:
        return None
    win_component = max(0.0, min(1.0, float(win_rate) / 100.0))
    mfe_component = 0.5
    if median_mfe is not None or median_mae is not None:
        mfe = float(median_mfe or 0)
        mae = abs(float(median_mae or 0))
        mfe_component = max(0.0, min(1.0, (mfe - mae + 10) / 20))
    return round((win_component * 0.7) + (mfe_component * 0.3), 4)


def build_setup_strategy_samples(feature_rows, outcome_rows, min_sample=MIN_REPORT_SAMPLE, horizon_days=3):
    feature_lookup = {
        (row.get("stock_id"), str(row.get("trade_date")), row.get("strategy_version")): row
        for row in feature_rows
    }
    by_key = {}
    for outcome in outcome_rows:
        if int(outcome.get("horizon_days") or 0) != horizon_days:
            continue
        lookup_key = (
            outcome.get("stock_id"),
            str(outcome.get("trade_date")),
            outcome.get("strategy_version"),
        )
        feature = feature_lookup.get(lookup_key, {})
        setup_key = _setup_key_from_feature(feature) or _setup_key_from_feature(outcome)
        if not setup_key:
            continue
        by_key.setdefault(setup_key, []).append(outcome)

    samples = {}
    for setup_key, rows in by_key.items():
        sample = len(rows)
        win_count = sum(1 for row in rows if (_num(row.get("close_return_pct")) or 0) > 0)
        win_rate = round(win_count / sample * 100, 2) if sample else None
        median_mfe = _safe_round(_median([_num(row.get("max_favorable_excursion_pct")) for row in rows]), 2)
        median_mae = _safe_round(_median([_num(row.get("max_adverse_excursion_pct")) for row in rows]), 2)
        samples[setup_key] = {
            "setup_key": setup_key,
            "status": "ready" if sample >= min_sample else "insufficient-data",
            "source_status": "available" if sample >= min_sample else "insufficient-data",
            "sample_count": sample,
            "sample": sample,
            "win_rate": win_rate,
            "median_mfe": median_mfe,
            "median_mae": median_mae,
            "mfe_mae_score": _score_from_setup_metrics(win_rate, median_mfe, median_mae),
            "decision_eligible": sample >= min_sample,
        }
    return samples


def build_classification_report(feature_rows, outcome_rows, min_sample=MIN_REPORT_SAMPLE, horizon_days=3):
    by_key = {}
    feature_lookup = {
        (row.get("stock_id"), str(row.get("trade_date")), row.get("strategy_version")): row
        for row in feature_rows
    }

    for outcome in outcome_rows:
        horizon = int(outcome.get("horizon_days") or 0)
        if horizon not in OUTCOME_HORIZONS:
            continue
        key = (
            outcome.get("stock_id"),
            str(outcome.get("trade_date")),
            outcome.get("strategy_version")
        )
        feature = feature_lookup.get(key, {})
        category = feature.get("watch_category") or outcome.get("watch_category")
        if category not in REPORT_CATEGORIES:
            if category == "弱勢淘汰":
                category = "淘汰"
            elif feature.get("reject_family") == "RR不足":
                category = "RR不足"
            else:
                continue
        by_key.setdefault(category, {}).setdefault(horizon, []).append(outcome)

    report = {}
    for category in REPORT_CATEGORIES:
        rows_by_horizon = by_key.get(category, {})
        primary_rows = rows_by_horizon.get(horizon_days, [])
        mfe_horizon = 5 if rows_by_horizon.get(5) else horizon_days
        mfe_rows = rows_by_horizon.get(mfe_horizon, primary_rows)
        sample = len(primary_rows)
        win_count = sum(1 for row in primary_rows if (_num(row.get("close_return_pct")) or 0) > 0)
        leak_count = sum(1 for row in mfe_rows if (_num(row.get("max_favorable_excursion_pct")) or 0) >= 5)
        report[category] = {
            "sample": sample,
            "sample_ready": sample >= min_sample,
            "win_rate": round(win_count / sample * 100) if sample else None,
            "median_return": _safe_round(_median([_num(row.get("close_return_pct")) for row in primary_rows]), 2),
            "median_mfe": _safe_round(_median([_num(row.get("max_favorable_excursion_pct")) for row in mfe_rows]), 2),
            "median_mae": _safe_round(_median([_num(row.get("max_adverse_excursion_pct")) for row in mfe_rows]), 2),
            "return_horizon": horizon_days,
            "mfe_horizon": mfe_horizon,
            "missed_rally_count": leak_count
        }

    return report


def audit_category_for_feature(category, family, result, data):
    chg5 = _pct_change(data.get("closes") or [], 5)
    chg10 = _pct_change(data.get("closes") or [], 10)
    heat = result.get("heat_state")
    behavior = result.get("price_behavior")
    phase = result.get("structure_phase")

    if category in ["淘汰", "弱勢淘汰"] and (chg5 is not None and chg5 >= 8 or chg10 is not None and chg10 >= 15):
        return "高波動強勢，非弱勢淘汰"
    if family == "追價風險" and (heat in ["HOT", "EXTREME"] or behavior in ["LIMIT_LOCK", "LIMIT_REBOUND"]):
        return "不追價合理，但需高波動觀察"
    if phase == "WEAK_REBOUND" and (chg5 is not None and chg5 >= 5):
        return "弱反彈語意需複核"
    return None


def build_audit_rows(feature_rows):
    rows = []
    for feature in feature_rows:
        audit = feature.get("audit_category")
        if not audit:
            continue
        rows.append({
            "stock_id": feature.get("stock_id"),
            "trade_date": feature.get("trade_date"),
            "strategy_version": feature.get("strategy_version"),
            "original_category": feature.get("watch_category"),
            "suggested_audit_category": audit,
            "distortion_type": "classification_semantics",
            "evidence_summary": (
                f"分類={feature.get('watch_category')}｜"
                f"5日={feature.get('chg_5d')}｜10日={feature.get('chg_10d')}｜"
                f"family={feature.get('reject_family')}"
            ),
            "severity": "medium",
            "review_status": "open"
        })
    return rows


def _strategy_sample_unavailable_lines(status, reason):
    return [
        "策略樣本 / 分類回測",
        "狀態：不可用",
        f"原因：{reason}",
        "解讀：本次不把策略樣本納入判斷；個股決策只看既有買點與風控。",
        f"狀態碼：{status}",
    ]


def format_strategy_evidence_summary(
    report=None,
    audits=None,
    error=None,
    source_status=None,
    source_reason=None,
):
    lines = [
        "📊 策略證據 v20.0",
        "說明：以下為 strategy sample 層，不影響 market/theme production confirmed evidence。",
    ]
    if error:
        if strategy_evidence_error_kind(error) == "schema_missing":
            reason = "缺 classification backtest source-of-truth"
            status = "missing-source"
        else:
            reason = "classification backtest 讀取失敗"
            status = "source-error"
        lines.extend(_strategy_sample_unavailable_lines(status, reason))
        return "\n".join(lines)

    if source_status:
        reason = source_reason or "classification backtest source-of-truth 不可用"
        lines.extend(_strategy_sample_unavailable_lines(source_status, reason))
        return "\n".join(lines)

    report = report or {}
    audits = audits or []

    if not report:
        lines.extend(_strategy_sample_unavailable_lines(
            "missing-source",
            "缺 classification backtest source-of-truth",
        ))
    else:
        ready_items = []
        max_sample = 0
        for category in REPORT_CATEGORIES:
            item = report.get(category) or {"sample": 0, "sample_ready": False}
            sample = item.get("sample") or 0
            max_sample = max(max_sample, sample)
            if not item.get("sample_ready"):
                continue
            ready_items.append((category, item))

        if not ready_items:
            lines.extend(_strategy_sample_unavailable_lines(
                "insufficient-sample",
                f"classification backtest 樣本不足（有效樣本 {max_sample}）",
            ))
        else:
            lines.append("策略樣本 / 分類回測")
            for category, item in ready_items:
                sample = item.get("sample") or 0
                win_rate = item.get("win_rate")
                mfe = item.get("median_mfe")
                mfe_text = "-" if mfe is None else f"{mfe:+.1f}%"
                return_horizon = item.get("return_horizon") or 3
                mfe_horizon = item.get("mfe_horizon") or 5
                missed = item.get("missed_rally_count")
                lines.append(
                    f"分類：{category}｜樣本：{sample} 筆｜"
                    f"觀察口徑：v20.0 classification backtest｜"
                    f"{return_horizon}日勝率 {win_rate}%｜"
                    f"{mfe_horizon}日MFE中位 {mfe_text}｜漏失 {missed}"
                )
            lines.append(
                "解讀：歷史樣本只作分類參考；是否進場仍看個股買點與風控。"
            )

    if audits:
        first = audits[0]
        name = first.get("stock_name") or first.get("stock_id")
        lines.append(f"⚠ 分類警示：{first.get('suggested_audit_category')} 1 筆（{name}）")

    return "\n".join(lines)


def report_from_rows(feature_rows, outcome_rows, audit_rows=None):
    report = build_classification_report(feature_rows, outcome_rows)
    rendered_text = format_strategy_evidence_summary(
        report,
        audit_rows or build_audit_rows(feature_rows)
    )
    setup_samples = build_setup_strategy_samples(feature_rows, outcome_rows)
    ready_count = sum(1 for item in setup_samples.values() if item.get("status") == "ready")
    row_count = sum((item.get("sample_count") or 0) for item in setup_samples.values())
    return {
        "rendered_text": rendered_text,
        "text": rendered_text,
        "structured_status": {
            "status": "available" if ready_count else "insufficient-data",
            "source": "daily_signal_snapshot",
            "row_count": row_count,
            "setup_ready_count": ready_count,
            "missing_fields": [],
            "completeness": "complete" if ready_count else "insufficient",
        },
        "setup_strategy_samples": setup_samples,
        "classification_report": report,
    }


def strategy_evidence_error_kind(error):
    text = str(error or "").lower()
    schema_markers = [
        "could not find the table",
        "schema cache",
        "daily_signal_snapshot",
        "daily_price",
        "relation",
        "does not exist",
        "pgrst205",
    ]
    if any(marker in text for marker in schema_markers):
        return "schema_missing"
    return "db_failure"


def format_strategy_evidence_error(error):
    if strategy_evidence_error_kind(error) == "schema_missing":
        return "策略證據尚未啟用：資料表未建立，主報文不受影響"
    return "證據層暫時略過：資料更新失敗，主報文不受影響"


def load_strategy_evidence_summary(client, version, limit=240):
    signal_rows = (
        client.table("daily_signal_snapshot")
        .select("stock_id,trade_date,version,close,volume_ratio,pattern,market_state,structure_state,position_state,rr,score,heat_level,action,reasons,is_tradeable,is_best_candidate")
        .order("trade_date", desc=True)
        .limit(limit)
        .execute()
        .data
        or []
    )
    price_rows = (
        client.table("daily_price")
        .select("stock_id,trade_date,open,high,low,close,volume")
        .order("trade_date", desc=True)
        .limit(limit)
        .execute()
        .data
        or []
    )
    feature_rows = feature_rows_from_signal_rows(signal_rows)
    if not feature_rows:
        return format_strategy_evidence_summary(
            source_status="missing-source",
            source_reason="缺 classification backtest source-of-truth",
        )
    if not price_rows:
        return format_strategy_evidence_summary(
            source_status="insufficient-data",
            source_reason="classification backtest 欄位不足（daily_price 無可用資料）",
        )
    outcome_rows = calculate_outcome_metrics(feature_rows, price_rows)
    return report_from_rows(feature_rows, outcome_rows, [])


def get_supabase_client():
    from supabase import create_client
    from config import SUPABASE_KEY, SUPABASE_URL
    return create_client(SUPABASE_URL, SUPABASE_KEY)


def record_strategy_evidence(version, phase, results_map, now=None, client=None):
    payloads = build_strategy_evidence_payloads(version, phase, results_map, now)
    if not payloads.get("recorded"):
        return payloads

    return {
        "recorded": False,
        "reason": "strategy_evidence_derived_from_daily_snapshot",
        "market_rows": 0,
        "feature_rows": 0,
        "audit_rows": 0,
    }
