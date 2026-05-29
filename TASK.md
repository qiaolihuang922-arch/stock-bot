# TASK: Evidence Phase 4 production schema read-only verification

## 任務狀態

- task_id: evidence_phase_4_prod_schema_readonly_verify_20260529
- 任務類型: process
- 任務尺寸判斷: process
- 狀態: ready_for_qa
- 版本建議: 本輪不升版；不影響 Telegram / CLI / 產品報文版本字串
- QA 分級建議: L1
- 單一主問題: Owner 已建立 production table，需要只讀確認 public.market_theme_confirmed_evidence 是否存在且符合 Evidence Phase 4 SQL contract
- 單一輸出契約: 產出一份可核驗的 schema verification 結論：pass / blocked / conditional，並列出 table、columns、check constraints、indexes、optional comments 的比對結果
- 不擴大到 loader、writer、backfill、RLS policy、strategy consumption、watchlist 或 Telegram 報文修改

## Owner 問題

Owner 已表示 production table 已建立。現在需要確認 production DB 內的 public.market_theme_confirmed_evidence 是否真的存在，且是否符合前一輪 SQL artifact 的契約，避免後續 read-only loader 或 GitHub fresh runner 依賴錯誤
schema。

本輪只做 schema / contract read-only verification。若安全、已配置的只讀 Supabase/Postgres connection 存在，QA 只能跑 schema introspection 查詢；若沒有連線，必須提供 Owner 可手動執行的精確只讀 SQL，並標記 blocked 或
conditional。

## 使用者可見結果

- Owner 會看到 QA/交接摘要明確回答：
- public.market_theme_confirmed_evidence 是否存在
- 欄位是否符合 SQL artifact contract
- freshness、support_level、evidence_status 等 check constraint 允許值是否符合 SQL contract
- indexes 是否存在，包含 latest confirmed partial index
- optional comments 是否存在或缺失
- 若無安全連線，Owner 會得到可直接貼到 Supabase SQL editor 的 read-only verification SQL
- 本輪不會改 Telegram 報文，也不會產生交易建議變化。

## 非目標

- 不改產品 Python / app code
- 不改 SQL artifact 的 schema intent
- 不新增 migration / rollback / RLS policy
- 不新增 loader / writer / backfill
- 不做 live Supabase write
- 不做正式 backfill
- 不做 live Telegram delivery
- 不改 strategy / watchlist / scheduler
- 不驗證其他 production table
- 不驗證資料內容是否足夠 confirmed，只驗 schema contract
- 不輸出 secrets、connection string、token、service role key 或憑證片段

## 影響模組

- 直接 scope:
- public.market_theme_confirmed_evidence
- Evidence Phase 4 SQL artifact contract: db/sql/evidence_phase_4_market_theme_confirmed_evidence.sql
- handoff/status docs 的 verification 摘要
- 直接消費者:
- Owner / operator：判斷 production table 是否已正確建立
- Architect：根據 QA 結論更新狀態與下一步
- 未來 Tech：若後續開 read-only loader，只能依通過的 schema contract 接手
- 不應影響:
- Telegram formatter
- strategy decision
- DB write path
- replay / backfill
- watchlist

## 直接消費者

- Owner：需要知道 production table 是否可作為 Phase 4 confirmed evidence 的持久 source-of-truth。
- QA：需要只讀 introspection query 與明確比對項目。
- Architect：需要可吸收進 DISPATCH.md / CURRENT_STATE.md 的簡短狀態。
- 後續 Tech：若 schema 通過，才可另開 read-only loader 任務；不得依聊天紀錄猜 schema。

## 輸出契約

QA 輸出必須包含以下 verification matrix：

┌────────────────────────────────┬───────────────────────┬──────────────────────────────────┬────────────────────┐
item                           │ expected source       │ observed                         │ result             │
├────────────────────────────────┼───────────────────────┼──────────────────────────────────┼────────────────────┤
table exists                   │ SQL artifact contract │ production introspection result  │ pass/fail          │
columns                        │ SQL artifact contract │ column name/type/null/default    │ pass/fail          │
check constraints              │ SQL artifact contract │ constraint definitions           │ pass/fail          │
freshness values               │ SQL artifact contract │ allowed values from constraint   │ pass/fail          │
support_level values           │ SQL artifact contract │ allowed values from constraint   │ pass/fail          │
evidence_status values         │ SQL artifact contract │ allowed values from constraint   │ pass/fail          │
indexes                        │ SQL artifact contract │ index definitions                │ pass/fail          │
latest confirmed partial index │ SQL artifact contract │ partial index predicate/order    │ pass/fail          │
comments                       │ SQL artifact contract │ comment presence/content summary │ optional/pass/warn │
└────────────────────────────────┴───────────────────────┴──────────────────────────────────┴────────────────────┘

本輪 PM 摘要已知欄位契約至少包含：market_index、sector_theme_key、watchlist_breadth、as_of、trade_date、freshness、evidence_value、support_level、lineage、source_family、source_name。若 SQL artifact 另有
evidence_status 或其他欄位，QA 必須以 SQL artifact 為準；若 production table 與 SQL artifact 不一致，不能自行判定可接受。

若沒有安全只讀連線，QA 必須輸出 Owner 可手動執行的 read-only SQL，不得宣告 schema pass。

## 已存在且不得回退的契約

