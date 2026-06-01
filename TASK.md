# TASK: Telegram 卡片 Source 人話化與持倉 RR 顯示契約修正

## 任務狀態

- task_id: telegram_card_source_humanize_v20_4_16
- 任務類型: normal_patch
- 狀態: QA 通過，待 git 收口
- 版本建議: 升版至 v20.4.16
- QA 分級建議: L2
- 本輪主 bug: 第一則持倉卡、第二則未持倉卡內 Source 行為工程欄位直出，且持倉卡出現新倉 RR 數字造成語意衝突。
- 本輪停止條件: 完整三則 Telegram sample 中，第一則與第二則卡片的 Source/資料行已手機可讀、沒有 raw field/status dump、持倉卡不再顯示新倉 RR 數字，未持倉缺資料時明確 fail-closed。其他報文文案優化、策略排序、分數公式、
資料補齊流程只記待辦，不納入本輪。

## Owner 問題

Owner 指出 Telegram 第一則持倉卡與第二則未持倉卡的 Source 行不可讀，例如：

- Source：position available｜price available｜risk derived｜RR derived
- Source：price available｜OHLCV available｜RR derived｜score derived｜volume derived

這些是工程欄位直出，手機閱讀時沒有決策價值。Owner 要求改成手機可讀的「資料」或「依據」短句，說明哪些資料已確認、哪些是推算、缺資料時 fail-closed。

同時 Owner 指出持倉卡有顯示衝突：持倉卡理應「持倉不看新倉 RR」，卻出現 RR 2.33 之類數字，容易被誤讀成持倉仍以新倉 RR 判斷。

## 使用者可見結果

Telegram 報文中：

- 第一則持倉卡不再出現 raw position available｜price available｜risk derived｜RR derived。
- 第二則未持倉卡不再出現 raw price available｜OHLCV available｜RR derived｜score derived｜volume derived。
- Source 行改名或改寫為手機可讀短句，例如：資料：持倉與現價已確認；風控由持倉成本/停損推算。
- 未持倉缺必要資料時，卡片明確顯示不可行動，例如：資料：缺 OHLCV，停止新倉判斷，不得用像推薦的語氣。
- 持倉卡不得顯示新倉 RR 數字；若保留 RR 欄位，必須明確寫成 新倉 RR：持倉不適用 或等價不可誤讀文案。

## 非目標

- 不改策略 decision、買賣 / 加減碼 / 停損停利判斷。
- 不改分數公式、RR 計算公式、volume 判斷公式。
- 不改 DB schema、RLS、grant、policy、role、index、constraint。
- 不改 DB write path，不新增 production backfill。
- 不 live Telegram delivery。
- 不重排三則 Telegram 報文的主流程與卡片分組。
- 不做全量文案重寫或報文大改版。

## 影響模組

Tech 需定位並僅修改 Telegram 報文 formatter / card renderer / sample fixture / 對應測試。

預期影響範圍：

- Telegram 第一則持倉卡的 Source/資料行 formatter。
- Telegram 第二則未持倉卡的 Source/資料行 formatter。
- 持倉卡 RR 顯示條件或文案契約。
- Telegram sample/golden output 測試。
- 版本字串或報文 header 常量升至 v20.4.16。

不得影響：

- strategy decision function return。
- DB payload / write contract。
- live delivery command。
- screening universe / ranking / scoring logic。
- 持倉狀態機。

## 直接消費者

- Owner 手機閱讀 Telegram 三則報文。
- Telegram message renderer / formatter 的既有測試或 snapshot。
- 任何依賴 Telegram sample/golden output 的 QA 檢查流程。

## 已存在且不得回退的契約

- Telegram 報文仍維持既有三則 sample 結構；本輪只修第一則持倉卡與第二則未持倉卡的資料來源可讀性與持倉 RR 衝突。
- Summary 仍只回答決策：今天能不能買、持倉先處理什麼、未持倉哪些只是追蹤、哪些不可行動。
- 可買、可準備、僅追蹤、淘汰 / 不可行動不得混在同一語意。
- 無可買時不得使用像推薦的文案。
- 同一持倉在同一份報文只能有一個主行動。
- 今日買入後預設只能新倉風控觀察；若轉弱要賣，必須同行說明跌破警戒、停損或策略失效。
- 使用者可見版本不得回退；本輪應升至 v20.4.16。
- 若 Tech 無法確認目前三則報文結構、版本常量或 Source 行生成位置，必須 blocked，要求 Architect 補充，不得自行重構報文架構。

## 輸出契約

### 第一則：持倉卡資料行

Raw field/status dump 禁止輸出：

Source：position available｜price available｜risk derived｜RR derived

應輸出手機可讀短句，建議欄名為 資料 或 依據：

