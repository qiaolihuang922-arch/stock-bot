# TASK: Evidence Chain Production Ingestion And Read-only Ops Artifacts

## 任務狀態

- task_id: evidence_chain_production_ops_artifacts_20260529
- 任務類型：risk_patch
- 任務尺寸判斷：risk_patch
- 狀態：ready_for_tech
- 版本建議：none；本輪不改 Telegram 使用者可見報文與 VERSION。若 Tech 實際改到 Telegram header / formatter / message list，必須 blocked 回 PM 重定版本契約。
- QA 分級建議：L2+；聚焦 repo-side 非 live artifact、dry-run contract、SQL safety、read-only smoke、fresh runner fail-closed。不得擴成 full pytest、正式 backfill 或 live DB 驗證，除非 Owner 另行批准。
- 本輪主問題：把 public.market_theme_confirmed_evidence 從 manual handoff 推進到 production ingestion / backfill / RLS / read-only role / GitHub runner smoke 的可營運方案，但只交付 repo 內非 live artifact。

## Owner 問題

目前已完成並 push：

- public.market_theme_confirmed_evidence production schema。
- read-only loader。
- non-live manual handoff builder。

下一步需要在正式 production 閉環前，定義最小 repo-side 交付，讓 Owner 可以安全手動執行 production 相關步驟，且讓 Tech / QA 能驗證：

- ingestion payload contract 是否可檢查。
- backfill 是否只能 dry-run / SQL artifact，不會被 agent 直接寫入 production。
- RLS / read-only role 是否有可手動執行與可驗證 SQL。
- GitHub fresh runner 是否只讀 production table，缺資料時 fail closed。
- 文件與 smoke artifact 不會誤導成「已上線」或「已正式回填」。

本輪不是啟動 live ingestion，也不是正式 backfill。

## 使用者可見結果

Owner 本輪可見的結果不是新的 Telegram 報文，而是 repo 內可審核、可手動執行、可驗證的 operational artifact：

- ingestion payload contract / dry-run validation script。
- manual SQL template：RLS、read-only role/grant、可選 backfill insert/upsert template。
- read-only smoke command / docs：給 GitHub runner 或本機只讀驗證使用。
- RLS verification SQL：只讀檢查 policy、grant、role、table visibility。
- CHANGELOG.md 說明哪些是 repo 可實作，哪些必須 Owner 手動批准或執行。
- QA_REPORT.md 驗證沒有 fake confirmed、沒有 local state 當 production、沒有 live write、沒有把 artifact 說成已上線。

Owner 手機 Telegram 閱讀路徑本輪預期不變；production table 無資料或無權限時，報文仍只能呈現來源不足 / 不作確認，不得顯示 confirmed 或推薦語意。

## 非目標

- 不做 live Supabase write。
- 不做正式 production backfill。
- 不直接改 production RLS / policy / grant / role。
- 不 live Telegram delivery。
- 不改 BUY / SELL / RR / 加減碼 / 停損停利 / 過熱 / 漲停不追門檻。
- 不把 confirmed market/theme evidence 變成放寬買點。
- 不新增外部新聞 / 題材 ingestion provider。
- 不改 watchlist。
- 不做全 repo 清理、策略重設或 unrelated refactor。
- 不把 runtime/local/cache/worktree/agent context 當 production source-of-truth。

## 影響模組

Tech 可在最小範圍內新增或修改 repo-side artifact，實際檔名依現有結構調整：

