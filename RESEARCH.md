# RESEARCH.md

本文件由 Architect 維護，用來承接研究型任務。PM、Tech、QA 可在各自區塊填寫摘要；Architect 最後只吸收結論，不接收完整聊天紀錄。

## Question

- 任務類型：產品研究
- 任務日期：2026-05-26
- 研究對象：v19.4 顯著功能升級方向
- 背景：v19.3.4 報文解釋力已接近穩定。Owner 認為 v19.4 不應只是小幅 formatter / label 更新，需要有明顯功能升級感。
- 核心問題：
  - v19.4 是否需要強化策略門檻，而不只是 formatter。
  - 買入訊號稀少是否應改善，如何避免變成追高。
  - 持倉處理是否需要更完整的升級 / 降級 / 隔日追蹤規則。
  - 回測資訊是否應從顯示解釋進一步進入決策權重。
  - v19.3.4 是否還有必須先補的顯示殘留問題。
  - v19.4 應新增哪些明顯可見能力，讓使用者感覺不是又一個小版本。

## Evidence

- v19.3.4 已能顯示：
  - R3 不新增原因。
  - 回測參考度與判讀。
  - 今日新倉浮虧風控語氣。
  - 減碼 / 停利 / 停損原因與下一步。
- Owner 認為 v19.3.4 已接近穩定。
- 最新貼文仍出現一個疑似殘留顯示風險：
  - 旺宏價格行疑似少全形右括號：`價格：159.75（+4.75%`
  - 需判斷是複製截斷、Telegram split 問題，還是 formatter 未完全覆蓋。

## PM Findings

### PM 結論

v19.4 應定位為「交易閉環升級」，不是 formatter 小修，也不是單純放寬策略。v19.3.4 已經把報文讀得懂；v19.4 要讓使用者每天看完報文後知道「今天做什麼、明天追什麼、持倉若沒修復怎麼辦」。

v19.4 最小但顯著的功能組合應包含三件事：

1. `隔日追蹤`：把今天不能買但值得明天重看的標的獨立出來。
2. `持倉處理優先級`：把持倉從普通清單升級為待處理隊列。
3. `明日觸發條件`：每個追蹤標的和風控持倉都要有明確的次日檢查條件。

這三件事會讓版本從「更會解釋」升級為「能管理明天的交易流程」。

### v19.4 升級定位

v19.4 不應直接放寬 RR / 過熱 / 加碼 / 減碼門檻。直接放寬會讓系統從「不追高」變成「找理由追高」，這不符合目前產品方向。

v19.4 應新增一層「交易流程狀態」，讓策略不只輸出買或不買，而是輸出：

- 今天是否能交易。
- 如果不能，明天是否要追蹤。
- 追蹤的觸發條件是什麼。
- 持倉是否要升級風控。
- 今天的狀態明天如何驗證。

### v19.4 必做能力

#### 1. 隔日追蹤

`隔日追蹤` 是 v19.4 主功能，必做。

目的：

- 解決「今天都不買，使用者不知道明天看什麼」。
- 將 `等待冷卻 / 等RR修復 / 等量能 / 隔日確認` 從未持倉詳情中拉出來。
- 讓報文從當日結論變成次日交易計畫。

建議區塊：

```text
🕒 隔日追蹤
1. 光寶科｜等冷卻｜明日觸發：回測不破且過熱降溫
2. 建準｜等RR修復｜明日觸發：價格回落或目標空間打開
3. 仁寶｜隔日確認｜明日觸發：站回今日高點且量能不失控
```

追蹤分類：

- `等冷卻`
- `等回測`
- `等RR修復`
- `等量能`
- `隔日確認`

#### 2. 待確認候選

`待確認候選` 應從未持倉清單中獨立出來，必做。

目的：

- 避免所有非買點標的都停留在 `不買 / 觀察`。
- 讓使用者知道哪些標的是「不買但值得排隊」。

建議摘要：

