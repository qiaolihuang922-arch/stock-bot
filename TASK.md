# TASK: 2301 今日買入與盤後弱勢盤面誤讀風險修正

## 任務狀態

- task_id: risk_patch_20260601_2301_today_buy_after_close_reading
- 任務類型: risk_patch
- 狀態: ready_for_tech
- 版本建議: 使用者可見報文若有版本字串，需升版或同步更新，不得回退既有版本。
- QA 分級建議: L2；若 Tech 判定涉及策略層 distance/can_buy 計算錯誤並修改策略 decision，升為 L3。

## Owner 問題

06/01 盤後報文中，光寶科 2301 持倉卡顯示「今日 買 50股」，但同一卡片盤面顯示「洗盤回測｜弱勢｜普通｜遠離突破（5.43%）」。使用者會誤讀為策略在 distance 5.43% > can_buy distance > 4、弱勢且遠離突破時仍推薦 BUY。

本輪只處理「今日已買入」與「盤後當前盤面不可繼續買」之間的可見口徑與 fail closed，不重設整體策略。

## 使用者可見結果

手機閱讀報文時，持倉卡與第三則不得讓使用者以為「現在仍可買」。

必須區分三種情況：

1. 今日買入來自盤中早些時候的有效策略觸發，但盤後漂移後當前盤面不再滿足買點：
- 顯示「今日已執行」。
- 同卡或相鄰行用人話說明「盤後轉為新倉風控觀察，當前不代表可繼續買」。
2. 今日買入來自手動單或 ledger，而非策略 BUY：
- 報文必須標明來源或限制，例如「今日買入來源：手動/ledger，非當前策略買點」。
- 不得讓使用者以為策略在弱勢、遠離突破時仍推薦買入。
3. 若來源無法判斷，或 Tech 發現策略層 distance/can_buy 計算路徑錯誤導致錯誤 BUY：
- 來源無法判斷時 fail closed，顯示「來源未確認，不視為當前可買」或等價文案。
- 策略計算錯誤時不得用文案掩蓋；需 blocked 或修策略並補 probe。

## 非目標

- 不改 DB schema、RLS、grant、policy、role、index、constraint。
- 不發 live Telegram。
- 不做 production DB write/backfill。
- 不重設買點策略、停損停利策略或整體 ranking。
- 不清理全量報文格式。
- 不處理其他股票的獨立策略問題，除非同一 fixture 契約直接覆蓋。
- 不把 local cache、runtime dict 或 agent 對話當跨日 source-of-truth。

## 影響模組與直接消費者

- 影響模組:
- 盤後 Telegram 報文產生器。
- 持倉卡今日買入顯示邏輯。
- 第三則/詳情中與今日買入、買點、風控觀察相關的文案。
- 若既有資料契約有來源欄位，讀取今日買入來源的 formatter/helper。
- 若策略計算錯誤，限縮到 distance/can_buy decision path 與對應 probe。
- 直接消費者:
- Owner 在手機 Telegram 閱讀 06/01 盤後報文。
- 後續 QA 用 fixture 驗證「今日買入但當前不可買」的報文口徑。
- 下游任何依賴 message list / card payload / detail block 的報文 renderer。

## 已存在且不得回退的契約

- Summary 只回答決策：今天能不能買、持倉先處理什麼、未持倉哪些只是追蹤。
- 可買、可準備、僅追蹤、淘汰/不可行動必須分開。
- 無可買時不得使用像推薦的文案；只能寫「新倉：無有效進場」或等價不可買表述。
- 分組標題、卡片狀態、漏斗、索引、詳情必須一致。
- 同一持倉在同一份報文只能有一個主行動。
- 今日買入後預設只能新倉風控觀察；若轉弱要賣，必須同行說明跌破警戒、停損或策略失效。
- 同一行動不得在多個區塊重複長句。
- 空區塊、0-count、無新增下單占位預設不顯示。
- 使用者可見報文變更需核對版本字串；不得回退版本。
- production / runner 視為無狀態；跨日執行記憶必須來自 production DB 或 Owner 指定持久 source-of-truth。
- 持久來源缺資料、讀取失敗、欄位不足或可信度不足時，必須 fail closed。

若 Tech 發現上述契約與現有實作不一致，本輪只修與 2301 類今日買入誤讀直接相關的最小範圍；其他差異記待辦。

## 輸出契約

### 持倉卡

對 today_buy_holding == true 且當前盤面不滿足買點的持倉，卡片需同時表達：

- 今日已執行的事實。
- 當前盤面狀態。
- 是否代表當前可繼續買。
- 今日買入來源狀態：strategy_intraday、manual_or_ledger、unknown，或現有等價欄位。
- fail closed 文案。

手機示例形狀：

【光寶科 2301】
今日已買 50股｜新倉風控觀察
盤後盤面：洗盤回測｜弱勢｜普通｜遠離突破（5.43%）
說明：今日買入已執行；盤後已不在買點，現在不代表可繼續買。

手動/ledger 來源示例：

