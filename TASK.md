# TASK: Evidence Phase 4 production DB schema SQL for confirmed market/theme evidence

## 任務狀態

- task_id: evidence-phase-4-confirmed-market-theme-schema-sql
- 任務類型: normal_patch
- 狀態: ready_for_tech
- 版本建議: 本輪不升版，因為只新增 repo-local SQL artifact，不改 Telegram / CLI / 策略 / runner 行為。
- QA 分級建議: L1 static SQL review + artifact contract review；不得升級到 live DB 驗證。
- 本輪停止條件: Tech 產出一個可手動執行的 Postgres/Supabase-compatible SQL 檔案，QA 靜態確認語法、安全邊界、契約欄位與 read-only reconstruction 支援後即完成。任何 backfill、production DB 執行、策略消費邏輯、Telegram 顯
示、watchlist 門檻調整只記待辦，不納入本輪。

## Owner 問題

Owner 已批准用 SQL 建立 production DB tables/fields，用於持久保存「已確認的 market/theme evidence」，讓 GitHub fresh runner 未來可從 production DB 讀取並重建跨日證據判斷，而不是依賴本機暫存、worktree、runtime dict、
agent 對話或非持久 context。

本輪只要交付一段可由 Owner 手動執行的 SQL，不做 live execution。

## 使用者可見結果

- Repo 內新增一個 SQL artifact，路徑由 Tech 依現有慣例選擇，優先 db/sql/...，若無慣例可放 docs/...。
- Architect / Owner 可看到：
- SQL 檔案路徑。
- 一個完整、可複製執行的 SQL block。
- 明確 execution notes：手動在 Supabase/Postgres SQL editor 執行；本輪不得由 agent 執行。
- 本輪不改 Telegram 報文、CLI output、交易建議、watchlist 結果或任何 runtime product behavior。

## 非目標

- 不連線 production DB。
- 不 live execute SQL。
- 不做 live Supabase write。
- 不做 backfill。
- 不新增 / 修改 strategy decision、trading threshold、watchlist threshold、Telegram formatter、runner read logic。
- 不導入完整 evidence consumption pipeline。
- 不要求 QA 在 production 或 staging DB 實際建表。
- 不重構既有 DB schema、migration 系統或資料讀取層。

## 影響模組

- 直接影響:
- repo-local SQL artifact for production schema setup。
- DB schema documentation / execution notes。
- 不應影響:
- Telegram formatter。
- strategy / scoring / watchlist selection。
- GitHub Actions runtime behavior。
- production DB data。
- replay / backfill / cron / live delivery。

## 直接消費者

- Owner: 手動檢查並執行 SQL。
- Architect: 收口時確認 SQL path、execution notes 與 no-live-write 邊界。
- Future Tech task: 後續實作 runner read-only reconstruction 時，以本 schema 作為 production source-of-truth。
- Future QA task: 驗證 GitHub fresh runner 是否只讀 production DB 並 fail closed。
- Production DB admin / Supabase SQL editor operator: 手動執行 SQL 的直接操作者。

## 輸出契約

Tech 必須新增一個 repo-local SQL 檔案，包含 idempotent Postgres/Supabase-compatible DDL。SQL 必須支援保存 confirmed market/theme evidence，至少涵蓋以下資料契約。

必要欄位或等價欄位:

- market_index: 市場指數或市場範圍識別，例如 TWSE, TPEx, NASDAQ, SPY。
- sector_theme_key: sector / theme 的穩定 key，例如 semiconductor, ai_server, shipping。
- watchlist_breadth: watchlist breadth evidence，可為 numeric / jsonb / structured 欄位，但須能追溯當日 breadth 狀態。
- as_of: evidence 生成或觀測時間，需含 timezone-aware timestamp。
- trade_date: 交易日期，供跨日重建與查詢。
- freshness: freshness 狀態或 freshness metadata，需能區分 fresh / stale / missing-source / source-error / insufficient-data，具體型別由 Tech 選擇但需有 comment。
- evidence_value: evidence 原始值或標準化值，可用 numeric / jsonb / text 組合，但須保留可重建判斷的值。
- support_level: confirmed support level，例如 confirmed, supporting, weak, invalidated，實際 enum/check 可由 Tech 定義。
- lineage: lineage metadata，需能記錄此 evidence 如何產生，例如 upstream table/source key/run id/rule version，可用 jsonb。
- source_family: source family，例如 market_data, watchlist, theme_classifier, manual_review。
- source_name: 具體來源名稱，例如 provider、job name、calculation name。
- 建議欄位:
- created_at
- updated_at
- evidence_status 或可等價表示 confirmed / rejected / superseded 的欄位。
- notes 或 metadata jsonb，若有助於 future compatibility。

