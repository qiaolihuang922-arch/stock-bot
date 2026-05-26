# RESEARCH.md

本文件由 Architect 維護，用來承接研究型任務。PM、Tech、QA 可在各自區塊填寫摘要；Architect 最後只吸收結論，不接收完整聊天紀錄。

## Question

- 任務類型：研究 + 後續處理判斷
- 任務日期：2026-05-26
- 研究對象：最新 v19.3.2 盤中報文
- 核心問題：
  - 策略層與顯示層是否不一致，導致報文語意錯誤。
  - 為什麼報文長期沒有明確買入提示。
  - 為什麼持倉幾乎都是續抱，缺少賣出 / 加碼 / 減碼提示。
  - 未持倉幾乎都是不買 / 觀察，是否是策略過嚴、資料問題，還是 formatter 壓縮語意。

## Evidence

Owner 提供的最新報文重點：

- 市場：進攻偏熱 `R3`。
- 資料源：即時價 `realtime`，日線 `yahoo`。
- 持倉：英業達、緯創、南亞科、技嘉、智原。
- 最強：無有效進場標的。
- 今日重點：先處理持倉，暫不新增。
- 持倉狀態集中在：
  - `核心續抱`
  - `洗盤續抱`
  - `續抱觀察`
- 未持倉狀態集中在：
  - `禁止追高`
  - `等待冷卻`
  - `可觀察但不可買`
  - `弱勢淘汰`
- 明顯疑慮：
  - 智原是今日買入且浮虧，但仍顯示 `續抱觀察`。
  - 強勢股多數因過熱或 RR 不足而不買。
  - 幾乎沒有出現買入、加碼、賣出、減碼提示。

## PM Findings

- PM 結論：目前 v19.3.2 已比 v19.3.1 清楚，但「續抱 / 不買」仍有語意壓縮風險。問題不一定是策略錯，而是交易產品需要把「不可交易原因」與「下一步處理姿態」分開顯示。
- 使用者看到大量 `不買 / 觀察` 時，會自然理解為系統沒有機會；但從產品角度，至少要分成：
  - `沒有買點`：條件未成立，暫時不列優先。
  - `等待冷卻`：標的仍強，但追價風險高。
  - `可觀察但不可買`：結構可追蹤，但 RR / 量能 / 位置未達標。
  - `弱勢淘汰`：不應佔用決策注意力。
- 使用者看到大量 `續抱` 時，會自然理解為不用處理；但持倉產品上必須區分：
  - `核心續抱`：高浮盈或主線核心，重點是守利潤。
  - `洗盤續抱`：縮量回測，暫不加碼但可觀察。
  - `洗盤警戒`：小虧或今日新買後回落，仍可觀察但需要更高風控語氣。
  - `續抱觀察`：未破位但優先級下降。
  - `風控觀察`：接近警戒 / 停損 / 結構轉弱，需要明確處理條件。
  - `減碼 / 停利 / 停損`：只要策略觸發，摘要層必須高亮，不可被 formatter 壓成續抱。
- 產品上必須出現但不一定代表立即交易的提示：
  - `排隊觀察`：目前不買，但若冷卻 / RR 修復可重新評估。
  - `禁止追高`：策略不是看空，而是禁止用錯價格買。
  - `風控觀察`：不是立即賣出，但使用者需準備處理。
  - `洗盤警戒`：不是停損，但比普通續抱更需要盯警戒價。
  - `加碼未成立`：持倉可續抱，但不得讓使用者誤以為可加碼。
- 智原案例產品判斷：今日買入、小幅浮虧、仍有收縮/洗盤語意時，不應顯示普通 `續抱觀察`。較合適為 `洗盤警戒`，因為它同時保留「不急賣」與「需要風控」兩個訊息。
- v19.3.2 產品邊界：本輪不要求策略變更得更激進；只要求報文能準確呈現「為什麼不能買、持倉是否需要處理、下一個觸發條件是什麼」。
- 若 Tech 證明策略其實已產生買入 / 加碼 / 減碼 / 停利 / 停損，但 formatter 壓縮成 `不買 / 續抱`，這是顯示 bug，應優先修 formatter。
- 若 Tech 證明策略本身長期不產生買入 / 加碼 / 減碼 / 停利 / 停損，PM 需另開 v19.4 策略語意任務，重新定義 RR、過熱、加碼、停利、洗盤保護與 R3 市場行為。