```text
待確認候選：
【等回測 2】光寶科、聯電
【等RR修復 2】建準、仁寶
【等量能 1】技嘉
```

弱勢淘汰仍保留，但不進待確認候選。

#### 3. 持倉處理優先級

`持倉處理優先級` 應新增為摘要區塊，必做。

目的：

- 解決持倉多時，使用者不知道先看哪一檔。
- 將風控、停利、減碼、新倉浮虧放在普通續抱前面。

建議區塊：

```text
📌 持倉處理優先級
1. 智原｜新倉風控｜明日未修復降級
2. 英業達｜核心風控觀察｜守警戒價
3. 緯創｜洗盤續抱｜跌破警戒升級風控
```

排序原則：

```text
停損 / 清倉
減碼 / 停利
新倉風控
核心風控觀察
減碼後觀察
洗盤警戒
洗盤續抱
核心續抱
普通續抱
```

#### 4. 明日觸發條件

`明日觸發條件` 應成為每個追蹤標的與風控持倉的必備文案，必做。

範例：

```text
明日觸發：回測不破且量能回升
明日觸發：RR 修復至達標，不追高
明日觸發：站回突破區，否則降級
明日觸發：跌破警戒價，升級風控
```

這是 v19.4 可感知升級的核心。沒有明日觸發條件，隔日追蹤只是另一個觀察清單。

#### 5. 今日狀態 -> 明日檢查閉環

v19.4 必須加入「今日狀態 -> 明日檢查」閉環。

產品規則：

- 今日 `等冷卻`：明日檢查是否降溫與回測不破。
- 今日 `等RR修復`：明日檢查價格是否回落或目標空間是否打開。
- 今日 `新倉風控觀察`：明日檢查是否站回買點 / 成本 / 突破區。
- 今日 `減碼後觀察`：明日檢查是否修復，否則降低優先級。
- 今日 `核心風控觀察`：明日檢查是否守警戒價。

### 回測資訊如何進入 v19.4

回測資訊應進入 `追蹤優先級`，不直接改交易 decision。

產品規則：

```text
參考度低：只顯示，不加權
參考度中：可影響隔日追蹤排序
參考度高：可影響隔日追蹤排序與候選順位
相對略優：追蹤順位上調
無明顯優勢：不調整
偏弱：追蹤順位下調
```

禁止：

- 回測略優不能直接產生 `可買`。
- 回測偏弱不能覆蓋既有停損 / 風控。
- 回測不能取消 RR、過熱、漲停不追。

### 買入訊號稀少的產品解法

v19.4 不應靠放寬買入條件解決。更好的產品解法是增加買入前序狀態：

```text
可準備：條件接近，明日可重看
等回測：強勢但過熱，不追高
等RR修復：強勢但風報不夠
等量能：結構可看但量未跟上
隔日確認：今日不成立，明天確認
```

使用者感知上的改善：

- v19.3.4：今天不能買。
- v19.4：今天不能買，但明天看這幾檔，符合這些條件才動。

### 持倉管理強化方向

v19.4 必須讓持倉有生命週期。

新增或強化狀態：

- `新倉風控觀察`
- `隔日未修復`
- `減碼後觀察`
- `減碼後修復`
- `核心風控觀察`
- `停利後核心倉`

產品語意：

- 新倉浮虧不是普通續抱，要進風控觀察。
- 減碼後不是結束，要追蹤是否修復。
- 核心倉高浮盈回落不是普通續抱，要有守利潤邏輯。

### 殘留顯示風險

旺宏價格行疑似少右括號：`價格：159.75（+4.75%`

PM 判斷：

- 這是 v19.3.x 顯示穩定性風險，不應混入 v19.4 策略升級。
- Architect 應先讓 Tech / QA 判斷是否為複製截斷、Telegram split 或 formatter 漏測。
- 若不能排除，應先開 v19.3.5 顯示穩定性小修。

### v19.4 必做 / 延後

v19.4 必做：

- `隔日追蹤`
- `待確認候選`
- `持倉處理優先級`
- `明日觸發條件`
- `今日狀態 -> 明日檢查`
- 回測影響追蹤排序

