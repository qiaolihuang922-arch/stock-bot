# TASK: 將 support 納入 strategy() 止損候選計算

## 任務狀態

- task_id: strategy-support-stop-candidate-20260601
- 任務類型: normal_patch
- 狀態: ready_for_tech
- 版本建議: 若使用者可見報文內容或策略版本字串會呈現 RR / 止損變化，需同步升版；若只影響內部測試 fixture 且無版本 header，則不新增版本字串。
- QA 分級建議: L2

## Owner 問題

services/analysis.py 的 strategy() 中已解包：

support, resistance = support_resistance(closes)

但 support 未參與止損候選計算。現有止損候選：

stop_candidate = min(ma5, avg(closes[-3:]))

完全忽略支撐位，可能導致止損價與 RR 計算偏離策略語意。Owner 指定本輪評估並修正是否應將 support 納入 stop_candidate，例如：

stop_candidate = max(support, min(ma5, avg(closes[-3:])))

並補測試驗證修改後 RR / 風險計算方向符合預期。

## 使用者可見結果

- 使用者看到的策略輸出、報文或 CLI 中，若包含止損價、風險距離、RR / risk-reward 類欄位，這些值可能因 support 被納入而改變。
- 當有效 support 高於原本 min(ma5, avg(closes[-3:])) 時，止損候選應優先貼近支撐位，而不是被較低的短均或近三日均值壓低。
- 若 support 無效、缺失、非數值、非正數，或納入後會產生不合理止損，應維持既有 fallback 行為，不讓策略輸出崩潰。

## 非目標

- 不重設策略核心。
- 不改買賣 / 加減碼 / 持倉狀態機。
- 不改 DB schema、RLS、grant、policy、role、index / constraint。
- 不做 live Telegram delivery。
- 不回填 production DB。
- 不調整 support_resistance() 本身演算法，除非現有函式輸出型別與本任務無法相容且需先 blocked。
- 不順手清理整個 services/analysis.py。
- 不擴大到所有策略指標的 RR 定義重構。

## 影響模組

- services/analysis.py
- strategy() 的止損候選計算。
- 由止損候選推導出的止損價、風險距離、RR / risk-reward 類輸出。
- 測試
- 需新增或更新覆蓋 support 介入與 fallback 的 focused tests。
- 可能受影響但不得任意改契約
- 既有報文 formatter。
- 既有 CLI / runner 消費 strategy() 結果的欄位。
- 既有 Telegram 報文組裝流程。

## 直接消費者

- strategy() 的既有 Python callers。
- 依賴 strategy() 回傳結果產生的策略報文 / Telegram message builder。
- 依賴止損價、RR 或風險距離的既有測試與 fixture。
- Owner 手機閱讀的最終策略報文，僅限本輪改動實際影響到報文欄位時。

## 已存在且不得回退的契約

- 不得移除或重新命名 strategy() 現有回傳欄位。
- 不得改變 strategy() 既有 public return type。
- 不得改變既有 caller 需要的欄位順序、payload shape 或 message list shape。
- 不得讓 support_resistance(closes) 的 resistance 既有用途退化。
- 不得將缺資料或無效 support 解讀成可交易訊號。
- 不得在 production DB 或 live Telegram 上產生寫入 / 發送副作用。
- 若 Tech 發現現有契約與上述描述不一致，必須 blocked 並回報 Architect，不得自行改契約。

## 輸出契約

- strategy() 必須維持既有輸入參數與回傳 shape。
- 止損候選計算契約：
- 先計算既有短線止損基準：baseline_stop = min(ma5, avg(closes[-3:]))。
- 若 support 是有效 numeric 且可作為合理多方止損候選，則 stop_candidate 應不低於 baseline_stop，建議為 max(support, baseline_stop)。
- 若 support 無效或不合理，stop_candidate 必須回退為 baseline_stop。
- RR / risk-reward 契約：
- 不新增新的 RR 欄位名稱。
- 不改既有 RR 欄位語意，除非現有名稱與計算方向本身不明確；若不明確，Tech 必須先記錄現有公式並只測「納入 support 後由 stop_candidate 造成的方向變化」。
- 報文契約：
- 若報文露出止損或 RR，文字區塊結構不得變。
- 示例形狀保持既有卡片 / 行格式，例如：

停損: <price>
RR: <value>

- 本輪不新增手機報文區塊、不新增解釋長句。

## 驗收條件

- support 高於原本 baseline_stop 的 fixture 中，strategy() 使用的止損候選必須因 support 納入而上移。
- 上述 fixture 中，由止損候選推導出的 RR / risk-reward 類值必須依現有公式呈現可解釋的方向變化，測試需明確 assert 舊 baseline 與新結果的差異方向。
- support 低於或等於 baseline_stop 時，結果不得比既有 baseline 更差，且不應出現非預期下移。
- support 無效時，策略仍可執行並維持 baseline fallback。
- 既有 strategy() consumers 的 return shape 測試不得失敗。
- 不產生 DB write、live Telegram send、持倉狀態機變更。
- Tech 需在 CHANGELOG.md 寫明實際公式、修改檔案、自檢命令與結果。

## 範例或 fixture

- fixture A: support > min(ma5, avg(closes[-3:]))
- 期待：stop_candidate 從 baseline 上移至 support 或 support 約束後的合理值。
- 期待：RR / risk-reward 依現有公式產生相對舊 baseline 的方向變化，測試名稱需說明該方向。
- fixture B: support <= min(ma5, avg(closes[-3:]))
- 期待：stop_candidate 等於既有 baseline，不因 support 更低而下移。
- fixture C: support 無效或資料不足
- 期待：fallback 至既有 baseline，strategy() 不 crash。

## 明確禁止事項

- 禁止改 DB schema 或 production DML。
- 禁止 live Telegram delivery。
- 禁止改持倉狀態機。
- 禁止把本任務擴成策略重構。
- 禁止改 support_resistance() 的輸出契約。
- 禁止刪除既有回傳欄位或改名。
- 禁止只改公式不補測試。
- 禁止用「看起來合理」取代可重跑測試證據。

## 阻塞條件

- Tech 無法確認 strategy() 現有 return shape 或 RR 公式時，blocked。
- support_resistance(closes) 可能回傳非 numeric 且現有程式無明確處理方式時，blocked 或先以最小 defensive guard 處理並列明。
- 納入 support 後會讓止損價高於或等於進場 / 現價，且現有策略沒有處理此情境時，blocked，需 Architect/Owner 決定 clamp 或 fallback 規則。
- 測試環境缺依賴且無法補齊時，blocked，不得宣告通過。

## 本輪停止條件

- 完成條件：strategy() 止損候選已按契約納入有效 support，focused tests 覆蓋 support 生效、support 不生效、support fallback 三類案例，且既有相關測試通過。
- 旁支不納入本輪：RR 命名重構、策略參數重新校準、報文文案優化、全量 fixture 更新、production replay、DB 回填。這些若被發現，只記為後續待辦，不阻塞本輪，除非直接導致本任務驗收無法判定。
