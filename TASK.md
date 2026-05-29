# TASK: data-authenticity-hardening-fail-closed

## 任務狀態

- task_id: risk_patch_data_authenticity_fail_closed
- 任務類型: risk_patch
- 狀態: ready_for_tech
- 版本建議: patch
- 若目前使用者可見版本為 v20.3.0，本輪建議升為 v20.3.1。
- 若 Tech 實際改到 Telegram / CLI header、formatter summary、message list contract 或使用者可見 unavailable 文案，必須同步顯示版本字串與測試期望。
- 若 Tech 證明只改內部 fail-closed guard、沒有任何使用者可見 header 或報文文案變更，可在 CHANGELOG.md 明確說明不升版理由。
- QA 分級建議: L3-lite
- 可做完整 repo 證據化掃描與相關測試。
- 禁止 live Supabase write、正式 backfill、live Telegram delivery。
- full pytest 可跑；replay/backfill 只能 dry-run，且不得寫正式 DB 或發送正式 Telegram。

## Owner 問題

Owner 明確要求：目前 DB 已有資料，所有 production runtime 中會影響策略、報文、證據鏈、行情、持倉、回測、DB payload 或 Telegram 結論的路徑，都必須拒絕假資料。任何 fake/mock/dummy/sample/synthetic/default/hardcoded
fallback 不得再被 runtime 用來生成可買、confirmed、市場證據、持倉、價格、交易或回測結論。

本輪不是調整策略邏輯，而是建立並落實 source-of-truth 與 fail-closed 契約：真實資料不存在或不可用時，系統必須輸出 missing-source / unavailable 類狀態，不得補假值讓流程看起來正常。

補充殘留契約：`position_events` DB 讀取失敗或來源缺失時，也不得回傳全 0 event summary 偽裝成今日無交易；只有 DB query 成功且 `res.data == []` 才能代表今日真實無事件。

## 使用者可見結果

Owner 在 Telegram / CLI / dry-run report 看到的變化：

- 若 DB、真實行情、真實 artifact 或 evidence source 不可用，報文不得產生「可買」、「confirmed」、「市場證據成立」、「持倉成立」、「價格有效」等結論。
- 缺來源時必須清楚顯示不可行動狀態，例如：
- 資料來源缺失：evidence unavailable
- 新倉：無有效進場，原因：missing-source
- 市場證據：unavailable，不納入決策
- 今日交易事件來源錯誤時，報文不得顯示或推導為 今日無交易 / 今日 無 / 0 event；必須 fail closed 或顯示 source-error / unavailable。
- 手機閱讀路徑：
1. Owner 打開 Telegram 先看到 summary。
2. summary 必須先回答今天是否能買。
3. 若資料缺失，第一屏不得出現像推薦的股票名單或 confirmed 語氣。
4. 詳情段落可列出缺失來源，但不得用 fallback 數字補成可交易訊號。

## 非目標

- 不改策略選股意圖、分數規則、買賣條件、持倉狀態機。
- 不新增 DB schema；若修復必須 schema change，Tech 必須 blocked 回報 Architect/Owner。
- 不改 watchlist 名單。
- 不做正式 backfill。
- 不做 live Supabase write。
- 不做 live Telegram delivery。
- 不清理 tests fixture 本身；tests fixture 可保留，但 runtime 不得 import/call。
- 不把 dev/demo/dry-run-only 工具重寫成 production feature。
- 不處理與假資料無關的舊 TODO、一般重構、格式美化或測試瘦身。

## 影響模組

Tech 必須至少掃描並分類以下範圍：

- services
- core
- scripts
- supabase
- functions
- runtime entrypoints
- Telegram / CLI report generation path
- strategy / evidence / watchlist breadth / market data / holdings / backtest / DB read-write adapter path

排除 tests 作為修復目標，但必須確認 tests fixture 不被 runtime import 或 call。

## 直接消費者

本輪直接消費者至少包含：

- production strategy decision path
- Telegram message formatter / generator
- CLI / dry-run report output
- DB repository / Supabase adapter
- market data loader / stock API adapter
- holdings loader
- evidence chain builder
- backtest / replay dry-run reader
- watchlist breadth / evidence cache consumer
- any runtime scheduler or script that can produce strategy, evidence, market, holdings, DB, backtest, or Telegram conclusions

## Source-of-Truth 契約

Production runtime 的唯一可信來源：

- DB 已有資料的路徑：以 DB 為 source of truth。
- 行情：以真實行情 API / 真實行情 artifact 為 source of truth。
- 持倉：以真實持倉來源 / DB holdings / Owner 已定義 artifact 為 source of truth。
- evidence：以 DB evidence table/cache 或真實 evidence artifact 為 source of truth。
- 回測：以真實 historical data / DB / 已生成 artifact 為 source of truth。
- Telegram / CLI 結論：只能由上述真實來源推導。