留到 v19.5 / v20：

- 直接放寬 RR 門檻。
- 動態過熱門檻。
- 自動跨多日追蹤資料庫。
- 多日任務狀態持久化。
- 擴大股票池。
- 讓回測直接改交易 decision。

### 可直接放入 TASK.md 的產品文案

```text
# TASK: v19.4 交易閉環升級

## 需求目標

v19.4 要從「當日報文」升級為「當日決策 + 隔日追蹤」。

使用者看完報文後，必須知道：
- 今天不能買的股票，明天哪些要重看。
- 每個待確認標的的觸發條件是什麼。
- 持倉中哪些需要優先處理。
- 今日新倉、減碼後、核心倉回落，明天如何檢查。

## 新增區塊

1. 持倉處理優先級
2. 待確認候選
3. 隔日追蹤
4. 明日觸發條件

## 報文範例

【05/26 盤中｜v19.4】
📊 市場：進攻偏熱｜R3
🎯 今日重點：持倉優先，新倉只進待確認
🧭 原因：強勢股多過熱，RR不足，不追高

📌 持倉處理優先級
1. 智原｜新倉風控｜明日未修復降級
2. 英業達｜核心風控觀察｜守警戒價
3. 緯創｜洗盤續抱｜跌破警戒升級風控

🕒 隔日追蹤
1. 光寶科｜等冷卻｜明日觸發：回測不破且過熱降溫
2. 建準｜等RR修復｜明日觸發：RR修復，不追價
3. 仁寶｜隔日確認｜明日觸發：站回突破區且量能不失控

待確認候選：
【等回測 1】光寶科
【等RR修復 2】建準、仁寶
【弱勢淘汰 1】旺宏
```

### 可直接放入 TASK.md 的驗收標準

```text
v19.4 驗收標準：

1. 報文新增「持倉處理優先級」區塊。
2. 報文新增「隔日追蹤」區塊。
3. 報文新增「待確認候選」分組。
4. 每個隔日追蹤標的都有「明日觸發」文案。
5. R3 市場下，強勢但過熱標的不進可買，進等冷卻 / 等回測 / 隔日追蹤。
6. RR 不足但結構強的標的不進可買，進等RR修復。
7. 量能不足但非弱勢的標的不進弱勢淘汰，進等量能。
8. 弱勢 / 遠離觸發標的不進隔日追蹤優先清單。
9. 今日新倉浮虧進新倉風控觀察，並有明日檢查條件。
10. 減碼後持倉進減碼後觀察，並有修復 / 未修復邏輯文案。
11. 核心倉高浮盈回落顯示核心風控觀察或等效語意。
12. 回測參考度可影響隔日追蹤排序，但不得直接產生 BUY。
13. 隔日追蹤不得覆蓋 RR、過熱、漲停不追等硬風控。
14. v19.4 不擴大股票池。
15. v19.4 不改 DB schema，除非 Tech 研究證明必要並由 Architect 另開任務。
```

### PM 建議下一步

- 先讓 Tech 做 v19.4 技術研究，確認現有資料是否足以支援：
  - 當日隔日追蹤清單。
  - 前一交易日追蹤回看。
  - 新倉隔日狀態。
  - 減碼後修復狀態。
  - 回測排序權重。
- 若 Tech 判斷不需 DB schema 變更，v19.4 可進入 TASK。
- 若 Tech 判斷需要持久化追蹤狀態，Architect 應拆分成 v19.4 MVP 與後續版本。

## Tech Findings

- Tech 結論：v19.4 可以先做「策略狀態層 + 隔日追蹤」的最小版本，不需要先放寬 RR / 過熱 / 加碼門檻，也不需要先改 DB schema。現有 `analysis` 結果欄位、`daily_signal_snapshot`、`daily_price`、`positions`、`position_events` 已足以支撐第一階段研究方向；真正風險在於狀態定義要保持為輔助語意，不能覆蓋硬風控。

