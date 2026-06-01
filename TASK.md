# TASK: evidence chain maturity 100% read-only artifacts / verifiers / gates

## 任務狀態

- task_id: evidence-chain-maturity-100
- 任務類型: risk_patch
- 狀態: ready_for_tech
- 版本建議: v20.4.19
- QA 分級建議: L3
- 本輪主問題: 先前完成的是 structural coverage 100%，但 Owner 要完成的是 evidence chain maturity 72/100 -> 100/100；本輪要把五個 evidence 成熟度維度補到可驗收、可重跑、read-only、fail-closed，而不是只證明欄位存在。

## Owner 問題

Owner 指正：目標不是「每層都有 source/status/use/limit/conflict slot」而已，而是把 evidence chain maturity 補到 100/100。

本輪必須涵蓋五個維度：

1. data source / anti-fake evidence: 100
2. Telegram evidence expression: 100
3. strategy sample evidence: 100
4. execution memory / ledger evidence: 100
5. repeatable runner / process: 100

完成口徑：

- 每個 evidence claim 都能追到 read-only source-of-truth artifact。
- 每個 artifact 都標明 source/status/use/limit/conflict。
- 缺資料、source-error、欄位不足或來源衝突時，不得被 synthetic fixture 或 optimistic 文案掩蓋。
- strategy sample 與 ledger / position_events 必須有 source-of-truth read-only artifact 與 verifier，不再只靠 synthetic fixture。
- runner / Tech worktree / QA handoff / git completion gate 必須能防止 stale artifact、stale handoff file、未 commit/push 卻宣告完成。

## 使用者可見結果

Owner 在手機 Telegram 看報文時，能清楚分辨：

1. 哪些資料來自 production source-of-truth。
2. 哪些只是 fixture / sample / synthetic 測試，不得當成 production evidence。
3. 哪些策略樣本可用、不可用、缺來源或不足。
4. 哪些持倉 / execution memory / ledger 判斷來自 positions、position_events 或其他已確認持久來源。
5. 哪些來源衝突導致保守處理。

手機閱讀路徑：

1. 第一則持倉報文：持倉主行動、已買 / 已賣 / 已停利 / 已減碼、風控與明日計畫，必須能追到 execution memory / ledger source。
2. 第二則未持倉 / 非持倉報文：可買、可準備、僅追蹤、淘汰 / 不可行動，必須能追到 strategy sample / price / RR / funnel evidence。
3. 第三則 evidence 報文：必須呈現 production source、artifact status、使用限制、衝突狀態；不得只顯示 synthetic fixture 成功。

示例輸出形狀：

📌 資料依據

策略樣本：
source: production-readonly-strategy-sample-artifact
status: missing-source
use: 不納入買賣判斷
limit: 缺 classification backtest source-of-truth
conflict: none

執行記憶 / Ledger：
source: production-readonly-position-events-artifact
status: unresolved-conflict
use: 停利 / 續抱判斷 fail closed
limit: positions 與 position_events 不一致
conflict: position-vs-events

Runner / Artifact：
source: qa-artifact-sync-gate
status: available
use: QA 驗證使用最新 TASK/CHANGELOG/artifact
limit: read-only，不代表 live delivery
conflict: none

## 非目標

- 不處理策略合理度。
- 不調整買賣策略門檻。
- 不重寫策略核心。
- 不修 production ledger / position_events 資料本身。
- 不 backfill production data。
- 不新增 DB schema、欄位、index、constraint、RLS、grant、policy、role。
- 不手寫 production DML。
- 不改 production write path。
- 不做 live Telegram delivery。
- 不把 synthetic fixture 當 production source-of-truth。
- 不清理全 repo。
- 不處理 Telegram reply markup 附著最後一則 message 的旁支風險。

## 影響模組

Tech 需自行定位實際檔案；預期影響範圍限於：

- evidence manifest / report_context 組裝。
- Telegram evidence renderer。
- strategy sample read-only artifact generator。
- strategy sample verifier。
- positions / position_events / ledger read-only audit artifact generator。
- ledger / execution memory verifier。
- structural evidence artifact generator 的 production-source 擴充或新 artifact generator。
- QA / runner handoff artifact sync。
- Tech worktree hygiene gate。
- git completion gate integration。
- 對應測試與 fixture。

不得觸碰：

- DB schema / migrations。
- production write path。
- live Telegram send path。
- unrelated strategy refactor。

## 直接消費者

- Owner 手機 Telegram 閱讀者。
- QA 重跑 evidence maturity verifier。
- Architect 收口 git completion gate。
- runner / CI evidence artifact consumer。
- Tech worktree handoff consumer。
- report_context / evidence_manifest 內部 consumer。
- future production read-only audit consumer。

## 已存在且不得回退的契約