禁止 runtime source：

- fake
- mock
- dummy
- sample
- synthetic
- default fallback
- hardcoded fallback
- placeholder
- demo data
- local testdata
- tests fixture
- dry-run mock value promoted as production data

## 輸出契約

Production runtime 缺資料時必須 fail closed：

- 不產生買入、加碼、confirmed、有效市場證據、有效價格、有效持倉、有效交易或回測成功結論。
- 對使用者可見輸出使用明確狀態：
- missing-source
- unavailable
- source-error
- not-actionable
- 缺資料狀態不得被歸類為：
- 可買
- 準備
- confirmed
- 市場證據成立
- 持倉有效
- Telegram summary 必須行動優先：
- 今天能不能買：缺資料時寫 新倉：無有效進場
- 持倉先處理什麼：缺持倉或今日交易事件來源時寫 持倉：unavailable，不產生交易建議
- 未持倉哪些只是追蹤：缺 evidence 時不得列為可買，只能列 不可行動
- 哪些不可行動：列缺失來源摘要

`position_events` 契約：

- query success + empty rows：可視為今日真實無事件。
- query success + event rows：使用真實事件統計。
- source-error / missing-source：必須標示 unavailable / source-error，並阻止下游把事件解讀成 0 buy / 0 sell / 今日無交易。

## v20.3.0 Watchlist Breadth Fallback 契約

Tech 必須重新審視 runtime watchlist breadth fallback：

- 若 DB evidence table/cache 已存在，或 Owner 要求 DB 優先，runtime 不得用 breadth fallback 替代 DB evidence。
- fallback 最多只能作為明確標注的非交易診斷。
- fallback 不得稱為市場證據。
- fallback 不得產生 confirmed。
- fallback 不得影響 strategy decision、Telegram 可買結論、持倉建議或 DB payload。
- 若現有契約與此衝突，Tech 必須修正為 fail-closed；若需要產品決策，blocked 回報。

## 已存在且不得回退的契約

- 固定流程文件不可刪除。
- tests fixture 可存在於 tests 範圍，但不得被 runtime import/call。
- 禁止 live Supabase write、正式 backfill、live Telegram delivery，除非 Owner 另行明確批准。
- 不得回退目前已存在的 Telegram 手機閱讀規則：summary 行動優先、可買/追蹤/不可行動分離、缺資料不得寫成推薦。
- 不得回退目前版本下限；若目前版本高於 v20.3.0，以現有版本為基準升 patch，不得降回 v20.3.0。
- 不得把 dry_run、demo、local 的假資料路徑提升為 production fallback。

若 Tech 發現 repo 內另有已存在的 runtime contract，本 TASK 未列但會被本輪影響，必須在 CHANGELOG.md 列出並避免回退；無法判斷時 blocked。

## Tech 證據表要求

Tech 必須提交完整證據表，至少包含欄位：

- path
- function
- keyword
- rg evidence
- import-or-call path
- classification
- risk
- action

classification 只能使用：

- test_fixture
- dev_only
- dry_run_only
- runtime_reachable
- false_positive

必掃 keyword：

- mock
- dummy
- sample
- fixture
- fallback
- synthetic
- hardcoded
- default
- fake
- placeholder
- TODO
- testdata
- demo
- local
- dry_run

Tech 對每個 runtime_reachable 必須採取行動：

- 移除 production 假資料使用；或
- 改為真實 source-of-truth；或
- 改為 fail-closed unavailable；或
- 若只能保留，必須降級為明確標注的 non-trading diagnostic，且不可影響策略/報文/DB 決策。

## 驗收條件

1. Repo 證據化掃描完成，CHANGELOG.md 有完整證據表，覆蓋指定目錄、entrypoints 與 keywords。
2. 所有 runtime reachable fake/mock/dummy/sample/synthetic/default/hardcoded fallback 都被分類並處理。
3. tests fixture 可保留，但 Tech 必須提供 runtime import/call path 反證，證明 tests fixture 不被 production runtime 使用。
4. DB 已有資料的路徑以 DB/真實行情/真實 artifact 為唯一來源。
5. DB empty、DB unavailable、stock API unavailable、evidence table missing/cache missing 時，production runtime fail closed。
6. position_events source-error / missing-source 不產生 fake 今日無交易；DB query 成功但空資料仍可作為真實 0 event。
7. 缺資料時 Telegram / CLI / dry-run report 不產生假可買、confirmed、持倉、價格、交易或回測成功結論。
8. v20.3.0 watchlist breadth fallback 不得替代 DB evidence，不得稱市場證據，不得 confirmed，不得影響決策。
9. 沒有新增 schema、沒有改 watchlist、沒有 live write/backfill/Telegram delivery。
10. 若改到 Telegram / CLI header 或使用者可見報文，版本字串與測試期望同步。
11. 若 Tech 發現必須 schema change、缺 Owner source-of-truth 定義、或無法判斷某 runtime fallback 是否 production 使用，必須 blocked，不得自行決策。

