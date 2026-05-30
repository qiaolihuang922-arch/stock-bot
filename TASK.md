# TASK: Market Theme Confirmed Evidence Repo-side Write CLI

## 任務狀態

- task_id: market_theme_confirmed_evidence_write_cli_20260530
- 任務類型：risk_patch
- 任務尺寸判斷：risk_patch；本輪建立 public.market_theme_confirmed_evidence 的 repo-side 非 schema 寫入接口 / CLI，會碰到 DB write path，但只允許 dry-run/validate 與 mock/fake client 測試 --execute，不得真實 production
write。
- 狀態：ready_for_tech
- 版本建議：none；本輪不改 Telegram 報文、不改策略 decision、不改 VERSION。若 Tech 實際改到 Telegram formatter、message list、策略 decision 或 header，必須 blocked 回 PM 重定版本契約。
- QA 分級建議：L2；需驗證 validation、dry-run、fail-closed、mock execute upsert payload、docs 邊界。不得擴成 full pytest、production live write、正式 backfill 或 RLS/grant 驗證。

## Owner 問題

Owner 已確認新流程邊界：只有新增表、擴字段、schema / RLS / grant / policy / role 變更才找 Owner。非 schema 的 evidence rows 新增 / 回寫 / backfill 不應再產普通 DML 給 Owner 手動跑，而要走既有接口、repo script 或
approved service API。

本輪要把 public.market_theme_confirmed_evidence 從「產生 review-only SQL / payload package」推進到「repo-side 寫入接口 / CLI」：輸入既有 docs/examples/market_theme_owner_approved_payload.template.json / .sample.json 形
狀或 approved payload，先 dry-run/validate；只有明確 --execute 且寫入 env/key 存在時才透過 Supabase client/API 寫入。缺 env 或 forbidden/runtime/local source 必須 fail closed，不再要求 Owner 手動跑普通 DML。

## 使用者可見結果

Owner / operator 會看到：

- 一個 repo-side CLI script，可對 approved market/theme evidence payload 做 validate / dry-run。
- dry-run 預設不寫 DB，輸出將寫入的 target table、row count、upsert key 或 conflict target、每列摘要、validation status。
- --execute 只有在明確指定且 Supabase 寫入 env/key 存在時才進入寫入路徑。
- 缺寫入 env/key 時，script 清楚列出需要哪些 env，並 fail closed；不得輸出「請 Owner 手動跑 DML」。
- forbidden source，例如 runtime/local/cache/worktree/report-derived/synthetic/default/test/fixture，必須 fail closed，不產生可寫入 payload。
- docs 明確說明：非 schema evidence rows 寫入不需要 Owner 手動 SQL；只有 schema/RLS/grant/policy/role 變更才需要 Owner 事前確認。
- Telegram 報文本輪不變；本輪 CLI 不代表 live Telegram 已消費新 rows。

## 非目標

- 不改 DB schema。
- 不新增 table。
- 不新增或擴充欄位。
- 不改 RLS / grant / policy / role。
- 不執行 production live write。
- 不做正式 backfill。
- 不 live Telegram delivery。
- 不改策略 decision、BUY/SELL、RR、加減碼、停損停利、watchlist。
- 不改 Telegram formatter、message list contract 或 VERSION。
- 不把 runtime/local/sample data 洗成 production confirmed。
- 不重寫既有 evidence chain 架構或做全 repo 清理。

## 影響模組

Tech 可在最小範圍內新增或更新：