- Telegram message list 順序維持：messages[0] 持倉、messages[1] 未持倉 / 非持倉、messages[2] short/evidence；include_detail=True 時 Details Backup 仍追加最後。
- 報文版本目前已升至 v20.4.18；本輪若有使用者可見 evidence expression 變更，版本建議升至 v20.4.19，不得回退。
- structural evidence coverage 100% 不得回退：必要層仍需具備 layer / target / source / status / use / limit / conflict / visible_refs。
- 必要層至少包含 market-theme、strategy-sample、positions、ledger、price-ohlcv、rr-score-volume、funnel-classification、execution-plan、next-day-plan、missing-data、conflict。
- verifier 對 blocking source status 下的 可買 / 通過 / 有效進場 必須 fail。
- market/theme 只能作背景，不等於買點。
- strategy sample 不可用時不得納入買賣判斷。
- 缺資料、source-error、insufficient-data、unresolved-conflict 必須 fail closed。
- read-only artifact 必須標示 schema_change=false、data_write=false、live_telegram=false、credential_values_included=false。
- 不得把 v20.4.17 / v20.4.18 的人話 evidence 回退成 raw debug dump。
- 若 Tech 發現現有契約與本 TASK 衝突，必須 blocked 回報 Architect，不得自行破壞既有報文結構。

## 輸出契約

### A. Maturity Score Contract

Tech 必須提供可重跑 verifier，輸出五個維度各自分數與總結論：

{
"maturity_score": 100,
"dimensions": {
"data_source_anti_fake": {"score": 100, "status": "pass"},
"telegram_evidence_expression": {"score": 100, "status": "pass"},
"strategy_sample_evidence": {"score": 100, "status": "pass"},
"execution_memory_ledger_evidence": {"score": 100, "status": "pass"},
"repeatable_runner_process": {"score": 100, "status": "pass"}
},
"blocking_findings": [],
"artifacts": []
}

若任一維度未達 100，總結論不得寫完成，只能寫 partial 或 blocked。

### B. Artifact Contract

每個 read-only artifact 至少包含：

- artifact_id
- generated_at
- source_type: production-readonly | fixture | synthetic | runner-log
- source_name
- source_version_or_query_id
- schema_change=false
- data_write=false
- live_telegram=false
- credential_values_included=false
- status: available | missing-source | source-error | insufficient-data | unresolved-conflict
- use
- limit
- conflict
- records_summary
- visible_refs
- verifier_result

Production read-only artifact 不得包含 credential values、tokens、完整 secrets、live delivery payload。

### C. Strategy Sample Evidence Contract

必須提供 strategy sample source-of-truth read-only artifact 與 verifier：

- 能區分 production source-of-truth、fixture、synthetic sample。
- 若缺 classification backtest / sample source-of-truth，必須輸出 missing-source。
- 若樣本不足，必須輸出 insufficient-data。
- 若只有 synthetic fixture，必須標示 source_type=synthetic 且不得作為 production 可買證據。
- Telegram 中 strategy sample 的使用限制必須可見。
- 任何 strategy sample 缺來源或不足時，不得使標的升格為可買 / 通過 / 有效進場。

### D. Execution Memory / Ledger Evidence Contract

必須提供 positions / position_events / ledger source-of-truth read-only audit artifact 與 verifier：

- 能標示持倉股數、狀態、已買、已賣、已停利、已減碼的來源。
- 能檢查 positions 與 position_events 是否一致。
- 若事件紀錄缺 label、缺股數、缺日期或與 positions 衝突，必須輸出 insufficient-data 或 unresolved-conflict。
- 衝突時 Telegram 不得輸出已確認停利、可賣股數或有效執行結論。
- artifact 只讀，不修 DB，不 backfill。

### E. Runner / Process Contract

必須補齊或驗證以下 gate：

- QA 啟動前同步最新 TASK.md、CHANGELOG.md、QA_REPORT.md、artifact spec 到 Tech / QA worktree。
- QA 使用的 artifact 必須可追溯到本輪最新 commit 或 worktree hash。
- Tech worktree 若有 stale candidate diff、stale handoff file、缺 artifact，runner 必須 fail 或 blocked。
- repo 落地任務 final 前必須整合 git completion gate：worktree clean、branch 有 upstream、local HEAD 等於 upstream HEAD。
- gate 失敗時，不得宣告完成。

## 驗收條件

1. 五維 maturity verifier

- Tech 提供單一標準命令產生 maturity report。
- 報告五個維度皆為 100。
- 若任一 artifact 缺 source/status/use/limit/conflict，該維不得 100。
- 若 production source 缺失卻被 synthetic fixture 補成 pass，verifier 必須 fail。

2. Strategy sample source-of-truth

- QA 可重跑 strategy sample read-only artifact。
- artifact 能顯示 production source、missing-source、insufficient-data 或 synthetic 限制。
- 缺 source-of-truth 時 Telegram 與 verifier 均 fail closed。
- 不得只用 synthetic fixture 證明 strategy sample maturity 100。

3. Ledger / position_events source-of-truth

- QA 可重跑 positions / position_events / ledger read-only audit artifact。
- artifact 能揭露 shares/status/event/date/label 來源摘要。
- conflict case 會輸出 unresolved-conflict。
- conflict case 不得輸出已確認停利、可賣股數或有效執行結論。

