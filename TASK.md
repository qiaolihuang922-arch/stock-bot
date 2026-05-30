# TASK: Market Theme Approved Payload Template And Dry-run Sample

## 任務狀態

- task_id: evidence_chain_approval_payload_template_20260530
- 任務類型：risk_patch
- 任務尺寸判斷：risk_patch；碰到 production evidence chain / DB approval 邊界，但本輪只建立可審核 template、sample、docs、tests，不做 live 寫入。
- 狀態：ready_for_tech
- 版本建議：none；本輪不改 Telegram 使用者可見報文、不改 Telegram VERSION。若 Tech 實際改到 Telegram formatter、策略 decision、message list 或 header，必須 blocked 回 PM 重定版本契約。
- QA 分級建議：L2；驗證 approval package 生成契約、source guard、sample 不被誤讀為 production confirmed、no-live-write pattern。不得擴成 full pytest、正式 backfill、live DB 驗證或 live Telegram。

## Owner 問題

Owner 要繼續 evidence chain 下一步：建立第一份 market/theme approved payload 模板與可執行 dry-run 樣本，讓 Owner 能用 scripts/generate_evidence_approval_package.py 產生 approval package。

本輪重點不是 production 上線，而是把 Owner 需要填的欄位、允許來源、禁止來源、dry-run 指令、輸出 JSON/MD/SQL package 的審核流程固定下來，避免 runtime/local/sample 被誤讀成 confirmed production evidence。

## 使用者可見結果

Owner 會在 repo 內看到：

- 一份 Owner 可填寫的 market/theme approved payload template。
- 一份可直接用於 dry-run 的 allowed owner_approved_persistent sample payload。
- 一份或一段 handoff docs，說明 Owner 要填哪些欄位、如何跑 dry-run、package 會輸出什麼、下一步哪些動作需要人工批准。
- 用 sample 執行 scripts/generate_evidence_approval_package.py 時，可產出 approval package JSON / Markdown / review-only SQL。
- forbidden/runtime/local/sample-as-production 類 payload 不會產生 review SQL，也不會被描述成 production confirmed。
- Telegram 報文本輪不變；未有 production confirmed rows 前，不得因 sample 或 package 顯示 confirmed。

## 非目標

- 不做 live Supabase write。
- 不做 formal backfill。
- 不改 production RLS / grant / policy / role。
- 不 live Telegram delivery。
- 不改策略 decision、BUY/SELL、RR、加減碼、停損停利、watchlist。
- 不改 Telegram formatter、message list contract 或 VERSION。
- 不新增 production ingestion automation。
- 不把 sample、template、docs、package 描述成 production 已入庫或 GitHub runner 已 confirmed。
- 不做全 repo 清理或 unrelated refactor。

## 影響模組

Tech 可在最小範圍內新增或更新：

