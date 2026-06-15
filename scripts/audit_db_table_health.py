import argparse
import json
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from supabase import create_client

import config


DEFAULT_TABLES = [
    "daily_price",
    "daily_signal_snapshot",
    "market_theme_confirmed_evidence",
    "market_theme_index_daily_bars",
    "position_events",
    "positions",
    "sector_theme_members",
    "signal_items",
    "signal_outcomes",
    "signal_runs",
]

TABLE_KEY_CANDIDATES = {
    "daily_price": [
        ("stock_id", "trade_date"),
    ],
    "daily_signal_snapshot": [
        ("stock_id", "trade_date", "version"),
        ("stock_id", "trade_date"),
    ],
    "signal_runs": [
        ("run_date", "run_phase"),
    ],
}


def client():
    return create_client(config.SUPABASE_URL, config.SUPABASE_KEY)


def fetch_all(client_obj, table, page_size):
    rows = []
    start = 0
    while True:
        chunk = (
            client_obj.table(table)
            .select("*")
            .range(start, start + page_size - 1)
            .execute()
            .data
            or []
        )
        rows.extend(chunk)
        if len(chunk) < page_size:
            break
        start += page_size
    return rows


def stable_json(value):
    return json.dumps(value, sort_keys=True, ensure_ascii=False, default=str)


def column_profile(rows, column):
    values = [row.get(column) for row in rows]
    nonnull = [value for value in values if value is not None]
    counter = Counter(stable_json(value) for value in values)
    decoded_top = []
    for raw, count in counter.most_common(10):
        try:
            decoded = json.loads(raw)
        except Exception:
            decoded = raw
        decoded_top.append({"value": decoded, "count": count})
    return {
        "column": column,
        "rows": len(rows),
        "nonnull": len(nonnull),
        "nulls": len(values) - len(nonnull),
        "distinct": len(counter),
        "top_values": decoded_top,
    }


def duplicate_profile(rows, columns):
    counter = Counter(tuple(row.get(column) for column in columns) for row in rows)
    extras = sum(count - 1 for count in counter.values() if count > 1)
    groups = sum(1 for count in counter.values() if count > 1)
    samples = [
        {"key": key, "count": count}
        for key, count in counter.items()
        if count > 1
    ][:10]
    return {
        "key": list(columns),
        "duplicate_groups": groups,
        "duplicate_extra_rows": extras,
        "sample_duplicate_groups": samples,
    }


def audit_table(rows, table, null_threshold):
    if not rows:
        return {
            "table": table,
            "rows": 0,
            "columns": [],
            "constant_columns": [],
            "mostly_null_columns": [],
            "duplicate_profiles": [],
        }

    columns = sorted({key for row in rows for key in row.keys()})
    profiles = [column_profile(rows, column) for column in columns]
    constant_columns = [
        profile for profile in profiles
        if profile["distinct"] == 1
    ]
    mostly_null_columns = [
        profile for profile in profiles
        if profile["nulls"] / max(profile["rows"], 1) >= null_threshold
    ]

    duplicate_profiles = []
    for key_columns in TABLE_KEY_CANDIDATES.get(table, []):
        if all(column in columns for column in key_columns):
            profile = duplicate_profile(rows, key_columns)
            if profile["duplicate_extra_rows"]:
                duplicate_profiles.append(profile)

    return {
        "table": table,
        "rows": len(rows),
        "column_count": len(columns),
        "constant_column_count": len(constant_columns),
        "mostly_null_column_count": len(mostly_null_columns),
        "constant_columns": constant_columns,
        "mostly_null_columns": mostly_null_columns,
        "duplicate_profiles": duplicate_profiles,
    }


def summarize_findings(table_report):
    findings = []
    table = table_report["table"]
    for profile in table_report.get("mostly_null_columns", []):
        findings.append({
            "table": table,
            "severity": "review",
            "type": "mostly_null_column",
            "column": profile["column"],
            "nonnull": profile["nonnull"],
            "rows": profile["rows"],
        })
    for profile in table_report.get("constant_columns", []):
        findings.append({
            "table": table,
            "severity": "info",
            "type": "constant_column",
            "column": profile["column"],
            "value": profile["top_values"][0]["value"] if profile["top_values"] else None,
        })
    for profile in table_report.get("duplicate_profiles", []):
        findings.append({
            "table": table,
            "severity": "review",
            "type": "duplicate_key",
            "key": profile["key"],
            "duplicate_extra_rows": profile["duplicate_extra_rows"],
        })
    return findings


def main():
    parser = argparse.ArgumentParser(
        description="Read-only Supabase table health audit: constants, mostly-null columns, and duplicate key candidates."
    )
    parser.add_argument("--tables", default=",".join(DEFAULT_TABLES))
    parser.add_argument("--page-size", type=int, default=1000)
    parser.add_argument("--null-threshold", type=float, default=0.95)
    args = parser.parse_args()

    client_obj = client()
    tables = [item.strip() for item in args.tables.split(",") if item.strip()]
    reports = []
    errors = []

    for table in tables:
        try:
            rows = fetch_all(client_obj, table, args.page_size)
            reports.append(audit_table(rows, table, args.null_threshold))
        except Exception as error:
            errors.append({"table": table, "error": str(error)})

    findings = []
    for report in reports:
        findings.extend(summarize_findings(report))

    print(json.dumps({
        "mode": "db_table_health_audit",
        "read_only": True,
        "live_telegram": False,
        "schema_change": False,
        "tables": tables,
        "errors": errors,
        "reports": reports,
        "findings": findings,
    }, ensure_ascii=False, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
