# CHANGELOG: dry_run_strategy_evidence_near_breakout_v21_1_20260616

## 修改內容與檔案

- `core/generator.py`
  - `generate_report(dry_run=True)` 改為 read-only 載入 `load_strategy_evidence_summary(get_supabase_client(), VERSION)`。
  - dry-run 仍不寫 DB；讀取失敗時沿用 `format_strategy_evidence_summary(error=...)` fail closed。
  - `unheld_funnel_assessment` 在掉入淘汰前，接住 `<=5%` 接近突破、`entry_quality=C`、非 D/E、非硬結構失敗的追蹤態。
- `tests/test_generator_report.py`
  - near-breakout C 品質 regression 直接驗證 funnel state 是追蹤態，不是淘汰。

## 契約影響

- 本地 dry-run 報文與 production strategy evidence 判斷更一致。
- 聯電這類接近突破 C 品質標的，不再因追蹤態未接住而變淘汰。
- 沒有新增可買 / 加碼。
- DB:
  - 無 schema change。
  - 無 write/backfill/prune。

## 版本同步

- Runtime 報文版本維持 `v21.1`。

## 直接消費者同步

- `generate_report(dry_run=True)` covered。
- `formatTelegramMessages` official message list covered。
- runner / live Telegram 未執行。

## 未影響模組

- 持倉風控核心未改。
- future watch / fundamentals / history analogy 未改。
- DB schema、RLS、grant、policy、role 未改。

## 自檢命令與結果

- Full:
  - `.\.venv\Scripts\python.exe -m pytest -q --tb=short`
  - `484 passed, 8 skipped, 110 subtests passed`
- Official dry-run:
  - `generate_report(dry_run=True)`
  - 聯電可見結果: `等型態｜觀察`，`距突破：4.06%｜接近突破`
  - summary: 未持倉 `僅追蹤8`，不含聯電淘汰。

## 覆蓋層級

- official generator dry-run: covered。
- official message list: covered。
- funnel helper: covered。
- live Telegram: not run by design。
- production runner artifact: not run。

## 殘留風險

- 若 production runner 仍顯示 `等資料`，優先查 runner 是否已部署本 commit。
- `.pytest_cache` local cache write 仍有 WinError 5 warning，不影響測試結果。