- public.market_theme_confirmed_evidence 是 Phase 4 production confirmed market/theme evidence table。
- 目的為未來 GitHub fresh runner 從 production DB read-only reconstruction confirmed market/theme evidence。
- confirmed / ready evidence 必須來自 production_db 或 owner_approved_persistent source family，runtime / local / report-derived / diagnostic 不得 confirmed。
- runtime / local context 不得作為跨日 source-of-truth。
- 本輪只允許 read-only schema introspection；不得 write、backfill、live Telegram。
- 固定 8 份 Markdown 不得刪除。
- 本輪不升 Telegram / CLI 版本，因無使用者可見報文變更。
- 若 SQL artifact 的完整 constraint/index contract 與摘要不一致，以 SQL artifact 為唯一比對來源；QA 不得用 PM 摘要覆蓋 SQL contract。

## 驗收條件

1. 有安全只讀 connection 時，QA 必須完成只讀 introspection 並列出：
- table existence
- all columns with type/null/default
- all check constraints
- allowed values for freshness、support_level、evidence_status
- all indexes
- latest confirmed partial index 是否存在且 predicate/order 符合 SQL artifact
- comments 是否存在；comments 缺失只可列 warning，除非 SQL artifact 明確要求 comments 為硬契約
2. 無安全只讀 connection 時，QA 必須：
- 標記 blocked 或 conditional
- 提供完整 read-only verification SQL
- 說明 Owner 執行後需回傳哪些結果欄位
- 不得宣告 production schema 已通過
3. 驗證 SQL 必須只讀：
- 只能查 information_schema、pg_catalog、obj_description / col_description 等 metadata
- 不得 insert/update/delete/drop/truncate/create/alter/grant/revoke
- 不得查 secrets 或輸出 connection settings
4. 若 production table 缺欄位、constraint、index 或 latest confirmed partial index，QA 必須標記 blocked，並列出差異；不得自行修 DB。
5. 若只發現 optional comments 缺失，QA 可標記 conditional pass，但必須說明 comments 不阻塞 runtime schema consumption。
6. 驗證完成即停止，不做任何 product code、strategy、Telegram、loader、backfill 或其他 table 檢查。

## 範例或 fixture

QA 若無安全連線，應提供形狀接近以下的 read-only SQL 給 Owner：

-- Read-only schema verification for public.market_theme_confirmed_evidence.
-- Do not include credentials. Do not run write/backfill statements.

select to_regclass('public.market_theme_confirmed_evidence') as table_regclass;

select
column_name,
data_type,
udt_name,
is_nullable,
column_default,
ordinal_position
from information_schema.columns
where table_schema = 'public'
and table_name = 'market_theme_confirmed_evidence'
order by ordinal_position;

select
conname,
pg_get_constraintdef(c.oid) as constraint_def
from pg_constraint c
join pg_class t on t.oid = c.conrelid
join pg_namespace n on n.oid = t.relnamespace
where n.nspname = 'public'
and t.relname = 'market_theme_confirmed_evidence'
order by conname;

select
indexname,
indexdef
from pg_indexes
where schemaname = 'public'
and tablename = 'market_theme_confirmed_evidence'
order by indexname;

select
obj_description('public.market_theme_confirmed_evidence'::regclass, 'pg_class') as table_comment;

QA report expected shape:

schema verification: blocked

table exists: pass
columns: fail
- missing from production: evidence_status
constraints: fail
- freshness values observed: fresh, stale
- expected from SQL artifact: fresh, stale, missing, source-error
indexes: fail
- missing latest confirmed partial index
comments: warning only
no writes/backfill/live Telegram executed

## 明確禁止事項

- 禁止輸出 secrets、connection string、token、service role key
- 禁止任何 write SQL：insert/update/delete/drop/truncate/create/alter/grant/revoke
- 禁止 backfill、replay write、live Supabase write
- 禁止 live Telegram delivery
- 禁止改產品代碼、測試或 SQL artifact schema intent
- 禁止檢查其他 table，除非 metadata query 為定位 public.market_theme_confirmed_evidence 必要
- 禁止把無連線狀態說成驗證通過
- 禁止把 optional comments 缺失擴大成 schema 重建任務，除非 SQL artifact 明確定義 comments 為硬契約
- 禁止把本輪擴成 read-only loader、RLS、performance、資料品質或 confirmed evidence 策略任務

## 阻塞條件

- 沒有安全、已配置、明確只讀的 Supabase/Postgres connection。
- 連線存在但權限不足以查 schema metadata。
- SQL artifact contract 無法取得或與 handoff/status 摘要矛盾，導致無法判定 expected columns / constraints / indexes。
- production table 不存在。
- production table 存在但缺少 SQL artifact 定義的 hard-contract column、check constraint 或 index。
- freshness、support_level、evidence_status allowed values 與 SQL artifact 不一致。
- latest confirmed partial index 缺失或 predicate/order 與 SQL artifact 不一致。
- 驗證過程需要 write / migration / backfill 才能繼續。

## 本輪停止條件

完成以下任一結果即停止：

- 有安全只讀連線：完成 public.market_theme_confirmed_evidence schema introspection，輸出完整 verification matrix 與 pass / blocked / conditional 結論。
- 無安全只讀連線：輸出 Owner 可手動執行的精確 read-only SQL，標記 blocked 或 conditional，並說明需回傳的結果。
- 發現 schema drift：列出 drift，標記 blocked，不修 DB。

旁支問題只記待辦，不納入本輪：

- 是否實作 read-only loader
- 是否寫入 confirmed evidence
- 是否 backfill historical evidence
- 是否新增 RLS / grants / policies
- 是否做 data freshness runtime consumption
- 是否優化 query performance
- 是否讓 Telegram 顯示 confirmed evidence
