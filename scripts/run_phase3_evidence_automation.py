#!/usr/bin/env python3
"""Scheduled Phase 3 evidence writer without live Telegram delivery."""

import argparse
import json
import subprocess
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path

try:
    from zoneinfo import ZoneInfo
except ImportError:
    ZoneInfo = None

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

TAIPEI = ZoneInfo("Asia/Taipei") if ZoneInfo else timezone.utc
AFTER_CLOSE_HOUR = 13
AFTER_CLOSE_MINUTE = 20
STALE_ALERT_THRESHOLD_DAYS = 2


def parse_now(value=None):
    if not value:
        return datetime.now(TAIPEI)
    parsed = datetime.fromisoformat(value)
    if parsed.tzinfo is None:
        return parsed.replace(tzinfo=TAIPEI)
    return parsed.astimezone(TAIPEI)


def is_after_close_window(now):
    return now.hour > AFTER_CLOSE_HOUR or (
        now.hour == AFTER_CLOSE_HOUR and now.minute >= AFTER_CLOSE_MINUTE
    )


def confirm_trading_day(trading_day, fetch_index_rows=None):
    from scripts.backfill_market_theme_sources import build_index_rows, fetch_twse_historical_index_rows

    try:
        fetcher = fetch_index_rows or fetch_twse_historical_index_rows
        index_rows = build_index_rows(fetcher(trading_day), trade_date=trading_day)
    except Exception as exc:
        return {
            "confirmed": False,
            "reason": "not-confirmed-trading-day",
            "source": "twse_official_mi_index",
            "source_status": "source-error",
            "error": str(exc),
        }

    if not index_rows:
        return {
            "confirmed": False,
            "reason": "not-confirmed-trading-day",
            "source": "twse_official_mi_index",
            "source_status": "missing-source",
        }

    return {
        "confirmed": True,
        "reason": "confirmed-trading-day",
        "source": "twse_official_mi_index",
        "source_status": "available",
    }


def should_run_evidence_writes(now, trading_day_checker=None):
    if now.weekday() >= 5:
        return False, "non_trading_day"
    if not is_after_close_window(now):
        return False, "before_after_close_window"
    trading_day = now.date().isoformat()
    checker = trading_day_checker or confirm_trading_day
    status = checker(trading_day)
    if not status.get("confirmed"):
        return False, "not-confirmed-trading-day"
    return True, "after_close_trading_day"


def emit(line):
    print(line, flush=True)


def _entry_is_confirmed_trading_day(entry, trading_day_checker=None):
    trade_date = str(entry.get("trade_date") or "")
    try:
        entry_date = datetime.fromisoformat(trade_date).date()
    except ValueError:
        return False
    if entry_date.weekday() >= 5:
        return False
    if trading_day_checker:
        return bool(trading_day_checker(trade_date).get("confirmed"))
    return entry.get("trading_day_confirmed") is True


def build_stale_alerts(source_history, threshold=STALE_ALERT_THRESHOLD_DAYS, trading_day_checker=None):
    alerts = []
    for source, entries in sorted((source_history or {}).items()):
        consecutive = 0
        last_status = ""
        for entry in sorted(entries or [], key=lambda item: str(item.get("trade_date") or "")):
            if not _entry_is_confirmed_trading_day(entry, trading_day_checker):
                continue
            status = str(entry.get("status") or "").lower()
            if status in {"stale", "unavailable"}:
                consecutive += 1
                last_status = status
            else:
                consecutive = 0
                last_status = status
        if consecutive >= threshold:
            alerts.append(
                {
                    "source": source,
                    "consecutive_days": consecutive,
                    "status": last_status,
                    "action": "fail_closed",
                }
            )
    return alerts


def emit_stale_alerts(source_history):
    for alert in build_stale_alerts(source_history):
        emit(
            "EVIDENCE_STALE_ALERT "
            f"source={alert['source']} "
            f"consecutive_days={alert['consecutive_days']} "
            f"status={alert['status']} "
            f"action={alert['action']}"
        )