## Tech Findings

### Scope

- 只讀局部源碼，不改代碼。
- 檢查範圍：
  - `services/analysis.py`
    - `strategy()`
    - `holding_signal()`
  - `core/generator.py`
    - `entry_blockers()`
    - `classify_watchlist_group()`
    - `is_valid_entry()`
    - `ensure_holding_decision()`
    - `position_summary_action()`
    - `formatTelegramPositionCard()`
    - `formatTelegramUnheldCard()`
    - `holding_detail_decision_lines()`

### 策略層與顯示層一致性

- 未持倉新進場：
  - 策略層只有在 `decision=BUY`、`action > 0`、品質達標時才可能成為買入候選。
  - 顯示層 `is_valid_entry()` 又要求：
    - `decision == BUY`
    - `action > 0`
    - `not entry_blockers(result)`
    - `entry_quality in A+ / A / B`
  - `entry_blockers()` 會阻擋：
    - 漲停 / 漲停反彈 / 弱反彈
    - `HOT / EXTREME / EXTENDED`
    - `RR < 1`
    - `NO_VOLUME` 或 `volume_state=WEAK`
    - `market_grade=D`
    - `breakout_distance > 4`
  - 因此目前未持倉大量不是「可買」，主要不是 formatter 任意改成不買，而是策略與 blocker 條件共同阻擋。

- 未持倉顯示語意：
  - `formatTelegramUnheldCard()` 已能依分組顯示：
    - `禁止追高`
    - `等待冷卻`
    - `觀察`
    - `淘汰`
  - 這比全部顯示 `不買` 更接近策略語意。
  - 但有一個潛在不一致：
    - `classify_watchlist_group()` 對 `is_valid_entry(result)` 目前回傳 `可觀察但不可買`。
    - 若未來真的出現合格 `BUY`，摘要分組可能把它放進 `可觀察但不可買`，但詳情卡會顯示 `🟢 可買`。
    - 這是顯示層摘要與詳情的潛在衝突，建議後續修正為獨立 `可買` 分組或讓 summary 特別列出買點成立。

### 是否存在策略訊號被 formatter 壓成續抱 / 不買

- 買入：
  - 若是未持倉合格買入，詳情卡 `formatTelegramUnheldCard()` 會顯示 `🟢 可買`。
  - 但摘要分組如上，可能被 `classify_watchlist_group()` 放到 `可觀察但不可買`，屬潛在 formatter 問題。

- 加碼：
  - 策略層 `holding_signal()` 可輸出：
    - `ADD_30`
    - `ADD_20`
    - `ADD_10`
  - 但 `position_summary_action()` 沒有明確處理 `ADD_30 / ADD_20 / ADD_10`。
  - 當策略真的給出加碼訊號時，Telegram 持倉卡片標題可能不會顯示 `加碼`，而是落到 `續抱` 或其他泛化狀態。
  - `holding_blocker_text()` 有 ADD 文案，但新版持倉卡片主標題與 `holding_detail_decision_lines()` 沒有 ADD 專用分支。
  - 這是明確的策略層 / 顯示層不一致風險，也是「為什麼很少看到加碼提示」的技術原因之一。

- 減碼 / 停損 / 停利：
  - 策略層可輸出：
    - `STOP_100`
    - `REDUCE_50`
    - `REDUCE_25`
    - `TAKE_PROFIT_50`
    - `TAKE_PROFIT_25`
  - `position_summary_action()` 目前：
    - `TAKE_PROFIT_*` 顯示為 `停利`
    - `REDUCE_*` 與 `STOP_100` 都顯示為 `減碼`
  - `STOP_100` 被標題壓成 `減碼`，會弱化「停損 / 清倉」語意。
  - `holding_detail_decision_lines()` 沒有停利 / 減碼 / 停損專用分支，可能回落到 blocker/reason 拆句，導致交易動作不夠直接。
  - 這是顯示層需要後續補強的另一個一致性風險。

### 為什麼買入提示少