- scripts/*market_theme*evidence*write*.py 或等價 repo-side CLI script。
- services/market_theme_evidence_store.py 或等價 Supabase client helper，但只限新增可測試寫入接口，不得改 read-only loader confirmed 判斷。
- docs/examples/market_theme_owner_approved_payload.template.json
- docs/examples/market_theme_owner_approved_payload.sample.json
- docs/handoff/*market_theme* 或等價操作文件。
- 對應局部 tests。
- CHANGELOG.md

不得修改：

- production DB schema / SQL migration。
- RLS / grant / policy / role artifacts。
- Telegram notifier / live sender。
- 策略核心門檻。
- core/generator.py 的 VERSION。

## 直接消費者

- Owner：確認本輪已不再要求手動跑普通 DML，只需提供 approved payload；schema 變更才另行批准。
- Operator / Architect：用 CLI 做 dry-run/validate，確認 row count、target table、寫入範圍與 env 缺失狀態。
- Tech：實作 repo-side CLI、validation、Supabase client/API write abstraction、mock execute tests。
- QA：驗證 allowed payload dry-run、forbidden fail-closed、缺 env fail-closed、mock/fake client --execute upsert payload。
- public.market_theme_confirmed_evidence read-only loader：未來只應消費 production DB 中符合 confirmed 條件的 rows；不得消費 local/runtime/template/sample artifact。
- GitHub fresh runner：仍只能依 production DB read-only rows 重建 confirmed evidence；本輪不要求驗證 live runner 實際讀取。

## 輸出契約

### CLI Contract

CLI 必須支援以下語意，實際檔名可由 Tech 依 repo pattern 命名：

python scripts/write_market_theme_confirmed_evidence.py \
--payload docs/examples/market_theme_owner_approved_payload.sample.json

預設模式為 dry-run / validate：

- 不寫 DB。
- 輸出 target table：public.market_theme_confirmed_evidence。
- 輸出 validation status。
- 輸出將寫入 row count。
- 輸出每列摘要，不得輸出 secret。
- 輸出 upsert payload shape 或 sanitized row preview。
- 明確標示 write_execution=disabled 或等價欄位。

Execute 必須只能由明確 flag 觸發：

python scripts/write_market_theme_confirmed_evidence.py \
--payload docs/examples/market_theme_owner_approved_payload.sample.json \
--execute

--execute 契約：

- 只有 validation passed 才可進入 execute。
- 只有 source family 是 approved persistent allowlist 才可進入 execute。
- 只有必要 Supabase write env/key 存在時才可進入 execute。
- 缺 env/key 時 exit non-zero，清楚列出缺少的 env 名稱。
- 透過 Supabase client/API 或 repo 既有 approved service helper upsert rows。
- 測試只用 mock/fake client 驗證 upsert payload；不得要求真 production write。

### Source Guard Contract

Allowed source family：

- owner_approved_persistent
- production_db
- market_data

Forbidden source family：

- runtime
- local
- cache
- worktree
- report-derived
- synthetic
- default
- test
- fixture
- 缺 source
- mixed allowed + forbidden source

Forbidden payload 必須 fail closed：

- 不寫 DB。
- 不產生 execute payload。
- 不回傳 confirmed success。
- exit non-zero 或明確 validation failed。

### Payload Contract

CLI 必須接受既有 docs/examples template/sample 形狀或 approved payload。若既有 template/sample 欄位名與 table schema 不完全一致，Tech 必須在 CLI 中做明確 mapping 或 blocked，不得猜測寫入 production 欄位。

寫入 target 固定為：

- schema/table：public.market_theme_confirmed_evidence

輸出 / upsert rows 必須只包含現有 table contract 欄位；本輪不得新增 schema 欄位。已知 contract 包含但不保證僅限：

- trade_date
- as_of
- source_family
- source_name
- freshness
- evidence_status
- support_level
- market_index
- sector_theme_key
- watchlist_breadth
- evidence_value
- lineage

若 required DB 欄位、unique/upsert conflict target 或 approved payload mapping 無法從 repo 既有程式 / docs 確認，Tech 必須 blocked，要求 Architect 補充，不得自行設計 production contract。

### Docs Contract

Docs 必須說明：

- dry-run 指令。
- execute 指令與 env 前置條件。
- 缺 env/key 時 fail closed。
- allowed / forbidden source family。
- 非 schema evidence rows 寫入不需要 Owner 手動 SQL。
- 只有新增表、擴字段、schema / RLS / grant / policy / role 變更才需要 Owner 事前確認。
- 本 script 不做 live Telegram、不改策略 decision、不改 VERSION。
- production write 實際執行仍需 operator 明確 --execute，且需 approved payload 與 env/key。

## 已存在且不得回退的契約

- public.market_theme_confirmed_evidence 目前是 schema_decision: no-schema-change；本輪不得擴表、擴字段或改 schema。
- Existing read-only loader 只能接受 approved persistent source family：production_db、owner_approved_persistent、market_data。
- fake/local/runtime/cache/worktree/report-derived/synthetic/default/test/fixture rows 不得 confirmed。
- mixed allowed + forbidden source 必須 fail closed。
- sample/template/runtime/local context 不得作為 GitHub fresh runner 的跨日 source-of-truth。
- approval package / sample 不代表 production deployment completed。
- 本輪不改 Telegram 報文與 VERSION。
- Owner 最新流程邊界不得回退：非 schema evidence rows 新增 / 回寫 / backfill 不再要求 Owner 手動跑普通 DML；應走 repo script / approved API，並保留 dry-run、validation、fail-closed、可追溯驗證。

## 驗收條件

1. CLI 預設 dry-run：allowed docs/examples/market_theme_owner_approved_payload.sample.json 可 validation passed，輸出 target table public.market_theme_confirmed_evidence、row count、sanitized rows / upsert preview，且
不呼叫 Supabase write。
2. CLI forbidden guard：runtime/local/cache/worktree/report-derived/synthetic/default/test/fixture 或缺 source payload validation failed，fail closed，不產生 execute payload，不寫 DB。
3. CLI 缺 env guard：--execute 在缺必要 Supabase write env/key 時 exit non-zero，清楚列出缺少 env，不要求 Owner 手動跑 SQL。
4. CLI execute path：用 mock/fake Supabase client 測試 --execute 會對 allowed payload 呼叫正確 table / upsert payload；不需要真 production write。
5. CLI 不讀 .env、不輸出 secret、connection string、service role key 或 password。
6. Docs 說明非 schema evidence rows 寫入走 repo script / approved service API，不需 Owner 手動 SQL；schema/RLS/grant/policy/role 變更才需要 Owner。
7. Docs 與 CLI 均標示本輪不做 live Telegram、不改策略 decision、不改 VERSION。
8. Tests 覆蓋 allowed dry-run、forbidden source fail-closed、缺 env --execute fail-closed、mock execute upsert payload。
9. Tech 不改 DB schema、RLS/grant/policy/role、Telegram formatter、策略 decision 或 VERSION。
10. 若 Tech 無法確認 table columns、required fields 或 upsert conflict target，必須 blocked，不得自行猜 production write contract。

## 範例或 fixture

### Allowed Payload Input Shape

可沿用既有 sample，或等價 approved payload：

{
"trade_date": "2026-05-29",
"source_family": "owner_approved_persistent",
"source_name": "owner_approved_market_theme_review_sample",
"evidence_status": "confirmed",
"freshness": "fresh",
"rows": [
{
"market_index": "TAIEX",
"sector_theme_key": "ai_supply_chain",
"watchlist_breadth": "supporting",
"support_level": "supporting",
"evidence_value": {
"summary": "Owner approved persistent evidence sample"
},
"lineage": {
"approval": "owner_approved_payload_sample"
}
}
]
}

### Expected Dry-run Output Shape

{
"mode": "dry-run",
"target_table": "public.market_theme_confirmed_evidence",
"write_execution": "disabled",
"payload_validation": {
"status": "passed"
},
"rows_to_upsert": 1,
"upsert_preview": [
{
"trade_date": "2026-05-29",
"source_family": "owner_approved_persistent",
"source_name": "owner_approved_market_theme_review_sample",
"freshness": "fresh",
"evidence_status": "confirmed",
"support_level": "supporting"
}
]
}

### Forbidden Payload Input Shape

{
"trade_date": "2026-05-29",
"source_family": "runtime",
"source_name": "same_run_runtime_sample",
"evidence_status": "confirmed",
"freshness": "fresh",
"rows": []
}

### Expected Forbidden Output Shape

{
"mode": "dry-run",
"target_table": "public.market_theme_confirmed_evidence",
"write_execution": "disabled",
"payload_validation": {
"status": "failed",
"reason": "forbidden source_family"
},
"rows_to_upsert": 0,
"execute_payload": null
}

### Expected Missing Env Execute Output Shape

{
"mode": "execute",
"target_table": "public.market_theme_confirmed_evidence",
"write_execution": "blocked",
"payload_validation": {
"status": "passed"
},
"env_validation": {
"status": "failed",
"missing": ["SUPABASE_URL", "SUPABASE_SERVICE_ROLE_KEY"]
},
"rows_written": 0
}

Env 名稱可依 repo 既有 Supabase write convention 調整；若調整，Tech 必須在 docs 與 tests 中固定，且不得讀取或輸出 env value。

## 明確禁止事項

- 禁止改 DB schema、table、column。
- 禁止改 RLS / grant / policy / role。
- 禁止新增 migration 或要求 Owner 手動跑普通 DML。
- 禁止 production live write 作為測試或交付證據。
- 禁止 formal backfill。
- 禁止 live Telegram delivery。
- 禁止改 Telegram formatter、message list contract 或 VERSION。
- 禁止改策略 decision、BUY/SELL、RR、加減碼、停損停利、watchlist。
- 禁止讀取 .env 或輸出 secrets、service role key、password、connection string。
- 禁止把 runtime/local/cache/worktree/report-derived/synthetic/default/test/fixture 寫入 production confirmed evidence。
- 禁止把 sample/template/mock/fake client 測試結果描述成 production rows 已寫入。
- 禁止用「請 Owner 手動跑 SQL」替代 repo-side write interface。
- 禁止把本輪擴成全量 DB ingestion framework、runner env 配置、production smoke 或 full repo cleanup。

## 阻塞條件

- 無法從既有 schema/docs/code 確認 public.market_theme_confirmed_evidence required columns 或 upsert conflict target。
- 既有 approved payload/template/sample 形狀無法安全 mapping 到現有 table 欄位。
- Repo 沒有可用 Supabase client/API pattern，且新增最小 client helper 仍需要未確認的 secret handling。
- --execute 必須依賴手動 SQL 或 production-only side effect 才能實作。
- 無法可靠區分 allowed / forbidden source family。
- 完成本輪必須改 schema、RLS/grant/policy/role、策略 decision、Telegram formatter 或 VERSION。
- 任一阻塞發生時，Tech 交 blocked CHANGELOG.md，列出缺口與需 Architect/Owner 補充事項，不得自行決定 production write contract。

## 本輪停止條件

完成以下即停止：

- CLI 支援 allowed payload dry-run/validate，輸出 target table、row count、upsert preview。
- CLI 對 forbidden/runtime/local source fail closed。
- CLI 對缺 env --execute fail closed，列出 required env。
- CLI --execute path 可用 mock/fake client 驗證 upsert table 與 payload。
- Docs 說清楚非 schema evidence rows 不需 Owner 手動 SQL，schema/RLS/grant/policy/role 才需 Owner 確認。
- CHANGELOG.md 清楚標示 no schema change、no RLS/grant、no production live write、no live Telegram、no strategy decision change、no VERSION change。

旁支問題只記待辦，不納入本輪：

- 真 production write 執行。
- 大量 historical backfill。
- GitHub runner read-only env 配置。
- production read-only smoke。
- RLS / read-only role 變更。
- Telegram confirmed evidence 實際報文驗證。
- 新外部資料源或策略調整。
