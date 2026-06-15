import argparse
import json
import sys
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from supabase import create_client

import config


DEFAULT_KEEP_VERSION = "v21.1"
PAGE_SIZE = 1000


def _client():
    return create_client(config.SUPABASE_URL, config.SUPABASE_KEY)


def _fetch_all(client, table, select, page_size=PAGE_SIZE):
    rows = []
    start = 0
    while True:
        chunk = (
            client.table(table)
            .select(select)
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


def build_prune_plan(rows, keep_version):
    by_stock_date = defaultdict(list)
    version_counts = Counter()
    for row in rows:
        version = row.get("version")
        version_counts[version] += 1
        by_stock_date[(row.get("stock_id"), row.get("trade_date"))].append(row)

    prune_keys = []
    prune_rows = []
    preserved_old_rows = []
    exact_duplicate_groups = 0
    exact_duplicate_extra_rows = 0

    by_full_key = defaultdict(int)
    for row in rows:
        by_full_key[(row.get("stock_id"), row.get("trade_date"), row.get("version"))] += 1
    for count in by_full_key.values():
        if count > 1:
            exact_duplicate_groups += 1
            exact_duplicate_extra_rows += count - 1

    for key, key_rows in sorted(by_stock_date.items()):
        has_keep = any(row.get("version") == keep_version for row in key_rows)
        old_rows = [row for row in key_rows if row.get("version") != keep_version]
        if has_keep and old_rows:
            prune_keys.append(key)
            prune_rows.extend(old_rows)
        elif old_rows:
            preserved_old_rows.extend(old_rows)

    return {
        "keep_version": keep_version,
        "total_rows": len(rows),
        "unique_stock_date": len(by_stock_date),
        "version_counts_before": dict(sorted(version_counts.items())),
        "exact_duplicate_stock_date_version_groups": exact_duplicate_groups,
        "exact_duplicate_extra_rows": exact_duplicate_extra_rows,
        "overlapped_stock_date_keys": len(prune_keys),
        "delete_candidate_rows": len(prune_rows),
        "delete_candidate_versions": dict(
            sorted(Counter(row.get("version") for row in prune_rows).items())
        ),
        "preserved_old_rows_without_keep_version": len(preserved_old_rows),
        "sample_delete_candidates": prune_rows[:10],
        "prune_keys": prune_keys,
    }


def execute_prune(client, prune_keys, keep_version):
    deleted_rows = 0
    for stock_id, trade_date in prune_keys:
        result = (
            client.table("daily_signal_snapshot")
            .delete()
            .eq("stock_id", stock_id)
            .eq("trade_date", trade_date)
            .neq("version", keep_version)
            .execute()
        )
        deleted_rows += len(result.data or [])
    return deleted_rows


def main():
    parser = argparse.ArgumentParser(
        description=(
            "Prune old daily_signal_snapshot versions when the same "
            "stock/date already has the selected keep version."
        )
    )
    parser.add_argument("--keep-version", default=DEFAULT_KEEP_VERSION)
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--write", action="store_true")
    parser.add_argument("--confirm-write", action="store_true")
    args = parser.parse_args()

    if args.write and not args.confirm_write:
        raise SystemExit("Refusing to delete without --confirm-write")
    if not args.write and not args.dry_run:
        raise SystemExit("Use --dry-run or --write --confirm-write")

    client = _client()
    rows = _fetch_all(
        client,
        "daily_signal_snapshot",
        "stock_id,trade_date,version",
    )
    plan = build_prune_plan(rows, args.keep_version)

    result = {
        "mode": "daily_signal_snapshot_version_prune",
        "write": bool(args.write),
        "live_telegram": False,
        "schema_change": False,
        "plan": {k: v for k, v in plan.items() if k != "prune_keys"},
    }

    if args.write:
        result["deleted_rows"] = execute_prune(
            client,
            plan["prune_keys"],
            args.keep_version,
        )
        after_rows = _fetch_all(
            client,
            "daily_signal_snapshot",
            "stock_id,trade_date,version",
        )
        after_plan = build_prune_plan(after_rows, args.keep_version)
        result["after"] = {k: v for k, v in after_plan.items() if k != "prune_keys"}
    else:
        result["deleted_rows"] = 0
        result["dry_run_only"] = True

    print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
