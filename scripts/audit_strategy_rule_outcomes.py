import argparse
import json
import sys
from collections import defaultdict
from datetime import datetime, timedelta, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.audit_strategy_buy_path_replay import (
    DEFAULT_LOOKBACK_DAYS,
    VERSION,
    WARMUP_DAYS,
    _client,
    _safe_round,
    fetch_daily_price_rows,
    replay_from_daily_price,
)
from core.watchlist import WATCHLIST_CODES
from scripts.dry_run_replay import parse_date


HORIZONS = [1, 3, 5, 10]
MIN_VERDICT_SAMPLE = 20


def _date_index(rows):
    return {
        row["trade_date"].isoformat(): idx
        for idx, row in enumerate(rows)
    }


def _pct(current, base):
    if current is None or not base:
        return None
    return (current / base - 1) * 100


def attach_outcomes(events, rows_by_stock, horizons=None):
    horizons = horizons or HORIZONS
    rows_by_stock = {
        str(stock_id): sorted(rows, key=lambda row: row["trade_date"])
        for stock_id, rows in rows_by_stock.items()
    }
    index_by_stock = {
        stock_id: _date_index(rows)
        for stock_id, rows in rows_by_stock.items()
    }

    enriched = []
    for event in events:
        stock_id = str(event["stock_id"])
        rows = rows_by_stock.get(stock_id) or []
        idx = index_by_stock.get(stock_id, {}).get(event["trade_date"])
        entry = event.get("close")
        item = dict(event)
        item["outcomes"] = {}
        if idx is None or entry in (None, 0):
            item["outcome_status"] = "missing-index"
            enriched.append(item)
            continue

        for horizon in horizons:
            future_idx = idx + horizon
            if future_idx >= len(rows):
                item["outcomes"][f"{horizon}d"] = {"status": "insufficient-forward-bars"}
                continue
            future_rows = rows[idx + 1:future_idx + 1]
            future_close = rows[future_idx].get("close")
            closes = [row.get("close") for row in future_rows if row.get("close") is not None]
            item["outcomes"][f"{horizon}d"] = {
                "status": "ready",
                "return_pct": _safe_round(_pct(future_close, entry), 4),
                "max_favorable_pct": _safe_round(_pct(max(closes), entry), 4) if closes else None,
                "max_adverse_pct": _safe_round(_pct(min(closes), entry), 4) if closes else None,
            }
        item["outcome_status"] = "ready"
        enriched.append(item)
    return enriched


def _values(items, horizon, field):
    key = f"{horizon}d"
    values = []
    for item in items:
        outcome = (item.get("outcomes") or {}).get(key) or {}
        if outcome.get("status") != "ready":
            continue
        value = outcome.get(field)
        if value is not None:
            values.append(float(value))
    return values


def _avg(values):
    return sum(values) / len(values) if values else None


def _median(values):
    values = sorted(values)
    if not values:
        return None
    mid = len(values) // 2
    if len(values) % 2:
        return values[mid]
    return (values[mid - 1] + values[mid]) / 2


def _summary_for_items(items):
    summary = {"sample": len(items)}
    for horizon in HORIZONS:
        returns = _values(items, horizon, "return_pct")
        mfe = _values(items, horizon, "max_favorable_pct")
        mae = _values(items, horizon, "max_adverse_pct")
        summary[f"{horizon}d"] = {
            "ready_sample": len(returns),
            "avg_return_pct": _safe_round(_avg(returns), 4),
            "median_return_pct": _safe_round(_median(returns), 4),
            "win_rate_pct": _safe_round(sum(1 for value in returns if value > 0) / len(returns) * 100, 2) if returns else None,
            "avg_mfe_pct": _safe_round(_avg(mfe), 4),
            "avg_mae_pct": _safe_round(_avg(mae), 4),
        }
    return summary


def _verdict_for_group(label, summary, actionable=False):
    five = summary.get("5d") or {}
    sample = five.get("ready_sample") or 0
    avg_ret = five.get("avg_return_pct")
    win_rate = five.get("win_rate_pct")
    if sample < MIN_VERDICT_SAMPLE or avg_ret is None or win_rate is None:
        return {
            "verdict": "insufficient_sample",
            "reason": f"5d樣本 {sample} < {MIN_VERDICT_SAMPLE}",
        }

    if actionable:
        if avg_ret > 0 and win_rate >= 50:
            return {"verdict": "supported", "reason": "可行動組 5d 平均報酬為正且勝率>=50%"}
        if avg_ret <= 0 and win_rate < 50:
            return {"verdict": "risk_flag", "reason": "可行動組 5d 平均報酬/勝率偏弱，需校準"}
        return {"verdict": "mixed", "reason": "可行動組 5d 報酬與勝率訊號不一致"}

    if avg_ret > 0 and win_rate >= 55:
        return {"verdict": "audit_needed_maybe_too_strict", "reason": "被阻擋組 5d 後續偏強，gate 可能太嚴"}
    if avg_ret < 0 or win_rate < 45:
        return {"verdict": "block_supported", "reason": "被阻擋組 5d 後續偏弱，阻擋有依據"}
    return {"verdict": "mixed", "reason": "被阻擋組 5d 後續普通，需看子分類"}


