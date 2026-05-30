# TASK: production market/theme 三表 correction audit 與防誤報任務

## 任務狀態

- task_id：correction-market-theme-prod-coverage-2026-05
- 任務類型：risk_patch
- 狀態：ready_for_tech
- 版本建議：本輪若只產出 audit report / dry-run report，不升 Telegram 版本；若後續改使用者可見報文或 formatter header，另開 patch 任務升版。
- QA 分級建議：L3，原因是本輪涉及 production DB 真實資料覆蓋、重複寫入、source-of-truth 誤判與後續寫入防線，但不包含 live Telegram delivery。
- 任務尺寸判斷：不是 tiny_patch。主 bug 是「market/theme 三張 production 表被誤宣稱為五月完整歷史，實際可能只有 latest-source 且有 as_of 重複批次」。本輪只做 correction audit、報告契約與安全 dry-run 邊界，不擴成策略重
設或全量資料補寫。

## Owner 問題

Owner 發現先前交付宣稱「五月資料 / integrity check 完成」與 production DB 截圖不一致：

- market_theme_confirmed_evidence
- market_theme_index_daily_bars
- sector_theme_members

三張表看起來只有 2026-05-29 latest-source rows，且同一 trade_date / sector_theme_key 因 as_of 不同重複寫入多批，不能稱為五月完整歷史。

本輪要修正的是資料狀態判斷與交付證據鏈：先用 production read-only audit 釐清 row coverage、duplicates、source/date 範圍，明確區分已存在的五月歷史資料與未完成的 market/theme 三表資料，並防止後續再把 latest-only source
誤稱為五月歷史。

## 使用者可見結果

Owner 最終應看到一份 correction report，而不是 Telegram 推播：

- 三張 market/theme production 表各自的真實 row coverage。
- 每張表的 trade_date 範圍、as_of 範圍、source 欄位分布與 row count。
- 是否存在同一 business key 因不同 as_of 重複寫入多批。
- 明確結論：
- daily_price / daily_signal_snapshot 的五月歷史狀態與 market/theme 三表分開描述。
- market/theme 三表若只有 latest-only source，不得稱為五月完整歷史。
- 若需要 cleanup / dedupe / write prevention，先只提供 dry-run / SQL proposal / blocked 說明，不直接改 production rows。

## 非目標

本輪不做以下事項：

- 不補寫五月 market/theme 歷史資料。
- 不刪 production rows。
- 不 live Telegram。
- 不新增假資料、推測資料或用 latest-only source 回填成歷史。
- 不改策略決策、持倉邏輯、買賣建議、watchlist。
- 不改 DB schema、index、unique constraint、RLS、grant、policy、role；若 audit 證明需要，必須 blocked 並交 Owner 審 SQL。
- 不把 daily_price / daily_signal_snapshot 的五月歷史狀態外推到 market/theme 三表。
- 不以本地 cache、worktree、agent 對話、截圖推測取代 production DB read-only 查詢。

## 影響模組

- production DB read-only audit path。
- market/theme ingestion 或 write path 的現有文件化檢查。
- correction report / CHANGELOG.md / QA_REPORT.md 的資料狀態描述。
- 若現有 repo 有資料完整性檢查腳本，可只在 dry-run/read-only 模式擴充或新增報告輸出。

## 直接消費者

- Owner：閱讀 correction report，判斷先前宣稱是否錯誤、三張表真實狀態與下一步是否需要批准 schema/index/cleanup。
- Architect：根據 CHANGELOG.md 與 QA_REPORT.md 收口，不依賴聊天紀錄。
- QA：使用 production read-only audit 反證 coverage 與 duplicates。
- 後續 Tech 任務：若需要補 history、dedupe、unique guard 或 schema migration，必須依本輪報告另開任務。

## 輸出契約

Tech 交付必須包含一份可被 QA 重跑或比對的 read-only audit report。報告至少包含：

table: market_theme_confirmed_evidence
row_count:
trade_date_min:
trade_date_max:
distinct_trade_dates:
as_of_min:
as_of_max:
distinct_as_of:
source_distribution:
latest_source_only: true/false/unknown
duplicate_groups:
key_fields:
duplicate_group_count:
duplicate_row_count:
sample_duplicate_groups:
- business_key:
trade_date:
sector_theme_key:
as_of_values:
rows:
coverage_conclusion:

三張表都必須有同樣結構：

- market_theme_confirmed_evidence
- market_theme_index_daily_bars
- sector_theme_members

報告另需有一段 cross-table conclusion：

daily_price_may_history_status: confirmed / not_checked / insufficient_evidence
daily_signal_snapshot_may_history_status: confirmed / not_checked / insufficient_evidence
market_theme_tables_may_history_status: complete / latest_only / partial / insufficient_evidence
must_not_claim:
- latest-only market/theme rows are May full history
next_action:
- read_only_audit_complete
- cleanup_dry_run_needed
- schema_or_unique_constraint_owner_approval_needed
- backfill_task_needed

若 Tech 需要查詢 daily_price / daily_signal_snapshot，只能用 production read-only aggregate audit 驗證五月 coverage，不得修改資料。

## 驗收條件