### 1. 現有資料結構支援度

- 未持倉策略狀態層可由現有欄位推導：
  - `decision / action / action_type`
  - `decision_type`
  - `trade_state`
  - `heat_state`
  - `structure_phase`
  - `price_behavior`
  - `market_grade`
  - `volume_state`
  - `volume_price_state`
  - `rr`
  - `breakout_distance`
  - `entry_quality / confidence_score`
- 目前 formatter 已有 `classify_watchlist_group()`，可作為 v19.4 的雛形；但 v19.4 不應只改 formatter，建議新增一個明確的 derived state，例如：
  - `ENTRY_READY`
  - `WAIT_PULLBACK`
  - `WAIT_RR_REPAIR`
  - `WAIT_VOLUME`
  - `NEXT_DAY_CONFIRM`
  - `WEAK_REJECT`
- 這個 derived state 可以先在顯示 / condition layer 產生，不改 `services/analysis.py` 的買賣門檻；若後續要真正進策略權重，再移入 analysis 或 condition engine。

### 2. 隔日追蹤清單可行性

- 當日報文的「隔日追蹤」不需要新增 DB：
  - 可直接從當天未持倉結果中挑選 `可準備 / 等回測 / 等RR修復 / 等量能 / 隔日確認`。
  - 不進 `可買`，只作為隔日重點清單與排序。
- 隔日報文要知道「昨天列入追蹤的標的」有兩種做法：
  - 低侵入做法：從 `daily_signal_snapshot` 讀取前一個交易日的 12 檔 snapshot，再依相同 derived state 重新計算昨天的追蹤名單。
  - 明確狀態做法：新增 tracking 表記錄昨日追蹤狀態，但 v19.4 第一階段不建議先改 schema。
- 技術建議：
  - v19.4 MVP 使用 `daily_signal_snapshot` + derived state 即可。
  - 只有當 Owner 需要人工標記、跨多日追蹤、追蹤完成/失效狀態時，才考慮新增 DB table。

### 3. 新倉隔日狀態可行性

- 現有 `position_events` 已記錄：
  - `event_date`
  - `action_label`
  - `shares_delta`
  - `shares_before`
  - `shares_after`
  - `avg_price_before / avg_price_after`
- 目前 Python 端只讀 `load_today_position_events()`，所以只能判斷「今日買 / 今日賣」。
- v19.4 若要判斷「新倉隔日未修復」，需要新增一個 read-only loader，例如讀最近 2-5 個交易日的 `position_events`：
  - 不需要改 schema。
  - 不需要改 Edge Function 寫入格式。
  - 需要補測試，避免沒有歷史事件時誤判。
- 注意風險：
  - 如果持倉是人工 `設定` 建立，而不是 `買入` 建立，系統只能知道設定日，不能精準知道真實建倉日。
  - 因此「新倉隔日」應以事件資料可得時啟用，缺資料時回退到一般持倉狀態，不應硬判。

### 4. 減碼後修復追蹤可行性

- `position_events` 已能辨識減碼 / 賣出 / 停利 / 清倉事件，因為 Edge Function 會寫入 `action_label`、`shares_delta`、`event_type`。
- v19.4 可在不改 DB 的情況下做：
  - 今日減碼後：顯示 `減碼後觀察`。
  - 隔日若重新站回突破區 / 盤面修復：回到 `底倉續抱` 或 `核心續抱`。
  - 隔日未修復：降低優先級或進 `風控觀察`。
- 技術上需要定義「修復」條件，但建議第一版只用現有欄位：
  - `structure_phase`
  - `price_behavior`
  - `trend`
  - `breakout_distance`
  - `market_regime`
  - `volume_state / volume_price_state`
- 不建議第一版直接新增再次減碼策略，避免 v19.4 scope 膨脹。

### 5. 核心倉風控升級可行性