【光寶科 2301】
今日已買 50股｜新倉風控觀察
盤後盤面：洗盤回測｜弱勢｜普通｜遠離突破（5.43%）
說明：今日買入來源為手動/ledger，非當前策略買點；現在不代表可繼續買。

來源未知示例：

【光寶科 2301】
今日已買 50股｜新倉風控觀察
盤後盤面：洗盤回測｜弱勢｜普通｜遠離突破（5.43%）
說明：今日買入來源未確認，且盤後不在買點；不得視為當前可買。

### 第三則 / 詳情

若第三則或詳情區會列出今日買入、買點、續買、加碼或策略理由，必須與持倉卡一致：

- 不得出現「可買」、「買進」、「推薦」、「加碼」等會被讀成當前 BUY 的主行動。
- 應顯示「今日已執行」與「盤後新倉風控觀察」的差異。
- 若來源是手動/ledger 或 unknown，需明確標示，不得歸因為當前策略 BUY。

### Payload / Message List

若內部 message list 或 payload 有 action/status 欄位：

- today bought 不得自動等於 current can_buy。
- 必須能表達：
- executed_today: true
- current_can_buy: false
- post_close_risk_watch: true
- buy_source: strategy_intraday | manual_or_ledger | unknown
- source_confidence 或現有等價 fail closed 判斷
- 若現有 payload 沒有足夠欄位，不得新增 DB schema；可在 formatter 層用既有 read-only source 或 blocked。

## 驗收條件

1. 光寶科類 fixture：today buy holding + 50股 + current distance 5.43% + weak/普通 + distance > 4。
- 報文不得呈現為當前仍可買。
- 持倉卡需顯示今日已執行與盤後新倉風控觀察。
- 第三則/詳情不可與持倉卡矛盾。
2. 盤中策略觸發、盤後漂移 fixture：
- buy source 可判定為策略盤中有效觸發。
- 報文顯示「今日已執行；盤後不代表可繼續買」。
3. 手動/ledger fixture：
- buy source 可判定非策略 BUY。
- 報文標明手動/ledger 或等價來源限制。
- 不得出現策略推薦買入語意。
4. 來源未知 fixture：
- 缺 production source-of-truth、欄位不足或讀取失敗時 fail closed。
- 報文顯示來源未確認，不視為當前可買。
- 不得 fallback 成策略 BUY。
5. 策略計算疑似錯誤 probe：
- 若 distance > 4 且弱勢/普通盤面仍產生 current strategy BUY，Tech 必須 blocked 或修 strategy decision path 並補 probe。
- 不得只改 formatter 文案後宣告完成。

## 範例 / Fixture

最小 fixture 需要覆蓋：

symbol: "2301"
name: "光寶科"
report_date: "2026-06-01"
holding:
shares: 50
bought_today: true
buy_source: "strategy_intraday"
current_market:
pattern: "洗盤回測"
strength: "弱勢"
quality: "普通"
distance_label: "遠離突破"
distance_pct: 5.43
can_buy_distance_threshold_pct: 4.0
expected:
current_can_buy: false
primary_action: "新倉風控觀察"
must_include:
- "今日已執行"
- "盤後"
- "不代表可繼續買"
must_not_include:
- "可買"
- "推薦買入"
- "加碼"

另需同形 fixture：

buy_source: "manual_or_ledger"
expected_must_include:
- "手動"
- "非當前策略買點"

buy_source: "unknown"
expected_must_include:
- "來源未確認"
- "不得視為當前可買"

## 明確禁止事項

- 禁止改 DB schema。
- 禁止 production DB write/backfill。
- 禁止 live Telegram delivery。
- 禁止用 local cache、runtime dict 或聊天紀錄判定今日買入來源。
- 禁止在來源未知時推定為策略 BUY。
- 禁止把「今日已買」顯示成「現在可買」。
- 禁止同一卡片同時出現新倉風控觀察與可買/加碼主行動。
- 禁止只改單一句文案但不補 fixture/probe。
- 禁止擴大成全市場報文重構或策略重設。

## 阻塞條件

Tech 必須 blocked 的情況：

- 找不到可用的 read-only production source-of-truth 或既有資料欄位來判定今日買入來源，且無法在 formatter 層安全 fail closed。
- 現有 message list/payload 無法表達 executed_today 與 current_can_buy 的差異，且需要 DB schema 才能補足。
- 發現策略層在 distance > 4、弱勢/普通、遠離突破時仍產生 current BUY，但本輪無法安全修正與驗證。
- 測試環境無法跑 fixture/probe。
- 任何修正需要 live Telegram 或 production write。

## 本輪停止條件

完成條件：

- 光寶科類 fixture 與三種來源情境均可重跑驗證。
- 手機閱讀路徑中，持倉卡與第三則/詳情不再把今日已買誤讀成當前可買。
- 若策略計算無錯，Tech 明確提供 read-only/source 判斷或 fail closed 證據。
- 若策略計算有錯，完成條件改為已修策略並補 probe，或明確 blocked。

不納入本輪、只記待辦：

- 其他股票是否也有同型資料來源缺口。
- 全量報文去重與版面重構。
- 買點策略門檻重設。
- DB schema 補來源欄位。
- live Telegram 補發或撤回。
