# TASK: 持倉弱勢觀察補充觀察天數 / 降級時鐘

## 任務狀態

- task_id: holding-weak-observation-clock-20260601
- 任務類型: normal_patch
- 狀態: ready_for_tech
- 版本建議: 使用者可見 Telegram / 報文內容有變更，需同步檢查並視現有版本規則升版；不得回退既有版本字串。
- QA 分級建議: L2
- 本輪主 bug: 弱勢且遠離突破的持倉卡只有「續抱觀察 / 降低優先級」語意，缺少可讀的觀察天數或 fail-closed 狀態，手機閱讀者無法判斷這是第幾天觀察、何時會降級。

## Owner 問題

3035 智原持倉卡顯示弱勢、遠離突破 4.07%、V 0.65x、持倉約 -0.28%，決策為「續抱觀察」，條件寫「若無法重新接近買點，降低優先級」，但沒有 observation_days 或量化降級時鐘。使用者不知道目前是第幾天弱勢觀察，也不知道什麼條件
會觸發降級。

## 使用者可見結果

手機閱讀持倉報文時，弱勢且遠離觸發 / 買點的持倉，必須在持倉卡或第三則持倉風控檢查中出現人話化觀察狀態：

- 若現有 holding_signal / result / persistent source 已有 observation_days、weak_far_from_trigger 或等價觀察狀態，顯示「弱勢觀察第 N 天」與明確降級條件。
- 若沒有可信持久來源，不得推算或假造天數，必須 fail-closed 顯示「觀察天數未確認」或等價人話，並保留降級條件為條件式描述。
- 既有買賣、加減碼、停損、停利 decision 不變。

## 非目標

- 不重設持倉策略、買賣決策、加減碼規則、停損停利規則。
- 不新增或修改 DB schema、RLS、grant、policy、role、index、constraint。
- 不做 production backfill。
- 不 live Telegram delivery。
- 不全量重構持倉報文、漏斗、策略分數或訊號來源。
- 不處理其他持倉卡文案噪音、排序或分組問題；若 Tech / QA 發現，記為 follow-up，不納入本輪完成條件。

## 影響模組與直接消費者

影響模組需由 Tech 依 repo 實際檔案確認，預期範圍限於：

- 持倉訊號 / result 到 Telegram 報文 formatter 的資料讀取與文字輸出路徑。
- 持倉卡或第三則持倉風控檢查的 message list 生成。
- 手機閱讀 probe / regression test fixture。

直接消費者：

- Telegram 持倉報文手機閱讀者。
- 持倉卡 formatter / message list 消費者。
- QA 的手機閱讀 probe。

## 輸出契約

### 已存在且不得回退的契約

- 同一持倉在同一份報文只能有一個主行動：加碼 / 續抱 / 觀察 / 減碼 / 停損 / 停利 / 不動作。
- 本任務不得改變任何買賣 / 加減碼 / 停損 / 停利 decision。
- 可買、可準備、僅追蹤、淘汰 / 不可行動的分組語意不得被本任務改動。
- 持倉卡既有價格、距離突破、量能、損益等欄位若原本輸出，不能因本任務消失。
- 缺資料時必須 fail closed，不得把 runtime dict、local cache 或對話記憶當跨日觀察天數來源。

### 新增 / 修正契約

弱勢且遠離觸發 / 買點、主行動仍為續抱觀察的持倉，輸出必須包含以下其中一種形狀：

有可信來源：

觀察：弱勢觀察第 2 天；若第 3 天仍未重新接近買點 / 突破區，降低優先級

缺可信來源：

觀察：觀察天數未確認；若無法重新接近買點 / 突破區，降低優先級

位置允許二選一，但同一份報文只需出現一次，不得重複長句：

- 持倉卡內的風控 / 條件行。
- 第三則持倉風控檢查中對該持倉的條目。

欄位語意：

- observation_days 若存在且可信，必須以正整數 N 顯示為「第 N 天」。
- 若只存在等價狀態，例如 weak_far_from_trigger 加上可信 observation start / day count，可轉成人話顯示。
- 若來源不存在、為 null、非正整數、無法證明來自 persistent source，輸出「觀察天數未確認」，不得輸出「第 1 天」或其他推測天數。
- 降級條件必須是條件式，不得把「降低優先級」寫成已發生事實，除非既有 decision/result 已明確標示已降級。

