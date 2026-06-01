# TASK: structural evidence coverage 100% 補齊 source/status/use/limit/conflict

## 任務狀態

- task_id: evidence-chain-structural-coverage-100
- 任務類型: risk_patch
- 狀態: ready_for_tech
- 版本建議: v20.4.18
- QA 分級建議: L3
- 本輪主問題: evidence chain 目前未保證 Telegram 報文與內部 report_context / evidence_manifest 的每個使用者可見決策 / 資料層都有可追溯結構欄位，導致 QA 無法重跑證明 structural evidence coverage 100%。

## Owner 問題

Owner 要先把 evidence chain completeness 推到 100%，本輪只處理 structural evidence coverage，不處理資料合理度與衝突本身。

定義為：

- Telegram 報文中每個使用者可見決策 / 資料層都必須能追溯到 evidence slot。
- 內部 report_context / evidence_manifest 中每個對應層都必須有 source/status/use/limit/conflict。
- 若來源不足，輸出 explicit missing-source。
- 若來源互相矛盾，輸出 explicit unresolved-conflict。
- 不得因來源不足或衝突，把標的升格為可買、通過或有效進場。
- 不得造假補來源；缺什麼就標什麼。

## 使用者可見結果

Owner 在手機 Telegram 閱讀三則報文時，所有可見決策與資料層都有清楚資料依據狀態。

手機閱讀路徑：

1. 第一則持倉報文：每個持倉主行動、持倉 / ledger / 價格 / 風控依據，能追溯到 evidence slot。
2. 第二則未持倉 / 非持倉報文：每個可買、可準備、僅追蹤、淘汰 / 不可行動分類，能追溯到 evidence slot。
3. 第三則資料依據 / evidence 報文：按層顯示資料來源狀態、用途、限制與衝突狀態；不足或衝突時明確顯示 missing-source 或 unresolved-conflict。
4. 若任一必要層為 missing-source 或 unresolved-conflict，該標的不得顯示為可買 / 通過 / 有效進場。

示例輸出形狀：

📌 資料依據

市場題材：
source: production-market-theme
status: available
use: 背景判斷
limit: 只作環境背景，不等於買點
conflict: none

策略樣本：
source: classification-sample
status: missing-source
use: 不納入買賣判斷
limit: 樣本來源不足
conflict: none

持倉 / ledger：
source: production-ledger
status: unresolved-conflict
use: 停利 / 續抱判斷暫停升格
limit: 持倉股數與事件紀錄不一致
conflict: position-vs-event

## 非目標

- 不處理資料合理度本身。
- 不解決資料衝突本身。
- 不 backfill production data。
- 不新增 DB schema、RLS、grant、policy、role、index、constraint。
- 不做 production DML。
- 不改 live Telegram delivery。
- 不重寫策略核心。
- 不改買賣策略門檻，除非只是 fail-closed 防止 missing-source / unresolved-conflict 升格為可買或通過。
- 不清理全 repo。
- 不把 v20.4.17 第三則人話資料依據回退成 raw debug dump。

## 影響模組

Tech 需自行定位實際檔案；預期影響範圍限於：

- Telegram report generator / renderer。
- report_context 組裝邏輯。
- evidence_manifest 組裝邏輯。
- evidence coverage verifier / read-only artifact 產生工具。
- 三則 Telegram 報文 sample / fixture。
- 對應測試。

不得觸碰：

- DB schema / migration。
- production write path。
- live Telegram send path。
- unrelated strategy refactor。

## 直接消費者

- Owner 手機 Telegram 閱讀者。
- QA 重跑三則 Telegram 報文的 verifier。
- 內部 report_context consumer。
- 內部 evidence_manifest consumer。
- runner / CI 中的 evidence coverage tests。

## 已存在且不得回退的契約

- Telegram message list 順序維持：messages[0] 持倉、messages[1] 未持倉 / 非持倉、messages[2] short / evidence；include_detail=True 時 Details Backup 仍追加最後。
- 第一則、第二則既有持倉 / 未持倉卡片主結構不得無關改動。
- market/theme 只能作背景，不等於買點。
- strategy sample 缺來源或不可用時不得納入買賣判斷。
- 缺資料必須 fail closed。
- 不得把資料不足寫成可用。
- 使用者可見版本目前不得回退到 v20.4.16 或更舊；本輪有使用者可見 evidence 狀態變更，版本建議升至 v20.4.18。
- v20.4.17 已完成人話資料依據；本輪允許新增標準 status token missing-source / unresolved-conflict，但不得回退為雜亂 raw 表名、欄位 dump 或 ISO timestamp debug output。
- 若 Tech 發現現有契約與本 TASK 衝突，必須 blocked 回報 Architect，不得自行決定破壞既有報文結構。

## 輸出契約

每個使用者可見決策 / 資料層，都必須在 report_context 或 evidence_manifest 中有一筆可追溯 evidence slot。

必要層級：

- 市場題材 / market-theme。
- 策略樣本 / classification or strategy sample。
- 持倉 / positions。
- ledger / execution memory / position events。
- 價格 / OHLCV。
- RR / score / volume。
- 漏斗 / funnel classification。
- 交易執行 / execution plan。
- 明日計畫 / next-day plan。
- 缺資料 / missing-data。
- 衝突 / conflict。

每個 slot 至少包含：

layer: stable layer id
target: symbol / report section / decision id
source: stable source id or missing-source
status: available | missing-source | source-error | insufficient-data | unresolved-conflict | not-used
use: why this source is used or explicitly not used
limit: known limitation
conflict: none | conflict id / summary
visible_refs: Telegram section/message/card ids consuming this slot