- 未持倉需要同時通過策略與顯示層 blocker：
  - RR 不足會直接出現 `RR不足`。
  - 過熱 / EXTENDED / HOT 會歸到 `過熱觀察` 或等待冷卻。
  - 漲停 / LIMIT_LOCK 會歸到 `漲停不追`。
  - 低量會被 `量能不足` 阻擋。
  - 市場弱 `market_grade=D` 會被 `市場弱` 阻擋。
  - 距離突破太遠 `breakout_distance > 4` 會被 `遠離觸發` 阻擋。
- 在 `R3 進攻偏熱` 場景下，強勢股容易同時命中過熱、漲停不追或 RR 不足，因此「沒有最強 / 沒有買入」大多是策略條件造成，不是單純 formatter 隱藏。
- 但如果未來出現真正合格買點，summary 目前仍可能因 `classify_watchlist_group()` 的 `is_valid_entry -> 可觀察但不可買` 造成摘要誤導。

### 為什麼加碼提示少

- 持倉加碼條件在 `holding_signal()` 中偏嚴，必須同時滿足：
  - `decision == BUY`
  - `price_source != twse`
  - `change < 9.5`
  - `market_regime == RISK_ON`
  - `trend == UP`
  - `volume != WEAK`
  - `heat != EXTREME`
  - price behavior 不能是弱反彈 / 漲停反彈 / 漲停鎖價
  - `entry_quality in A+ / A / B`
  - 浮盈門檻：
    - `ADD_30`: `pnl >= 2`, `rr >= 1.5`, `dist <= 2`, `confidence >= 80`
    - `ADD_20`: `pnl >= 1`, `rr >= 1.3`, `dist <= 3`, `confidence >= 72`
    - `ADD_10`: `pnl >= 0`, `rr >= 1.1`, `confidence >= 65`
- 這些條件會自然導致加碼訊號很少。
- 即使策略真的輸出 ADD，目前新 Telegram card 仍有顯示層未明確映射 ADD 的問題，需後續修正。

### 為什麼賣出 / 減碼提示少

- 策略層的賣出 / 減碼主要在以下情況觸發：
  - 跌破 hard stop 且不是洗盤保護。
  - `pnl <= -8` 且結構破壞。
  - 結構破壞 / `FAILED_BREAKOUT`。
  - 高浮盈且漲停 / EXTREME / HOT 延伸。
- 若持倉只是低量回測、縮量洗盤、小虧或尚未破結構，策略會偏向：
  - `洗盤警戒`
  - `洗盤續抱`
  - `續抱觀察`
  - `核心續抱`
- 所以目前賣出 / 減碼提示少，部分是策略設計偏保護持倉，部分是顯示層對 `STOP_100` / `REDUCE_*` / `TAKE_PROFIT_*` 的詳情語意仍不夠直。

### 智原狀態判斷

- 依目前策略與顯示規則，智原若符合：
  - 持倉
  - `PnL < 0`
  - `price_behavior = LOW_VOLUME_PULLBACK` 或 `structure_phase = SHAKEOUT`
  - `volume_state = WEAK` 或 `volume_price_state = COILING`
- 則策略應輸出 / 顯示為 `洗盤警戒`。
- `洗盤警戒` 是比 `續抱觀察` 更準確的狀態：
  - 表示仍非立即停損。
  - 但因小虧與弱量 / 收縮並存，需要更高風控語氣。
- 南亞科這類 `WEAK`、遠離觸發、轉弱觀察，才更適合 `續抱觀察`。

### Tech 結論

- 目前大量 `不買 / 觀察` 不全是 formatter 問題，主要由策略 blocker 造成，尤其是 RR、過熱、量能、市場弱、距離。
- 目前大量 `續抱` 也不全是 formatter 問題，策略層本身對洗盤 / 核心倉 / 小虧未破結構偏保護。
- 但確實存在顯示層一致性風險：
  1. 合格未持倉 `BUY` 在 summary 可能被歸入 `可觀察但不可買`。
  2. 持倉 `ADD_10 / ADD_20 / ADD_30` 可能被新版卡片標題壓成 `續抱`，加碼提示不夠明確。
  3. `STOP_100` 被 summary action 歸為 `減碼`，會弱化停損 / 清倉語意。
  4. 停利 / 減碼 / 停損在詳情決策行缺少專用分支，可能不如策略層 action 直接。
