# TASK: Evidence Chain Approval Package Generator

## 任務狀態

- task_id: evidence_chain_approval_package_20260530
- 任務類型：risk_patch
- 任務尺寸判斷：risk_patch；碰到 production DB approval/write 邊界，但本輪只做 repo-side non-live artifact，不做實際寫入。
- 狀態：ready_for_tech
- 版本建議：none；本輪不改 Telegram 使用者可見報文、不改 VERSION。若 Tech 實際改到 Telegram formatter/header/message list，必須 blocked 回 PM 重定版本契約。
- QA 分級建議：L2+；驗證 production source guard、approval package contract、SQL determinism、no-live-write pattern、read-only smoke fail closed。不得擴成 full pytest、正式 backfill、live DB 驗證或 live Telegram。

## Owner 問題

Owner 問「既然 market_theme_confirmed_evidence 不需要擴表/擴字段，為什麼還要人工 SQL」，現在要求繼續製作下一步最小閉環。

本輪要把「人工 SQL」過渡為 repo-side controlled approval package / write plan：Owner 提供 approved payload 後，系統能生成可審核的 package，包含 validation result、deterministic SQL、risk summary、preflight checklist、
post-run verification checklist、read-only smoke command，並清楚標示哪些步驟仍需 Owner 手動批准。

本輪不直接 live write；只生成可審核 artifact。

## 使用者可見結果

Owner 會看到 repo 內新增或更新的 non-live artifact，而不是新的 Telegram 報文：

- 一個 approval package generator，例如 scripts/generate_evidence_approval_package.py。
- 輸入 Owner-approved payload JSON 後，輸出 package JSON / Markdown / SQL 到指定目錄或 stdout。
- package 清楚顯示：
- payload validation result。
- deterministic SQL。
- risk summary。
- preflight checklist。
- post-run verification checklist。
- read-only smoke command。
- Owner manual approval steps。
- fake/local/runtime payload 不產生 approval SQL。
- allowed persistent payload 可產生 package，但不得暗示已寫入 production。
- Telegram 手機報文本輪不變；未有 production confirmed rows 前，仍不得顯示 confirmed 或買入推薦語意。

## 非目標

- 不做 live Supabase write。
- 不做正式 production backfill。
- 不直接修改 production RLS / grant / policy / role。
- 不 live Telegram delivery。
- 不改 production DB schema；除非 Tech 發現現有 schema 不足，則本輪 blocked 並只交 manual SQL proposal。
- 不改策略 decision、BUY/SELL、RR、加減碼、停損停利、watchlist。
- 不新增外部 ingestion provider。
- 不把 approval package 描述成已上線、已入庫或已被 GitHub runner 消費。
- 不做全 repo 清理。

## 影響模組

Tech 可在最小範圍內新增或更新：

