# TASK: 修復報文數據行與證據分數顯示問題

## 任務狀態

- task_id: report-score-evidence-display-20260603
- 任務類型: risk_patch
- 狀態: ready_for_tech
- 版本建議: 使用者可見報文需升版或更新可見版本字串；不得回退既有版本。
- QA 分級建議: L3

## Owner 問題

目前報文在持倉非加碼、證據加成、過熱/風控/資料不足、低量強度與低分百分比顯示上，讓手機閱讀者誤以為「既有持倉仍有新倉品質分」、「綜合分可超過 100」、「所有不可用原因都是資料不足」、「低量仍極強」、「低分仍有有效加成」。

## 使用者可見結果

手機閱讀路徑：Telegram 報文卡片的數據行、證據段、強度標籤與分數摘要。

- 持倉且 holding_decision 存在、且非加碼時，數據行整段顯示 不適用（既有持倉），不顯示綜合/技術/證據/RR 分。
- 只有新倉候選或持倉加碼才顯示綜合分。
- 所有卡片 綜合 分不得大於 100。
- 證據不可用文案需區分：
- heat / 過熱來源: 過熱不適用
- decision FAIL / 減碼 / 結構弱: 風控不適用
- 真無回測且 market 缺資料: 資料不足
- 盤後/收縮整理且量比 <0.8 時，不得顯示 極強；需降級為中性/待確認，或加縮量注記。
- technical < 10 或 round(final)==round(technical) 時，證據段不得顯示誤導性百分比；可省略百分比或顯示微幅。

示例輸出形狀：

建準｜既有持倉｜新倉風控觀察
數據：不適用（既有持倉）

某標的｜過熱 Lv.3
證據：過熱不適用

某新倉候選
技術 96｜證據 +4%｜綜合 100

低量標的｜收縮整理｜量比 0.7
強度：待確認（縮量）

## 非目標

- 不改 RR 公式。
- 不改 DB schema、RLS、grant、policy、role、index、constraint。
- 不改 production write path。
- 不做 live Telegram delivery。
- 不重設整體策略評分模型。
- 不重構全報文格式。
- 不處理本輪未列出的其他文案、排序或策略問題。

## 影響模組與直接消費者

影響模組：

- core/generator.py 的 apply_evidence_confidence 綜合分封頂。
- 報文 formatter / generator 中數據行、證據段、強度標籤、卡片渲染相關邏輯。
- official rendered/message probe 或等價官方報文產生路徑。
- 對應測試與 fixtures。

直接消費者：

- Telegram 手機閱讀者。
- official report/message generator。
- runner 產出的 rendered/message artifact。
- QA probe 與報文回歸測試。

## 輸出契約

既有且不得回退的契約：

- RR 顯示豁免邏輯不得被改壞；持倉非加碼與 RR 使用同一套豁免口徑。
- 新倉候選與持倉加碼仍需顯示綜合/技術/證據分。
- 分組標題、卡片狀態、漏斗、索引、詳情需保持一致。
- 同一持倉在同一份報文只能有一個主行動。
- 空區塊、0-count、無新增下單占位預設不顯示。
- 使用者可見報文版本不得回退。

本輪輸出契約：

- 持倉非加碼:
- 條件: holding_decision 存在，且不是加碼。
- 數據行: 整段固定為 不適用（既有持倉） 或等價明確不可新倉評分文案。
- 禁止: 顯示 綜合/技術/證據/RR 任一新倉品質分。
- 持倉加碼 / 新倉候選:
- 可顯示 技術、證據、綜合。
- 綜合 <= 100。
- 證據不可用:
- heat / overheat: 過熱不適用
- decision FAIL / 減碼 / 結構弱: 風控不適用
- no backtest 且 market 缺資料: 資料不足
- 強度標籤:
- 盤後/收縮整理且量比 <0.8 不得輸出 極強。
- 低分證據百分比:
- technical < 10 或 round(final)==round(technical) 時，不顯示明顯加成百分比；只能省略或標成微幅。

## 版本契約

- 報文可見輸出有變更，Tech 必須核對實際 header / version constant / rendered artifact 的版本字串。
- 若 repo 既有規則要求報文版本升版，需升版；若版本規則不明，Tech 需標 blocked 請 Architect 補充，不得自行假設「不用升版」。

## 驗收條件