- services/market_theme_evidence_store.py
- core/market_theme_evidence.py
- GitHub scheduled report / generator entrypoint 的 read-only smoke 或 env check helper
- scripts/*：只允許 dry-run / validation / read-only smoke script
- db/sql/*：manual SQL template，禁止自動執行 production
- docs/handoff/*：Owner 手動執行步驟與狀態說明
- 對應局部 tests / fixtures

不得修改 production DB、runner secrets、live Telegram 發送流程、正式 backfill runner。

## 直接消費者

- Owner：手動審核與執行 SQL / backfill / RLS 步驟。
- Architect：只依 TASK.md / CHANGELOG.md / QA_REPORT.md 判斷是否可進入 production 閉環下一步。
- Tech：依本任務交付非 live repo-side artifact。
- QA：驗證 artifact safety、fail-closed、無 live write、無 fake confirmed。
- GitHub fresh runner：未來只讀 production table；本輪只提供 smoke command / docs，不要求實際 production secret。
- services/market_theme_evidence_store.py read-only loader：production source-of-truth consumer。
- core/market_theme_evidence.py / core/generator.py：只能消費 read-only loader 結果；不得靠 local state 補 confirmed。
- Telegram Owner 手機報文：本輪不改版；缺 production confirmed rows 時仍顯示來源不足或不作確認。

## 輸出契約

### Repo-side Artifact Contract

Tech 必須交付至少以下四類 artifact，且全部為 non-live：

1. ingestion payload contract
- 定義 public.market_theme_confirmed_evidence 可接受 rows 的必要欄位、allowed values、source family、freshness、lineage。
- 提供 dry-run validation script 或 helper。
- validation 失敗不得輸出 insert/upsert SQL。
- confirmed 不得由 local/runtime/report-derived/fixture 推導。
2. manual SQL template
- 只作 Owner 手動執行。
- 必須在檔案 header 明確寫：agent 未執行、不是 migration、不是已上線證據。
- 若包含 RLS / grant / policy / backfill insert/upsert，必須以清楚段落分開，且需要 Owner 單獨批准。
- 不得包含 project URL、secret、service role key、password。
3. read-only smoke command/docs
- 提供本機或 GitHub runner 可用的只讀 smoke 入口。
- 必須區分 missing env、permission denied、0 rows、insufficient rows、valid rows。
- smoke 不得寫 DB，不得發 Telegram。
4. RLS verification SQL
- 只讀檢查 table visibility、policy、grant、role、RLS enabled。
- 結果只能代表「可供 Owner 判讀」，不得宣告 production 已完成，除非 Owner 回傳執行結果。

### Manual SQL Shape Required

Tech 必須輸出 Owner 可審核的 SQL artifact，形狀至少包含：

-- Manual only. Agent must not execute.
-- Step A: optional read-only role/grant, requires Owner approval.
-- Step B: optional RLS policy, requires Owner approval.
-- Step C: optional backfill/upsert template, requires Owner approval.
-- Step D: read-only verification queries.

-- Example placeholders must be explicit:
-- :READONLY_ROLE_NAME
-- :OWNER_APPROVED_SOURCE_NAME
-- :TRADE_DATE

若實際 production role name、Supabase auth role、policy naming convention 或 backfill source 未知，SQL 必須保留 placeholder 並在 docs 標記 owner-input-required，不得假設已可直接上線。

### CHANGELOG.md 必須包含

- 修改內容。
- 修改檔案。
- 契約影響。
- 版本同步：本輪不升版、不改 Telegram；若不符則 blocked。
- 直接消費者同步。
- Repo-side vs Owner manual boundary table：
- item
- repo artifact
- live side effect
- Owner approval needed
- status
- Fresh GitHub runner smoke matrix：
- missing env
- permission denied
- 0 rows
- stale rows
- unsupported support_level
- valid fresh confirmed/supporting rows
- 自檢命令與結果。
- 殘留風險。

## 驗收條件

1. 至少新增或更新一個 ingestion payload dry-run validation artifact。
2. 至少新增一份 manual SQL template，明確包含 RLS/read-only role/grant/backfill/verification 的安全邊界或 owner-input-required 標記。
3. 至少新增一個 read-only smoke command/docs，可驗 GitHub fresh runner 只讀 table 的行為。
4. RLS verification SQL 只能做只讀檢查，不得執行 production 改動。
5. 所有 artifact header 必須明確寫：未 live write、未正式 backfill、未改 production RLS、未上線。
6. 缺 env、DB error、permission denied、0 rows、insufficient data、stale rows、unsupported support_level 都必須 fail closed。
7. fake/local/runtime/report-derived/test fixture source 不得產生 confirmed row、不得通過 dry-run validation。
8. Tech 不得執行 production SQL，不得寫 Supabase，不得發 Telegram。
9. QA 必須反證：沒有 fake confirmed、沒有 local state 當 production、沒有 live write、fresh runner 只讀 production table、SQL/smoke artifact 不誤導為已上線。
10. 本輪完成後，只能表示「production ingestion/backfill/RLS/read-only smoke 方案與 artifact ready for Owner manual execution」，不得表示 production ingestion 已完成。

## 範例或 Fixture

### Dry-run Validation Fixture

input:
source_family=production_db
source_name=owner_approved_market_breadth
freshness=fresh
support_level=confirmed
evidence_status=confirmed
trade_date=2026-05-29
lineage={approved_by_owner:true}

expected:
valid=true
may_render_manual_sql=true
live_write=false

input:
source_family=runtime_diagnostic
source_name=telegram_report_text
freshness=fresh
support_level=confirmed
evidence_status=confirmed

expected:
valid=false
may_render_manual_sql=false
reason=fake-or-nonpersistent-source

### Read-only Smoke Output Shape

market_theme_confirmed_evidence smoke
mode: read-only
write: disabled
env: present
table_read: ok
rows: 0
status: fail-closed
telegram_confirmed: false
note: no production confirmed evidence available

### Owner 手機閱讀路徑

本輪不應改 Telegram。缺 production confirmed rows 時，手機上仍只能類似：

證據：production 來源不足，不作確認。

不得因 artifact 存在而輸出：

證據：題材 confirmed
新倉：可買

## 明確禁止事項

- 禁止 live Supabase write。
- 禁止正式 backfill。
- 禁止 live Telegram delivery。
- 禁止 agent 直接執行 production SQL。
- 禁止直接改 production RLS / policy / role / grant。
- 禁止使用 service role secret、password、connection string。
- 禁止把 SQL template 或 smoke docs 描述成已上線。
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
- production RLS / read-only role / formal backfill 尚未完成，不得被文件或 smoke 誤稱完成。

## 阻塞條件

遇到以下任一情況，Tech 或 QA 必須 blocked 或 conditional pass：

- 需要 production secret、DB connection 或 Owner 手動 SQL 結果才能繼續。
- production role name、policy name、auth role 或 backfill source 不明，且 SQL 無法用 placeholder 安全表示。
- 任何 artifact 會寫 DB、發 Telegram、執行 live backfill 或修改 production RLS。
- dry-run validation 允許 runtime/local/report-derived/fixture 產生 confirmed。
- smoke 需要 local state 才能通過。
- SQL artifact 含 secret、live connection string、不可審核 destructive DDL/DML。
- 文件暗示 ingestion/backfill/RLS 已上線。
- Tech 改到 Telegram 使用者可見輸出但沒有新版本契約。

## 本輪停止條件

做到以下即停止：

- ingestion payload contract / dry-run validation artifact 已交付。
- manual SQL template 已交付，且 live 步驟全部標為 Owner manual / approval required。
- read-only smoke command/docs 已交付。
- RLS verification SQL 已交付。
- QA 完成 fake confirmed、local state、no live write、fresh runner read-only、artifact wording 五類反證。

以下旁支只記 follow-up，不納入本輪：

- Owner 實際執行 SQL。
- 正式 production backfill。
- production RLS / grant 真實啟用。
- GitHub runner 使用 production secrets 實跑。
- 新外部 ingestion provider。
- Telegram 報文改版。
- 策略 evidence chain 下一階段決策調整。
