from scripts.prune_daily_signal_snapshot_versions import build_prune_plan


def test_build_prune_plan_deletes_old_rows_only_when_keep_version_exists():
    rows = [
        {"stock_id": "2301", "trade_date": "2026-06-15", "version": "v20.4"},
        {"stock_id": "2301", "trade_date": "2026-06-15", "version": "v21.1"},
        {"stock_id": "2301", "trade_date": "2026-06-14", "version": "v20.4"},
        {"stock_id": "2337", "trade_date": "2026-06-15", "version": "v19.1"},
        {"stock_id": "2337", "trade_date": "2026-06-15", "version": "v21.1"},
    ]

    plan = build_prune_plan(rows, "v21.1")

    assert plan["delete_candidate_rows"] == 2
    assert plan["overlapped_stock_date_keys"] == 2
    assert plan["preserved_old_rows_without_keep_version"] == 1
    assert plan["delete_candidate_versions"] == {"v19.1": 1, "v20.4": 1}


def test_build_prune_plan_reports_exact_duplicates_without_selecting_keep_rows():
    rows = [
        {"stock_id": "2301", "trade_date": "2026-06-15", "version": "v21.1"},
        {"stock_id": "2301", "trade_date": "2026-06-15", "version": "v21.1"},
        {"stock_id": "2301", "trade_date": "2026-06-15", "version": "v20.4"},
    ]

    plan = build_prune_plan(rows, "v21.1")

    assert plan["exact_duplicate_stock_date_version_groups"] == 1
    assert plan["exact_duplicate_extra_rows"] == 1
    assert plan["delete_candidate_rows"] == 1
    assert plan["delete_candidate_versions"] == {"v20.4": 1}