1. Tech 必須對三張 market/theme production 表執行 read-only audit，列出 row count、trade_date 範圍、as_of 範圍、distinct 日期數、source 分布。
2. Tech 必須檢查 duplicates，至少按各表實際 business key 定義分組；若 business key 不明，必須列出候選 key 與 blocked/風險說明。
3. Tech 必須明確判斷三張表是否只有 latest-source / latest-date rows，不得用「五月資料完成」描述 latest-only 結果。
4. Tech 必須把 daily_price / daily_signal_snapshot 與 market/theme 三表分開結論；不確定則寫 not_checked 或 insufficient_evidence。
5. Tech 不得執行 production delete/update/insert；若需要 cleanup / dedupe，只能輸出 dry-run affected rows、候選 SQL 或 blocked 說明。
6. 若需要 DB schema/index/unique constraint 才能防止重複寫入，Tech 必須 blocked，列出建議 SQL、影響範圍、rollback 方向，交 Owner 批准。
7. QA 必須用 production read-only audit 反證 Tech 的 duplicates 與 coverage，不得只跑本地測試或只看 report 文字。
8. QA 必須檢查報告是否仍有把 latest-only market/theme source 稱為五月完整歷史的語句；若有，必須 blocked。
9. 本輪停止條件：三張表 read-only coverage / duplicates / source-date audit 完成，並產出下一步分類。任何 backfill、dedupe 實寫、schema guard、Telegram 文案修正都只列入後續任務，不納入本輪完成範圍。

## 範例或 fixture

期望 correction report 形狀示例：

Correction Audit Summary

daily_price:
- May history: confirmed by production aggregate audit from 2026-05-01 to 2026-05-29

daily_signal_snapshot:
- May history: confirmed by production aggregate audit from 2026-05-01 to 2026-05-29

market_theme_confirmed_evidence:
- May history: not complete
- observed trade_date range: 2026-05-29 to 2026-05-29
- observed as_of batches: multiple
- duplicate risk: same trade_date / sector_theme_key appears in multiple as_of batches
- conclusion: latest-source rows only; do not call this May history

market_theme_index_daily_bars:
- May history: not complete / partial / insufficient_evidence
- observed trade_date range: ...
- duplicate groups: ...

sector_theme_members:
- May history: not complete / partial / insufficient_evidence
- observed trade_date range: ...
- duplicate groups: ...

Next:
- read-only audit complete
- cleanup write is not approved
- schema/index prevention requires Owner approval if needed

## 明確禁止事項

- 禁止 live Telegram。
- 禁止 production insert/update/delete。
- 禁止刪 production duplicate rows。
- 禁止新增假歷史資料。
- 禁止用 latest-only source 補成五月歷史結論。
- 禁止把 daily_price / daily_signal_snapshot 的五月歷史完成狀態套用到 market/theme 三表。
- 禁止改 DB schema、index、unique constraint、RLS、grant、policy、role。
- 禁止修改策略 decision、持倉建議、watchlist、排程入口。
- 禁止用本地資料、cache、worktree 或截圖替代 production read-only audit。
- 禁止把 Owner 的「開始 / 繼續 / 處理 / 修復 / 檢查 / 清理 / 直接來」解讀成跳過 PM / Tech / QA 或直接改代碼授權。

## 已存在且不得回退的契約

- production DB 是跨日狀態與歷史資料判斷的 source-of-truth。
- local/runtime/cache 不能作為 GitHub runner 或正式報文的跨日歷史依據。
- DB schema / index / unique constraint / RLS / grant / policy / role 變更必須 Owner 事前確認。
- live Telegram delivery 必須 Owner 單獨批准。
- 固定交付流程仍是 PM TASK.md -> Tech CHANGELOG.md -> QA QA_REPORT.md。
- 若 production read-only audit 不足以判定資料真實狀態，必須標 insufficient_evidence 或 blocked，不得補推論。

## 阻塞條件

遇到以下情況 Tech 必須 blocked：

- 無法以 read-only 權限查 production DB 三張 market/theme 表。
- 表 schema 或 business key 不足以定義 duplicates，且無法從現有摘要或 DB metadata 判斷。
- 查詢需要 production 寫入權限才能完成。
- 發現需要 schema/index/unique constraint 才能防止重複寫入。
- 發現需要刪除、合併或回寫 production rows 才能完成本輪驗收。
- 無法區分 latest-source rows 與 May historical rows。
- daily_price / daily_signal_snapshot 的五月狀態缺 production aggregate evidence，但交付文字需要引用它們為 confirmed。

## QA 分級建議

- 分級：L3
- QA 必須做：
- 重跑或獨立執行 production read-only aggregate queries。
- 反證三張 market/theme 表的 date coverage 與 duplicate group count。
- 檢查 as_of 多批是否造成同一 business key 重複。
- 檢查 report 是否明確區分 daily_price / daily_signal_snapshot 與三張 market/theme 表。
- 檢查沒有 production write、delete、Telegram live delivery。
- QA 不得只看本地測試、fixture 或 Tech report 文字。
- QA 結論若不是 通過，必須明確指出是 coverage 不足、duplicates 未反證、權限不足、還是需要 Owner 批准 schema/cleanup。