Idempotency contract:

- SQL 必須可重複執行，不因 table / index / policy 已存在而失敗。
- 使用 create table if not exists、create index if not exists 或等價安全寫法。
- 若使用 enum / policy / trigger，需避免重跑失敗，或以清楚 comment 說明手動處理方式。

Index contract:

- 至少提供支援 future read-only reconstruction 的索引:
- trade_date
- (market_index, trade_date)
- (sector_theme_key, trade_date)
- (source_family, source_name, trade_date)
- 可查最新 evidence 的 as_of 或 (trade_date, as_of) 索引。
- 若使用 unique constraint / upsert key，需 comment 說明唯一性語意，例如同一 trade_date + market_index + sector_theme_key + source_family + source_name 是否允許多筆版本。

RLS / permissions guidance:

- 若 Tech 能以安全、無副作用、通用 Supabase DDL 表達最小 guidance，可加入 comment 或非啟用式範例。
- 不得假設 production role 名稱。
- 不得在 SQL 中 grant 過寬權限。
- 若不確定現有 Supabase role/policy，應以 SQL comment 說明「RLS / grants 需由 Owner 按 production role 手動決定」，不要啟用危險 policy。

Execution notes contract:

- SQL 檔案或 CHANGELOG.md 必須列出 exact execution notes:
- 檔案路徑。
- 手動執行位置: Supabase SQL editor / Postgres console。
- 本輪 agent 未執行 SQL。
- 執行前建議 Owner 在 DB console review。
- 若有 RLS/grant comment，需說明哪些是 guidance、哪些是 executable DDL。

## 已存在且不得回退的契約

- Production source-of-truth 契約: 跨日狀態、歷史分類、連續觀察天數、歷史證據權重、已執行事件等正式判斷不得依賴 local/runtime/context；future runner 必須以 production DB 或 Owner 指定持久來源為準。
- Fail-closed 契約: production DB / 持久來源缺資料、讀取失敗、欄位不足或可信度不足時，future consumption 必須走 missing-source / source-error / insufficient-data / fail closed，不得用 runtime fallback 補成 confirmed
history。
- 本輪 no-live-write 契約: 不 live execute SQL、不寫 production DB、不 backfill、不 live Telegram delivery。
- 策略不變契約: 本輪不改 strategy decision、threshold、watchlist selection、持倉狀態機或報文分類。
- GitHub fresh runner 契約: schema 必須讓未來 fresh runner 可只讀 production DB 重建 confirmed market/theme evidence；不得要求本機檔案、agent 對話或 worktree cache 才能判斷。

## 驗收條件

