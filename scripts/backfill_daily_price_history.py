#!/usr/bin/env python3
"""Approved daily_price history backfill CLI.

The script plans and optionally writes complete OHLCV rows to ``daily_price``.
It uses the existing Supabase upsert contract for ``stock_id,trade_date`` and
never writes during dry-run.
"""

import argparse
import json
import os
import sys
from datetime import date, datetime, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from core.watchlist import WATCHLIST_CODES
from scripts.backfill_signals import upsert_rows as approved_upsert_rows
from services.stock_api import get_twse_ohlcv_history

APPROVED_WRITE_INTERFACE = "scripts.backfill_signals.upsert_rows(price_rows, signal_rows=[], client=...)"
REQUIRED_FIELDS = ["stock_id", "trade_date", "open", "high", "low", "close", "volume", "source"]


class BackfillBlocked(RuntimeError):
    def __init__(self, reason, detail=""):
        super().__init__(detail or reason)
        self.reason = reason
        self.detail = detail


def parse_date(value):
    try:
        return datetime.strptime(value, "%Y-%m-%d").date()
    except (TypeError, ValueError) as exc:
        raise BackfillBlocked("source-error", f"invalid date: {value}") from exc


def resolve_date_range(args, today=None):
    today = today or date.today()
    end = parse_date(args.end) if args.end else today
    if args.start:
        start = parse_date(args.start)
    else:
        start = end - timedelta(days=max(1, args.years) * 365)
    if start > end:
        raise BackfillBlocked("source-error", "start must be <= end")
    return start, end


def resolve_symbols(symbols_text=None):
    if symbols_text:
        symbols = [item.strip() for item in symbols_text.split(",") if item.strip()]
    else:
        symbols = [str(item) for item in WATCHLIST_CODES if item]
        if len(symbols) != 12:
            raise BackfillBlocked("universe-not-12", f"resolved universe_count={len(symbols)}")
    deduped = []
    for symbol in symbols:
        if symbol not in deduped:
            deduped.append(symbol)
    if not deduped:
        raise BackfillBlocked("missing-watchlist-source", "no symbols resolved")
    return deduped


def _load_config_module(skip_config=False):
    if skip_config:
        return None
    try:
        import config
    except Exception:
        return None
    return config


def _config_value(config_module, name):
    return getattr(config_module, name, "") if config_module is not None else ""


def resolve_supabase_credentials(env=None, config_module=None, skip_config=False):
    source = env if env is not None else os.environ
    config_source = config_module
    if config_source is None:
        config_source = _load_config_module(skip_config=skip_config)
    url = source.get("SUPABASE_URL") or _config_value(config_source, "SUPABASE_URL")
    key = (
        source.get("SUPABASE_KEY")
        or source.get("SUPABASE_SERVICE_ROLE_KEY")
        or _config_value(config_source, "SUPABASE_KEY")
        or _config_value(config_source, "SUPABASE_SERVICE_ROLE_KEY")
    )
    missing = []
    if not url:
        missing.append("SUPABASE_URL")
    if not key:
        missing.append("SUPABASE_KEY|SUPABASE_SERVICE_ROLE_KEY")
    if missing:
        raise BackfillBlocked("missing-credentials", "missing required Supabase credentials: " + ",".join(missing))
    return url, key


def build_supabase_client(env=None, config_module=None, skip_config=False, client_factory=None):
    url, key = resolve_supabase_credentials(env, config_module, skip_config)
    if client_factory is None:
        try:
            from supabase import create_client
        except Exception as exc:
            raise BackfillBlocked("source-error", "supabase client unavailable") from exc
        client_factory = create_client
    return client_factory(url, key)


def _date_text(value):
    return value.isoformat() if hasattr(value, "isoformat") else str(value)


def normalize_market_rows(rows):
    normalized = []
    for row in rows or []:
        clean = dict(row)
        clean["stock_id"] = str(clean.get("stock_id") or "").strip()
        clean["trade_date"] = _date_text(clean.get("trade_date"))
        if not all(clean.get(field) not in [None, ""] for field in REQUIRED_FIELDS):
            continue
        normalized.append({field: clean[field] for field in REQUIRED_FIELDS})
    return sorted(normalized, key=lambda item: (item["stock_id"], item["trade_date"]))


def fetch_existing_daily_price(client, symbols, start_date, end_date):
    try:
        query = client.table("daily_price").select("stock_id,trade_date")
        if hasattr(query, "in_"):
            query = query.in_("stock_id", list(symbols))
        if hasattr(query, "gte"):
            query = query.gte("trade_date", start_date.isoformat())
        if hasattr(query, "lte"):
            query = query.lte("trade_date", end_date.isoformat())
        result = query.execute()
    except Exception as exc:
        raise BackfillBlocked("daily-price-read-error", "daily_price existing-row read failed") from exc
    return {
        (str(row.get("stock_id")), str(row.get("trade_date")))
        for row in (result.data or [])
        if row.get("stock_id") and row.get("trade_date")
    }


def load_market_rows(symbols, start_date, end_date, loader=get_twse_ohlcv_history):
    by_symbol = {}
    errors = {}
    for symbol in symbols:
        try:
            rows = normalize_market_rows(loader(symbol, start_date, end_date))
        except Exception as exc:
            rows = []
            errors[symbol] = str(exc)
        if not rows and symbol not in errors:
            errors[symbol] = "empty source rows"
        by_symbol[symbol] = rows
    return by_symbol, errors