- scripts/generate_evidence_approval_package.py
- docs/handoff/*market_theme* 或等價 handoff docs
- fixtures/*market_theme*、examples/*market_theme*、docs/examples/*market_theme* 或等價 sample/template 路徑
- 對應局部 tests
- CHANGELOG.md

不得修改 live runner secrets、production DB、正式 backfill runner、Telegram 發送流程、策略核心門檻或 production RLS/grant。

## 直接消費者

- Owner：填寫 approved payload、執行 dry-run、審核 JSON/MD/SQL package，決定是否另行批准後續人工 SQL / read-only smoke。
- Architect：依 TASK.md / CHANGELOG.md / QA_REPORT.md 判斷本輪是否形成可交給 Owner 審核的 package workflow。
- Tech：建立 template、sample、docs、tests，必要時補強 generator 的 template/sample 支援。
- QA：驗證 allowed sample 可產 package，forbidden/runtime/local/sample-as-production 不會被誤讀為 confirmed。
- 未來 manual operator：只在 Owner 另行批准後，才可拿 review-only SQL 手動執行。
- 未來 GitHub fresh runner：只可透過 production DB read-only rows 消費 confirmed evidence，不可消費 sample/template/local artifact。

## 輸出契約

### Payload Template Contract

Owner-facing template 必須清楚標示必填欄位，至少包含：

- trade_date
- source_family
- source_name
- evidence_status
- freshness
- rows
- row-level market/theme evidence 欄位，例如 symbol、theme、support_level、evidence_url、reason

Template 必須明確寫出：

- allowed source family：owner_approved_persistent、production_db、market_data
- forbidden source family：runtime、local、cache、worktree、report-derived、synthetic、default、test、fixture、缺 source
- sample/template 不是 production confirmed。
- package SQL 是 review-only；script 不執行 SQL。

### Dry-run Sample Contract

必須提供至少一份 allowed sample：

- source_family 必須是 owner_approved_persistent
- 可用 scripts/generate_evidence_approval_package.py 產出 JSON / Markdown / SQL package
- package 固定標示 write_execution=disabled
- package / docs 必須標示 manual approval required
- SQL header 必須標示 Agent did not execute this SQL，且不能暗示 production deployment completed

必須提供或測試至少一份 forbidden sample / fixture：

- source_family 為 runtime、local 或 fixture 之一
- validation fail closed
- 不產生 deterministic SQL
- 不得輸出 confirmed production 語意

### Generator Contract

scripts/generate_evidence_approval_package.py 應可用類似命令執行：

python scripts/generate_evidence_approval_package.py \
--payload docs/examples/market_theme_owner_approved_payload.sample.json \
--output-dir artifacts/evidence_approval/sample

輸出 package 至少包含：

- approval_package.json
- approval_package.md
- validation passed 且 source allowed 時的 review-only .sql

若既有 generator 已支援，Tech 只需補 template/sample/docs/tests；不得為了本輪重寫整個 generator。

## 已存在且不得回退的契約

- public.market_theme_confirmed_evidence 目前結論是 schema_decision: no-schema-change；本輪不得無理由擴表或擴字段。
- scripts/generate_evidence_approval_package.py 是 non-live approval package generator；不得連線執行 production SQL。
- Approval package 固定應標示 mode=non-live-approval-package、write_execution=disabled 或等價語意。
- read-only loader 只接受 approved persistent source family。
- fake/local/runtime/cache/worktree/report-derived/synthetic/default/test/fixture rows 不得 confirmed。
- allowed + forbidden 混合來源必須 fail closed。
- sample、fixture、template、runtime/local context 不得作為 GitHub fresh runner 的跨日 source-of-truth。
- 本輪不改 Telegram 報文與版本字串。

## 驗收條件

1. Repo 內存在一份 Owner-facing payload template，清楚列出 Owner 要填的欄位、allowed / forbidden source family、sample 不等於 production confirmed。
2. Repo 內存在一份 allowed owner_approved_persistent sample payload，可用 scripts/generate_evidence_approval_package.py dry-run 產出 JSON / MD / SQL package。
3. Allowed sample 產出的 package 明確標示 no live write、manual approval required、not production deployment evidence。
4. Forbidden runtime / local / fixture 類 payload fail closed，不產生 deterministic SQL。
5. Docs 清楚說明 dry-run 指令、輸出檔案、Owner 下一步要人工批准哪些動作。
6. Package、docs、SQL、sample 不含 secrets、connection string、service role key、password。
7. Tech 不改策略 decision、Telegram formatter、Telegram VERSION、RLS/grant、formal backfill 或 live write path。
8. QA 必須補一個 sample-as-production 誤讀風險反證：確認 template/sample/docs/package 都沒有把 sample 描述為 production confirmed。
9. QA 必須補一個 no-live-write pattern 檢查：generator / sample workflow 不含 Supabase insert/upsert/rpc/execute 或等價 live execution。
10. 若 Tech 發現缺 Owner payload 欄位或 production schema 不足，必須 blocked，列出缺口與需 Owner/Architect 確認事項，不得自行定 production payload contract。

## 範例或 fixture

### Allowed sample payload

{
"trade_date": "2026-05-29",
"source_family": "owner_approved_persistent",
"source_name": "owner_approved_market_theme_review_sample",
"evidence_status": "confirmed",
"freshness": "fresh",
"rows": [
{
"symbol": "2330",
"theme": "AI supply chain",
"support_level": "supporting",
"evidence_url": "owner-to-replace-with-approved-reference",
"reason": "Owner approved persistent evidence sample; replace before production review"
}
]
}

Expected package shape:

{
"schema_decision": "no-schema-change",
"mode": "non-live-approval-package",
"write_execution": "disabled",
"payload_validation": {"status": "passed"},
"manual_approval_required": [
"Owner reviews payload fields",
"Owner approves SQL execution separately",
"Owner runs read-only verification after manual execution"
],
"not_executed": [
"no live Supabase write",
"no formal backfill",
"no RLS/grant change",
"no live Telegram"
]
}

### Forbidden sample payload

{
"trade_date": "2026-05-29",
"source_family": "runtime",
"source_name": "same_run_runtime_sample",
"evidence_status": "confirmed",
"freshness": "fresh",
"rows": []
}

Expected result:

{
"payload_validation": {
"status": "failed",
"reason": "forbidden source_family"
},
"deterministic_sql": null,
"write_execution": "disabled"
}

## 明確禁止事項

- 禁止 live Supabase write。
- 禁止 formal backfill。
- 禁止 agent 執行 production SQL。
- 禁止修改 production RLS / grant / policy / role。
- 禁止 live Telegram delivery。
- 禁止讀取或輸出 secrets、service role key、password、connection string。
- 禁止把 sample、template、docs、SQL、package 說成 production 已變更、已入庫、已 confirmed。
- 禁止 fake confirmed、synthetic confirmed、fixture-derived confirmed、sample-as-production confirmed。
- 禁止把 local/runtime/cache/worktree/agent context 當 production source-of-truth。
- 禁止改策略核心門檻、watchlist、Telegram formatter 或 VERSION。
- 禁止因本輪 sample/docs 任務擴成 production ingestion automation 或 full repo cleanup。

## 阻塞條件

- 無法定義 Owner 必填 payload 欄位，導致 template 會誤導 production review。
- 現有 scripts/generate_evidence_approval_package.py 無法在不 live write 的情況下產生可審核 package。
- 無法可靠區分 allowed / forbidden source family。
- Generator 必須依賴 secret、connection string 或 production credentials 才能 dry-run。
- 需要改 production schema、RLS/grant、formal backfill 或 Telegram VERSION 才能完成本輪。
- 任一阻塞發生時，Tech 只交 blocked CHANGELOG.md，列出缺口與需 Owner/Architect 補充的事項，不得自行做 production 決策。

## 本輪停止條件

完成以下即停止：

- Template、allowed sample、forbidden sample/fixture、docs、局部 tests 可被 QA 驗證。
- Allowed sample 可 dry-run 產 JSON / MD / SQL package。
- Forbidden/runtime/local/sample-as-production 不會產 SQL、不會 confirmed。
- CHANGELOG.md 清楚標示 no live write、no formal backfill、no RLS/grant、no live Telegram、no Telegram VERSION change。

旁支問題只記待辦，不納入本輪：

- production DB execution。
- production ingestion automation。
- formal backfill。
- RLS/grant 正式變更。
- GitHub runner read-only env 配置。
- live Telegram confirmed consumption 驗證。
- 新外部資料來源或策略調整。