- `services/analysis.py` 已有高浮盈回落分支：
  - `pnl >= 15`
  - `heat_state in HOT / EXTREME` 或 `trade_state = EXTENDED`
  - `price_behavior in VOLUME_DROP / LOW_VOLUME_PULLBACK / NORMAL`
  - 跌破警戒價時輸出 `RISK_WATCH`，否則 `HOLD_CORE`
- 這代表核心倉風控升級已有基礎，不需要重新發明。
- v19.4 可做的是把 lifecycle 語意補完整：
  - `核心續抱`
  - `核心風控觀察`
  - `停利後核心倉`
  - `減碼後觀察`
- 技術建議：
  - 第一階段先建立「持倉生命週期顯示/derived state」。
  - 第二階段再評估是否調整 analysis 的分支門檻。

### 6. 回測判讀進排序 / 追蹤優先級可行性

- 目前 `load_backtest_context()` 已查詢近 90 日 `daily_signal_snapshot` 與 `daily_price`，並計算：
  - `sample`
  - `win_rate`
  - `avg_return`
  - `verdict`
  - `action`
- v19.4 可把這些資料用於「追蹤優先級」：
  - `參考度低`：只顯示，不加權。
  - `參考度中`：可調整隔日追蹤排序。
  - `參考度高`：可調整隔日追蹤排序與摘要順位。
  - `相對偏弱`：降低追蹤優先級。
  - `相對略優`：提高追蹤優先級，但不產生 BUY。
- 技術上不建議讓回測直接改 `decision` 或覆蓋 RR / 過熱 / 停損：
  - 可新增 `tracking_priority`。
  - 不改 `is_tradeable`。
  - 不改 `is_best_candidate`。
  - 不改 strongest candidate 的硬規則。

### 7. 買入訊號稀少的技術處理建議

- 稀少買入不應先靠放寬門檻處理。
- 目前未持倉已有 `可買 / 禁止追高 / 等待冷卻 / 可觀察但不可買 / 弱勢淘汰`，v19.4 可細分 `可觀察但不可買`：
  - `等RR修復`
  - `等量能`
  - `隔日確認`
  - `可準備`
- 這可以改善 Owner 對「全部都是不買」的感受，同時維持策略安全性。
- 實作上應產出明確欄位或 helper，不建議只在字串層拼文案，否則 QA 很難驗證。

### 8. 旺宏價格行右括號風險

- 目前 formatter 的 `price_change_line(price, change)` 固定輸出：
  - `價格：{price}（{change}）`
- v19.3.4 的預設持倉 / 未持倉卡片都使用同一個 `price_change_line()`。
- `formatTelegramMessages()` 預設三段訊息目前不走 `split_message()`，只有完整詳情備份會 split。
- 初步判斷：
  - 單一價格行少右括號不太像 `price_change_line()` 本身漏括號。
  - 更可能是 Owner 複製截斷、Telegram 顯示截圖截斷，或舊版報文殘留。
- 仍建議先開一個 v19.3.5 顯示穩定性 QA 小項：
  - 對預設三段 messages 驗證所有 `價格：` 行都符合 `價格：...（...%）`。
  - 驗證預設每段訊息長度低於 Telegram 4096 字元，或讓預設三段也走 split guard。
- 若 QA 證明預設訊息可能超過 Telegram 限制，應先修 v19.3.5，不要混入 v19.4 策略升級。

### 9. v19.4 技術拆分建議

- 建議拆成兩個任務，而不是一次大改：
  - `v19.3.5`：顯示穩定性小修，只驗價格行括號與 Telegram message length / split guard。
  - `v19.4.0`：策略狀態層與隔日追蹤 MVP。
- v19.4.0 最小技術範圍：
  - 新增 derived strategy state helper。
  - 新增隔日追蹤清單 formatter。
  - 從 `daily_signal_snapshot` 讀前一交易日追蹤狀態。
  - 從 `position_events` 讀最近事件，支援新倉隔日 / 減碼後觀察。
  - 讓 backtest context 只影響 tracking priority，不改 BUY / STOP / RR 硬規則。
