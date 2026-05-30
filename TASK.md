# TASK: correction/full-integrity blocker wording 與 production read-only coverage audit

## 任務狀態

- task_id：correction-market-theme-prod-coverage-2026-05
- 任務類型：risk_patch
- 狀態：ready_for_tech
- 版本建議：不升 Telegram 版本；本輪只改 correction/full-integrity report 與 read-only audit 證據輸出。
- QA 分級建議：L3
- 任務尺寸判斷：不是 tiny_patch。本輪涉及 production read-only audit、blocked 結論、防誤報與 current core/generator.py VERSION 的 production 覆蓋檢查，但禁止擴成 backfill、cleanup、schema guard 或策略重設。

## Owner 問題

目前 correction-market-theme-prod-coverage-2026-05 blocker 不要再延長成「繼續補證據鏈」任務。先把 correction/full-integrity report 的 blocked wording 與 next_action 修正清楚，並加入 production read-only audit：

- market_theme_confirmed_evidence
- market_theme_index_daily_bars
- sector_theme_members

audit 必須覆蓋 row coverage、date range、source distribution、business-key duplicates。

同時必須檢查 May daily_signal_snapshot 是否有「目前 core/generator.py VERSION」的 production rows；若 current VERSION 無五月 rows，本輪 report 必須 blocked，不得宣稱完整。

## 使用者可見結果

Owner 看到的是 correction/full-integrity report 的明確 blocked/next_action 結論，不是 Telegram 推播：

- market/theme 三表 production read-only audit 摘要。
- May daily_signal_snapshot current generator VERSION coverage 摘要。
- 若 current VERSION 無五月 rows，報告結論必須是 blocked。
- next_action 必須指向「需要哪個後續任務或 Owner 批准」，不得寫成已完成或繼續泛化證據鏈。

## 非目標

- 不繼續擴大證據鏈。
- 不補寫 production DB。
- 不 cleanup / dedupe / backfill。
- 不新增或修改 schema、RLS、grant、policy、role、index、constraint。
- 不 live Telegram。
- 不改策略 decision、持倉建議、watchlist 或交易狀態機。
- 不把 daily_price 或非 current VERSION snapshot 覆蓋外推成 current report 完整。
- 不用 local cache、worktree、runtime dict、agent 對話或截圖替代 production read-only audit。

## 影響模組

- correction/full-integrity report 產生路徑。
- production read-only audit 查詢或 report helper。
- daily_signal_snapshot May coverage 檢查，需以 production DB 與目前 core/generator.py VERSION 為準。
- CHANGELOG.md 與 QA_REPORT.md 的 blocker 結論描述。

## 直接消費者

- Owner：判斷 blocker 是否被正確收斂，知道目前不能宣稱完整的原因與下一步。
- Architect：依 TASK.md、CHANGELOG.md、QA_REPORT.md 收口，不依賴聊天紀錄。
- QA：以 production read-only audit 反證 Tech report。
- 後續 Tech 任務：若需要 backfill、cleanup、dedupe 或 schema guard，必須另開任務。

## 輸出契約

Tech 必須交付 correction/full-integrity report，至少包含以下欄位與順序：

status: pass | blocked
blocked_reason: null | string
generator_version:
source: core/generator.py VERSION
value: string
daily_signal_snapshot_may_current_version_coverage:
row_count: number
date_min: YYYY-MM-DD | null
date_max: YYYY-MM-DD | null
distinct_trade_dates: number
conclusion: covered | no_current_version_may_rows | insufficient_evidence
market_theme_tables:
market_theme_confirmed_evidence:
row_count: number
date_min: YYYY-MM-DD | null
date_max: YYYY-MM-DD | null
distinct_dates: number
source_distribution: map
business_key_fields: list
duplicate_group_count: number
duplicate_row_count: number
sample_duplicate_groups: list
conclusion: complete | latest_only | partial | insufficient_evidence
market_theme_index_daily_bars:
same_shape_as_above
sector_theme_members:
row_count: number
valid_from_min: YYYY-MM-DD | null
valid_from_max: YYYY-MM-DD | null
valid_to_min: YYYY-MM-DD | null
valid_to_max: YYYY-MM-DD | null
active_rows: number
source_distribution: map
business_key_fields: list
duplicate_group_count: number
duplicate_row_count: number
sample_duplicate_groups: list
conclusion: mapping_only | insufficient_evidence
next_action:
- read_only_audit_complete
- blocked_current_version_snapshot_missing
- followup_backfill_task_needed
- followup_cleanup_or_dedupe_task_needed
- owner_approval_required_for_schema_or_write

契約要求：