def run_daily_signal_snapshot(trading_day, report_generator=None, client_factory=None):
    from core.generator import VERSION, generate_report
    from core.watchlist import WATCHLIST_CODES
    from services.daily_snapshot_store import (
        get_supabase_client,
        read_daily_signal_snapshot_status,
    )

    generator = report_generator or generate_report
    result = generator(return_write_results=True)
    write_results = result[2] if isinstance(result, tuple) and len(result) >= 3 else {}
    snapshot_result = write_results.get("daily_signal_snapshot") or {}
    if not snapshot_result.get("recorded"):
        reason = snapshot_result.get("reason") or "source-error"
        emit(
            "EVIDENCE_WRITE_FAILED "
            f"source=daily_signal_snapshot trading_day={trading_day} "
            f"status={reason} action=fail_closed"
        )
        return 2

    client = client_factory() if client_factory else get_supabase_client()
    status = read_daily_signal_snapshot_status(
        client,
        trading_day,
        VERSION,
        expected_stock_ids=WATCHLIST_CODES,
    )
    if status["read_after_write"] != "ok":
        emit(
            "EVIDENCE_WRITE_FAILED "
            f"source=daily_signal_snapshot trading_day={trading_day} "
            "read_after_write=fail action=fail_closed"
        )
        return 2

    emit(
        "EVIDENCE_WRITE_CONFIRMED "
        f"source=daily_signal_snapshot trading_day={trading_day} "
        f"rows={status['row_count']} read_after_write=ok"
    )
    return 0


def _twse_confirmed_rows_payload(trading_day):
    from scripts.backfill_market_theme_sources import (
        build_source_payloads,
        fetch_twse_historical_breadth_rows,
        fetch_twse_historical_index_rows,
        fetch_twse_company_profiles,
    )

    payloads = build_source_payloads(
        fetch_twse_historical_index_rows(trading_day),
        fetch_twse_historical_breadth_rows(trading_day),
        fetch_twse_company_profiles(),
        trade_date=trading_day,
    )
    if payloads.get("status") != "ready" or not payloads.get("confirmed_rows"):
        raise RuntimeError(payloads.get("reason") or "missing-source")
    return payloads["confirmed_rows"]


def run_market_theme_confirmed_evidence(trading_day, payload_path=None, runner=None):
    runner = runner or subprocess.run
    with tempfile.TemporaryDirectory() as tmpdir:
        if payload_path:
            path = Path(payload_path)
        else:
            path = Path(tmpdir) / "market_theme_confirmed_evidence_payload.json"
            path.write_text(
                json.dumps(_twse_confirmed_rows_payload(trading_day), ensure_ascii=False),
                encoding="utf-8",
            )
        completed = runner(
            [
                sys.executable,
                str(ROOT / "scripts" / "write_market_theme_confirmed_evidence.py"),
                "--payload",
                str(path),
                "--execute",
            ],
            cwd=ROOT,
            text=True,
            capture_output=True,
            check=False,
        )

    if completed.stdout:
        print(completed.stdout, end="" if completed.stdout.endswith("\n") else "\n")
    if completed.stderr:
        print(completed.stderr, file=sys.stderr, end="" if completed.stderr.endswith("\n") else "\n")

    if completed.returncode != 0:
        emit(
            "EVIDENCE_WRITE_FAILED "
            f"source=market_theme_confirmed_evidence trading_day={trading_day} "
            "action=fail_closed"
        )
        return completed.returncode

    emit(
        "EVIDENCE_WRITE_CONFIRMED "
        f"source=market_theme_confirmed_evidence trading_day={trading_day} "
        "read_after_write=ok"
    )
    return 0


def main(argv=None):
    parser = argparse.ArgumentParser(description="Run scheduled Phase 3 evidence production.")
    parser.add_argument("--now", help="Asia/Taipei ISO timestamp for probes.")
    parser.add_argument("--market-theme-payload", help="Approved market/theme payload JSON for tests or manual runs.")
    parser.add_argument("--stale-status-json", help="JSON source status history for stale alert probes.")
    args = parser.parse_args(argv)

    now = parse_now(args.now)
    trading_day = now.date().isoformat()
    should_run, reason = should_run_evidence_writes(now)

    if args.stale_status_json:
        emit_stale_alerts(json.loads(Path(args.stale_status_json).read_text(encoding="utf-8")))

    if not should_run:
        for source in ("daily_signal_snapshot", "market_theme_confirmed_evidence"):
            emit(f"EVIDENCE_WRITE_SKIPPED source={source} trading_day={trading_day} reason={reason}")
        return 0

    daily_status = run_daily_signal_snapshot(trading_day)
    market_status = run_market_theme_confirmed_evidence(
        trading_day,
        payload_path=args.market_theme_payload,
    )
    return 0 if daily_status == 0 and market_status == 0 else 2


if __name__ == "__main__":
    raise SystemExit(main())