- 建議後續若轉實作，優先做 formatter 映射修正，不先改策略門檻：
  - summary 增加 `可買` 分組或合格買點置頂。
  - position summary / detail 補 ADD 專用顯示。
  - STOP / REDUCE / TAKE_PROFIT 補明確標題與決策行。
  - 增加策略輸出到 Telegram card 的最小一致性測試。

## QA Findings

- QA 結論：目前已有部分 formatter / snapshot 測試可覆蓋 v19.3.2 顯示修正，但不足以完整覆蓋「策略輸出到 Telegram 報文顯示」的一致性。
- 已有測試能力可覆蓋：
  - 持倉小虧洗盤語意顯示為 `洗盤警戒`。
  - RR raw 為 0 或接近 0 時顯示 `RR 0.00（不足）`。
  - 價格行保留完整全形右括號。
  - 未持倉不退回全部 `不買`，可維持四分類。
- 目前一致性測試缺口：
  1. 合格未持倉 `BUY` 是否在摘要層明確顯示 `可買`，而不是被 `classify_watchlist_group()` 歸入 `可觀察但不可買`。
  2. 持倉 `ADD_10 / ADD_20 / ADD_30` 是否在持倉摘要與詳情標題明確顯示 `加碼`，而不是被壓成 `續抱`。
  3. `STOP_100` 是否明確顯示 `停損 / 清倉`，而不是被摘要層泛化為 `減碼`。
  4. `TAKE_PROFIT_* / REDUCE_* / STOP_100` 是否在詳情決策行有專用文案，而不是只靠 blocker/reason 拆句。
  5. RR 不足、過熱、弱勢、量能不足、遠離觸發等 blocker 是否在摘要與詳情都能保持原因一致，不被 formatter 壓縮成含糊 `觀察`。

### 建議最小測試案例

QA 建議後續補以下最小 formatter / snapshot tests，不需要全局測試：

1. 合格買入訊號顯示買入
   - Arrange：建立未持倉 payload，`decision=BUY`、`action>0`、`entry_quality=A`、`rr>=1`、非過熱、非低量、非市場弱、距離不遠。
   - Assert：
     - 未持倉詳情卡顯示 `🟢 可買`。
     - 摘要層不可歸入 `可觀察但不可買`。
     - 若產品決定新增 `可買` 分組，摘要需顯示 `【可買 N】...`。

2. 合格加碼訊號顯示加碼
   - Arrange：建立持倉 payload，`holding_decision.level=ADD_10 / ADD_20 / ADD_30`。
   - Assert：
     - 持倉摘要顯示 `加碼` 或明確加碼等級。
     - 持倉詳情標題顯示 `📌 加碼`。
     - 詳情決策行顯示 `決策：加碼...`，不可顯示普通 `續抱`。

3. 停利 / 減碼 / 停損不被 formatter 改成續抱
   - Arrange：分別建立 `TAKE_PROFIT_25`、`REDUCE_25`、`STOP_100` 持倉 payload。
   - Assert：
     - `TAKE_PROFIT_*` 顯示 `停利`。
     - `REDUCE_*` 顯示 `減碼`。
     - `STOP_100` 顯示 `停損` 或 `清倉`，不可只顯示 `減碼`，也不可顯示 `續抱`。
     - 詳情決策行需直接呈現策略 action。

4. 阻擋原因一致顯示
   - Arrange：建立未持倉 payload，分別命中 `RR不足`、`過熱觀察`、`市場弱`、`量能不足`、`遠離觸發`。
   - Assert：
     - 摘要分組與詳情標題 / 買點行原因一致。
     - 不可只顯示泛化 `不買` 或 `觀察` 而缺少阻擋原因。

### QA 判斷

- 若下一步只修 formatter 映射，QA 可用 `tests/test_generator_report.py` 增加 snapshot / formatter cases 驗證，不需要跑 replay / backfill。
- 若下一步調整 `holding_signal()` 或 `strategy()` 的判斷門檻，QA 需同步補 `tests/test_analysis_engine.py` 的策略案例，再跑對應局部測試。
- 本研究階段未執行全局測試、未跑 replay/backfill、未做 live Telegram / Supabase 驗證。
- QA 建議 Architect 將後續任務優先切為「formatter 一致性修正」，先補上述最小測試，再決定是否另開 v19.4 策略門檻任務。

## Architect Conclusion