- scripts/generate_evidence_approval_package.py
- scripts/validate_market_theme_evidence_ingestion.py
- scripts/smoke_market_theme_evidence_readonly.py
- db/sql/*market_theme*
- docs/handoff/*market_theme*
- 對應局部 tests / fixtures
- CHANGELOG.md

不得修改 live runner secrets、production DB、正式 backfill runner、Telegram 發送流程或策略核心門檻。

## 直接消費者

- Owner：審核 approval package，決定是否手動批准後續 SQL / read-only smoke。
- Architect：依 TASK.md / CHANGELOG.md / QA_REPORT.md 判斷是否可進 Owner manual approval。
- Tech：實作 repo-side non-live generator 與測試。
- QA：驗證 package contract、source guard、no secrets、no live write、fail closed。
- 未來 manual operator：只在 Owner 明確批准後，才可拿 deterministic SQL 手動執行。
- 未來 GitHub fresh runner：只可透過 production DB read-only result 消費 confirmed evidence。

## 輸出契約

### Approval Package Generator

新增或更新一個 CLI，例如：

python scripts/generate_evidence_approval_package.py \
--payload path/to/approved_payload.json \
--output-dir artifacts/evidence_approval/2026-05-30

允許 stdout mode，但必須可測試、可重現。

### Package 必備內容

package 至少包含：

- schema_decision: no-schema-change
- mode: non-live-approval-package
- write_execution: disabled
- payload_validation: passed / failed 與原因
- deterministic_sql: review-only SQL；只有 validation passed 且 source allowed 時才可生成
- risk_summary: source、freshness、trade_date、row count、manual-only warning
- preflight_checklist: Owner 執行前需確認事項
- post_run_verification_checklist: Owner 手動執行後的 read-only verification
- read_only_smoke_command: smoke command 範例
- manual_approval_required: 明確列出需 Owner 批准的步驟
- not_executed: 明確列出未做 live write / backfill / RLS / Telegram

### Deterministic SQL Contract

- 相同 payload 在相同版本程式下必須輸出相同 SQL。
- SQL 不得包含 secret、project URL、service role key、password。
- SQL header 必須標示：
- Owner manual approval required。
- Agent did not execute this SQL。
- This package is not evidence of production deployment。
- SQL 只能作為 manual review/write plan；不得由 script 連線執行。

### Source Guard Contract

- allowed persistent source family 才能生成 approval SQL：production_db、owner_approved_persistent、market_data。
- forbidden source family 必須 fail closed，且不得生成 approval SQL：local、runtime、cache、worktree、report-derived、synthetic、default、test、fixture、缺 source。
- 若 payload 混入任何 forbidden source，即使同時有 allowed source，也不得生成 approval SQL。

## 已存在且不得回退的契約

- public.market_theme_confirmed_evidence 目前結論是 schema_decision: no-schema-change；不得無理由改成擴表/擴字段。
- read-only loader 已有 source_family guard；只接受 approved persistent source family。
- fake/local/runtime/cache/worktree/report-derived/synthetic/default/test/fixture rows 不得 confirmed。
- validation CLI、manual SQL template、read-only smoke 已存在；不得回退其 fail-closed 行為。
- read-only smoke 缺 env、無 rows、權限錯誤、不合格 rows 時必須 telegram_confirmed=false。
- runtime/local context 只能作為同 run 輔助 guard，不得作為 GitHub fresh runner 的跨日 source-of-truth。
- 本輪不改 Telegram 報文與版本字串。

## 驗收條件

1. allowed payload 可生成完整 approval package，包含 validation result、SQL、risk summary、preflight、post-run verification、read-only smoke command。
2. fake/local/runtime/cache/worktree/report-derived/synthetic/default/test/fixture payload 不能生成 approval SQL。
3. 混合 allowed + forbidden source payload 必須 fail closed。
4. SQL output deterministic；同一 fixture 連跑兩次內容一致。
5. package 不含 secrets，不暗示已上線、已寫入、已 backfill、已完成 RLS/grant。
6. generator 不連 Supabase、不呼叫 live insert/upsert/rpc、不執行 SQL。
7. read-only smoke 仍 fail closed；本輪不得因 package 存在而讓 Telegram confirmed。
8. 若 Tech 發現仍需要 schema change，必須 blocked，交 manual SQL proposal 與原因，不得自行擴 schema。
9. CHANGELOG.md 必須列出修改檔案、契約影響、版本同步、直接消費者、自檢命令、殘留風險。
10. QA 必須補驗 no-live-write pattern、package 無 secrets、wording 不誤導、forbidden payload 無 SQL、allowed payload 有 package。

## 範例或 fixture

### allowed payload shape

{
"trade_date": "2026-05-29",
"source_family": "owner_approved_persistent",
"source_name": "owner_approved_market_theme_review",
"evidence_status": "confirmed",
"freshness": "fresh",
"rows": [
{
"symbol": "2330",
"theme": "AI supply chain",
"support_level": "supporting",
"evidence_url": "manual-owner-approved-reference",
"reason": "Owner approved persistent evidence"
}
]
}

Expected package shape:

{
"schema_decision": "no-schema-change",
"mode": "non-live-approval-package",
"write_execution": "disabled",
"payload_validation": {"status": "passed"},
"deterministic_sql_path": "market_theme_confirmed_evidence_2026-05-29.sql",
"manual_approval_required": [
"Owner reviews package",
"Owner approves SQL execution separately",
"Owner runs read-only verification after manual execution"
],
"read_only_smoke_command": "python scripts/smoke_market_theme_evidence_readonly.py --trade-date 2026-05-29"
}

### forbidden payload shape

{
"trade_date": "2026-05-29",
"source_family": "runtime",
"evidence_status": "confirmed",
"freshness": "fresh",
"rows": []
}

Expected result:

{
"payload_validation": {"status": "failed", "reason": "forbidden source_family"},
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
- 禁止把 package、SQL、docs、smoke 說成 production 已變更。
- 禁止 fake confirmed、synthetic confirmed、fixture-derived confirmed。
- 禁止把 local/runtime/cache/worktree/agent context 當 production source-of-truth。
- 禁止改策略核心門檻、watchlist、Telegram formatter 或 VERSION。
- 禁止因「順手」做全 repo 清理或 full pytest。

## 阻塞條件

- Tech 發現現有 market_theme_confirmed_evidence schema 無法承接 approval package 必要欄位。
- 無法可靠區分 allowed / forbidden source family。
- 無法保證 generator 不 live write。
- payload contract 缺少必要欄位，導致無法定義 validation result 或 deterministic SQL。
- package 必須包含 production secret 才能運作。
- 任一阻塞發生時，Tech 只交 blocked CHANGELOG.md、原因、manual SQL proposal 或需 Owner 補充的 payload contract，不得自行做 production 決策。

## 本輪停止條件

完成以下即停止：

- generator / docs / tests 覆蓋 allowed payload 與 forbidden payload。
- approval package contract 可被 QA 驗證。
- read-only smoke fail-closed 行為未回退。
- CHANGELOG.md 清楚標示 no live write、no formal backfill、no production RLS/grant、no live Telegram。

旁支問題只記待辦，不納入本輪：

- production ingestion automation。
- actual production DB execution。
- RLS/grant 正式變更。
- GitHub runner read-only env 配置。
- Telegram confirmed consumption 的 live 驗證。
- 新外部資料來源或策略調整。