def group_outcomes(events, key, actionable_values=None):
    actionable_values = set(actionable_values or [])
    grouped = defaultdict(list)
    for event in events:
        grouped[str(event.get(key) if event.get(key) is not None else "missing")].append(event)
    result = {}
    for label, items in sorted(grouped.items()):
        summary = _summary_for_items(items)
        summary["verdict"] = _verdict_for_group(label, summary, actionable=label in actionable_values)
        result[label] = summary
    return result


def summarize_rule_outcomes(events, rows_by_stock, start_date, end_date, version):
    enriched = attach_outcomes(events, rows_by_stock)
    actionable_states = {"可買", "趨勢延續"}
    output = {
        "mode": "strategy_rule_outcome_audit",
        "version": version,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "read_only": True,
        "db_write": False,
        "schema_change": False,
        "live_telegram": False,
        "source": "Supabase daily_price read-only",
        "date_range": {
            "start": start_date.isoformat(),
            "end": end_date.isoformat(),
        },
        "horizons": HORIZONS,
        "totals": {
            "events": len(enriched),
            "events_with_10d_outcome": sum(
                1
                for event in enriched
                if ((event.get("outcomes") or {}).get("10d") or {}).get("status") == "ready"
            ),
        },
        "by_funnel_state": group_outcomes(enriched, "funnel_state", actionable_values=actionable_states),
        "by_primary_blocker": group_outcomes(enriched, "primary_blocker"),
        "by_decision_type": group_outcomes(enriched, "decision_type"),
        "by_entry_quality": group_outcomes(enriched, "entry_quality", actionable_values={"A+", "A", "B"}),
        "by_volume_state": group_outcomes(enriched, "volume_state"),
        "by_heat_state": group_outcomes(enriched, "heat_state"),
    }
    output["flags"] = _collect_flags(output)
    return output


def _collect_flags(artifact):
    flags = []
    for group_name in ["by_funnel_state", "by_primary_blocker", "by_decision_type", "by_entry_quality", "by_volume_state", "by_heat_state"]:
        for label, summary in artifact.get(group_name, {}).items():
            verdict = (summary.get("verdict") or {}).get("verdict")
            if verdict in {"risk_flag", "audit_needed_maybe_too_strict"}:
                flags.append({
                    "group": group_name,
                    "label": label,
                    "verdict": verdict,
                    "reason": (summary.get("verdict") or {}).get("reason"),
                    "sample_5d": (summary.get("5d") or {}).get("ready_sample"),
                    "avg_return_5d": (summary.get("5d") or {}).get("avg_return_pct"),
                    "win_rate_5d": (summary.get("5d") or {}).get("win_rate_pct"),
                })
    return flags


def default_dates(lookback_days):
    end = datetime.now().date()
    while end.weekday() >= 5:
        end -= timedelta(days=1)
    return end - timedelta(days=lookback_days), end


def main():
    parser = argparse.ArgumentParser(description="Read-only outcome audit for each v21 strategy rule/gate.")
    parser.add_argument("--start-date")
    parser.add_argument("--end-date")
    parser.add_argument("--stock-id", action="append")
    parser.add_argument("--version", default=VERSION)
    parser.add_argument("--output")
    parser.add_argument("--lookback-days", type=int, default=DEFAULT_LOOKBACK_DAYS)
    args = parser.parse_args()

    default_start, default_end = default_dates(args.lookback_days)
    end_date = parse_date(args.end_date) if args.end_date else default_end
    start_date = parse_date(args.start_date) if args.start_date else default_start
    warmup_start = start_date - timedelta(days=WARMUP_DAYS)
    stock_ids = [str(item) for item in (args.stock_id or WATCHLIST_CODES)]

    client = _client()
    rows_by_stock = {
        stock_id: fetch_daily_price_rows(client, stock_id, warmup_start, end_date)
        for stock_id in stock_ids
    }
    rows_by_stock = {stock_id: rows for stock_id, rows in rows_by_stock.items() if rows}
    events = replay_from_daily_price(rows_by_stock, start_date, end_date, version=args.version)
    artifact = summarize_rule_outcomes(events, rows_by_stock, start_date, end_date, args.version)

    text = json.dumps(artifact, ensure_ascii=False, indent=2, sort_keys=True)
    if args.output:
        output = Path(args.output)
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(text + "\n", encoding="utf-8")
    print(text)


if __name__ == "__main__":
    main()