- 研究結論：目前問題不是單一層錯誤，而是「策略門檻偏嚴 + 顯示映射不完整」共同造成使用者感覺一直沒有買入 / 加碼 / 賣出提示。

### 1. 策略層與顯示層是否不一致

- 未持倉「大多不買」主要來自策略與 blocker 條件，不是 formatter 任意改壞。
- 目前 R3 盤中場景下，強勢股容易命中：
  - 過熱 / EXTENDED / HOT
  - 漲停不追
  - RR 不足
  - 量能不足
  - 遠離觸發
- 這些 blocker 會自然導致 `最強：無有效進場標的`。
- 但顯示層確實有一致性風險：
  - 合格未持倉 `BUY` 可能在摘要被放進 `可觀察但不可買`。
  - `ADD_10 / ADD_20 / ADD_30` 缺少持倉摘要與詳情專用顯示，可能被泛化成續抱。
  - `STOP_100` 被摘要壓成 `減碼`，停損 / 清倉語意不足。
  - `TAKE_PROFIT_* / REDUCE_* / STOP_100` 詳情決策行缺少直接交易動作文案。

### 2. 為什麼一直沒有買入提示

- 主要原因是策略 blocker 生效，尤其是 RR、過熱、漲停不追、量能與距離。
- 這符合「不追高」風控，但產品語意需要更清楚地告訴使用者：
  - 不是看空。
  - 是價格 / 風報 / 過熱條件不允許現在買。
  - 哪些標的是等待冷卻，哪些是弱勢淘汰。
- 後續不應先放寬策略門檻，應先修摘要層：若真的出現合格 `BUY`，必須明確顯示 `可買` 或置頂，不得被歸入 `可觀察但不可買`。

### 3. 為什麼賣出 / 加碼 / 減碼提示少

- 加碼少：策略條件本身嚴格，需要盈利、結構、量能、RR、信心與市場狀態同時滿足。
- 賣出 / 減碼少：策略對洗盤、小虧未破結構、核心倉偏保護，因此會偏向 `洗盤續抱 / 續抱觀察 / 核心續抱`。
- 但顯示層仍需修正：
  - 策略一旦輸出 ADD，報文必須顯示加碼。
  - 策略一旦輸出 STOP，報文必須顯示停損 / 清倉，不可只叫減碼。
  - 策略一旦輸出 TAKE_PROFIT / REDUCE，詳情決策行必須直接顯示停利 / 減碼。

### 4. 智原案例

- 智原今日買入、小幅浮虧、仍有洗盤 / 收縮語意時，產品與 Tech 研究都支持 `洗盤警戒` 比普通 `續抱觀察` 更準確。
- `洗盤警戒` 不代表立即賣出，而是保留觀察但提高風控語氣。
- 南亞科這類弱勢、遠離觸發、優先級下降，更適合 `續抱觀察`。

### 5. Architect 判斷

- 下一步應優先開「formatter 一致性修正」任務，不先改策略門檻。
- 修正重點是讓策略已有 action 被 Telegram summary/detail 正確呈現。
- 同時補最小一致性測試，避免策略輸出被 formatter 壓縮。
- 若 formatter 修正後仍長期沒有買入 / 加碼 / 賣出，再另開 v19.4 策略門檻研究。

## Next Action

- 轉為開發任務：`v19.3.3 formatter 一致性修正`。
- PM 需先改寫 `TASK.md`，只定義顯示層需求，不改策略門檻：
  - 合格未持倉 `BUY` 摘要需明確顯示 `可買` 或置頂。
  - `ADD_10 / ADD_20 / ADD_30` 持倉摘要與詳情需明確顯示加碼。
  - `STOP_100` 需明確顯示停損 / 清倉，不可只顯示減碼。
  - `TAKE_PROFIT_* / REDUCE_* / STOP_100` 詳情決策行需有專用文案。
  - 阻擋原因在摘要與詳情需保持一致。
- Tech 等 `TASK.md` ready 後實作 formatter 映射與必要最小測試。
- QA 驗證 `tests/test_generator_report.py` 與必要 `tests/test_analysis_engine.py` 局部案例，不跑全局測試，除非 Architect 另行要求。
- 暫不調整：
  - RR 門檻
  - 過熱規則
  - 加碼 / 減碼策略門檻
  - DB / replay / backfill
  - v19.4 策略方向
