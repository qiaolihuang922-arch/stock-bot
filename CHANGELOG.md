# CHANGELOG: Evidence Phase 4 confirmed market/theme evidence SQL

  ## 任務尺寸與風險

  - 任務尺寸: normal_patch
  - 風險判斷: repo-local SQL artifact only；不改 runtime、策略、Telegram、runner、DB write path。

  ## 修改內容

  - 新增一個手動執行用 Postgres/Supabase-compatible SQL artifact。
  - 建立 public.market_theme_confirmed_evidence schema，支援 future GitHub fresh runner 從 production DB read-only reconstruction confirmed market/theme evidence。
  - SQL 內含 execution notes、欄位 comments、idempotent create table if not exists / create index if not exists。
  - RLS / permissions 僅提供 comment guidance，未啟用 policy，未假設 production role。

  ## 修改檔案

  - db/sql/evidence_phase_4_market_theme_confirmed_evidence.sql

  ## 最小改動策略

  - 只新增 TASK.md 指定的 SQL artifact。
  - 未修改產品代碼、測試、runner、formatter、strategy、watchlist 或既有 DB 存取層。
  - Repo 沒有既有 .sql 或 migration 慣例；supabase/ 僅見 functions，因此新增 db/sql/ 作為手動 artifact，避免放入可能被自動套用的路徑。

  ## 契約影響

  - 新增 repo-local SQL schema artifact。
  - 不改函式回傳、message list、payload、報文排序、CLI output、DB runtime write path。
  - SQL 欄位覆蓋: market_index、sector_theme_key、watchlist_breadth、as_of、trade_date、freshness、evidence_value、support_level、lineage、source_family、source_name。
  - 索引覆蓋: trade_date、(market_index, trade_date)、(sector_theme_key, trade_date)、(source_family, source_name, trade_date)、(trade_date, as_of desc)，另含 latest confirmed partial index。
  - Unique index 語意: 同一 trade_date + market_index + sector_theme_key + source_family + source_name 可因不同 as_of 保留多版本。

  ## 直接消費者同步

  - Owner / Production DB admin: SQL 檔案內已寫明手動在 Supabase SQL editor / Postgres console review 後執行。
  - Architect: 可依 SQL path、execution notes、no-live-write 邊界收口。
  - Future Tech: 可用本 schema 作為 production source-of-truth contract 實作 read-only loader。
  - Future QA: 可靜態驗證欄位、索引、freshness / lineage / source traceability 與 fail-closed 支援。
  - 無 runtime 直接呼叫方需同步，因本輪未改 public helper、payload、formatter 或 runner consumption logic。

  ## 未影響模組

  - 未改 Telegram formatter。
  - 未改 strategy decision / trading threshold / watchlist threshold。
  - 未改持倉狀態機。
  - 未改 replay / backfill / cron / live delivery。
  - 未執行 production DB write、live Supabase write、production backfill、live Telegram。
  - 未讀取或輸出 secrets、connection string、service role key、.env。

  ## 已跑自檢命令

  - git diff --check：通過。
  - git diff --no-index --check /dev/null db/sql/evidence_phase_4_market_theme_confirmed_evidence.sql：無 whitespace errors。
  - rg -n "drop table|truncate|delete from|update\\s+public\\.|insert into|alter table|grant\\s|service_role|password|secret|token|connection string|supabase db|psql\\s|curl\\s|wget\\s" db/sql/
    evidence_phase_4_market_theme_confirmed_evidence.sql：無命中。
  - rg -n "market_index|sector_theme_key|watchlist_breadth|as_of|trade_date|freshness|evidence_value|support_level|lineage|source_family|source_name|idx_market_theme_evidence_trade_date|
    idx_market_theme_evidence_market_trade_date|idx_market_theme_evidence_theme_trade_date|idx_market_theme_evidence_source_trade_date|idx_market_theme_evidence_trade_date_as_of" db/sql/
    evidence_phase_4_market_theme_confirmed_evidence.sql：必要欄位與索引命中。
  - command -v psql || true：本環境未提供 psql；未執行 SQL，符合本輪 no-live-execution 邊界。

  ## 殘留風險

  - 未在本地或 production DB execute SQL；需 QA 做 static SQL review。
  - RLS / permissions 需要 Owner 依 production role 手動決定，本輪未啟用 executable policy。
  - Future write/upsert path 需自行維護 updated_at；本輪未安裝 trigger，避免額外 function / trigger idempotency 風險。
  - 若 production 已存在同名 table 但欄位不完整，Owner 需先在 DB console review schema 差異後再手動處理。

  ## 旁支待辦

  - 後續另開任務實作 GitHub fresh runner read-only loader。
  - 後續另開任務定義 production RLS / permissions 與 runner role access。
  - 後續另開任務規劃 backfill / writer path；正式 DB write、backfill、live delivery 仍需 Owner 單獨批准。
