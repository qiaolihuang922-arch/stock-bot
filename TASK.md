# TASK: 修復 06/01 盤後簡報「今日新倉」判斷與持倉卡矛盾

## 任務狀態

- task_id: risk_patch-afterhours-brief-today-buy-holdings-20260601
- 任務類型: risk_patch
- 狀態: ready_for_tech
- 版本建議: 不升版；不得修改 VERSION
- QA 分級建議: L2
- 本輪主 bug: 盤後第三則簡報只看 watch_items 判斷新倉，漏掉「今日買入後已進入 holding_items」的標的，導致與第一則持倉卡衝突。

## Owner 問題

06/01 盤後報文出現嚴重矛盾：

- 第一則持倉卡顯示建準、光寶科、旺宏今日都有「今日 買 N股」。
- 第三則盤後簡報卻寫「今日無有效新倉」。

疑似根因：_afterhours_brief_lines 只從 watch_items 或未持倉候選判斷今日新倉，未納入已進入 holding_items 的今日買入標的。

## 使用者可見結果

手機閱讀盤後第三則簡報時，不得再讓使用者看到：

- 第一則說今日已買入。
- 第三則又說「今日無有效新倉」。

修復後，若 holding_items 中存在今日買入標的，即使 watch_items 沒有可買標的，第三則也必須顯示「今日已有新倉 / 今日已執行 / 今日交易已完成」等不衝突的人話。

同時仍要保留「新增有效進場：無」這類語義，用來表示盤後沒有額外可繼續買的新標的，避免誤導使用者以為還能追買。

## 非目標

本輪只修復第三則盤後簡報的新倉/交易摘要矛盾，不處理以下旁支：

- 不改策略 decision。
- 不改 DB write path。
- 不改 live Telegram delivery。
- 不改 VERSION。
- 不重新設計整份盤後報文。
- 不調整買賣、加減碼、停損停利策略。
- 不處理光寶科買入解釋。
- 不處理技嘉 RR 0.00。
- 不處理縮量漲停風險。
- 不處理智原 observation_days。
- 不把 watch_items 無可買解讀成今日完全沒有交易。

旁支問題只列 follow-up，不納入本輪驗收。

## 影響模組

預期影響範圍：

- 盤後第三則簡報產生邏輯，尤其 _afterhours_brief_lines 或其直接 helper。
- 盤後 Telegram / message list 的文字輸出。
- 對應測試或手機閱讀 probe。

不得影響：

- 策略評分與 decision 產生。
- 持倉狀態機。
- DB schema / RLS / grant / policy / role / index / constraint。
- DB 寫入、backfill、replay。
- live Telegram 發送。
- 報文版本常量。

## 直接消費者

- Owner 手機閱讀 Telegram 盤後報文。
- 盤後報文 message list 組裝流程。
- QA 手機閱讀 probe / snapshot 測試。
- 後續 Tech/QA 用於重跑驗收的測試命令。

## 輸出契約

### 已存在且不得回退的契約

- 第一則持倉卡若已有今日買入，仍可顯示類似「今日 買 N股」。
- 第三則盤後簡報仍要區分：
- 今日已執行的新倉/交易。
- 盤後新增有效進場機會是否為無。
- watch_items 無可買時，仍可輸出「新增有效進場：無」或等價語義。
- 使用者可見版本不得變更。
- 不得新增 live 發送行為。
- 不得新增或修改 DB schema。
- 不得把今日已買入標的再次包裝成「現在仍可買」的推薦。

若 Tech 發現現有實際契約與上述不一致，必須 blocked 並回報 Architect 補充，不得自行擴大需求。

### 本輪輸出契約

當 holding_items 中存在今日買入標的時，第三則盤後簡報必須納入這些標的進行「今日新倉 / 今日交易」判斷。

輸出形狀需符合手機閱讀：

今日交易：已建立新倉 3 檔（建準、光寶科、旺宏）
新增有效進場：無

或等價人話：

今日已執行：建準、光寶科、旺宏已買入
新增有效進場：無

不得出現下列衝突形狀：

今日無有效新倉

尤其不得在同一份盤後報文中同時出現：

今日 買 N股
今日無有效新倉

若文字使用簡繁混排延續現有報文風格即可，本輪不要求全面文案統一。

## 驗收條件

1. 當 holding_items 中有建準、光寶科、旺宏類的 today buy，且 watch_items 無可買標的時：
- 第三則盤後簡報不得出現「今日無有效新倉」或等價否定今日新倉的句子。
- 第三則必須明確表示今日已有新倉或今日已執行交易。
- 第三則仍可顯示「新增有效進場：無」或等價語義，表示沒有額外可買標的。
2. 當 holding_items 無 today buy，且 watch_items 也無可買標的時：
- 第三則仍可顯示無新增有效進場。
- 不得誤報今日已有新倉。
3. 第一則持倉卡既有「今日 買 N股」顯示不得回退。
4. 不改策略 decision、DB write、live Telegram、VERSION。
5. 補一個手機閱讀 probe 或等價測試，覆蓋「holding_items 有 today buy、watch_items 無可買」的矛盾場景。

## 範例或 Fixture

### Fixture A: 今日買入後已進持倉，watch 無可買

輸入形狀：

holding_items:
- name: 建準
today_action: buy
buy_qty: 1000
- name: 光寶科
today_action: buy
buy_qty: 1000
- name: 旺宏
today_action: buy
buy_qty: 2000
watch_items: []

期望第三則手機閱讀形狀：

今日交易：已建立新倉 3 檔（建準、光寶科、旺宏）
新增有效進場：無

不得包含：

今日無有效新倉

### Fixture B: 今日無買入，watch 無可買

輸入形狀：

holding_items:
- name: 既有持倉A
today_action: hold
watch_items: []

期望第三則手機閱讀形狀：

新增有效進場：無

不得誤報：

今日交易：已建立新倉

## 明確禁止事項

- 禁止改策略 decision。
- 禁止改 DB schema、RLS、grant、policy、role、index、constraint。
- 禁止改 DB write / backfill / replay。
- 禁止 live Telegram delivery。
- 禁止修改 VERSION。
- 禁止把今日已買入標的再次列成可追買推薦。
- 禁止用刪除第三則簡報、刪除第一則今日買入資訊來掩蓋矛盾。
- 禁止順手處理本輪非目標問題。
- 禁止只改文案而不補手機閱讀 probe 或等價測試。

## 阻塞條件

Tech 必須 blocked 的情況：

- 無法辨識 holding_items 中今日買入的可靠欄位或既有 helper。
- 現有資料結構無法區分「今日買入」與「既有持倉」。
- 需要 DB schema 或 DB write 改動才能完成。
- 需要 live Telegram 驗證才能確認結果。
- 找不到盤後第三則簡報的可測入口。
- 實際現有報文契約與本 TASK 的「不得回退契約」衝突。

## 本輪停止條件

驗到以下範圍即可完成本輪：

- _afterhours_brief_lines 或直接簡報入口已納入 holding_items 的 today buy 判斷。
- 手機閱讀 probe 覆蓋 holding_items 有 today buy、watch_items 無可買時第三則不再輸出「今日無有效新倉」。
- 無 today buy、無 watch 可買的情境不誤報今日新倉。
- 確認未改策略 decision、DB write、live Telegram、VERSION。

以下只記 follow-up，不阻塞本輪完成：

- 光寶科買入解釋。
- 技嘉 RR 0.00。
- 縮量漲停風險。
- 智原 observation_days。
- 其他盤後報文排版或長文精簡問題。
