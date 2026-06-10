#!/usr/bin/env python3
"""Scheduled Phase 3 evidence writer without live Telegram delivery."""

import argparse
import json
import os
import subprocess
import sys
import tempfile
from datetime import datetime, timedelta, timezone
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
FRESHNESS_LOOKBACK_DAYS = 5
FRESHNESS_SAFE_WRITE_HOUR = 14
FRESHNESS_SAFE_WRITE_MINUTE = 0
STALE_ALERT_THRESHOLD_DAYS = 2
FRESHNESS_CHECK_VERSION = "market_theme_freshness_v1"
FRESHNESS_SOURCES = (
    "market_theme_confirmed_evidence",
    "market_theme_index_daily_bars",
)
EXPECTED_CONFIRMED_SECTOR_THEMES = {
    "twse_electronics",
    "twse_semiconductor",
    "twse_computer_peripheral",
    "twse_optoelectronics",
    "twse_electronic_components",
    "twse_communications",
    "twse_electronic_distribution",
    "twse_information_services",
    "twse_other_electronics",
}


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


def _parse_positive_int(value, default):
    try:
        parsed = int(value)
    except (TypeError, ValueError):
        return default
    return parsed if parsed > 0 else default


def _parse_hhmm(value, default_hour=FRESHNESS_SAFE_WRITE_HOUR, default_minute=FRESHNESS_SAFE_WRITE_MINUTE):
    text = str(value or "").strip()
    if not text:
        return default_hour, default_minute
    try:
        hour_text, minute_text = text.split(":", 1)
        hour = int(hour_text)
        minute = int(minute_text)
    except ValueError:
        raise RuntimeError(f"invalid safe write time: {text}")
    if hour < 0 or hour > 23 or minute < 0 or minute > 59:
        raise RuntimeError(f"invalid safe write time: {text}")
    return hour, minute


def _is_after_freshness_safe_write_time(now, safe_write_time=None):
    safe_hour, safe_minute = _parse_hhmm(safe_write_time)
    return now.hour > safe_hour or (now.hour == safe_hour and now.minute >= safe_minute)


def recent_confirmed_trade_dates(now, lookback_days=FRESHNESS_LOOKBACK_DAYS, trading_day_checker=None):
    checker = trading_day_checker or confirm_trading_day
    trade_dates = []
    current = now.date()
    scanned = 0
    while len(trade_dates) < lookback_days and scanned < lookback_days * 10:
        scanned += 1
        trade_date = current.isoformat()
        candidate_weekday = current.weekday()
        current -= timedelta(days=1)
        if candidate_weekday >= 5:
            continue
        status = checker(trade_date)
        if status.get("source_status") == "source-error":
            raise RuntimeError(f"calendar source-error for {trade_date}: {status.get('error') or status.get('reason')}")
        if status.get("confirmed"):
            trade_dates.append(trade_date)
    if len(trade_dates) < lookback_days:
        raise RuntimeError(f"unable to resolve {lookback_days} confirmed trading days")
    return trade_dates


def _query_trade_date_rows(client, table, fields, trade_date, limit=1000):
    try:
        result = (
            client.table(table)
            .select(fields, count="exact")
            .eq("trade_date", trade_date)
            .limit(limit)
            .execute()
        )
        rows = result.data or []
        count = getattr(result, "count", None)
        return {"status": "ok", "rows": rows, "row_count": count if count is not None else len(rows)}
    except Exception as exc:
        return {"status": "source-error", "rows": [], "row_count": 0, "reason": str(exc)}


def _confirmed_evidence_complete(rows):
    required = {
        "trade_date",
        "market_index",
        "sector_theme_key",
        "source_family",
        "source_name",
        "freshness",
        "evidence_status",
        "support_level",
    }
    valid = [
        row for row in rows or []
        if all(row.get(field) not in (None, "") for field in required)
        and row.get("freshness") == "fresh"
        and row.get("evidence_status") == "confirmed"
    ]
    observed_themes = {row.get("sector_theme_key") for row in valid}
    return EXPECTED_CONFIRMED_SECTOR_THEMES.issubset(observed_themes)


def _index_daily_bars_complete(rows):
    required = {
        "trade_date",
        "index_scope",
        "market_index",
        "source_family",
        "source_name",
        "close",
    }
    valid = [
        row for row in rows or []
        if all(row.get(field) not in (None, "") for field in required)
    ]
    has_market = any(row.get("index_scope") == "market" for row in valid)
    has_theme = any(
        row.get("index_scope") == "sector_theme" and row.get("sector_theme_key") not in (None, "")
        for row in valid
    )
    return has_market and has_theme