def build_plan(symbols, start_date, end_date, market_rows_by_symbol, existing_keys=None, skip_existing=True):
    existing_keys = existing_keys or set()
    rows_to_write = []
    per_symbol = []
    for symbol in symbols:
        rows = market_rows_by_symbol.get(symbol, [])
        existing_for_symbol = {
            key for key in existing_keys
            if key[0] == symbol
        }
        write_rows = [
            row for row in rows
            if not (skip_existing and (row["stock_id"], row["trade_date"]) in existing_keys)
        ]
        rows_to_write.extend(write_rows)
        per_symbol.append(
            {
                "symbol": symbol,
                "planned_rows": len(rows),
                "existing_rows": len(existing_for_symbol),
                "rows_to_write": len(write_rows),
                "skipped_rows": len(rows) - len(write_rows),
            }
        )
    return {
        "date_range": {"start": start_date.isoformat(), "end": end_date.isoformat()},
        "per_symbol": per_symbol,
        "rows_to_write": rows_to_write,
    }


def upsert_daily_price_rows(client, rows):
    if not rows:
        return 0
    approved_upsert_rows(rows, [], client=client)
    return len(rows)


def read_after_write(client, symbols, start_date, end_date):
    keys = fetch_existing_daily_price(client, symbols, start_date, end_date)
    per_symbol = []
    for symbol in symbols:
        dates = sorted(key[1] for key in keys if key[0] == symbol)
        per_symbol.append(
            {
                "symbol": symbol,
                "row_count": len(dates),
                "min_trade_date": dates[0] if dates else None,
                "max_trade_date": dates[-1] if dates else None,
            }
        )
    return {
        "status": "ok" if all(item["row_count"] > 0 for item in per_symbol) else "fail",
        "per_symbol": per_symbol,
    }


def blocked_report(reason, detail=""):
    return {
        "status": "blocked",
        "fail_closed_reason": reason,
        "detail": detail,
        "approved_write_path": APPROVED_WRITE_INTERFACE,
        "live_write": False,
    }


def build_report(args, client=None, market_loader=get_twse_ohlcv_history):
    symbols = resolve_symbols(args.symbols)
    start_date, end_date = resolve_date_range(args)
    mode = "write" if args.write else "dry-run"
    client_required = args.write or args.read_after_write
    if client_required and client is None:
        client = build_supabase_client(skip_config=args.no_config)

    existing_keys = set()
    if client is not None:
        existing_keys = fetch_existing_daily_price(client, symbols, start_date, end_date)

    market_rows_by_symbol, source_errors = load_market_rows(symbols, start_date, end_date, market_loader)
    source_status = "ok" if not source_errors else "source-error"
    plan = build_plan(symbols, start_date, end_date, market_rows_by_symbol, existing_keys, args.skip_existing)
    report = {
        "mode": mode,
        "result": "no-write" if not args.write else "pending-write",
        "source": "daily_price_history_backfill",
        "market_data_source": {"name": "twse", "status": source_status, "errors": source_errors},
        "approved_write_path": APPROVED_WRITE_INTERFACE,
        "universe_symbols": symbols,
        "universe_count": len(symbols),
        "requested_date_range": plan["date_range"],
        "skip_existing": bool(args.skip_existing),
        "per_symbol": plan["per_symbol"],
        "read_after_write": "not-run",
        "live_write": False,
    }
    if source_errors:
        report.update(blocked_report("source-error", "market data source returned errors"))
        report["mode"] = mode
        report["market_data_source"] = {"name": "twse", "status": source_status, "errors": source_errors}
        report["universe_symbols"] = symbols
        report["universe_count"] = len(symbols)
        report["requested_date_range"] = plan["date_range"]
        report["per_symbol"] = plan["per_symbol"]
        return report, 2
    if not args.write:
        return report, 0
    if not args.confirm_write:
        report.update(blocked_report("missing-approved-write-confirmation", "write requires --confirm-write"))
        report["mode"] = mode
        report["universe_symbols"] = symbols
        report["universe_count"] = len(symbols)
        report["requested_date_range"] = plan["date_range"]
        report["per_symbol"] = plan["per_symbol"]
        return report, 2

    written = upsert_daily_price_rows(client, plan["rows_to_write"])
    report["result"] = "write-complete"
    report["rows_written"] = written
    report["live_write"] = True
    if args.read_after_write:
        smoke = read_after_write(client, symbols, start_date, end_date)
        report["read_after_write"] = smoke
        if smoke["status"] != "ok":
            report["status"] = "blocked"
            report["fail_closed_reason"] = "daily-price-read-error"
            return report, 2
    return report, 0


def parse_args(argv=None):
    parser = argparse.ArgumentParser(description="Backfill daily_price OHLCV history through approved upsert path")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--write", action="store_true")
    parser.add_argument("--confirm-write", action="store_true")
    parser.add_argument("--symbols", help="Comma-separated symbols; default resolves core.watchlist 12")
    parser.add_argument("--start", help="Inclusive start date YYYY-MM-DD")
    parser.add_argument("--end", help="Inclusive end date YYYY-MM-DD")
    parser.add_argument("--years", type=int, default=1)
    parser.add_argument("--skip-existing", action="store_true")
    parser.add_argument("--read-after-write", action="store_true")
    parser.add_argument("--no-config", action="store_true")
    args = parser.parse_args(argv)
    if args.write and args.dry_run:
        raise BackfillBlocked("source-error", "choose only one of --dry-run or --write")
    if not args.write and not args.dry_run:
        args.dry_run = True
    return args


def main(argv=None):
    try:
        args = parse_args(argv)
        report, exit_code = build_report(args)
    except BackfillBlocked as exc:
        report = blocked_report(exc.reason, exc.detail)
        exit_code = 2
    print(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True))
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