1. 持倉非加碼豁免：
- fixture/probe 包含 建準、holding_decision=暫不加碼 或等價非加碼狀態。
- official rendered/message artifact 中不再出現 綜合106 或任何新倉品質分。
- 對應位置顯示 不適用（既有持倉）。
2. 綜合分封頂：
- core/generator.py apply_evidence_confidence 最終分數需等價於 final=min(100.0, technical*modifier)。
- official rendered/message probe 覆蓋至少一張原本會超過 100 的卡片。
- 渲染結果沒有任何 綜合>100。
3. 證據不可用文案：
- 過熱 Lv.3 卡片顯示 過熱不適用。
- decision FAIL / 減碼 / 結構弱卡片顯示 風控不適用。
- 真無回測且 market 缺資料卡片顯示 資料不足。
- 不得把三種情境一律輸出成 資料不足。
4. 極強與量能一致性：
- 盤後/收縮整理且量比 <0.8 的低量標的不顯示 極強。
- 顯示中性/待確認或縮量注記，且不與其他區塊語意衝突。
5. 低分證據百分比：
- technical<10 案例不得出現類似 +6% 但 綜合=技術=7 的誤導顯示。
- round(final)==round(technical) 案例需省略百分比或顯示微幅。
6. 覆蓋層級：
- Tech 自檢必須覆蓋 helper/formatter 與 official generator/message artifact。
- QA 必須補一個 Tech 未覆蓋的直接消費者、負面案例、使用者誤讀路徑或契約風險。
- 若只能測 helper 或局部 formatter，結論只能是 partial，不得宣告使用者可見問題完成。

## 範例或 Fixture

必要 fixture/probe 類型：

- holding_non_add: 建準，既有持倉，holding_decision=暫不加碼/新倉風控觀察/減碼/續抱 任一非加碼。
- holding_add: 既有持倉但加碼，仍可顯示綜合分。
- new_candidate: 新倉候選，仍可顯示綜合分。
- over_cap: technical 與 modifier 乘積大於 100。
- overheat_lv3: boost blocked by heat/overheat。
- risk_blocked: decision FAIL / 減碼 / 結構弱。
- missing_data: 無回測且 market 缺資料。
- low_volume_strong: 盤後/收縮整理且量比 <0.8，原本可能顯示極強。
- low_score_flat: technical<10 或 round(final)==round(technical)。

## 失敗標本與驗收路由

Owner 指定失敗標本：

- 建準暫不加碼持倉顯示 綜合106，應改為 不適用（既有持倉）。
- 過熱 Lv.3 卡片一律顯示 資料不足，應改為 過熱不適用。
- 低量標的仍顯示 極強。
- 低分卡顯示 +6% 但 綜合=技術=7。
- 任一卡片出現 綜合>100。

驗收路由：

- official generator/message artifact 為主驗收層。
- formatter/helper 單測只能作定位與防回歸，不可單獨代表使用者可見完成。
- QA 需用 rendered/message artifact 從手機閱讀視角反證。

## 明確禁止事項

- 禁止修改 RR 公式。
- 禁止 DB schema/write/live Telegram。
- 禁止直接手寫 production DML。
- 禁止把持倉非加碼仍顯示為新倉品質分。
- 禁止任何卡片 綜合>100。
- 禁止把過熱、風控、資料缺失三種情境一律寫成 資料不足。
- 禁止低量收縮整理仍標 極強。
- 禁止只用 synthetic helper fixture 宣告整體報文完成。
- 禁止順手重構策略核心或全報文結構。

## 阻塞條件

- 找不到 official rendered/message artifact 產生路徑，且無等價 replay artifact。
- 無法構造或取得 Owner 失敗標本等價 payload。
- 既有版本字串規則不明且報文版本是否需升版無法判定。
- 持倉加碼與非加碼的資料欄位無法可靠區分。
- boost_blocked 來源無法保留 heat / decision / missing-data 三種原因。
- 測試環境缺依賴且無法補齊。

## 本輪停止條件

完成到以下範圍即停止：

- official rendered/message probe 覆蓋持倉非加碼、持倉加碼或新倉、過熱、風控失敗/減碼/結構弱、資料不足、低量、低分、綜合封頂。
- QA L3 對手機閱讀路徑給出 通過，或因 artifact/source 不足給出 conditional pass/阻塞。
- 不處理其他分數模型、排序、候選池、DB 持久化、live delivery 或未列出的 Telegram 文案問題；發現旁支只記待辦，不納入本輪。
