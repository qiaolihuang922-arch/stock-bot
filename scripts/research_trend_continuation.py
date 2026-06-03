#!/usr/bin/env python3
"""Read-only production DB research for pullback trend continuation.

This script reads historical OHLCV rows from ``daily_price`` and computes
candidate outcomes locally. It never sends Telegram and never mutates DB state.
"""

import argparse
import json
import os
import sys
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

REQUIRED_COLUMNS = ["stock_id", "trade_date", "open", "high", "low", "close", "volume"]
HORIZONS = [1, 3, 5, 10]
EXTENDED_LEVELS = [1.08, 1.15, 1.22]
DEFAULT_MIN_SAMPLE = 30


class ResearchBlocked(RuntimeError):
    def __init__(self, reason, detail=""):
        super().__init__(detail or reason)
        self.reason = reason
        self.detail = detail


@dataclass
class Bar:
    stock_id: str
    trade_date: str
    open: float
    high: float
    low: float
    close: float
    volume: float


def _num(value):
    try:
        if value in [None, ""]:
            return None
        return float(value)
    except (TypeError, ValueError):
        return None


def _avg(values):
    values = [item for item in values if item is not None]
    return sum(values) / len(values) if values else None


def _pct(current, base):
    if current is None or not base:
        return None
    return (current - base) / base


def _fmt_pct(value):
    if value is None:
        return "n/a"
    return f"{value * 100:.2f}%"


def _fmt_num(value):
    if value is None:
        return "n/a"
    return f"{value:.4f}"


def _load_config_module(skip_config=False):
    if skip_config:
        return None
    try:
        import config
    except Exception:
        return None
    return config


def _config_value(config_module, name):
    if config_module is None:
        return ""
    return getattr(config_module, name, "") or ""


def resolve_read_credentials(env=None, config_module=None, skip_config=False):
    source = env if env is not None else os.environ
    config_source = config_module
    if config_source is None:
        config_source = _load_config_module(skip_config=skip_config)

    url = source.get("SUPABASE_URL") or _config_value(config_source, "SUPABASE_URL")
    key = (
        source.get("SUPABASE_READONLY_KEY")
        or source.get("SUPABASE_KEY")
        or _config_value(config_source, "SUPABASE_READONLY_KEY")
        or _config_value(config_source, "SUPABASE_KEY")
    )

    missing = []
    if not url:
        missing.append("SUPABASE_URL")
    if not key:
        missing.append("SUPABASE_READONLY_KEY|SUPABASE_KEY")
    if missing:
        raise ResearchBlocked(
            "missing-production-db-credentials",
            "missing required Supabase read credentials: " + ",".join(missing),
        )
    return url, key


def build_supabase_client(env=None, config_module=None, skip_config=False, client_factory=None):
    url, key = resolve_read_credentials(env, config_module, skip_config)
    if client_factory is None:
        try:
            from supabase import create_client
        except Exception as exc:
            raise ResearchBlocked("source-error", "supabase client unavailable") from exc
        client_factory = create_client
    return client_factory(url, key)


def _classify_source_error(exc):
    text = str(exc).lower()
    if "could not find the table" in text or "missing table" in text:
        return "missing-table"
    if "column" in text or "schema cache" in text:
        return "missing-column"
    return "source-error"


def fetch_daily_price_rows(client, page_size=1000, max_rows=200000):
    rows = []
    start = 0
    try:
        while len(rows) < max_rows:
            end = min(start + page_size - 1, max_rows - 1)
            result = (
                client.table("daily_price")
                .select(",".join(REQUIRED_COLUMNS))
                .order("trade_date")
                .range(start, end)
                .execute()
            )
            page = result.data or []
            rows.extend(page)
            if len(page) < page_size:
                break
            start += page_size
    except Exception as exc:
        raise ResearchBlocked(_classify_source_error(exc), "daily_price read failed") from exc

    if not rows:
        raise ResearchBlocked("insufficient-data", "daily_price returned no rows")
    return rows


def normalize_bars(rows):
    bars = []
    missing_columns = set()
    bad_rows = 0
    for row in rows:
        for column in REQUIRED_COLUMNS:
            if column not in row:
                missing_columns.add(column)
        if missing_columns:
            continue
        values = {column: _num(row.get(column)) for column in ["open", "high", "low", "close", "volume"]}
        if any(value is None for value in values.values()):
            bad_rows += 1
            continue
        stock_id = str(row.get("stock_id") or "").strip()
        trade_date = str(row.get("trade_date") or "").strip()
        if not stock_id or not trade_date:
            bad_rows += 1
            continue
        bars.append(Bar(stock_id=stock_id, trade_date=trade_date, **values))

    if missing_columns:
        raise ResearchBlocked("missing-column", "daily_price missing columns: " + ",".join(sorted(missing_columns)))
    if not bars:
        raise ResearchBlocked("insufficient-data", f"no usable OHLCV rows; bad_rows={bad_rows}")
    return bars


