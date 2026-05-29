# TASK: 修正 Supabase SQL artifact 結尾語法錯誤

## 任務狀態

- task_id: urgent_tiny_patch_sql_evidence_phase_4_syntax
- 任務類型: tiny_patch
- 狀態: ready_for_tech
- 版本建議: 本輪不升版；不影響 Telegram / CLI / 產品報文版本字串
- QA 分級建議: L1
- 任務尺寸判斷: tiny_patch
- 單一主 bug: db/sql/evidence_phase_4_market_theme_confirmed_evidence.sql 在 Supabase 執行時出現 ERROR 42601 syntax error at end of input
- 單一輸出契約: 該 SQL artifact 必須可作為一個完整 Supabase/Postgres SQL block 複製並解析
- 不擴大到 schema 重設、策略調整、全量 SQL 清理、production 驗證或 L3 測試

## Owner 問題

Owner 需要一份更安全、完整、可複製到 Supabase SQL editor 執行的 SQL artifact，避免因結尾缺失、分號不足、parser-ambiguous construct 或 copy block 不完整導致 syntax error at end of input。

本輪也需讓交接文件清楚說明可能原因與正確複製 / 執行方式，避免再次只貼到部分 SQL 或誤以為要 live backfill。

## 使用者可見結果

- Owner 打開 db/sql/evidence_phase_4_market_theme_confirmed_evidence.sql 時，看到的是一個完整 SQL block：
- 每個 statement 明確以 ; 結尾
- 避免不必要的 parser-ambiguous constructs
- 無缺失的 END / $$ / ) / ;
- 可整段複製到 Supabase SQL editor
- Owner 打開 docs/handoff 相關文件時，能看到：
- 本 SQL 的用途
- 建議整段複製執行
- 不要連 production 做驗證
- 不做 backfill
- 可能錯因摘要

## 非目標

- 不改產品 Python / app code
- 不改策略、報文、Telegram formatter、watchlist、排程入口
- 不新增或執行 production backfill
- 不連線 production Supabase
- 不做 live write 驗證
- 不新增 grants、secrets、token 或 production credential 依賴
- 不做全量 SQL 目錄清理
- 不重設 schema intent
- 不把本輪擴成 DB migration framework 重構

## 影響模組

- 直接檔案:
- db/sql/evidence_phase_4_market_theme_confirmed_evidence.sql
- docs/handoff 中直接提到此 SQL artifact 的交接文件
- 直接消費者:
- Owner / operator 手動複製 SQL 到 Supabase SQL editor
- Tech / QA 的本地非 production SQL syntax 檢查流程
- Architect 後續交接摘要
- 不應影響:
- Telegram 報文
- strategy decision
- DB runtime read/write path
- production runner
- backfill / replay

## 直接消費者

- Owner: 需要可複製的一整段 SQL artifact 與安全執行注意事項
- Supabase SQL editor / Postgres parser: 需要完整、明確終止的 SQL statement
- QA: 需要能用 static scan 與本地非 production parser 驗證語法完整性

## 輸出契約

- db/sql/evidence_phase_4_market_theme_confirmed_evidence.sql 必須維持原本 schema intent，只修正語法完整性與可複製執行安全性。
- SQL artifact 必須是單一完整 copy block：
- statement 明確分號結尾
- 若使用 function / DO block / dollar quote，必須有成對 delimiter 且最後有 ;
- 若可避免，移除或簡化容易造成 Supabase editor parser 歧義的 construct
- 不包含 destructive DML / DDL，例如 DROP TABLE, TRUNCATE, 無保護的 DELETE / UPDATE
- 不包含 grants、secrets、credential、production-specific token
- docs/handoff 只補本 artifact 的交接說明：
- 如何整段複製
- 不要局部複製
- 不要連 production 驗證
- 不做 backfill
- 可能原因：SQL block 結尾缺少必要 terminator、dollar quote / BEGIN END / parenthesis 未閉合、或複製時漏掉尾段

## 已存在且不得回退的契約

