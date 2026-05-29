# QA_REPORT: 修正 Supabase SQL artifact 結尾語法錯誤

## 測試範圍

- 任務尺寸 / qa_level: tiny_patch / L1，未擴大到 full pytest、replay、backfill、production DB 驗證。
- 檢查輸入: `TASK.md`、`CHANGELOG.md`、git diff、`db/sql/evidence_phase_4_market_theme_confirmed_evidence.sql`、`docs/handoff/evidence_phase_4_market_theme_confirmed_evidence.md`。
- 可吸收 diff: `CHANGELOG.md`、`db/sql/evidence_phase_4_market_theme_confirmed_evidence.sql`、未追蹤但符合 TASK 的 `docs/handoff/evidence_phase_4_market_theme_confirmed_evidence.md`。
- worktree 殘留: `docs/` 目前是 untracked directory；只確認其中唯一檔案為本輪 handoff 文件，不建議整包盲合併。

## 風險預算與停止條件

- 風險 1: SQL 尾端仍不完整或 copy block 仍可能造成 end-of-input。驗證: 結尾有效字元、括號、dollar quote、statement terminator scan。停止條件: 最後有效字元為 `;`，括號數平衡，無 dollar quote 未閉合。
- 風險 2: handoff 文案讓 Owner 誤以為 QA / agent 要連 production 或做 backfill。驗證: 按 Owner 打開 handoff 後的閱讀順序檢查 Purpose、Copy notes、Syntax context。停止條件: 明確寫整段複製、agent 不連 production、不 backfill、不加 credentials。
- 風險 3: tiny_patch 混入範圍外產品或策略變更。驗證: `git diff --stat` / `git diff --name-status` / diff 內容。停止條件: 僅 SQL artifact、handoff、CHANGELOG 相關。

## 關聯風險掃描

- `git diff --check`: 通過。
- 危險詞 scan: 未命中 `drop table`、`truncate`、`delete from`、`update public.`、`insert into`、`grant`、`service_role`、`password`、`secret`、`token`、`connection string`、`curl`、`wget`。
- SQL 靜態完整性: `paren_open=25 paren_close=25 dollar_quote_markers=0 single_quote_count=88 last_char=;`。
- Parser 驗證: `psql_not_found`、`docker_not_found`、`podman_not_found`；QA 不連 production，因此未做真正 Postgres parser validation，改以 static scan 驗證。

## 跨區塊語意一致性

- `TASK.md` 要求只修 SQL artifact 語法完整性與 handoff notes；`CHANGELOG.md` 與 diff 對齊。
- SQL 檔新增內容只在 header 補 copy/validation notes，尾端新增 read-only marker `select ... as sql_artifact_validation_marker;`，未改 table、欄位、constraint、index 語意。
- Handoff 文件與 SQL header 都強調整段複製、不要局部複製、local/non-production validation；沒有要求 QA / agent production 驗證或 backfill。

## 使用者誤讀風險

- Owner 打開 handoff 先看到用途，再看到 copy notes；文案明確區分「整段複製執行」與「agent 不做 production validation / backfill」。
- 可接受殘留風險: SQL header 仍提到 Owner manually opens Supabase SQL editor / Postgres console，這符合 artifact 原用途，但不是 QA 已驗證 production 可執行的承諾。Architect 收口時應避免把本輪描述成 production migration 已驗證。

## 質疑與反證

- 反證 Tech 的「未改 schema contract」: diff 顯示 SQL DDL 主體未變，只新增 comments 與尾端 marker select，未發現 schema intent 變更。
- 反證「無 destructive / credential」: 對 SQL 與 handoff 做危險詞 scan，未命中 destructive DML、grant、secret、token、connection string。
- 反證直接消費者: Owner/operator 的 copy path 有 handoff；Supabase/Postgres parser 的尾端 terminator 已補；QA 的 local parser path 不可用但有明確降級 evidence，未用缺 parser 假裝通過。

## 未測項目

- 未連 production Supabase，符合禁止事項。
- 未執行 backfill / live migration / live Telegram。
- QA 未做真正 Postgres parser validation，因本機沒有 `psql`、Docker/Podman 或可用 SQL parser package。
- 未驗證 production 既有同名 table 是否 schema drift；這是旁支 production review，不屬本輪 tiny_patch。

## QA 結論

conditional pass

條件: 本輪可吸收的內容限於上述 SQL artifact、handoff 文件與 `CHANGELOG.md`；不要把整個 untracked `docs/` 盲目視為已審核。另需在 Architect 收口時保留「未做 production/parser validation」限制，避免誤寫成 SQL 已在 Supabase 實際驗證通過。
