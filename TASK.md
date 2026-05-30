# TASK: production DB market/theme evidence source audit 與 approved payload dry-run preview

## 任務狀態

- task_id: production-evidence-approved-payload-audit
- 任務類型: normal_patch
- 狀態: ready_for_tech
- 版本建議: none
- 版本契約: 本輪不改 Telegram / CLI 使用者報文版本；若既有 script 有版本 header，沿用目前版本。
- QA 分級建議: L2
- 任務尺寸判斷: normal_patch。理由是本輪不改策略、不寫 DB、不發 Telegram，但會新增或擴充 repo-side read-only audit / dry-run payload generator，且輸出 contract 會被後續 evidence write path 消費；不是 tiny_patch。

## Owner 問題

Owner 要繼續 production evidence 閉環：目前 market_theme_confirmed_evidence production rows=0，但 production DB 已有 daily_signal_snapshot、signal_runs、signal_items、daily_price、positions、position_events 等資料。需
要先判斷這些現有 production DB 資料是否足以安全生成 market_theme_confirmed_evidence 的 approved payload preview。

PM 結論：僅有 row count 不足以判定可生成 confirmed/supporting market/theme evidence。Tech 本輪只能做 read-only source audit 與 dry-run payload preview；只有在 production DB 欄位能明確映射到既有 evidence contract，且
lineage 可追溯時，才可輸出 approved_payload_preview。若缺 market/theme source semantics，必須 fail closed / blocked，不得用個股策略快照或 report-derived 推論硬補。

## 使用者可見結果

Owner / Architect 會看到一份 repo-side read-only audit / dry-run 輸出，明確回答：

- can_generate_approved_payload: true|false
- 若 true：輸出可審核的 approved_payload_preview，但不 execute、不 upsert、不 backfill。
- 若 false：輸出 blocked，列出缺少哪些 production source semantics，需要 Owner 確認哪些欄位或來源才可作為 confirmed/supporting market/theme evidence。
- 輸出必須標示 production 查詢日期與來源表 row count，例如 daily_signal_snapshot 2026-05-29 rows=48、signal_runs 2026-05-29 daily_close、signal_items rows=12。

本輪不是 Telegram / UI 任務，無手機報文輸出；不需要手機閱讀路徑。

## 非目標

- 不 live write。
- 不 backfill。
- 不 execute approved payload。
- 不改 DB schema、table、column、RLS、grant、policy、role。
- 不發 Telegram。
- 不改策略 decision、watchlist、持倉狀態機、Telegram formatter。
- 不使用 fake/local/runtime/report-derived/chat data。
- 不把 production row count 當成 market/theme semantics。
- 不重設 evidence chain 架構。
- 不做 full production data ingestion pipeline。

## 影響模組

- 直接模組:
- 既有 market_theme_confirmed_evidence read/write/dry-run 相關 script 或 service。
- 若現有 script 可擴充，優先擴充現有 read-only audit / dry-run generator；若不適合，新增最小 repo-side read-only audit script。
- 對應直接測試。
- 直接消費者:
- Architect / Owner 用來判斷是否可進入 evidence write approval 的 dry-run output。
- 後續 market_theme_confirmed_evidence approved payload generator / write CLI。
- QA 用來驗證 production fresh runner 是否不依賴 local/runtime/chat context。

## 輸出契約

- 單一主問題: 現有 production DB 資料能否安全映射成 market_theme_confirmed_evidence approved payload preview。
- 單一輸出契約: read-only audit / dry-run JSON。

必要輸出欄位:

{
"mode": "read-only-production-audit",
"write_execution": "disabled",
"live_write": false,
"source_family": "production_db",
"trade_date": "2026-05-29",
"source_tables": [
{
"table": "daily_signal_snapshot",
"rows": 48,
"usable_for_market_theme_evidence": false,
"reason": "missing explicit market_index / sector_theme_key / breadth semantics"
}
],
"can_generate_approved_payload": false,
"status": "blocked",
"missing_source_semantics": [
"market_index",
"sector_theme_key",
"watchlist_breadth definition",
"evidence_value meaning",
"support_level rule",
"lineage from production DB columns"
],
"approved_payload_preview": null
}

若 mapping 安全，approved_payload_preview 必須只包含既有 market_theme_confirmed_evidence contract 欄位，至少包含：

- trade_date
- as_of
- market_index
- sector_theme_key
- watchlist_breadth
- freshness
- evidence_value
- support_level
- lineage
- source_family
- source_name
- evidence_status

已存在且不得回退的契約:

- market_theme_confirmed_evidence 目前 production rows=0 時，read consumer 必須 fail closed，不得 runtime fallback 成 confirmed。
- confirmed / ready 來源只允許 production/persistent source family；runtime/local/cache/worktree/report-derived/chat/test/fixture 不得 confirmed。
- write CLI / approval package 預設 dry-run；只有明確 execute path 才能寫入，但本輪禁止 execute。
- read-only smoke 可用 config fallback 讀 production，但不得使用 service-role 或高權限 key 來做本輪 read-only audit。
- 缺 source semantics 時必須 blocked 或 insufficient-data，不得用推論補成 approved。