4. Telegram evidence expression

- 三則 Telegram sample 可重跑。
- message order 不變。
- 第三則 evidence 報文能讓手機使用者分辨 production、fixture、synthetic、missing-source、unresolved-conflict。
- 第一則 / 第二則若有可買 / 通過 / 有效進場，對應 evidence 不得是 blocking status。

5. Runner / process

- QA handoff 不得讀 stale CHANGELOG.md 或 stale artifact。
- Tech worktree hygiene gate 能攔 stale diff / stale handoff / missing artifact。
- git completion gate 已納入收口流程或提供可重跑命令。
- gate 失敗時輸出 blocked，不得寫完成。

6. 既有契約不回退

- structural evidence coverage 100% 仍成立。
- v20.4.18 既有 message order 與人話 evidence 不回退。
- market/theme 未被升格成買點。
- strategy sample 不可用時仍不納入買賣判斷。
- 不改 DB schema / write path / live Telegram。

## 範例或 fixture

Tech 至少提供以下 artifact / verifier cases：

1. production_all_sources_available

- 使用 read-only source-of-truth artifact。
- 五維 maturity score = 100。
- Telegram evidence 可區分 source/use/limit/conflict。
- 不包含 credential values。

2. strategy_sample_missing_source

- strategy sample artifact status = missing-source。
- verifier 不允許用 synthetic fixture 補成 production pass。
- Telegram 顯示不納入買賣判斷。
- 不得輸出可買 / 通過 / 有效進場。

3. strategy_sample_synthetic_only

- strategy sample artifact source_type = synthetic。
- 可用於測試 renderer / verifier。
- 不得被計為 production source-of-truth maturity pass。
- verifier 必須在 production maturity gate 中 fail 或標 partial。

4. ledger_position_conflict

- positions 與 position_events 衝突。
- ledger artifact status = unresolved-conflict。
- Telegram 顯示衝突未解與保守處理。
- 不得輸出已確認停利、可賣股數或有效執行結論。

5. runner_stale_artifact_blocked

- 模擬 QA handoff artifact 與最新 TASK/CHANGELOG 不一致。
- runner / verifier 必須 fail 或 blocked。
- 不得宣告 maturity 100。

## 明確禁止事項

- 禁止改 DB schema。
- 禁止新增欄位、index、constraint、RLS、grant、policy、role。
- 禁止 production DML / backfill。
- 禁止 live Telegram delivery。
- 禁止用 local cache、runtime dict、agent 對話當跨日 source-of-truth。
- 禁止把 synthetic fixture 當 production evidence。
- 禁止偽造 source/status/use/limit/conflict。
- 禁止 missing-source、source-error、insufficient-data、unresolved-conflict 下升格為可買 / 通過 / 有效進場。
- 禁止只補 Telegram 文案但沒有 read-only artifact / verifier。
- 禁止只補 internal manifest 但手機報文不可讀。
- 禁止把本任務擴成策略合理度、資料修復、production ledger 清洗或全 repo cleanup。
- 禁止 QA 只重跑 Tech 命令而不做反證。

## 阻塞條件

Tech 必須 blocked 並列 Owner approval point，如果出現以下任一情況：

- 要達成 maturity 100 必須新增 DB schema、欄位、index、constraint、RLS、grant、policy 或 role。
- 要達成 maturity 100 必須手寫 production DML、backfill 或修 production ledger。
- 要達成 maturity 100 必須 live Telegram delivery。
- repo 沒有可用 read-only source 或 approved service API 產生 strategy sample source-of-truth artifact。
- repo 沒有可用 read-only source 或 approved service API 產生 positions / position_events / ledger audit artifact。
- 無法避免 credential values 進入 artifact。
- 無法建立 production source、fixture、synthetic 三者的明確區分。
- 無法把 Telegram visible decision 對回 artifact / manifest。
- runner 無法取得最新 handoff files 或無法判斷 stale artifact。
- 測試環境缺失且無法補齊，導致 QA 不能重跑 maturity verifier。

## 本輪停止條件

驗到以下即算本輪完成：

- 五個 maturity 維度 verifier 全部 100。
- strategy sample 有 source-of-truth read-only artifact / verifier，缺來源或 synthetic-only 會 fail closed。
- ledger / position_events 有 source-of-truth read-only audit artifact / verifier，衝突會 fail closed。
- 三則 Telegram sample 可重跑，手機閱讀能看出 source/status/use/limit/conflict。
- runner / QA artifact sync / Tech worktree hygiene / git completion gate 有可重跑 gate，且 stale artifact case 會 fail 或 blocked。
- QA 至少補一個 Tech 未覆蓋的反證：synthetic-only 不得通過 production maturity、ledger conflict 不得產生已確認執行結論、或 stale artifact 不得通過 runner gate。
- 不處理策略合理度、資料修復、production backfill、live delivery、Telegram reply markup 旁支；這些只記待辦，不納入本輪完成口徑。