def _series_metrics(series, index):
    closes = [bar.close for bar in series]
    volumes = [bar.volume for bar in series]
    if index < 20:
        return None
    close_window = closes[: index + 1]
    volume_window = volumes[: index + 1]
    ma5 = _avg(close_window[-5:])
    ma10 = _avg(close_window[-10:])
    ma20 = _avg(close_window[-20:])
    vol_ma5 = _avg(volume_window[-5:])
    vol_ratio = series[index].volume / vol_ma5 if vol_ma5 else None
    net_10d = _pct(series[index].close, series[index - 10].close) if index >= 10 else None
    return {
        "ma5": ma5,
        "ma10": ma10,
        "ma20": ma20,
        "vol_ma5": vol_ma5,
        "vol_ratio": vol_ratio,
        "net_10d": net_10d,
    }


def _is_trend(series, index, metrics):
    bar = series[index]
    return bool(
        metrics
        and metrics["ma20"]
        and metrics["ma5"]
        and metrics["net_10d"] is not None
        and bar.close > metrics["ma20"]
        and metrics["ma5"] > metrics["ma20"]
        and metrics["net_10d"] > 0
    )


def _touches_without_breaking(bar, ma_value):
    if not ma_value:
        return False
    return ma_value * 0.99 <= bar.low <= ma_value * 1.01


def is_pullback_continuation(series, index, metrics_by_index):
    entry_metrics = metrics_by_index.get(index)
    if not _is_trend(series, index, entry_metrics):
        return False
    entry = series[index]
    if not entry_metrics["ma5"] or entry.close <= entry_metrics["ma5"]:
        return False
    if entry_metrics["vol_ratio"] is None or entry_metrics["vol_ratio"] < 1:
        return False

    for pullback_index in range(max(20, index - 3), index):
        pullback_metrics = metrics_by_index.get(pullback_index)
        if not _is_trend(series, pullback_index, pullback_metrics):
            continue
        pullback = series[pullback_index]
        previous = series[pullback_index - 1]
        touched = (
            _touches_without_breaking(pullback, pullback_metrics["ma5"])
            or _touches_without_breaking(pullback, pullback_metrics["ma10"])
        )
        volume_contracts = (
            pullback_metrics["vol_ma5"] is not None
            and pullback.volume < pullback_metrics["vol_ma5"]
        )
        price_pulls_back = pullback.close <= previous.close
        if touched and volume_contracts and price_pulls_back:
            return True
    return False


def is_extended_spike(series, index, metrics, level):
    return bool(
        _is_trend(series, index, metrics)
        and metrics["ma20"]
        and series[index].close / metrics["ma20"] >= level
    )


def _event_outcome(series, index):
    entry = series[index]
    future = series[index + 1 : index + 11]
    if len(future) < 10:
        return None
    outcome = {
        "mfe": _pct(max(bar.high for bar in future), entry.close),
        "mae": _pct(min(bar.low for bar in future), entry.close),
    }
    for horizon in HORIZONS:
        outcome[f"return_{horizon}d"] = _pct(series[index + horizon].close, entry.close)
    return outcome


def collect_events(bars):
    by_stock = defaultdict(list)
    for bar in bars:
        by_stock[bar.stock_id].append(bar)
    events = defaultdict(list)
    for stock_id, series in by_stock.items():
        series.sort(key=lambda item: item.trade_date)
        metrics_by_index = {
            index: _series_metrics(series, index)
            for index in range(len(series))
        }
        for index in range(20, len(series) - 10):
            outcome = _event_outcome(series, index)
            if outcome is None:
                continue
            base_event = {
                "stock_id": stock_id,
                "trade_date": series[index].trade_date,
                **outcome,
            }
            metrics = metrics_by_index[index]
            if is_pullback_continuation(series, index, metrics_by_index):
                events[("pullback_continuation", None)].append(base_event)
            for level in EXTENDED_LEVELS:
                if is_extended_spike(series, index, metrics, level):
                    events[("extended_spike", level)].append(base_event)
    return events


def summarize_group(group, level, group_events, min_sample=DEFAULT_MIN_SAMPLE):
    summary = {
        "group": group,
        "extended_level": level,
        "sample_count": len(group_events),
        "mfe": _avg([event.get("mfe") for event in group_events]),
        "mae": _avg([event.get("mae") for event in group_events]),
    }
    for horizon in HORIZONS:
        returns = [event.get(f"return_{horizon}d") for event in group_events]
        returns = [item for item in returns if item is not None]
        summary[f"win_rate_{horizon}d"] = (
            sum(1 for item in returns if item > 0) / len(returns)
            if returns
            else None
        )
        summary[f"avg_return_{horizon}d"] = _avg(returns)

    h5_win = summary["win_rate_5d"]
    h5_avg = summary["avg_return_5d"]
    if len(group_events) < min_sample:
        conclusion = "insufficient-data"
    elif h5_win is not None and h5_avg is not None and h5_win > 0.5 and h5_avg > 0:
        conclusion = "positive"
    else:
        conclusion = "negative"
    summary["conclusion"] = conclusion
    return summary