## 驗收條件

1. Read-only audit 可讀 production metadata / row counts:
- 能在 read-only credential 下讀取或查詢 Owner 已知 production sources 的可用性。
- 至少回報 market_theme_confirmed_evidence rows=0，以及 Owner 指定的 daily_signal_snapshot、signal_runs、signal_items 是否有 2026-05-29 資料。
- 不輸出 secret、URL、key、hash、truncated key 或 credential fingerprint。
2. Safe mapping gate:
- 只有當 production DB 欄位明確提供 market_index、sector_theme_key、watchlist_breadth、as_of/trade_date freshness、evidence_value/support_level、lineage 時，才可產出 approved_payload_preview。
- 若 daily_signal_snapshot / signal_items 只能證明個股策略快照、分類、或 watchlist item 狀態，不能提升為 confirmed market/theme evidence；輸出必須 status=blocked 或 can_generate_approved_payload=false。
3. Dry-run only:
- 本輪任何命令都不得 upsert / insert / update / delete production DB。
- 輸出必須固定包含 write_execution=disabled 與 live_write=false。
- 不產生可被誤執行的 live SQL；若產生 review artifact，必須明確標示 preview only / not executed。
4. Direct consumer contract:
- 若產出 approved_payload_preview，必須可被既有 approved payload validation / write dry-run 接受，但不得 execute。
- 若 blocked，必須列出 Owner 需要確認的 source semantics，而不是只寫「資料不足」。

## 範例或 fixture

blocked 範例輸出形狀:

{
"mode": "read-only-production-audit",
"trade_date": "2026-05-29",
"can_generate_approved_payload": false,
"status": "blocked",
"source_tables": [
{"table": "market_theme_confirmed_evidence", "rows": 0},
{"table": "daily_signal_snapshot", "rows": 48},
{"table": "signal_runs", "rows": 1, "run_type": "daily_close"},
{"table": "signal_items", "rows": 12}
],
"missing_source_semantics": [
"which column is market_index",
"which column is sector_theme_key",
"how watchlist_breadth is computed from production rows",
"which production value is evidence_value",
"how support_level is assigned"
],
"approved_payload_preview": null,
"write_execution": "disabled",
"live_write": false
}

safe mapping 範例輸出形狀:

{
"can_generate_approved_payload": true,
"status": "dry-run-preview",
"approved_payload_preview": [
{
"trade_date": "2026-05-29",
"as_of": "2026-05-29T13:30:00+08:00",
"market_index": "TAIEX",
"sector_theme_key": "example_theme",
"watchlist_breadth": 0.67,
"freshness": "same_day",
"evidence_value": "supporting",
"support_level": "supporting",
"source_family": "production_db",
"source_name": "daily_signal_snapshot+signal_items",
"lineage": {
"tables": ["daily_signal_snapshot", "signal_runs", "signal_items"],
"trade_date": "2026-05-29"
},
"evidence_status": "approved"
}
],
"write_execution": "disabled",
"live_write": false
}

## 明確禁止事項

- 禁止 fake/local/runtime/report-derived/chat data。
- 禁止 production live write、upsert、insert、update、delete。
- 禁止 backfill。
- 禁止 DB schema / RLS / grant / policy / role 變更。
- 禁止發 Telegram。
- 禁止把 row count、個股分數、watchlist snapshot 直接包裝成 market/theme confirmed evidence，除非欄位語意與 lineage 明確可核驗。
- 禁止讀取 .env、*.pem、~/.aws/credentials、~/.ssh/*、token、browser profile。
- 禁止輸出 secret、connection string、credential hash、partial value、fingerprint。
- 禁止使用 service-role 或高權限 key 做本輪 read-only audit。
- 禁止修改策略 decision、Telegram formatter、watchlist、持倉行動、交易建議。

## 阻塞條件

- production DB 欄位無法明確映射到 market_index。
- production DB 欄位無法明確映射到 sector_theme_key。
- watchlist_breadth 的計算來源、分母、分子、日期邊界不明。
- evidence_value / support_level 的語意與閾值不明。
- lineage 只能來自 report/runtime/chat/local artifact，而不是 production DB row。
- 需要 Owner 決定 daily_signal_snapshot 是否可被視為 market/theme evidence source semantics。
- 需要新增 schema、view、function、RLS、grant、policy 或 role 才能完成。
- 需要 live write、backfill 或 Telegram delivery 才能驗證。
- 測試只能靠真實 secret 或不可 mock 的 production side effect 才能通過。

## 本輪停止條件

- 完成 read-only audit / dry-run output contract。
- 對 Owner 指定 production tables 做到 row count / source availability / mapping gate 檢查。
- 明確輸出 can_generate_approved_payload=true 的 preview，或 blocked 並列出缺少的 source semantics。
- QA 驗證 dry-run 不寫 DB、不使用 forbidden source、不把 runtime/report/chat data 提升為 confirmed。
- 若發現旁支問題，例如歷史資料品質、更多日期回補、Telegram 顯示、正式 execute 流程、schema 擴充、RLS 設計，只記入後續待辦，不納入本輪。