- 不建議第一版改動：
  - RR 門檻。
  - 過熱 / 漲停不追規則。
  - 加碼 / 減碼 / 停利 / 停損策略門檻。
  - DB schema。
  - 股票池。

### 10. 建議 QA 先設計的最小驗證矩陣

- R3 強勢但過熱：
  - 不進 `可買`。
  - 進 `等待冷卻 / 等回測 / 隔日追蹤`。
- RR 接近但不足：
  - 不進 `可買`。
  - 進 `等RR修復`。
- 量能不足但非弱勢：
  - 不進 `弱勢淘汰`。
  - 進 `等量能`。
- 今日新倉浮虧：
  - 當日顯示 `新倉風控觀察 / 洗盤警戒`。
  - 隔日未修復降級。
- 減碼後：
  - 當日顯示 `減碼後觀察`。
  - 隔日修復 / 未修復分支可驗證。
- 回測加權：
  - 只能改追蹤排序。
  - 不得產生 BUY。
  - 不得改 strongest candidate 硬規則。

### 11. Tech 結論

- v19.4 可以進入 PM 定義 TASK，但應限定為「狀態層 + 隔日追蹤」，不是放寬策略。
- 現有資料結構足以支援 MVP；暫不需要 DB schema 變更。
- 需要新增 read-only 歷史事件讀取與前一交易日 snapshot 讀取。
- 回測可進 tracking priority，不應直接進交易 decision。
- 旺宏右括號問題建議先由 QA 以 v19.3.5 顯示穩定性驗證處理；若測出預設訊息長度或 split 風險，再先修 v19.3.5。

## QA Findings

- QA 結論：v19.4 最小驗證應聚焦「策略狀態層 + 隔日追蹤 MVP」，不驗證放寬策略門檻，不要求 DB schema 變更，不跑全局測試。驗證目標是確認新狀態能提供更清楚的準備 / 等待 / 追蹤語意，同時不破壞現有硬風控。

### v19.4 最小驗證矩陣