## 驗收條件

1. Tech 先盤點現有 holding_signal / result / persistent source 是否已有 observation_days、weak_far_from_trigger 或等價觀察狀態，並在 CHANGELOG.md 寫明使用來源；若沒有可信來源，實作 fail-closed 文案。
2. 有 observation_days = N 的 weak far holding fixture，手機閱讀輸出包含「弱勢觀察第 N 天」或等價第 N 天文案，並包含降級條件。
3. 缺 observation_days / 缺可信 source 的 weak far holding fixture，手機閱讀輸出包含「觀察天數未確認」或等價人話，且不得輸出任何確認天數。
4. 3035 類型情境仍維持原主決策為「續抱觀察」；不得因顯示修正改成買入、賣出、減碼、停損、停利或加碼。
5. 手機閱讀 probe 覆蓋至少兩個案例：有觀察天數、缺 source fail-closed。
6. 版本字串 / header 若現有規則要求使用者可見報文變更升版，需同步；若不升版，Tech 必須在 CHANGELOG.md 說明現有契約為何允許不升版。

## 範例或 Fixture

### Fixture A: 有可信 observation_days

輸入形狀示意：

{
"symbol": "3035",
"name": "智原",
"position_return_pct": -0.28,
"distance_to_trigger_pct": 4.07,
"volume_ratio": 0.65,
"holding_action": "續抱觀察",
"weak_far_from_trigger": true,
"observation_days": 2
}

預期手機閱讀形狀：

3035 智原｜續抱觀察
弱勢、遠離突破 4.07%、V 0.65x、持倉約 -0.28%
觀察：弱勢觀察第 2 天；若第 3 天仍未重新接近買點 / 突破區，降低優先級

### Fixture B: 缺可信 observation_days

輸入形狀示意：

{
"symbol": "3035",
"name": "智原",
"position_return_pct": -0.28,
"distance_to_trigger_pct": 4.07,
"volume_ratio": 0.65,
"holding_action": "續抱觀察",
"weak_far_from_trigger": true,
"observation_days": null
}

預期手機閱讀形狀：

3035 智原｜續抱觀察
弱勢、遠離突破 4.07%、V 0.65x、持倉約 -0.28%
觀察：觀察天數未確認；若無法重新接近買點 / 突破區，降低優先級

不得出現：

弱勢觀察第 1 天
弱勢觀察第 2 天
已降級
建議賣出

除非可信來源或既有 decision 明確支持。

## 明確禁止事項

- 禁止改 DB schema / RLS / grant / policy / role / index / constraint。
- 禁止 live Telegram delivery。
- 禁止修改買賣、加減碼、停損、停利 decision。
- 禁止用 local cache、runtime dict、agent 記憶、聊天內容推算跨日觀察天數。
- 禁止缺 source 時假造「第 1 天」。
- 禁止把「降低優先級」顯示成已發生事實，除非既有 result 明確表示已降級。
- 禁止順手重構整份報文、策略核心或持倉狀態機。

## 阻塞條件

- 找不到任何持倉報文 formatter / message list 可測入口，且無法建立手機閱讀 probe。
- 既有 holding_signal / result / persistent source 無法判斷觀察天數可信度，且產品要求必須顯示確認天數；此時必須 blocked，不得假造。
- 需要新增 DB 欄位或 production backfill 才能取得 observation days；本輪不得做，需 blocked 並交由 Architect / Owner 確認後續 production source。
- 版本契約不明且現有測試無法確認是否需要升版；不得自行忽略，需在 CHANGELOG.md 標示 blocked 或請 Architect 補充。

## 本輪停止條件

完成範圍只到：弱勢遠離觸發的持倉觀察狀態，在手機閱讀輸出中能顯示可信第 N 天，或在缺 source 時 fail-closed 顯示「觀察天數未確認」，並有兩個 probe 防回退。

以下旁支只記待辦，不納入本輪：

- production source 如何長期補齊 observation start / observation days。
- 其他持倉策略降級規則重設。
- 全部持倉卡文案統一。
- DB schema 或 backfill 設計。
- live Telegram 驗證。
