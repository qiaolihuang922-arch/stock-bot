#!/usr/bin/env python3
"""Read-only drift monitor for trend_continuation live outcomes."""

import argparse
import json
import sys
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts import research_trend_continuation as research

DEFAULT_ARTIFACT = ROOT / "reports" / "research" / "trend_continuation_20260603.json"
DEFAULT_ALERT_THRESHOLD_WIN_RATE = 0.45
DEFAULT_ALERT_AFTER_TRADES = 5


class MonitorBlocked(RuntimeError):
    def __init__(self, status, detail):
        super().__init__(detail)
        self.status = status
        self.detail = detail


def _num(value):
    try:
        if value in [None, ""]:
            return None
        return float(value)
    except (TypeError, ValueError):
        return None


def _load_backtest_baseline(path):
    try:
        payload = json.loads(Path(path).read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise MonitorBlocked("insufficient-data", f"missing backtest artifact: {path}") from exc
    except json.JSONDecodeError as exc:
        raise MonitorBlocked("source-error", f"invalid backtest artifact json: {path}") from exc

    for row in payload.get("groups") or []:
        if row.get("group") != "pullback_continuation":
            continue
        return {
            "win_rate_5d": _num(row.get("win_rate_5d")),
            "avg_return_5d": _num(row.get("avg_return_5d")),
            "sample_count": row.get("sample_count"),
        }
    raise MonitorBlocked("insufficient-data", "backtest artifact has no pullback_continuation group")


def _build_client(no_config=False, client_factory=None):
    try:
        url, key = research.resolve_read_credentials(skip_config=no_config)
    except research.ResearchBlocked as exc:
        raise MonitorBlocked("source-error", exc.detail or exc.reason) from exc
    if client_factory is None:
        try:
            from supabase import create_client
        except Exception as exc:
            raise MonitorBlocked("source-error", "supabase client unavailable") from exc
        client_factory = create_client
    return client_factory(url, key)


def _execute(query, table_name):
    try:
        result = query.execute()
    except Exception as exc:
        raise MonitorBlocked("source-error", f"{table_name} read failed") from exc
    return result.data or []


def _query_live_rows(client, trade_date=None, limit=200):
    signal_query = (
        client.table("daily_signal_snapshot")
        .select("stock_id,trade_date,version,action,decision,decision_type,setup_key")
    )
    if trade_date and hasattr(signal_query, "lte"):
        signal_query = signal_query.lte("trade_date", trade_date)
    if hasattr(signal_query, "order"):
        signal_query = signal_query.order("trade_date", desc=True)
    if hasattr(signal_query, "limit"):
        signal_query = signal_query.limit(limit)
    signals = _execute(signal_query, "daily_signal_snapshot")
    live_hits = [
        row for row in signals
        if (
            row.get("setup_key") == "trend_continuation"
            or row.get("decision_type") == "trend_continuation"
        )
        and str(row.get("action") or row.get("decision") or "").upper() == "BUY"
    ]
    if not live_hits:
        return [], []

    outcome_query = client.table("signal_outcomes").select(
        "stock_id,trade_date,strategy_version,horizon_days,close_return,return_5d,outcome_label"
    )
    if hasattr(outcome_query, "eq"):
        outcome_query = outcome_query.eq("horizon_days", 5)
    outcomes = _execute(outcome_query, "signal_outcomes")
    return live_hits, outcomes


def _outcome_return(row):
    value = _num(row.get("return_5d"))
    if value is None:
        value = _num(row.get("close_return"))
    return value


def _match_outcomes(live_hits, outcomes):
    hit_keys = {
        (str(row.get("stock_id")), str(row.get("trade_date")), str(row.get("version") or ""))
        for row in live_hits
    }
    matched = []
    for row in outcomes:
        key = (
            str(row.get("stock_id")),
            str(row.get("trade_date")),
            str(row.get("strategy_version") or row.get("version") or ""),
        )
        loose_key = (key[0], key[1], "")
        if key not in hit_keys and loose_key not in hit_keys:
            continue
        value = _outcome_return(row)
        if value is None:
            continue
        matched.append({**row, "_return_5d": value})
    return matched


def _consecutive_below_threshold(matched, threshold):
    count = 0
    for row in reversed(matched):
        if row["_return_5d"] > 0:
            break
        count += 1
    return count if count else 0


def base_output(args, baseline):
    return {
        "status": "ok",
        "trade_date": args.trade_date,
        "source": "production-read-only",
        "setup_key": "trend_continuation",
        "live_hit_count": 0,
        "evaluated_trade_count": 0,
        "live_win_rate_5d": None,
        "backtest_win_rate_5d": baseline["win_rate_5d"],
        "backtest_avg_return_5d": baseline["avg_return_5d"],
        "win_rate_diff": None,
        "consecutive_below_threshold": 0,
        "alert_threshold_win_rate": args.alert_threshold_win_rate,
        "alert_after_trades": args.alert_after_trades,
        "alert": False,
    }


def run_monitor(args, client=None):
    baseline = _load_backtest_baseline(args.artifact)
    output = base_output(args, baseline)
    if client is None:
        client = _build_client(no_config=args.no_config)

    live_hits, outcomes = _query_live_rows(client, trade_date=args.trade_date, limit=args.limit)
    output["live_hit_count"] = len(live_hits)
    if not live_hits:
        output["status"] = "insufficient-data"
        output["detail"] = "no production trend_continuation BUY hits found"
        return output

    matched = _match_outcomes(live_hits, outcomes)
    output["evaluated_trade_count"] = len(matched)
    if not matched:
        output["status"] = "insufficient-data"
        output["detail"] = "trend_continuation live hits exist but no 5d outcome source matched"
        return output

    wins = sum(1 for row in matched if row["_return_5d"] > 0)
    live_win_rate = wins / len(matched)
    output["live_win_rate_5d"] = live_win_rate
    output["win_rate_diff"] = (
        live_win_rate - baseline["win_rate_5d"]
        if baseline["win_rate_5d"] is not None
        else None
    )
    output["consecutive_below_threshold"] = _consecutive_below_threshold(
        matched,
        args.alert_threshold_win_rate,
    )
    output["alert"] = (
        len(matched) >= args.alert_after_trades
        and live_win_rate < args.alert_threshold_win_rate
        and output["consecutive_below_threshold"] >= args.alert_after_trades
    )
    output["status"] = "alert" if output["alert"] else "ok"
    return output


def parse_args(argv=None):
    parser = argparse.ArgumentParser(description="Read-only trend_continuation monitor")
    parser.add_argument("--trade-date", default=date.today().isoformat())
    parser.add_argument("--artifact", default=str(DEFAULT_ARTIFACT), help="Existing trend_continuation research JSON artifact")
    parser.add_argument("--alert-threshold-win-rate", type=float, default=DEFAULT_ALERT_THRESHOLD_WIN_RATE)
    parser.add_argument("--alert-after-trades", type=int, default=DEFAULT_ALERT_AFTER_TRADES, help="Consecutive completed trades below threshold before alerting")
    parser.add_argument("--limit", type=int, default=200)
    parser.add_argument("--no-config", action="store_true", help="Only read environment credentials; fail closed if absent")
    return parser.parse_args(argv)


def main(argv=None):
    args = parse_args(argv)
    try:
        output = run_monitor(args)
        code = 0 if output["status"] in {"ok", "insufficient-data"} else 2
    except MonitorBlocked as exc:
        baseline = {"win_rate_5d": None, "avg_return_5d": None}
        try:
            baseline = _load_backtest_baseline(args.artifact)
        except MonitorBlocked:
            pass
        output = base_output(args, baseline)
        output["status"] = exc.status
        output["detail"] = exc.detail
        code = 2
    print(json.dumps(output, ensure_ascii=False, indent=2, sort_keys=True))
    return code


if __name__ == "__main__":
    raise SystemExit(main())