| 編號 | 場景 | 最小輸入條件 | 預期輸出 | 必測重點 | 建議測試層級 |
| --- | --- | --- | --- | --- | --- |
| V19.4-QA-01 | R3 強勢但過熱 | `market=R3`、未持倉、結構強、`heat_state=HOT/EXTREME` 或漲停延伸 | 不進 `可買`；進 `等待冷卻 / 等回測 / 隔日追蹤` | 不追高原則維持；不可產生 BUY | formatter / derived state unit |
| V19.4-QA-02 | RR 接近但不足 | 未持倉、結構強、非弱勢、`0 < rr < 1` 或接近門檻 | 不進 `可買`；顯示 `等RR修復`；可進隔日追蹤 | RR 硬門檻不放寬；語意從不買升級為可追蹤 | formatter / derived state unit |
| V19.4-QA-03 | 量能不足但非弱勢 | 未持倉、結構可觀察、`volume_state=WEAK`、`market_grade != D` | 不進 `弱勢淘汰`；顯示 `等量能` | 量能不足與弱勢淘汰不可混淆 | formatter / derived state unit |
| V19.4-QA-04 | 隔日確認 | 未持倉、`price_behavior=LIMIT_REBOUND/WEAK_REBOUND` 或訊號需隔日確認 | 不進 `可買`；顯示 `隔日確認`；進隔日追蹤 | 反彈 / 漲停反彈不直接買 | formatter / derived state unit |
| V19.4-QA-05 | 弱勢淘汰 | 未持倉、`market_grade=D` 或結構弱、遠離觸發 | 顯示 `弱勢淘汰`；不進隔日追蹤優先清單 | 弱勢標的不佔用追蹤順位 | formatter / derived state unit |
| V19.4-QA-06 | 合格 BUY 仍可買 | 未持倉、`decision=BUY`、`action>0`、`rr>=1`、非過熱、非弱勢、無 blocker | 顯示 `可買`；不進等待 / 追蹤分組 | 新狀態層不得壓掉真正買點 | formatter regression |
| V19.4-QA-07 | 今日新倉浮虧 | 今日有買入事件、持倉、`pnl < 0` | 當日顯示 `新倉風控觀察 / 洗盤警戒` | 不回退普通續抱；不直接停損除非策略觸發 | formatter / position event unit |
| V19.4-QA-08 | 新倉隔日未修復 | 前一交易日買入，隔日仍未修復或轉弱 | 顯示 `隔日未修復 / 風控觀察`；下一步提示降級 | 需依近 2-5 日 position events；缺事件時安全回退 | position event unit |
| V19.4-QA-09 | 減碼後觀察 | 今日或前一日有減碼 / 賣出事件，仍有底倉 | 顯示 `減碼後觀察`；保留底倉語意 | 不把減碼後狀態誤判成新買點或普通續抱 | formatter / position event unit |
| V19.4-QA-10 | 減碼後修復 | 減碼後隔日重新站回突破區或盤面修復 | 可回到 `底倉續抱 / 核心續抱` | 修復條件只影響顯示與追蹤，不自動加碼 | formatter / derived state unit |
| V19.4-QA-11 | 減碼後未修復 | 減碼後隔日未站回、結構轉弱 | 顯示 `風控觀察 / 降低優先級` | 不直接新增賣出策略，除非 analysis 已輸出 | formatter / derived state unit |
| V19.4-QA-12 | 核心倉高浮盈回落 | 持倉高浮盈、量縮或過熱後回落，未觸發停損 | 顯示 `核心風控觀察` 或 `核心續抱` 附下一步 | 不把核心倉普通化為續抱；不憑空停利 | formatter / holding lifecycle unit |
| V19.4-QA-13 | 停利後核心倉 | 已有停利事件，仍保留持倉 | 顯示 `停利後核心倉` 或等效語意 | 不重複提示同日連續停利；保留核心倉語意 | formatter / position event unit |
| V19.4-QA-14 | 回測參考度低 | `sample < 10`、相對略優 | 只顯示，不提高交易 decision；可低權重追蹤 | 參考度低不可推動 BUY | backtest context unit |
| V19.4-QA-15 | 回測參考度中/高且略優 | `sample >= 10`、相對 `>= +1.0%` | 可提高追蹤排序 / priority | 不改 `is_tradeable`、不改 strongest hard rule | tracking priority unit |
| V19.4-QA-16 | 回測偏弱 | 相對 `<= -0.5%` | 降低追蹤優先級 | 不覆蓋停損 / 風控；不把弱勢改可買 | tracking priority unit |
| V19.4-QA-17 | 前一交易日追蹤名單 | 使用前一交易日 `daily_signal_snapshot` 推導追蹤清單 | 能產生昨日追蹤 / 今日修復對照 | 不新增 DB schema；缺 snapshot 時安全顯示無追蹤 | snapshot read unit |
| V19.4-QA-18 | 缺 position events | 持倉存在，但沒有近 2-5 日事件 | 回退一般持倉狀態，不硬判新倉 / 減碼後 | 缺資料不可誤判 | position event unit |

### 最小測試分層

- L1 formatter / derived state：
  - 未持倉狀態層：`可買 / 可準備 / 等回測 / 等RR修復 / 等量能 / 隔日確認 / 弱勢淘汰`。
  - 持倉 lifecycle：`新倉風控觀察 / 隔日未修復 / 減碼後觀察 / 核心風控觀察 / 停利後核心倉`。
  - 只跑 `tests/test_generator_report.py` 或新增對應 formatter test file。
- L2 局部 integration：
  - 前一交易日 `daily_signal_snapshot` 讀取與 derived tracking list。
  - 近 2-5 日 `position_events` read-only loader。
  - 只跑新增的局部 store / loader tests，不跑 replay/backfill。
- 禁止作為 v19.4 MVP 驗證項：
  - full regression。
  - formal backfill。
  - live Telegram。
  - live Supabase write。
  - 全市場掃描。

### 不變性檢查