- 固定 8 份 Markdown 不得刪除。
- 本輪不改產品代碼、不改策略、不改 Telegram / CLI 使用者可見版本。
- 不允許 live Supabase write、正式 backfill、live Telegram delivery。
- SQL artifact 的 schema intent 必須保留；只能做語法完整性、可複製性與安全註記修正。
- 若 Tech 發現原 SQL 實際意圖不明、需要新增/刪除欄位、改 table ownership 或改 migration strategy 才能修，必須 blocked 回報，不得自行改 schema intent。

## 驗收條件

1. SQL artifact 靜態完整性通過：
- 檔案最後一個有效 statement 明確以 ; 結尾
- 沒有未閉合的 $$ / quote / parenthesis / BEGIN ... END
- 每個 SQL statement 有明確 terminator
- 沒有 destructive/write DML、grants、secrets 或 production credential
2. 本地非 production parser 驗證：
- Tech 應先嘗試使用可用本地 parser，例如 psql 或已存在的 local non-production Postgres container
- 若本地 parser 可用，需證明該 SQL 至少能被 parser 接受或指出任何剩餘 non-production parse error
- 若 psql / local container 不可用，不得連 production；改為簡化 SQL 並在 CHANGELOG.md 說明未跑 parser 的原因與已做 static scan
3. docs/handoff 有本 artifact 的安全複製 / 執行 notes，且沒有要求 production 驗證或 backfill。
4. QA 至少做：
- static scan
- 若本地非 production parser 可用，執行 syntax validation
- 確認未連 production、未執行 backfill、未加入 destructive DML / grants / secrets

## 範例或 fixture

SQL artifact 期望形狀：

-- Purpose: create/adjust evidence phase 4 market theme confirmed evidence schema.
-- Copy and execute this entire file as one block in Supabase SQL editor.
-- Do not run production backfill from this artifact.

create table if not exists example_table (
id uuid primary key,
created_at timestamptz not null default now()
);

create index if not exists example_table_created_at_idx
on example_table (created_at);

docs/handoff 期望說明形狀：

### evidence_phase_4_market_theme_confirmed_evidence.sql

Copy the entire SQL file into Supabase SQL editor and execute it as one block.
Do not copy only the middle section; missing the final semicolon or closing delimiter can produce `ERROR 42601 syntax error at end of input`.

Validation for this patch is local/non-production only. Do not connect to production, do not run backfill, and do not add grants or secrets.

## 明確禁止事項

- 禁止連 production Supabase 驗證
- 禁止 live write / live migration execution
- 禁止正式 backfill
- 禁止改產品代碼
- 禁止改 strategy / Telegram / scheduler / watchlist
- 禁止新增 destructive DML / grants / secrets
- 禁止擴大修其他 SQL artifact，除非該檔是 docs/handoff 直接引用本 artifact 必須同步的文件
- 禁止把缺本地 parser 當成通過理由；只能說明限制並加強 static scan / SQL simplification
- 禁止用「看起來應該可以」代替 evidence

## 阻塞條件

- 原 SQL 內容無法判斷 schema intent，修正需要 Owner/Architect 決定是否新增、刪除或改欄位。
- 本 artifact 其實依賴 production-only state 或不可公開的 credential 才能解析。
- Tech 發現修復必須改產品 DB read/write contract、runtime code 或 migration strategy。
- docs/handoff 位置或直接引用文件不明，且無法從摘要定位。
- local parser 顯示語法仍失敗，但失敗原因不是單純 terminator / block closure，需重新確認 schema intent。

## 本輪停止條件

完成以下即可停止，不繼續擴大：

- db/sql/evidence_phase_4_market_theme_confirmed_evidence.sql 已修成完整、明確終止、可複製的一個 SQL block。
- docs/handoff 已補最小安全執行說明與可能錯因。
- Tech 已做 static scan，並在本地非 production parser 可用時做 syntax validation。
- QA 已獨立 static scan，並在本地非 production parser 可用時驗證 syntax。
- 確認沒有 production 連線、沒有 backfill、沒有產品代碼變更。

旁支問題只記待辦，不納入本輪：

- 其他 SQL artifact 風格不一致
- 是否需要正式 migration framework
- 是否需要 production DB schema drift audit
- 是否需要全量 Supabase SQL lint
- 是否需要補完整 DB migration rollback 策略
