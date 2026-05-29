# QA_REPORT: Evidence Phase 4 SQL Artifact Static Review

## 測試範圍

本輪任務尺寸為 `normal_patch`，QA level 為 `L1 static SQL review + artifact contract review`。驗證範圍限於 `TASK.md`、`CHANGELOG.md`、實際 diff / untracked artifact、SQL 靜態安全與直接消費者契約；未升級到 full pytest、replay、backfill 或 live DB 驗證，符合 `TASK.md` 停止條件。

已檢查：

- `TASK.md` 與 `CHANGELOG.md`
- `git status --short`
- `git diff --stat`
- `git diff -- CHANGELOG.md`
- `db/sql/evidence_phase_4_market_theme_confirmed_evidence.sql`
- repo SQL / Supabase artifact 慣例
- 靜態安全掃描：destructive DDL/DML、grant、secret-like、live command patterns
- whitespace check：`git diff --check` 通過；untracked SQL 的 no-index whitespace check 無 whitespace error

## 風險預算與停止條件

本輪最值得抓的風險：

1. SQL artifact 不足以支援 future GitHub fresh runner read-only reconstruction。
   - 驗證：欄位、comments、freshness fail-closed states、lineage/source traceability、索引與 future query shape。
   - 停止條件：必要欄位與索引存在，且 no runtime/local cache requirement。
2. SQL 或交付文件誤導 Owner 以為 agent 已執行、可 live write、或能安全處理 production role/policy。
   - 驗證：execution notes、RLS/grant guidance、live command / secret / destructive pattern 掃描。
   - 停止條件：SQL 僅為 manual artifact，無 grant、無連線命令、無 destructive DML path。
3. `TASK.md` / `CHANGELOG.md` / worktree diff 不一致，導致 Architect 吸收錯誤範圍。
   - 驗證：比對實際 modified/untracked files 與 `CHANGELOG.md` 修改檔案。
   - 停止條件：可吸收 diff 明確限定為 `CHANGELOG.md` 與新增 SQL artifact。

## 關聯風險掃描

可吸收 diff：

- `CHANGELOG.md`：更新為 Evidence Phase 4 SQL 交付摘要。
- `db/sql/evidence_phase_4_market_theme_confirmed_evidence.sql`：新增 SQL artifact，需由 Architect 吸收時明確納入。

worktree 殘留：

- `git status --short` 僅顯示 `M CHANGELOG.md` 與 `?? db/`。
- 未看到其他產品代碼、測試、runner、formatter、strategy、watchlist diff。
- 不建議整包合併；只應吸收上述兩項與本任務一致的 diff。

SQL contract 檢查：

- 必要欄位存在：`market_index`、`sector_theme_key`、`watchlist_breadth`、`as_of`、`trade_date`、`freshness`、`evidence_value`、`support_level`、`lineage`、`source_family`、`source_name`。
- Freshness 明確包含 `fresh`、`stale`、`missing-source`、`source-error`、`insufficient-data`，comment 要求 future consumer fail closed。
- 支援索引存在：`trade_date`、`market_index/trade_date`、`sector_theme_key/trade_date`、`source_family/source_name/trade_date`、`trade_date/as_of desc`，另有 latest confirmed partial index。
- 未命中 destructive / live / secret patterns：未發現 `drop table`、`truncate`、`delete from`、`insert into`、`grant`、`service_role`、`password`、`secret`、`token`、`connection string`、`supabase db`、`psql`、`curl`、`wget`。
- 清理 / 瘦身 / refactor 證據表要求不適用；本輪不是清理任務。

## 跨區塊語意一致性

`TASK.md` 要求 repo-local manual SQL artifact、不 live execute、不改產品 runtime。`CHANGELOG.md` 宣稱同一範圍，實際 worktree 也未顯示產品代碼 diff，三者一致。

SQL execution notes 寫明 Owner 手動在 Supabase SQL editor / Postgres console review 後執行，且本任務未執行 SQL、未 backfill、未 write production DB、未 live Telegram。這與 `TASK.md` 的 no-live-write 邊界一致。

Telegram / summary / dashboard 使用者可見輸出未被修改；本輪無手機 Telegram 報文可檢查。使用者可見面集中在 Owner / DB admin 打開 SQL artifact 後的執行說明，閱讀順序先看到 manual execution only，再看到 no backfill / no write / no live Telegram，沒有把 SQL 包裝成已上線功能。

## 使用者誤讀風險

主要誤讀風險是「idempotent」可能被 Owner 理解成可無條件套到任何既有 production table。實際 SQL 對 clean create 與同 schema repeat execution 是安全的；若 production 已有同名但欄位不完整的 table，comment on column 或 index creation 可能失敗。`CHANGELOG.md` 已把此點列為殘留風險，要求 Owner 在 DB console review schema 差異後手動處理，因此不阻塞本輪，但 Architect 收口時不得說成「可不經檢查直接執行」。

未發現會讓 Owner 誤以為已完成 runner consumption、backfill 或 production write 的文字。`CHANGELOG.md` 也明確列出後續另開 read-only loader、RLS/permissions、backfill/write path。

## 質疑與反證

補充 Tech 未覆蓋的直接消費者反證：

- Production DB admin / Supabase SQL editor operator 只拿 SQL 檔時，能辨識本輪不能由 agent 執行：SQL header 已明確寫 manual execution only、review full SQL block、task did not execute SQL/backfill/write/live Telegram。
- Future runner 不需要 local/runtime/cache 才能重建：SQL artifact 本身不引入 local dependency；必要 production 欄位、lineage、source fields、trade_date/as_of、freshness 都在 table contract 中。
- Repo artifact 放置不會自動 migration 套用：repo 未見 migration SQL 慣例；放在 `db/sql/` 作 manual artifact 可接受。

負面案例：

- Fresh runner 遇到 `missing-source`、`source-error`、`insufficient-data` 時，SQL contract 能保存該狀態，comment 要求 fail closed；不應被 future consumer 當 confirmed history。
- `support_level = invalidated` 或 `evidence_status = rejected/superseded` 時，latest confirmed partial index 與 future query shape 不會把它們當 fresh confirmed 入口。

## 未測項目

- 未連線 production / staging DB，符合 `TASK.md` 明確禁止 live execute SQL。
- 未用 `psql` 實際 parse / execute；本環境未提供 `psql`，且本輪 QA 要求為 static SQL review，不以缺 DB 執行阻塞。
- 未驗證 future writer/upsert、updated_at trigger、RLS policy、runner read-only loader；這些已在 `CHANGELOG.md` 旁支待辦，非本輪範圍。
- 未跑 full pytest、replay、backfill dry-run；本輪為 SQL artifact L1，升級會超出 `TASK.md` 停止條件。

## QA 結論

通過。

條件說明：Architect 吸收時應只納入 `CHANGELOG.md` 與 `db/sql/evidence_phase_4_market_theme_confirmed_evidence.sql`，並保留「Owner 需先 review production 是否已有同名不完整 table」的執行風險。不得把本輪描述成已建 production DB、已 backfill、已啟用 runner read-only reconstruction，或已完成 RLS/permissions。