def summarize_events(events, min_sample=DEFAULT_MIN_SAMPLE):
    rows = [
        summarize_group(
            "pullback_continuation",
            None,
            events.get(("pullback_continuation", None), []),
            min_sample,
        )
    ]
    for level in EXTENDED_LEVELS:
        rows.append(
            summarize_group(
                "extended_spike",
                level,
                events.get(("extended_spike", level), []),
                min_sample,
            )
        )
    return rows


def _summary_lookup(rows, group, level=None):
    for row in rows:
        if row["group"] == group and row["extended_level"] == level:
            return row
    return {}


def build_report(rows, source_rows, min_sample=DEFAULT_MIN_SAMPLE):
    pullback = _summary_lookup(rows, "pullback_continuation")
    status = "completed"
    edge = pullback.get("conclusion") or "insufficient-data"
    if edge == "positive":
        reason_prefix = "pullback continuation shows positive 5d edge"
    elif edge == "negative":
        reason_prefix = "pullback continuation does not clear 5d edge checks"
    else:
        reason_prefix = "pullback continuation sample is below minimum"
    return {
        "title": "research_trend_continuation",
        "source": "production-db-readonly",
        "status": status,
        "source_table": "daily_price",
        "source_rows": source_rows,
        "min_sample": min_sample,
        "groups": rows,
        "conclusion": {
            "pullback_continuation_edge": edge,
            "reason": (
                f"{reason_prefix}; "
                f"win_rate_5d={_fmt_pct(pullback.get('win_rate_5d'))}, "
                f"avg_return_5d={_fmt_pct(pullback.get('avg_return_5d'))}, "
                f"sample_count={pullback.get('sample_count', 0)}"
            ),
        },
    }


def blocked_report(reason, detail=""):
    return {
        "title": "research_trend_continuation",
        "status": "blocked",
        "reason": reason,
        "detail": detail,
        "no_synthetic_data": True,
    }


def render_report(report):
    if report.get("status") == "blocked":
        lines = [
            "research_trend_continuation",
            "status: blocked",
            f"reason: {report.get('reason')}",
            "no_synthetic_data: true",
        ]
        if report.get("detail"):
            lines.append(f"detail: {report['detail']}")
        return "\n".join(lines)

    lines = [
        "research_trend_continuation",
        "source: production-db-readonly",
        "status: completed",
        "",
        (
            "group                    level   n    h1_win h1_avg h3_win h3_avg "
            "h5_win h5_avg h10_win h10_avg mfe   mae"
        ),
    ]
    for row in report["groups"]:
        level = "none" if row["extended_level"] is None else f"{row['extended_level']:.2f}"
        lines.append(
            f"{row['group']:<24} {level:<7} {row['sample_count']:<4} "
            f"{_fmt_pct(row['win_rate_1d']):<6} {_fmt_pct(row['avg_return_1d']):<6} "
            f"{_fmt_pct(row['win_rate_3d']):<6} {_fmt_pct(row['avg_return_3d']):<6} "
            f"{_fmt_pct(row['win_rate_5d']):<6} {_fmt_pct(row['avg_return_5d']):<6} "
            f"{_fmt_pct(row['win_rate_10d']):<7} {_fmt_pct(row['avg_return_10d']):<7} "
            f"{_fmt_pct(row['mfe']):<5} {_fmt_pct(row['mae']):<5}"
        )
    lines.extend(
        [
            "",
            "conclusion:",
            f"pullback_continuation_edge: {report['conclusion']['pullback_continuation_edge']}",
            f"reason: {report['conclusion']['reason']}",
        ]
    )
    return "\n".join(lines)


def run_research(args, client=None):
    if client is None:
        client = build_supabase_client(skip_config=args.no_config)
    source_rows = fetch_daily_price_rows(client, args.page_size, args.max_rows)
    bars = normalize_bars(source_rows)
    events = collect_events(bars)
    summaries = summarize_events(events, args.min_sample)
    return build_report(summaries, len(source_rows), args.min_sample)


def parse_args(argv=None):
    parser = argparse.ArgumentParser(description="Read-only trend continuation research")
    parser.add_argument("--page-size", type=int, default=1000)
    parser.add_argument("--max-rows", type=int, default=200000)
    parser.add_argument("--min-sample", type=int, default=DEFAULT_MIN_SAMPLE)
    parser.add_argument("--json", action="store_true", help="Print machine-readable JSON")
    parser.add_argument(
        "--no-config",
        action="store_true",
        help="Only read environment credentials; useful for fail-closed QA probes.",
    )
    return parser.parse_args(argv)


def main(argv=None):
    args = parse_args(argv)
    try:
        report = run_research(args)
    except ResearchBlocked as exc:
        report = blocked_report(exc.reason, exc.detail)
        print(json.dumps(report, ensure_ascii=False, indent=2) if args.json else render_report(report))
        return 2

    print(json.dumps(report, ensure_ascii=False, indent=2) if args.json else render_report(report))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