def read_market_theme_freshness_status(client, trade_date):
    confirmed = _query_trade_date_rows(
        client,
        "market_theme_confirmed_evidence",
        "trade_date,market_index,sector_theme_key,source_family,source_name,freshness,evidence_status,support_level",
        trade_date,
    )
    if confirmed["status"] != "ok":
        return {
            "trade_date": trade_date,
            "complete": False,
            "source_status": "source-error",
            "missing_sources": ["market_theme_confirmed_evidence"],
            "error_stage": "read",
            "reason": confirmed.get("reason") or "read failed",
        }
    index_bars = _query_trade_date_rows(
        client,
        "market_theme_index_daily_bars",
        "trade_date,index_scope,market_index,sector_theme_key,source_family,source_name,close",
        trade_date,
    )
    if index_bars["status"] != "ok":
        return {
            "trade_date": trade_date,
            "complete": False,
            "source_status": "source-error",
            "missing_sources": ["market_theme_index_daily_bars"],
            "error_stage": "read",
            "reason": index_bars.get("reason") or "read failed",
        }
    missing = []
    if not _confirmed_evidence_complete(confirmed["rows"]):
        missing.append("market_theme_confirmed_evidence")
    if not _index_daily_bars_complete(index_bars["rows"]):
        missing.append("market_theme_index_daily_bars")
    return {
        "trade_date": trade_date,
        "complete": not missing,
        "source_status": "ok",
        "missing_sources": missing,
        "row_counts": {
            "market_theme_confirmed_evidence": confirmed["row_count"],
            "market_theme_index_daily_bars": index_bars["row_count"],
        },
    }


def backfill_market_theme_sources_for_trade_date(trade_date, client=None):
    from scripts.backfill_market_theme_sources import (
        build_source_payloads,
        fetch_twse_company_profiles,
        fetch_twse_historical_breadth_rows,
        fetch_twse_historical_index_rows,
        get_supabase_client,
        upsert_source_payloads,
    )

    payloads = build_source_payloads(
        fetch_twse_historical_index_rows(trade_date),
        fetch_twse_historical_breadth_rows(trade_date),
        fetch_twse_company_profiles(),
        trade_date=trade_date,
    )
    if payloads.get("status") != "ready":
        raise RuntimeError(payloads.get("reason") or "missing-source")
    writer = client or get_supabase_client()
    return upsert_source_payloads(
        writer,
        payloads,
        start_date=trade_date,
        end_date=trade_date,
    )


def run_market_theme_freshness_check(
    now=None,
    lookback_days=None,
    safe_write_time=None,
    client=None,
    trading_day_checker=None,
    backfill_func=None,
):
    from scripts.backfill_market_theme_sources import get_supabase_client

    now = now or parse_now()
    lookback = _parse_positive_int(
        lookback_days if lookback_days is not None else os.environ.get("MARKET_THEME_FRESHNESS_LOOKBACK_DAYS"),
        FRESHNESS_LOOKBACK_DAYS,
    )
    safe_time = safe_write_time or os.environ.get("MARKET_THEME_SAFE_WRITE_TIME") or "14:00"
    writer_client = client or get_supabase_client()
    trade_dates = recent_confirmed_trade_dates(
        now,
        lookback_days=lookback,
        trading_day_checker=trading_day_checker,
    )
    can_write = _is_after_freshness_safe_write_time(now, safe_time)
    backfill = backfill_func or backfill_market_theme_sources_for_trade_date
    results = []
    failures = []

    for trade_date in trade_dates:
        status = read_market_theme_freshness_status(writer_client, trade_date)
        if status.get("source_status") == "source-error":
            failures.append({**status, "status": "source-error"})
            emit(
                "MARKET_THEME_FRESHNESS_FAILED "
                f"version={FRESHNESS_CHECK_VERSION} trade_date={trade_date} "
                f"source={','.join(status['missing_sources'])} "
                f"stage={status['error_stage']} reason={status['reason']} action=fail_closed"
            )
            continue
        if status["complete"]:
            row = {**status, "status": "already-complete"}
            results.append(row)
            emit(
                "MARKET_THEME_FRESHNESS "
                f"version={FRESHNESS_CHECK_VERSION} trade_date={trade_date} "
                "source=all status=already-complete action=skip"
            )
            continue
        missing = ",".join(status["missing_sources"])
        if not can_write:
            row = {**status, "status": "skipped-before-safe-write-time"}
            results.append(row)
            emit(
                "MARKET_THEME_FRESHNESS "
                f"version={FRESHNESS_CHECK_VERSION} trade_date={trade_date} source={missing} "
                f"status=skipped-before-safe-write-time safe_write_time={safe_time}"
            )
            continue
        try:
            backfill(trade_date, client=writer_client)
            verified = read_market_theme_freshness_status(writer_client, trade_date)
        except Exception as exc:
            failures.append({**status, "status": "upsert-error", "reason": str(exc)})
            emit(
                "MARKET_THEME_FRESHNESS_FAILED "
                f"version={FRESHNESS_CHECK_VERSION} trade_date={trade_date} "
                f"source={missing} stage=upsert "
                f"reason={str(exc)} action=fail_closed"
            )
            continue
        if not verified.get("complete"):
            still_missing = ",".join(verified.get("missing_sources") or status["missing_sources"])
            failures.append({**verified, "status": "read-after-write-mismatch"})
            emit(
                "MARKET_THEME_FRESHNESS_FAILED "
                f"version={FRESHNESS_CHECK_VERSION} trade_date={trade_date} source={still_missing} "
                "stage=read-after-write reason=business-key-incomplete action=fail_closed"
            )
            continue
        row = {**verified, "status": "backfilled-and-verified"}
        results.append(row)
        emit(
            "MARKET_THEME_FRESHNESS "
            f"version={FRESHNESS_CHECK_VERSION} trade_date={trade_date} "
            f"source={missing} status=backfilled-and-verified"
        )

    return {
        "status": "fail-closed" if failures else "ok",
        "version": FRESHNESS_CHECK_VERSION,
        "lookback_days": lookback,
        "safe_write_time": safe_time,
        "checked_trade_dates": trade_dates,
        "results": results,
        "failures": failures,
    }


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