1. SQL artifact 存在於 repo-local path，且 Tech 在 CHANGELOG.md 明確列出 path。
2. SQL 為單一可手動執行 block，Postgres/Supabase-compatible，且具備 idempotent DDL。
3. SQL schema 明確包含或等價支援:
- market_index
- sector_theme_key
- watchlist_breadth
- as_of
- trade_date
- freshness
- evidence_value
- support_level
- lineage
- source_family
- source_name
4. SQL 有 comments 說明欄位用途，尤其是 freshness、lineage、support_level、source fields。
5. SQL 包含 reconstruction 查詢需要的 indexes，至少覆蓋 trade_date、market/date、theme/date、source/date、latest/as_of 查詢。
6. SQL 不包含 production connection string、secret、token、service role key 或任何 live execution command。
7. SQL 不包含 destructive migration，例如無條件 drop table、truncate、大量 update/delete production data。
8. Tech 不修改產品行為檔案；若因格式或文件慣例需更新文檔，必須限於 SQL execution notes。
9. CHANGELOG.md 必須說明本輪沒有 production DB write、沒有 backfill、沒有 Telegram live、沒有策略/threshold/watchlist 改動。
10. QA 必須做 static safety validation，不得 live execute SQL；需明確檢查 GitHub fresh runner 未來可透過 production DB read-only reconstruction 取得必要欄位。
11. QA 結論若發現 SQL 無法支援 freshness / lineage / source traceability 或 idempotency，必須 blocked。

## 範例或 fixture

SQL shape 示例，Tech 可調整命名與型別，但不得低於此資訊量:

-- Evidence Phase 4: confirmed market/theme evidence source-of-truth.
-- Manual execution only. Do not run from agents in this task.

create table if not exists public.market_theme_confirmed_evidence (
id bigserial primary key,
trade_date date not null,
as_of timestamptz not null,
market_index text not null,
sector_theme_key text not null,
source_family text not null,
source_name text not null,
freshness text not null,
evidence_value jsonb not null default '{}'::jsonb,
watchlist_breadth jsonb not null default '{}'::jsonb,
support_level text not null,
lineage jsonb not null default '{}'::jsonb,
metadata jsonb not null default '{}'::jsonb,
created_at timestamptz not null default now(),
updated_at timestamptz not null default now()
);

create index if not exists idx_market_theme_evidence_trade_date
on public.market_theme_confirmed_evidence (trade_date);

create index if not exists idx_market_theme_evidence_market_trade_date
on public.market_theme_confirmed_evidence (market_index, trade_date);

create index if not exists idx_market_theme_evidence_theme_trade_date
on public.market_theme_confirmed_evidence (sector_theme_key, trade_date);

Future read-only reconstruction query shape:

select *
from public.market_theme_confirmed_evidence
where trade_date = :trade_date
and freshness in ('fresh', 'confirmed')
order by market_index, sector_theme_key, as_of desc;

Execution notes shape expected from Tech:

SQL path: db/sql/<filename>.sql
How to execute: Owner manually opens Supabase SQL editor, reviews the full SQL, then runs the block once. It is designed to be idempotent for repeat execution.
Not executed in this task: production SQL execution, backfill, live DB write, Telegram live delivery.

## 明確禁止事項

- 禁止 agent 執行 SQL。
- 禁止連線 production DB。
- 禁止讀取或輸出 secrets、.env、service role key、connection string。
- 禁止 live Supabase write。
- 禁止 production backfill。
- 禁止 Telegram live delivery。
- 禁止修改 watchlist/trading threshold。
- 禁止修改 strategy decision 或持倉狀態機。
- 禁止用 runtime/local cache 當作 confirmed evidence source-of-truth。
- 禁止為了本 schema 順手改 runner consumption logic。
- 禁止新增過寬 grants 或假設 production roles。
- 禁止 destructive DDL/DML，除非純 comment guidance 且不在 executable path。

## 阻塞條件

- Tech 找不到 repo 既有 SQL/docs artifact 慣例且無法判斷放置位置時，需 blocked 要求 Architect 指定 path。
- 若現有專案已有正式 migration 框架，但 Tech 無法確認新增 artifact 是否應進 migration path，需 blocked，不得放錯造成 production auto-apply。
- 若 Owner / Architect 要求本輪 live execute SQL、backfill 或驗證 production DB 實際建表，需 blocked，因為本輪明確只產 repo-local SQL artifact。
- 若無法以 SQL 表達 lineage / freshness / source traceability，需 blocked，不得交付只含普通行情欄位的 schema。
- 若 RLS / permissions 需要 production role 細節才能安全定義，Tech 不得臆測，應改用 comment guidance；若 Owner 要求 executable policy，需 blocked 要求補 role/policy 規格。