## 範例或 fixture

### Telegram 手機 summary 期望形狀：DB evidence missing

Stock Bot v20.3.1

今日結論
新倉：無有效進場
原因：evidence unavailable，未使用 fallback

持倉
unavailable：持倉來源缺失，不產生交易建議

市場證據
unavailable：DB evidence table/cache 不可用
非交易診斷：watchlist breadth fallback 已停用於決策

### CLI / dry-run 期望形狀：stock API unavailable

status: unavailable
source: stock_api
actionable: false
decision: no_trade
reason: missing-source
confirmed: false
price_source: unavailable

### 禁止形狀

市場證據 confirmed：使用 fallback breadth
今日可買：ABC
價格：100.0 default
持倉：sample position

上述輸出即使測試通過，也必須視為驗收失敗。

## 明確禁止事項

- 禁止 production runtime 使用 fake/mock/dummy/sample/synthetic/default/hardcoded/placeholder/demo/local/testdata 資料生成策略、持倉、交易、證據、回測、行情、DB payload 或 Telegram 結論。
- 禁止 tests fixture 被 runtime import/call。
- 禁止 DB 已有資料路徑改用 fallback 取代 DB。
- 禁止缺資料時補假價格、假持倉、假 evidence、假回測、假 confirmed。
- 禁止 live Supabase write。
- 禁止正式 backfill。
- 禁止 live Telegram delivery。
- 禁止改 watchlist。
- 禁止新增 DB schema；若必須新增，blocked。
- 禁止把 non-trading diagnostic 包裝成市場證據。
- 禁止用「保守預設值」或 default 讓交易判斷繼續執行。
- 禁止把本輪擴張成策略重設、報文大改版、資料管線重構或全專案清理。

## 阻塞條件

Tech 必須 blocked 的情況：

- 無法確認目前 production runtime entrypoint。
- 無法確認 DB/evidence/holdings/market data 的 source-of-truth。
- 修復必須新增或修改 DB schema。
- 修復必須改 watchlist。
- 某 runtime fallback 是否可交易使用無法由 import/call path 判斷。
- 缺測試環境導致無法驗證 fail-closed。
- 發現 live write/backfill/Telegram delivery 才能驗證，本輪不得執行，需回報 Architect/Owner。
- 發現現有版本常量或 header 與本 TASK 版本契約矛盾，且無法安全同步。

## QA 分級建議

L3-lite

QA 必須驗證：

- 重跑或抽查 Tech 證據表中的 runtime reachable 項目。
- 補至少一個 Tech 未覆蓋的 runtime fail-closed 負面案例。
- 驗證 DB empty、DB unavailable、stock API unavailable、evidence table/cache missing 時，不產生假可買、confirmed、持倉、價格或交易建議。
- 驗證 tests fixture 不被 runtime import/call。
- 驗證 watchlist breadth fallback 只能作 non-trading diagnostic，且不得影響決策。
- 驗證 no forbidden diff：無 schema、無 watchlist、無 live write/backfill/Telegram delivery。
- 若 Telegram / CLI 有變更，從 Owner 手機閱讀順序檢查 summary 第一屏是否清楚 fail closed，且版本 header 是否同步。
- 可跑 full pytest；不得做 live/backfill 寫入。

## 本輪停止條件

本輪完成定義：

- 指定目錄與 runtime entrypoints 已完成 keyword 掃描。
- 所有命中的候選項都有證據表分類。
- 所有 runtime_reachable 假資料路徑已修復為真實 source-of-truth、fail-closed，或明確 non-trading diagnostic。
- 指定缺資料情境均驗證不會產生可交易結論。
- CHANGELOG.md 與 QA_REPORT.md 均能對應本 TASK 的 source-of-truth、fail-closed、no forbidden diff 契約。

不納入本輪，只記待辦：

- 與假資料無關的 TODO。
- 純測試 fixture 命名清理。
- 大型資料管線重構。
- 新 schema 設計。
- watchlist 策略改版。
- Telegram 版面全面改版。
- historical artifact 長期治理。
- 非 runtime 可達的 demo/dev tool 清理，除非它會被 production import/call。
