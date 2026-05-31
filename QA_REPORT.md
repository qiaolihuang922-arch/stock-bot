# QA_REPORT:

## 測試範圍

- 任務尺寸：risk_patch，QA level：L3。
- 驗證對象：`TASK.md`、`CHANGELOG.md`、`scripts/backfill_market_theme_sources.py`、`tests/test_market_theme_source_backfill.py`、production read-after-write audit。
- 可吸收 diff：
  - `CHANGELOG.md`
  - `TASK.md`
  - `scripts/backfill_market_theme_sources.py`
  - `tests/test_market_theme_source_backfill.py`
- 不吸收 worktree 整包；只吸收上述任務相關 diff。

## 風險預算與停止條件

1. production 仍是 latest-only 卻被誤宣告完成。
   - 驗證：獨立重跑 `scripts/smoke_market_theme_evidence_readonly.py --correction-audit-json --limit 20000`。
   - 停止條件：`status` 不是 `pass`、date range 不是 20 trade dates、或 `latest_source_only=true`。
2. duplicate groups 只是被 script 忽略，production business-key duplicates 未清零。
   - 驗證：核對 audit 的 `duplicate_group_count` 與 business-key fields。
   - 停止條件：confirmed evidence 或 index bars 任一 duplicate group 不為 0。
3. `sector_theme_members` 被誤當 daily history，或本輪偷偷擴成 schema / Telegram / strategy 變更。
   - 驗證：核對 audit `mapping_only`，並檢查 diff 不含 schema / Telegram / strategy。
   - 停止條件：mapping 被計入 daily history，或出現 schema / live Telegram 變更。

## 關聯風險掃描

- production write 使用 repo script，不是手寫普通 DML：
  - `PYTHONPATH=. arch -arm64 .venv/bin/python scripts/backfill_market_theme_sources.py --historical-range --start-date 2026-05-04 --end-date 2026-05-29 --write --confirm-write`
- 寫入結果：
  - `market_theme_confirmed_evidence` written rows：180。
  - `market_theme_index_daily_bars` written rows：200。
  - `schema_change=false`，`live_telegram=false`。
- 獨立 read-only audit：
  - `PYTHONPATH=. arch -arm64 .venv/bin/python scripts/smoke_market_theme_evidence_readonly.py --correction-audit-json --limit 20000`
  - exit code：0。
  - `status=pass`，`next_action=["read_only_audit_complete"]`。
- CAO `run_qa_code.sh` 仍會 blocked，原因是 runner 強制用 `.qa_tmp/config.py` dummy Supabase (`SUPABASE_URL=http://localhost`)；此為 runner gap，不代表 production audit 失敗。

## 跨區塊語意一致性

- `market_theme_confirmed_evidence`：
  - row_count：180。
  - date range：`2026-05-04` to `2026-05-29`。
  - distinct trade dates：20。
  - `latest_source_only=false`。
  - duplicate business-key groups：0。
  - conclusion：`complete`。
- `market_theme_index_daily_bars`：
  - row_count：200。
  - date range：`2026-05-04` to `2026-05-29`。
  - distinct trade dates：20。
  - `latest_source_only=false`。
  - duplicate business-key groups：0。
  - conclusion：`complete`.
- `sector_theme_members`：
  - row_count：12。
  - conclusion：`mapping_only`。
  - duplicate business-key groups：0。
  - 不計入 May daily history。
- `daily_signal_snapshot`：
  - history coverage 仍為 `covered`。
  - current `v20.4.6` May 0 rows 仍是 diagnostic，`blocks_history_coverage=false`。

## 使用者誤讀風險

- 本輪不改 Telegram / UI / summary；無手機報文閱讀路徑。
- Owner 可見 audit JSON 第一層現在是 `status=pass`，且 market/theme 兩張歷史表均為 `complete`；不再是 latest-only。
- `sector_theme_members` 仍明確標示 `mapping_only`，避免誤讀成 daily history。

## 質疑與反證

- Tech / Architect 自檢：
  - `PYTHONPATH=. arch -arm64 .venv/bin/python -m pytest tests/test_market_theme_source_backfill.py -q`
    - 結果：14 passed。
  - `git diff --check`
    - 結果：通過。
  - dry-run:
    - `source_gaps=[]`。
    - candidate rows：confirmed 180、index 200。
    - coverage：20 trade dates。
- Production read-after-write audit 反證：
  - confirmed evidence 不再 latest-only：20 trade dates，`latest_source_only=false`。
  - index bars 不再 latest-only：20 trade dates，`latest_source_only=false`。
  - confirmed duplicate groups 清零：0。
  - index duplicate groups 清零：0。
- Source gap 反證：
  - 測試覆蓋 source gap 時 `upsert_source_payloads` 拒寫並丟 `ValueError`，不會用假資料填洞。

## 未測項目

- 未跑 full repo pytest；本輪風險集中在 market/theme production write path、read-only audit 與 duplicate contract。
- 未補更多月份；本輪只處理 2026-05-04 到 2026-05-29。
- 未把 market/theme trend 轉成新的策略加權；本輪只完成資料抓取、寫入、去重與 audit 通過。
- CAO QA runner 需另修：允許 production read-only audit 使用主 repo config 或讓 Architect 注入只讀 audit artifact，否則此類任務會被 dummy config 誤阻塞。

## QA 結論

通過
