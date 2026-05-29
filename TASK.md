# TASK: Evidence Chain Production Closure Gap Assessment

## 任務狀態

- task_id: evidence_chain_production_closure_gap_20260529
- 任務類型：risk_patch
- 任務尺寸判斷：risk_patch
- 狀態：ready_for_tech
- 版本建議：none；本輪不改 Telegram 使用者可見報文、不改 VERSION。若 Tech 實際改到 Telegram header / formatter / message list，必須 blocked 回 PM 重定版本契約。
- QA 分級建議：L2+；聚焦 production source-of-truth contract、schema sufficiency evidence、manual SQL safety、read-only smoke/backfill readiness。不得擴成 full pytest、正式 production backfill、live DB 驗證或 live
Telegram。

## Owner 問題

Owner 要繼續 evidence chain production 化，但現在不能直接進 production write / backfill。下一步最小任務是確認 production 閉環還缺什麼，尤其是 public.market_theme_confirmed_evidence 現有 schema 是否足夠承接 read-only
smoke / manual backfill，或是否仍需要擴字段 / 擴表。

本輪要把問題收斂成一個 repo-side non-live 結論：

- 若現有表足夠：Tech 必須產出明確 no-schema-change 結論、證據、下一步人工 SQL / smoke / manual backfill 步驟或文件改進。
- 若現有表不足：Tech 必須產出手動 SQL 文件與 verification SQL，供 Owner 審核後自行執行。
- 不管哪一支，都不得 live Supabase write、不得正式 backfill、不得直接改 production RLS/grant、不得 live Telegram。

## 使用者可見結果

Owner 本輪會看到 repo 內交付物與交付摘要，而不是新的 Telegram 報文：

- 一份 production closure gap assessment，明確回答：
- market_theme_confirmed_evidence 現有表是否足夠。
- 還缺 ingestion / manual backfill / read-only smoke / RLS 或 grant 的哪一段。
- 下一步能否進入 read-only smoke 或 manual backfill。
- 若不需 schema change：明確的 no-schema-change 結論、證據矩陣與下一步人工操作清單。
- 若需要 schema change：manual SQL artifact 與 verification SQL，且標明 Owner manual only。
- CHANGELOG.md 說清楚 repo-side artifact 與 Owner manual/live 邊界。
- QA_REPORT.md 驗證沒有 fake confirmed、沒有 local state 當 production、SQL 不誤導為已上線。

Owner 手機 Telegram 閱讀路徑本輪不變。即使 repo 產出 SQL 或 docs，production confirmed rows 未實際存在前，Telegram 仍不得顯示 confirmed 或買入推薦語意。

## 非目標

- 不做 live Supabase write。
- 不做正式 production backfill。
- 不直接修改 production RLS / grant / role / policy。
- 不 live Telegram delivery。
- 不改 BUY / SELL / RR / 加減碼 / 停損停利 / 過熱 / 漲停不追門檻。
- 不新增外部新聞 / 題材 ingestion provider。
- 不重設策略、不改 watchlist、不做全 repo 清理。
- 不把 runtime/local/cache/worktree/agent context 當 production source-of-truth。
- 不把本輪 artifact 描述為 production 已上線。

## 影響模組

Tech 只能在最小範圍內處理 repo-side non-live artifact，實際檔名依現有結構調整：