- 若 May daily_signal_snapshot current VERSION row count 為 0，status 必須是 blocked，blocked_reason 必須明確寫 current VERSION 無五月 rows。
- next_action 不得使用「continue evidence chain」或等價泛化描述。
- market/theme 三表若只有 latest-only rows，不得稱為 May full history。
- sector_theme_members 是 membership mapping，不是 daily history；不得要求 trade_date exact May coverage，也不得把 mapping rows 稱為 May full history。
- 若 business key 無法可靠判斷，該表 conclusion 必須是 insufficient_evidence 或整份 report blocked。

## 驗收條件

1. Tech 讀取目前 core/generator.py VERSION，並用 production read-only query 檢查 May daily_signal_snapshot 是否有該 VERSION rows。
2. Tech 對三張 market/theme production 表做 read-only audit，列出 row coverage、date range、source distribution、business-key duplicates。
   - `sector_theme_members` 例外：列出 membership mapping coverage、valid_from/valid_to、active rows、source distribution、business-key duplicates；不得當作 daily trade_date history。
3. Tech 修正 correction/full-integrity report 的 blocked wording，使 current VERSION 無五月 rows時必然 blocked。
4. Tech 修正 next_action，不得再把本 blocker導向「繼續證據鏈」。
5. Tech 不得執行任何 production insert/update/delete、cleanup、backfill 或 schema/RLS/grant/policy/role/index/constraint 變更。
6. QA 必須用 production read-only audit 獨立反證 Tech 結論，尤其是 current VERSION May snapshot coverage 與三張 market/theme duplicates。
7. QA 必須檢查 report wording，確認沒有把 latest-only 或 non-current VERSION rows 寫成完整 coverage。
8. 本輪停止條件：report wording、next_action、current VERSION May snapshot coverage、三張表 read-only audit 都完成或明確 blocked；任何 cleanup、backfill、schema guard、live Telegram 都只記後續，不納入本輪。

## 範例或 fixture

Correction Full-Integrity Report

status: blocked
blocked_reason: daily_signal_snapshot has no May rows for current generator VERSION vX.Y.Z

generator_version:
- source: core/generator.py VERSION
- value: vX.Y.Z

daily_signal_snapshot May current-version coverage:
- rows: 0
- date range: null to null
- conclusion: no_current_version_may_rows

market_theme_confirmed_evidence:
- rows: 128
- date range: 2026-05-29 to 2026-05-29
- source distribution: latest=128
- duplicate groups: 12
- conclusion: latest_only; do not call May full history

next_action:
- blocked_current_version_snapshot_missing
- followup_backfill_task_needed
- owner_approval_required_for_any_production_write_or_schema

## 已存在且不得回退的契約

- production DB 是跨日狀態與歷史資料判斷的 source-of-truth。
- runner 視為無狀態；local/cache/runtime/worktree 不能當 production history。
- 使用者可見 Telegram 版本以 core/generator.py VERSION 為準。
- DB schema / RLS / grant / policy / role / index / constraint 變更需 Owner 事前確認。
- production 寫入、cleanup、backfill 不在本輪授權內。
- live Telegram delivery 需 Owner 單獨批准。
- PM -> Tech -> QA 完整交付，不得跳過 QA。
- 證據不足時必須 blocked 或 insufficient_evidence，不得推論補齊。

## 明確禁止事項

- 禁止 production DB 寫入。
- 禁止 schema、RLS、grant、policy、role、index、constraint 變更。
- 禁止 live Telegram。
- 禁止 cleanup、dedupe、backfill。
- 禁止繼續擴大證據鏈。
- 禁止用 non-current VERSION 的 May rows 代表 current VERSION 覆蓋。
- 禁止把 latest-only market/theme rows 稱為 May full history。
- 禁止把 Owner 的「開始 / 繼續 / 處理 / 修復 / 檢查 / 清理 / 直接來」解讀成跳過 Tech / QA 或直接改代碼授權。

## 阻塞條件

Tech 遇到以下任一情況必須 blocked：

- 無法讀取目前 core/generator.py VERSION。
- 無法以 read-only 權限查 production DB。
- May daily_signal_snapshot 沒有 current VERSION rows。
- 三張 market/theme 表的 business key 無法可靠定義或 duplicates 無法 audit。
- report 需要 production 寫入、cleanup、backfill 或 schema 變更才能完成。
- 無法區分 latest-only rows、partial coverage 與完整 May history。
- 任何必要資料來源回傳 source-error 或 insufficient-data。

## QA 分級建議

- QA level：L3
- QA 必須獨立執行 production read-only audit。
- QA 必須反證 current core/generator.py VERSION 的 May daily_signal_snapshot coverage。
- QA 必須反證三張 market/theme 表的 row coverage、date range、source distribution、business-key duplicates。
- QA 必須檢查 blocked wording 與 next_action 沒有導向「繼續證據鏈」。
- QA 不得只重跑 Tech 命令或只看 report 文字。
- QA 結論只能是 通過、阻塞、conditional pass。