Telegram 輸出契約：

- 第三則必須覆蓋上述層級的 status/use/limit/conflict 摘要。
- 第一則與第二則中若顯示可買 / 通過 / 有效進場，該決策對應 slot 不得為 missing-source、source-error、insufficient-data 或 unresolved-conflict。
- 若必要 slot 不足或衝突，Telegram 必須顯示保守結論，例如僅追蹤、不可行動、資料不足、衝突未解。
- Telegram 可用人話呈現，但 verifier 必須能從輸出或 manifest 對回 slot。

Verifier / artifact 契約：

- 提供 read-only artifact，內容包含三則報文與 evidence manifest。
- artifact 必須標示：
- schema_change=false
- data_write=false
- live_telegram=false
- credential_values_included=false
- verifier 必須輸出 coverage 結果：
- total visible decision/data layers
- covered layers
- missing slots
- conflict slots
- pass/fail
- structural coverage 必須為 100%，否則 fail。

## 驗收條件

1. 三則報文完整性

- 可重跑產生完整三則 Telegram sample。
- message order 不變。
- 版本顯示 v20.4.18 或 Tech 明確證明本 repo 另有版本契約不需升版；若不確定則 blocked。

2. Structural evidence coverage

- verifier 對三則報文與 evidence_manifest 計算 coverage。
- 每個必要層都有 source/status/use/limit/conflict slot。
- coverage 必須為 100%。
- 不允許用空字串、假 source、硬編 placeholder 冒充 coverage。

3. Missing-source / unresolved-conflict fail closed

- 任一必要買賣判斷來源為 missing-source 時，不得輸出可買 / 通過 / 有效進場。
- 任一必要買賣判斷來源為 unresolved-conflict 時，不得輸出可買 / 通過 / 有效進場。
- Telegram 必須明確顯示缺來源或衝突未解。

4. QA 可重跑 artifact

- Tech 提供標準 read-only artifact 產生命令。
- QA 可在不連 live Telegram、不寫 DB、不改 schema 的情況下重跑。
- artifact 不包含 credential values。
- QA 至少驗三則完整報文，不得只驗單一 formatter。

5. 既有契約不回退

- market/theme 未被升格成買點。
- strategy sample 不可用時仍未納入買賣判斷。
- v20.4.17 的人話資料依據不得回退成 raw debug dump。
- 第一則 / 第二則主結構與 message order 不因本任務破壞。

## 範例或 fixture

Tech 至少提供 3 組可重跑 fixture 或 artifact case：

1. all_sources_available

- 市場題材、策略樣本、持倉 / ledger、價格、RR / score / volume、漏斗、交易執行、明日計畫皆有 slot。
- verifier coverage = 100%。
- 可買 / 通過只允許出現在必要 slot 都可用且無衝突的標的。

2. missing_strategy_sample_source

- strategy sample slot 為 missing-source。
- Telegram 顯示本輪不納入買賣判斷。
- 不得升格可買 / 通過。
- verifier coverage = 100%，因缺來源本身也有 slot。

3. ledger_position_conflict

- 持倉與 ledger / execution memory 互相矛盾。
- slot 顯示 unresolved-conflict。
- Telegram 顯示衝突未解與保守處理。
- 不得輸出已確認停利、可賣股數或有效執行結論，除非來源可追溯且無衝突。

## 明確禁止事項

- 禁止改 DB schema。
- 禁止 production DML / backfill。
- 禁止 live Telegram delivery。
- 禁止用 local cache、runtime dict、agent 對話當跨日 source-of-truth。
- 禁止偽造 source/status/use/limit/conflict。
- 禁止將 missing-source 或 unresolved-conflict 升格為可買、通過、有效進場。
- 禁止只在 Telegram 補文案但 report_context / evidence_manifest 沒有結構 slot。
- 禁止只補 internal manifest 但 Telegram 使用者可見決策無法追溯。
- 禁止把本任務擴成策略合理度修正、資料衝突修復或 production 資料清洗。
- 禁止把 read-only artifact 寫入 production 或觸發 live delivery。

## 阻塞條件

Tech 必須 blocked 並列 Owner approval point，如果出現以下任一情況：

- 要達成 coverage 100% 必須新增 DB schema、欄位、index、constraint、RLS、grant、policy 或 role。
- 要達成 coverage 100% 必須直接手寫 production DML。
- 現有 repo 沒有可用 read-only source 或 approved service API 產生必要 evidence slot。
- 無法定位 report_context 或 evidence_manifest 的實際生成位置。
- 無法建立三則報文與 manifest 的可重跑 artifact。
- 現有資料不足以判定某層 source，且沒有辦法以 missing-source 結構化標示。
- 現有報文決策與 evidence slot 無法建立穩定映射。
- 測試環境缺失且無法補齊，導致 QA 不能重跑完整三則報文與 manifest verifier。

## 本輪停止條件

驗到以下即算本輪完成：

- 三則 Telegram sample 可重跑。
- report_context / evidence_manifest 中所有必要使用者可見層都有 source/status/use/limit/conflict。
- verifier 報告 structural coverage = 100%。
- missing-source / unresolved-conflict case 仍可被覆蓋，但會 fail closed，不升格可買或通過。
- QA 使用 Tech 提供命令重跑完整三則報文與 manifest verifier，並另補至少一個反證案例。
- 未處理的資料合理度、資料衝突修復、ledger 稽核、策略門檻調整，只記為後續待辦，不納入本輪完成口徑。