def _load_market_theme_payload_rows(payload_path):
    payload = json.loads(Path(payload_path).read_text(encoding="utf-8"))
    if isinstance(payload, dict):
        for key in ("rows", "payloads", "confirmed_rows"):
            rows = payload.get(key)
            if isinstance(rows, list):
                return rows
    if isinstance(payload, list):
        return payload
    return []


def validate_market_theme_payload_trade_date(payload_path, trading_day):
    rows = _load_market_theme_payload_rows(payload_path)
    if not rows:
        raise RuntimeError("approved payload has no rows")
    mismatched = sorted(
        {
            str(row.get("trade_date") or "")
            for row in rows
            if str(row.get("trade_date") or "") != trading_day
        }
    )
    if mismatched:
        raise RuntimeError(
            "approved payload trade_date mismatch: "
            f"expected {trading_day}, got {', '.join(mismatched)}"
        )
    return True


def run_market_theme_confirmed_evidence(trading_day, payload_path=None, runner=None):
    runner = runner or subprocess.run
    with tempfile.TemporaryDirectory() as tmpdir:
        if payload_path:
            path = Path(payload_path)
            validate_market_theme_payload_trade_date(path, trading_day)
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
    parser.add_argument(
        "--require-market-theme-payload",
        action="store_true",
        help="Fail closed when the approved market/theme payload is not provided.",
    )
    parser.add_argument("--stale-status-json", help="JSON source status history for stale alert probes.")
    parser.add_argument(
        "--freshness-check-only",
        action="store_true",
        help="Check recent market/theme source freshness and run idempotent backfill when safe.",
    )
    parser.add_argument("--freshness-lookback-days", help="Recent confirmed trading days to check. Defaults to 5.")
    parser.add_argument("--safe-write-time", help="Asia/Taipei HH:MM time after which missing sources may be backfilled.")
    args = parser.parse_args(argv)

    now = parse_now(args.now)
    trading_day = now.date().isoformat()

    if args.freshness_check_only:
        try:
            report = run_market_theme_freshness_check(
                now=now,
                lookback_days=args.freshness_lookback_days,
                safe_write_time=args.safe_write_time,
            )
        except Exception as exc:
            emit(
                "MARKET_THEME_FRESHNESS_FAILED "
                f"version={FRESHNESS_CHECK_VERSION} trade_date={trading_day} source=market_theme "
                f"stage=preflight reason={str(exc)} action=fail_closed"
            )
            return 2
        return 0 if report["status"] == "ok" else 2

    should_run, reason = should_run_evidence_writes(now)

    if args.stale_status_json:
        emit_stale_alerts(json.loads(Path(args.stale_status_json).read_text(encoding="utf-8")))

    if not should_run:
        for source in ("daily_signal_snapshot", "market_theme_confirmed_evidence"):
            emit(f"EVIDENCE_WRITE_SKIPPED source={source} trading_day={trading_day} reason={reason}")
        return 0

    if args.require_market_theme_payload and not args.market_theme_payload:
        emit(
            "EVIDENCE_WRITE_FAILED "
            f"source=market_theme_confirmed_evidence trading_day={trading_day} "
            "reason=missing-approved-payload action=fail_closed"
        )
        return 2

    daily_status = run_daily_signal_snapshot(trading_day)
    if args.market_theme_payload:
        market_status = run_market_theme_confirmed_evidence(
            trading_day,
            payload_path=args.market_theme_payload,
        )
    else:
        try:
            freshness_report = run_market_theme_freshness_check(
                now=now,
                lookback_days=args.freshness_lookback_days,
                safe_write_time=args.safe_write_time,
            )
            market_status = 0 if freshness_report["status"] == "ok" else 2
        except Exception as exc:
            emit(
                "MARKET_THEME_FRESHNESS_FAILED "
                f"version={FRESHNESS_CHECK_VERSION} trade_date={trading_day} source=market_theme "
                f"stage=scheduled-run reason={str(exc)} action=fail_closed"
            )
            market_status = 2
    return 0 if daily_status == 0 and market_status == 0 else 2


if __name__ == "__main__":
    raise SystemExit(main())
