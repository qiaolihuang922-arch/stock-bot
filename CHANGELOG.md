# CHANGELOG:

## 任務尺寸與風險

- 任務尺寸：risk_patch。
- 風險判斷：本輪修正 correction/full-integrity blocker 的 read-only audit、fail-closed 狀態、current VERSION May coverage、market/theme coverage、mapping-only 語義與 CLI return code；不涉及 DB write、schema、backfill、cleanup/dedupe、live Telegram 或策略 decision。

## 修改內容

- `services/market_theme_evidence_store.py`
  - 新增 `build_market_theme_production_correction_audit()`，輸出 correction audit JSON。
  - 讀取 `core/generator.py VERSION`，檢查 `daily_signal_snapshot` May current-version coverage。
  - 對 `market_theme_confirmed_evidence`、`market_theme_index_daily_bars` 做 daily market/theme read-only audit：row coverage、date range、source distribution、business-key duplicates。
  - May 2026 coverage 改為 exact `MAY_2026_EXPECTED_TRADE_DATES` equality：`2026-05-04` 至 `2026-05-29` 共 20 個交易日；多出 `2026-05-01` 或少任一 expected date 都 fail closed。
  - current VERSION `daily_signal_snapshot` 若 `row_count` 大於 fetched rows，視為受限樣本，必須 fail closed，不得用 sample 外推 covered。
  - `sector_theme_members` 修正為 membership mapping coverage，輸出 `valid_from_min/max`、`valid_to_min/max`、`active_rows`，結論為 `mapping_only`，不當作 May daily history。
  - `conclusion` 維持 TASK enum：`complete/latest_only/partial/insufficient_evidence/mapping_only`；詳細原因保留在 `coverage_conclusion`。
  - `read_only_audit_complete` 只在 daily signal covered、兩張 daily market/theme 表 complete、members mapping readable 時出現；latest-only、partial、source-error、missing-source、current VERSION missing 仍 blocked。
- `scripts/smoke_market_theme_evidence_readonly.py`
  - 新增 `--correction-audit-json` CLI。
  - Supabase client missing、dependency/import error 或 client 建立失敗時，輸出 blocked JSON，不 traceback、不輸出 secret 細節。
  - correction audit blocked 時 return code 為 2。
- `tests/test_market_theme_evidence_handoff.py`
  - 覆蓋 latest-only、duplicates、source-error、current VERSION missing、exact expected dates、wrong date set、extra `2026-05-01`、limited sample、19 dates insufficient、members mapping-only、positive complete path、CLI missing/import/client exception blocked JSON。

## 修改檔案

- `services/market_theme_evidence_store.py`
- `scripts/smoke_market_theme_evidence_readonly.py`
- `tests/test_market_theme_evidence_handoff.py`

## 最小改動策略

- 只做 `TASK.md` 指定的 correction/full-integrity read-only audit、fail-closed CLI 與必要 regression tests。
- 未擴大成 production write、schema guard、cleanup/dedupe、backfill、Telegram 或策略任務。

## 契約影響

- 新增 public helper：`build_market_theme_production_correction_audit(client, limit=10000, generator_version=None)`。
- 新增 CLI：`scripts/smoke_market_theme_evidence_readonly.py --correction-audit-json`。
- JSON report 包含 `status`、`blocked_reason`、`generator_version`、`daily_signal_snapshot_may_current_version_coverage`、`market_theme_tables`、`next_action`。
- 行為契約收緊：read incomplete 或資料語義不足時必須 `blocked`；members mapping-only 不再被錯當 daily history backfill 需求。
- 未改 Telegram message list、payload、報文分組、DB schema、DB write path 或 `core/generator.py VERSION`。

## 直接消費者同步

- Owner / Architect：可依 correction audit JSON 判斷 blocker 是否仍 blocked，不依賴聊天紀錄。
- QA：可用 helper 與 CLI 反證 current VERSION May coverage、daily market/theme coverage、members mapping-only 與 duplicates。
- CLI consumer：已同步 `--correction-audit-json` 與 blocked rc=2。
- Test consumer：已同步新增 helper / CLI contract regression tests。

## 未影響模組

- 未執行 live Telegram。
- 未執行 live Supabase write。
- 未做 production insert/update/delete。
- 未做正式 backfill、cleanup 或 dedupe。
- 未改 schema、RLS、grant、policy、role、index、constraint。
- 未改策略 decision、持倉建議、watchlist、交易狀態機。
- 未宣稱 production audit 完成。

## 已跑自檢命令

- `git diff --check`：通過。
- `.venv/bin/python -m pytest tests/test_market_theme_evidence_handoff.py -q`：通過，50 passed。

## 殘留風險

- 自檢使用 local fake client / unit tests，不代表 production 三張 market/theme 表五月資料完整。
- 若 production audit 仍顯示 current VERSION snapshot missing、latest-only、partial、source-error 或 duplicates，本輪只會正確 blocked，不會修資料。

## 旁支待辦

- 另開 current `v20.4.6` May snapshot backfill 任務。
- 另開 market/theme historical coverage 任務。
- 另開 confirmed evidence duplicate cleanup/dedupe 任務；需要 production write 或 schema 變更時先取得 Owner 批准。
