from services.strategy_evidence import (
    _fetch_recent_date_window_rows,
    _median,
    _num,
    _safe_round,
    calculate_outcome_metrics,
    feature_rows_from_signal_rows,
)


VOLUME_BUCKETS = [
    ("lt_0_7", None, 0.7),
    ("0_7_0_9", 0.7, 0.9),
    ("0_9_1_1", 0.9, 1.1),
    ("1_1_1_4", 1.1, 1.4),
    ("gte_1_4", 1.4, None),
]


SIGNAL_COLUMNS_V21_1 = (
    "stock_id,trade_date,version,close,volume_ratio,volume_ratio_10,volume_ratio_20,"
    "pattern,market_state,structure_state,position_state,rr,score,heat_level,action,"
    "reasons,is_tradeable,is_best_candidate,breakout_distance_20,breakout_distance_60"
)

SIGNAL_COLUMNS_LEGACY = (
    "stock_id,trade_date,version,close,volume_ratio,pattern,market_state,"
    "structure_state,position_state,rr,score,heat_level,action,reasons,"
    "is_tradeable,is_best_candidate"
)


def _is_missing_column_error(error):
    text = str(error).lower()
    return (
        "column" in text
        and (
            "could not find" in text
            or "does not exist" in text
            or "schema cache" in text
        )
    )


def volume_bucket(value):
    value = _num(value)
    if value is None:
        return "missing"
    for label, low, high in VOLUME_BUCKETS:
        if low is not None and value < low:
            continue
        if high is not None and value >= high:
            continue
        return label
    return "missing"


def setup_context(row):
    position = row.get("position_state") or "UNKNOWN"
    market = row.get("market_state")
    pattern = row.get("pattern")
    if position in {"BREAKOUT", "NEAR_BREAKOUT", "WATCH_BREAKOUT"}:
        return "near_breakout"
    if pattern in {"SHAKEOUT", "HEALTHY_PULLBACK"}:
        return "pullback"
    if position == "FAR" and market in {"D", "E"}:
        return "far_weak_market"
    if position == "FAR":
        return "far_no_breakout_setup"
    return "other"


def summarize_outcomes(rows):
    sample = len(rows)
    returns = [_num(row.get("close_return_pct")) for row in rows]
    returns = [item for item in returns if item is not None]
    mfes = [_num(row.get("max_favorable_excursion_pct")) for row in rows]
    maes = [_num(row.get("max_adverse_excursion_pct")) for row in rows]
    win_rate = None
    if returns:
        win_rate = round(sum(1 for item in returns if item > 0) / len(returns) * 100, 2)
    return {
        "sample": sample,
        "win_rate": win_rate,
        "median_return": _safe_round(_median(returns), 2),
        "median_mfe": _safe_round(_median(mfes), 2),
        "median_mae": _safe_round(_median(maes), 2),
    }


def build_volume_calibration(signal_rows, price_rows, *, horizon_days=3, min_sample=20):
    feature_rows = feature_rows_from_signal_rows(signal_rows)
    outcome_rows = calculate_outcome_metrics(feature_rows, price_rows, horizons=[horizon_days])
    signal_lookup = {
        (row.get("stock_id"), str(row.get("trade_date")), row.get("version")): row
        for row in signal_rows
    }
    feature_lookup = {
        (row.get("stock_id"), str(row.get("trade_date")), row.get("strategy_version")): row
        for row in feature_rows
    }

    grouped = {}
    for outcome in outcome_rows:
        key = (
            outcome.get("stock_id"),
            str(outcome.get("trade_date")),
            outcome.get("strategy_version"),
        )
        feature = feature_lookup.get(key)
        signal = signal_lookup.get(key)
        if not feature or not signal:
            continue
        context = setup_context({
            "position_state": signal.get("position_state"),
            "market_state": signal.get("market_state"),
            "pattern": signal.get("pattern"),
        })
        bucket = volume_bucket(signal.get("volume_ratio_20") if signal.get("volume_ratio_20") is not None else signal.get("volume_ratio"))
        grouped.setdefault(context, {}).setdefault(bucket, []).append(outcome)

    contexts = {}
    for context, buckets in sorted(grouped.items()):
        contexts[context] = {}
        for bucket, rows in sorted(buckets.items()):
            item = summarize_outcomes(rows)
            item["source_status"] = "available" if item["sample"] >= min_sample else "insufficient-data"
            item["decision_eligible"] = item["sample"] >= min_sample
            contexts[context][bucket] = item

    ready_count = sum(
        1
        for buckets in contexts.values()
        for item in buckets.values()
        if item.get("decision_eligible")
    )
    return {
        "source": "daily_signal_snapshot+daily_price",
        "db_write": False,
        "schema_change": False,
        "volume_window": "volume_ratio_20_fallback_volume_ratio",
        "horizon_days": horizon_days,
        "min_sample": min_sample,
        "source_status": "available" if ready_count else "insufficient-data",
        "contexts": contexts,
    }


def load_volume_calibration(client, *, limit=120, horizon_days=3, min_sample=20):
    schema_fallback = False
    try:
        signal_rows = _fetch_recent_date_window_rows(
            client,
            "daily_signal_snapshot",
            SIGNAL_COLUMNS_V21_1,
            limit,
        )
    except Exception as error:
        if not _is_missing_column_error(error):
            raise
        schema_fallback = True
        signal_rows = _fetch_recent_date_window_rows(
            client,
            "daily_signal_snapshot",
            SIGNAL_COLUMNS_LEGACY,
            limit,
        )
    price_rows = _fetch_recent_date_window_rows(
        client,
        "daily_price",
        "stock_id,trade_date,open,high,low,close,volume",
        limit,
    )
    if not signal_rows or not price_rows:
        return {
            "source": "daily_signal_snapshot+daily_price",
            "db_write": False,
            "schema_change": False,
            "schema_fallback": schema_fallback,
            "source_status": "insufficient-data",
            "contexts": {},
        }
    artifact = build_volume_calibration(
        signal_rows,
        price_rows,
        horizon_days=horizon_days,
        min_sample=min_sample,
    )
    artifact["schema_fallback"] = schema_fallback
    return artifact
