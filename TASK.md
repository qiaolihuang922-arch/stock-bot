# TASK: 修復 WAIT breakout 低 RR 缺口顯示

## 任務狀態

- task_id: risk_patch_wait_breakout_low_rr_gap_20260601
- 任務尺寸判斷: risk_patch
- 狀態: ready_for_tech
- QA 分級建議: L2
- 版本建議: 使用者可見 WAIT 等待原因會被修正；若 repo 對 Telegram / 報文內容變更要求版本追蹤，需依既有版本契約升版，禁止回退既有版本字串。

## Owner 問題

condition_engine.py 在 decision_type=wait_breakout_low_rr 且 rr=1.2 時，本應依 breakout 類 WAIT 門檻 rr >= 1.5 判斷為 RR 不足。

目前末尾兜底：

if rr >= 1.0:
conditions["rr"] = True

覆蓋了按 decision_type 差異化的 RR 閾值判斷，導致 summarize_conditions(WAIT) 回傳空缺口列表，Telegram / 報文中 WAIT 標的沒有任何等待原因。

## 使用者可見結果

手機閱讀 WAIT breakout 標的時，若 RR 低於 breakout 門檻，報文必須顯示等待原因含「RR不足」或既有等價 RR 缺口文案。

示例輸出形狀：

WAIT / 等待突破
等待原因：RR不足

實際標題、符號、排序、欄位名稱需沿用現有報文格式；本任務只修 WAIT 缺口原因，不重寫報文版面。

## 非目標

- 不改策略 decision 結果。
- 不改 decision_type 產生邏輯。
- 不改 breakout RR 門檻數值 1.5。
- 不改一般非 breakout WAIT 的 RR 門檻語意。
- 不改 DB schema、RLS、grant、policy、role、index / constraint。
- 不改 DB write path、不做 backfill。
- 不做 live Telegram delivery。
- 不做 condition engine 全面 refactor。
- 不擴大為所有 WAIT 類型策略重新設計。

## 影響模組

- condition_engine.py
- RR condition 判斷。
- WAIT 缺口摘要輸入。
- 相關測試 / probe
- 新增或更新可重跑 probe，覆蓋 wait_breakout_low_rr + rr=1.2。

## 直接消費者

- summarize_conditions(WAIT) 或現有等價 WAIT 缺口摘要函式。
- Telegram / 報文 WAIT 區塊等待原因列表。
- QA 可重跑 probe。

## 輸出契約

當輸入符合以下條件：

- decision_type = "wait_breakout_low_rr"
- decision = "WAIT" 或等價 WAIT 狀態
- rr = 1.2
- breakout RR 門檻為 1.5

必須滿足：

- RR condition 不得被末尾 rr >= 1.0 兜底覆蓋為通過。
- WAIT 缺口列表不得為空。
- WAIT 缺口列表必須包含 RR 不足。
- 報文 WAIT 等待原因必須可讓手機閱讀者看出等待原因是 RR 未達 breakout 門檻。
- 既有缺口列表格式、欄位名稱、排序規則、中文文案 key 不得回退；若 Tech 無法確認既有契約，需 blocked 並要求 Architect 補上下游契約。

## 已存在且不得回退的契約

- WAIT 缺口摘要由 condition 結果驅動。
- breakout 類 WAIT 的 RR 判斷需使用 breakout 對應門檻 1.5。
- 非 breakout 場景既有 RR 顯示與通過 / 不通過語意不得被本修復改變。
- WAIT 報文不得出現無等待原因的空白 WAIT 狀態。
- 本修復不得影響 strategy decision、DB write、live Telegram delivery。

## 驗收條件

1. 新增或更新可重跑 probe，覆蓋 decision_type=wait_breakout_low_rr、rr=1.2，驗證 WAIT 缺口列表包含 RR 不足且不是空列表。
2. Probe 必須能由 Tech 在 CHANGELOG.md 記錄固定命令與結果。
3. 測試需確認修復範圍只影響 condition gap / summarize output，不改策略 decision。
4. QA 需補至少一個 Tech 未覆蓋的反證，例如確認非 breakout WAIT 或 rr >= 1.5 breakout 場景未被誤標 RR不足。
5. 不得產生 DB write、不觸發 live Telegram、不要求 production credential。

## 範例或 Fixture

最小 fixture：

decision_type = "wait_breakout_low_rr"
rr = 1.2
breakout_rr_threshold = 1.5
decision = "WAIT"

預期：

gaps = summarize_conditions(...)

assert gaps
assert any("RR" in gap and ("不足" in gap or "low" in gap.lower()) for gap in gaps)

若專案既有測試使用 enum、dataclass、dict payload 或固定中文文案，Tech 必須沿用既有 fixture 風格，不新增平行測試框架。

## 明確禁止事項

- 禁止修改策略買賣 / WAIT decision 判斷。
- 禁止修改 DB schema 或 production write path。
- 禁止新增 production DML、backfill、live Telegram delivery。
- 禁止把本 risk_patch 擴大成 condition engine 全面重構。
- 禁止只改報文文案來掩蓋 condition 判斷錯誤。
- 禁止刪除、放寬既有測試來讓 probe 通過。
- 禁止把 Owner 的「修復」解讀成可跳過 PM -> Tech -> QA。

## 阻塞條件

- 找不到 condition_engine.py 或找不到 WAIT 缺口摘要直接消費路徑。
- 現有 RR 缺口文案 / key 完全不可判定，無法確認「RR不足」應如何表示。
- 測試環境補齊後仍無法重跑 probe。
- Tech 發現 rr >= 1.0 兜底被其他明確契約依賴，修復會改變非 breakout 行為。
- Tech 發現需改策略 decision、DB write 或 live Telegram 才能完成。

## 本輪停止條件

驗到以下範圍即完成本輪：

- wait_breakout_low_rr + rr=1.2 的 WAIT 缺口列表含 RR 不足。
- 可重跑 probe 通過。
- 確認未改 strategy decision、DB write、live Telegram。

以下旁支只記待辦，不納入本輪：

- 全部 WAIT 類型門檻審計。
- RR 門檻產品策略調整。
- 報文整體版面重整。
- condition engine 大規模 refactor。
- production ledger / Telegram delivery consumer 檢查。