- services/market_theme_evidence_store.py
- scripts/validate_market_theme_evidence_ingestion.py
- scripts/smoke_market_theme_evidence_readonly.py
- db/sql/*market_theme*
- docs/handoff/*market_theme*
- 對應局部 tests / fixtures
- CHANGELOG.md

不得修改 live runner secrets、正式 backfill runner、production DB、live Telegram 發送流程或策略核心門檻。

## 直接消費者

- Owner：審核是否需要執行 manual SQL、是否可進 manual backfill / read-only smoke。
- Architect：依 TASK.md / CHANGELOG.md / QA_REPORT.md 判斷下一步是否可進 Owner manual execution。
- Tech：依本任務交付 non-live repo artifact。
- QA：驗證 schema sufficiency conclusion、SQL safety、source-of-truth contract、fail-closed。
- services/market_theme_evidence_store.py read-only loader：未來只讀 production source-of-truth。
- GitHub fresh runner：未來只能用 production DB read-only result，不得靠 local state。
- Telegram Owner 手機報文：本輪不改；缺 production confirmed rows 時仍只能來源不足 / 不作確認。

## 輸出契約

### 1. Production Gap Assessment Contract

Tech 必須產出一份可被 QA 驗證的結論，放在 CHANGELOG.md 並可同步到 docs/handoff artifact。結論必須包含：

- current_table_contract：現有 market_theme_confirmed_evidence 可支援哪些欄位與 confirmed 條件。
- required_for_readonly_smoke：read-only smoke 最少需要哪些 production rows / env / permissions。
- required_for_manual_backfill：manual backfill 最少需要哪些 source data / lineage / freshness / owner approval。
- schema_decision：只能是 no-schema-change 或 schema-change-required。
- evidence：引用 repo 內 schema / loader / validation / SQL artifact 的可核驗證據。
- blocked_or_followup：未能 repo-side 驗證的 production 事實，例如 Owner 尚未執行 SQL、尚未提供 read-only env、尚未有 production rows。

### 2. Branch A: no-schema-change Contract

若 Tech 判定現有表足夠，必須交付：

- 明確 no-schema-change 結論。
- 證據矩陣：逐項對照 loader confirmed 條件、manual backfill 必要欄位、read-only smoke 必要查詢、validation payload。
- 下一步人工步驟：
- Owner 可先執行哪些 read-only verification。
- Owner 若要 manual backfill，應使用哪個現有 SQL template / placeholder / validation command。
- GitHub read-only smoke 需要哪些 env 與 fail-closed 預期。
- 文件或 smoke 改進可以做，但不得把 artifact 說成已上線。

### 3. Branch B: schema-change-required Contract

若 Tech 判定需要擴字段或擴表，必須交付：

- 一份 manual SQL 文件。
- 一份 verification SQL 或同檔 verification section。
- SQL header 必須寫明：
- Owner manual only。
- agent 未執行。
- 不是 migration 已上線證據。
- 執行前需 Owner 單獨批准。
- SQL 必須包含 rollback / verification / fail condition 說明，或明確標記哪些部分需 Owner 決策。
- 不得包含 secret、project URL、service role key、password。

### 4. CHANGELOG.md 必須包含

- 修改內容。
- 修改檔案。
- 契約影響。
- 版本同步：本輪不升版、不改 Telegram。
- 直接消費者同步。
- schema decision：no-schema-change 或 schema-change-required。
- production closure matrix：
- schema
- ingestion validation
- manual backfill
- read-only smoke
- RLS / grant
- Telegram confirmed consumption
- 自檢命令與結果。
- 殘留風險與 blocked/follow-up。

## 驗收條件

1. Tech 必須明確回答 market_theme_confirmed_evidence 是否需要擴字段 / 擴表，不得只寫「可能」。
2. 若宣稱 no-schema-change，必須有 repo 內 evidence matrix 支撐，且 QA 能逐項核對。
3. 若需要 schema change，必須產出 manual SQL 與 verification SQL，且 SQL 不會被誤讀為已執行或已上線。
4. 不得產生 fake confirmed；runtime/local/cache/worktree/report-derived/test fixture source 不得變成 production confirmed。
5. 不得把 local state、agent context、same-run runtime 當 production source-of-truth。
6. read-only smoke / manual backfill 步驟必須 fail closed：missing env、permission denied、0 rows、stale rows、unsupported values、insufficient data 都不得 confirmed。
7. Tech 不得執行 production SQL、不得寫 Supabase、不得發 Telegram。
8. 本輪不得改策略 decision、Telegram message list、formatter header 或 VERSION。
9. QA 必須驗證 SQL / docs / CHANGELOG 的 wording 不暗示 production ingestion/backfill/RLS 已完成。
10. 本輪完成後，只能表示「production closure gap 已判定，下一步 manual artifact ready 或 no-schema-change path ready」，不得表示 production 閉環已完成。

## 範例或 fixture

### no-schema-change 結論形狀

schema_decision: no-schema-change
reason:
- loader confirmed contract already maps to existing columns:
support_level in ('confirmed','supporting')
evidence_status='confirmed'
freshness='fresh'
- manual backfill can populate existing lineage/source fields.
- read-only smoke only needs SELECT on existing table.

next_manual_steps:
1. Owner runs read-only verification SQL.
2. Owner validates payload with dry-run CLI.
3. Owner manually reviews generated SQL before any backfill.
4. GitHub read-only smoke runs only after read-only env is configured.

not_done:
- no live write
- no formal backfill
- no production RLS/grant change

### schema-change-required SQL 形狀

-- Owner manual only. Agent must not execute.
-- This file is not evidence that production has changed.
-- Step A: optional schema change, requires Owner approval.
-- Step B: verification query, read-only.
-- Step C: fail/blocked conditions.

-- Placeholder examples:
-- :TRADE_DATE
-- :OWNER_APPROVED_SOURCE_NAME
-- :READONLY_ROLE_NAME

### read-only smoke 輸出形狀

market_theme_confirmed_evidence smoke
mode: read-only
write: disabled
schema_decision: no-schema-change
table_read: ok
rows: 0
status: fail-closed
telegram_confirmed: false
note: no production confirmed evidence available

### Owner 手機閱讀路徑

本輪不應改 Telegram。缺 production confirmed rows 時，手機上仍只能類似：

證據：production 來源不足，不作確認。

不得因 SQL / docs / smoke artifact 存在而輸出：

證據：題材 confirmed
新倉：可買

## 明確禁止事項

- 禁止 live Supabase write。
- 禁止正式 production backfill。
- 禁止 agent 直接執行 production SQL。
- 禁止直接改 production RLS / policy / role / grant。
- 禁止 live Telegram delivery。
- 禁止使用 service role secret、password、connection string。
- 禁止把 SQL template、docs、smoke 說成已上線。
- 禁止 fake confirmed、synthetic confirmed、fixture-derived confirmed。
- 禁止把 local/runtime/cache/worktree/agent context 當 production。
- 禁止改策略核心門檻。
- 禁止改 watchlist。
- 禁止未經 PM 版本契約修改 Telegram 使用者可見輸出。

## 已存在且不得回退的契約

- 最新 Telegram 使用者可見版本：v20.4.3。
- public.market_theme_confirmed_evidence production schema 已由 Owner 回傳 hard schema PASS。
- read-only loader 已存在；confirmed 條件為 support_level in ('confirmed','supporting')、evidence_status='confirmed'、freshness='fresh'。
- support_level=strong 不得 accepted 或轉 confirmed。
- handoff builder 自身不得回傳 confirmed=True。
- local/runtime/cache/worktree/test/report-derived/synthetic/default source 不得產生 SQL 或 confirmed。
- 缺 DB env、DB error、0 rows、資料不足時必須 fail closed。
- confirmed market/theme evidence 只作背景證據，不改 BUY / SELL / RR / 加減碼 / 停損停利 / 過熱 / 漲停不追門檻。
- GitHub runner 必須視為無狀態；跨日狀態與 confirmed evidence 必須來自 production DB 或 Owner 指定持久 source-of-truth。
- production ingestion、formal backfill、RLS / grant 真實啟用、actual production data smoke 尚未完成，不得被文件或 smoke 誤稱完成。

## 阻塞條件

遇到以下任一情況，Tech 或 QA 必須 blocked 或 conditional pass：

- 無法從現有摘要與 repo-side artifact 判定 schema 是否足夠。
- 宣稱 no-schema-change 但缺 evidence matrix。
- 需要 production secret、DB connection 或 Owner 手動 SQL 結果才能繼續。
- 需要知道 production role name、policy name、auth role 或 backfill source，但無法用 placeholder 安全表示。
- 任何 artifact 會寫 DB、發 Telegram、執行 live backfill 或修改 production RLS。
- dry-run validation 允許 runtime/local/report-derived/fixture 產生 confirmed。
- smoke 需要 local state 才能通過。
- SQL artifact 含 secret、live connection string、不可審核 destructive DDL/DML。
- 文件暗示 ingestion/backfill/RLS 已上線。
- Tech 改到 Telegram 使用者可見輸出但沒有新版本契約。

## 本輪停止條件

做到以下即停止：

- market_theme_confirmed_evidence schema decision 已明確產出：no-schema-change 或 schema-change-required。
- 若 no-schema-change：證據矩陣、下一步 manual SQL / read-only smoke / manual backfill 步驟已交付。
- 若 schema-change-required：manual SQL、verification SQL、fail/blocked 條件已交付。
- QA 已反證 fake confirmed、local state as production、SQL wording、read-only smoke fail-closed、schema decision evidence。
- 未完成的 production live execution、Owner 實際跑 SQL、正式 backfill、RLS/grant 真實啟用、GitHub secrets 實跑、Telegram 改版，一律只列 follow-up，不納入本輪。