資料：持倉與現價已確認；風控由持倉成本/停損推算

若缺持倉或現價必要資料，必須 fail-closed：

資料：缺持倉或現價，停止持倉建議

持倉卡不得出現新倉 RR 數字：

新倉 RR：持倉不適用

或直接不顯示新倉 RR 欄位。

### 第二則：未持倉卡資料行

Raw field/status dump 禁止輸出：

Source：price available｜OHLCV available｜RR derived｜score derived｜volume derived

應輸出手機可讀短句：

資料：現價與 OHLCV 已確認；RR/分數/量能為模型推算

若缺必要資料，必須 fail-closed 並不可行動：

資料：缺 OHLCV，停止新倉判斷
狀態：不可行動

若只有推算資料，不得寫成「已確認」。

### 欄位順序

- 保留既有卡片主要欄位順序。
- Source/資料行只替換原 Source 行位置，不新增長段落。
- 手機單行優先；必要時最多兩個短分句。
- 不輸出英文 raw key：available、derived、OHLCV available、score derived、volume derived、RR derived。

## 驗收條件

1. 完整三則 Telegram sample 產出後，第一則持倉卡與第二則未持倉卡均無 raw Source/status dump。
2. 第一則持倉卡不顯示新倉 RR 數字，例如不得出現 RR 2.33 這類未標明持倉不適用的數字。
3. 第二則未持倉卡在資料完整時，以人話說明「已確認」與「推算」來源。
4. 第二則未持倉卡在缺 price 或 OHLCV 任一必要資料時 fail-closed，顯示不可行動或停止新倉判斷，不得給可買/準備買語氣。
5. 報文版本/header 顯示 v20.4.16，且沒有回退既有三則報文結構。
6. Tech 自檢需包含至少一個 fixture 或 golden sample 更新；QA 需另外用完整三則 Telegram sample 做手機閱讀路徑檢查。

## 範例或 Fixture

### Fixture A：持倉卡資料完整

輸入條件：

- position 存在
- price 存在
- risk 由持倉資料推算
- 原本可能有 RR derived

期望輸出形狀：

[第一則 / 持倉]
...既有持倉主行動...
資料：持倉與現價已確認；風控由持倉成本/停損推算
新倉 RR：持倉不適用

不得出現：

Source：position available｜price available｜risk derived｜RR derived
RR 2.33

### Fixture B：未持倉卡資料完整

輸入條件：

- price 存在
- OHLCV 存在
- RR / score / volume 由模型推算

期望輸出形狀：

[第二則 / 未持倉]
...既有候選狀態...
資料：現價與 OHLCV 已確認；RR/分數/量能為模型推算

不得出現：

Source：price available｜OHLCV available｜RR derived｜score derived｜volume derived

### Fixture C：未持倉缺 OHLCV

輸入條件：

- price 存在
- OHLCV 缺失

期望輸出形狀：

[第二則 / 未持倉]
狀態：不可行動
資料：缺 OHLCV，停止新倉判斷

不得出現可買、推薦、準備進場等語氣。

## QA 要求

QA 分級：L2

QA 必須檢查：

- 完整三則 Telegram sample，而不是只看單一卡片 formatter。
- 手機閱讀路徑：第一則持倉卡、第二則未持倉卡在窄寬閱讀時 Source/資料行可理解且不過長。
- 第一則持倉卡沒有新倉 RR 數字衝突。
- 第二則未持倉卡資料完整時，人話區分已確認資料與推算結果。
- 第二則未持倉卡缺資料時仍 fail-closed。
- 版本顯示為 v20.4.16。
- QA 必須補一個 Tech 未覆蓋的反證案例：例如缺 price 或缺 OHLCV 任一項時，不得仍輸出可買語氣。

## 明確禁止事項

- 禁止修改策略 decision。
- 禁止修改 DB schema / RLS / grant / policy / role / index / constraint。
- 禁止新增或修改 production DB write。
- 禁止 live Telegram delivery。
- 禁止把 raw engineering field/status 直接換成另一組 raw key。
- 禁止把持倉卡新倉 RR 數字改名後繼續顯示為可判斷指標。
- 禁止擴大成全報文重構、策略重設或全量清理。
- 禁止用 local cache、runtime dict 或 agent 對話當跨日持倉 source-of-truth。

## 阻塞條件

- 無法定位 Telegram 三則 sample 或卡片 renderer。
- 無法確認目前版本常量 / header 位置。
- 缺少可產出完整三則 Telegram sample 的 fixture 或命令。
- 修改 Source/資料行會牽動 strategy decision、DB schema/write 或 live delivery。
- 無法在缺 price / 缺 OHLCV 情境維持 fail-closed。
- 現有契約與本 TASK 衝突時，Tech 必須 blocked 並回報差異，不得自行擴大範圍。