v19.4 驗證必須額外確認以下不變性：

- `BUY` 硬門檻不因 `可準備 / 隔日追蹤` 被放寬。
- `is_tradeable` 不因回測略優或追蹤優先級提高而變成 true。
- `is_best_candidate` 不因 tracking priority 而覆蓋原本硬規則。
- 過熱、漲停鎖價、RR 不足仍不可被追蹤語意改成可買。
- STOP / TAKE_PROFIT / REDUCE 既有 action 不被 lifecycle 顯示覆蓋。
- 缺前日 snapshot 或缺 position events 時，必須安全回退，不得硬判追蹤或新倉狀態。

### 建議最小測試命令

若 v19.4 只改 formatter / derived state：

```bash
.venv/bin/python -m pytest tests/test_generator_report.py
```

若新增 read-only position event loader：

```bash
.venv/bin/python -m pytest tests/test_position_store.py
```

若新增前一交易日 snapshot tracking loader：

```bash
.venv/bin/python -m pytest tests/test_daily_snapshot_store.py
```

只有當 Tech 實際改到 strategy hard rules、snapshot persistence contract 或 replay/backfill scripts，才升級到相應局部策略 / snapshot / replay tests。v19.4 MVP 不應預設 full pytest。

### QA 結論

- v19.4 可以進入 PM 撰寫 `TASK.md`，但驗收矩陣必須鎖定「狀態層 + 隔日追蹤」。
- QA 不建議第一版驗證策略門檻放寬；應先驗證新狀態不破壞硬風控。
- v19.4 若要落地，Tech 應先補最小 fixture / snapshot tests，再實作 formatter / derived helper；QA 後續按上述矩陣做局部驗證。

## Architect Conclusion

- PM 已完成 v19.4 顯著功能升級研究，並補出可直接放入 `TASK.md` 的產品文案、報文範例與驗收標準。Architect 判斷：研究階段已足夠，下一步直接產出正式 v19.4 `TASK.md`。

### PM 研究結論摘要

- v19.4 不應第一階段直接放寬 RR、過熱或加碼門檻。
- v19.4 應新增「策略狀態層」，補齊 `可準備 / 等回測 / 等RR修復 / 等量能 / 隔日確認`。
- R3 市場不應等同全面禁止交易；應保留不追高原則，但增加「可準備 / 隔日追蹤」。
- 持倉管理應補齊生命週期：
  - 新倉浮虧隔日未修復降級。
  - 減碼後觀察修復。
  - 核心倉高浮盈回落進入核心風控觀察。
- 回測可進入輔助權重，但不應覆蓋 RR / 過熱 / 風控等硬規則。
- 旺宏價格行右括號疑慮不作為 v19.4 阻塞；目前視為非策略問題，不另開 v19.3.5。

### Architect 判斷

- 直接進入 v19.4，不開 v19.3.5。
- v19.4 定位為「交易閉環升級」，不是 formatter 小修。
- v19.4 必須包含三個可感知主能力：
  - `隔日追蹤`
  - `持倉處理優先級`
  - `明日觸發條件`
- v19.4 應把「今天不能買」轉化為「明天怎麼看」。
- `待確認候選`、回測追蹤排序、今日狀態到明日檢查閉環應納入驗收。
- 現有資料結構足以支援 MVP；暫不改 DB schema。
- 回測只進 tracking priority，不覆蓋 BUY / STOP / RR / 過熱硬規則。
- 既有 QA 最小驗證矩陣可保留，後續 `TASK.md` 需引用不變性檢查。

## Next Action

- 轉 PM 正式改寫 `TASK.md`。
- `TASK.md` 必須使用 PM Findings 內的「可直接放入 TASK.md 的產品文案」作為主體。
- `TASK.md` 必須保留不可變更範圍：
  - 不直接放寬 RR / 過熱 / 漲停不追。
  - 不讓回測直接產生 BUY。
  - 不改 DB schema。
  - 不擴大股票池。
  - 不做全 repo refactor。
