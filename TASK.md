# TASK: Post Trade Reduce Cooldown Strategy Fix

## 任務狀態

- task_id: post-trade-reduce-cooldown-strategy-fix
- 任務類型: holding_strategy_event_aware_bugfix
- 狀態: ready_for_tech
- 版本建議: patch
- 版本契約: 本輪不升版，沿用目前 VERSION v20.0.9；Telegram 報文 header / formatter 測試期望不得回退。
- QA 分級建議: L2
- QA 升級原因: 本輪改持倉策略行動優先級與報文使用者可見建議，需驗證策略不變性、formatter、直接消費者與負面風控覆蓋案例。

## Owner 問題

Owner 指出最新 Telegram 報文出現持倉策略衝突：

- 緯創 今日已賣出 40 股，約等於持倉 27%，但後續報文仍再次給同級 減碼 25%，造成重複減碼建議。
- 智原 今日買入 40 股 後，報文又顯示 減碼 50%，與新倉行為衝突。
- Owner 明確要求修的是策略 / 持倉狀態機的 event-aware 判斷，不是 formatter 文案遮罩，也不是「今天賣過就永不賣」的硬鎖。
- 本輪目標是讓策略理解今日交易事件，避免同級重複減碼，同時保留真正停損、跌破警戒、結構惡化或更高級風控可覆蓋的能力。

## 使用者可見結果

Owner 在手機打開 Telegram 後，持倉決策區應先看到：

1. 今日已減碼且比例接近建議比例的股票，不再被列為同級再次減碼。
2. 這類股票主行動改為 減碼後觀察 或等價風控觀察語意。
3. 今日剛買入的股票，不得無脈絡顯示一般 減碼 50%；預設應顯示 新倉風控觀察。
4. 若今日買入後真的跌破停損、跌破警戒、結構進一步惡化或觸發更高級風控，報文可以顯示風控賣出 / 減碼，但必須在同一行說明觸發條件。
5. Summary、持倉卡、明日清單、詳情中的同一檔股票只能有一個主行動，不得一段觀察、一段減碼。

手機閱讀路徑：

- Header: 【MM/DD 盤後｜v20.0.9】
- 第一屏 summary: 先看到「持倉先處理什麼」，且不出現重複同級減碼。
- 持倉卡: 每檔股票顯示唯一主行動與 event-aware 原因。
- 詳情 / 追溯: 可追溯今日已買 / 已賣事件、原始風控訊號、是否被 cooldown 降級或被硬風控覆蓋。

## 非目標

- 不改 DB schema。
- 不改 watchlist。
- 不 live Telegram delivery。
- 不 live Supabase write。
- 不做正式 backfill / replay 寫入。
- 不重寫整體策略框架。
- 不把所有今日已賣股票永久鎖成不可賣。
- 不把所有今日買入股票永久鎖成不可減碼 / 不可停損。
- 不只改 formatter 文案來掩蓋 strategy decision 衝突。
- 不改未持倉漏斗、淘汰股、策略證據區塊或 unrelated summary 排版。

## 影響模組

直接影響模組：

- services/analysis.py: 持倉策略 decision / reduce / risk action 來源。
- core/generator.py: Telegram 持倉 summary、持倉卡、明日清單、詳情輸出。
- services/position_store.py: 若現有資料已提供今日買賣事件，Tech 可讀取並傳入策略；不得改 schema。
- 相關測試: strategy / generator / notifier 直接契約測試。

不得影響模組：

- core/watchlist.py
- services/signal_store.py
- services/daily_snapshot_store.py
- scripts/backfill_signals.py 正式寫入路徑
- scripts/dry_run_replay.py 正式資料副作用
- Supabase schema / migrations
- Telegram live send path

## 直接消費者

- Owner 手機 Telegram 報文。
- Telegram formatter message list / summary / holding cards。
- 持倉策略 decision 的下游 formatter。
- 測試 snapshots / formatter expectations。
- 若存在 notifier payload tests，需確認 header 版本與 message list 仍可被發送端消費。

## 輸出契約

### 1. Post-trade cooldown / event-aware reduce 契約

對同一檔持倉，策略需在產生主行動前讀取「今日交易事件」：

- today_sold_qty
- today_sold_ratio
- today_bought_qty
- today_bought_ratio
- last_trade_side
- last_trade_time 或等價 trading-date 判斷
- 若現有資料沒有上述欄位，Tech 必須 blocked，不得用推測或 hardcoded fixture 代替。

今日已賣且符合以下任一條件時，視為已執行接近同級減碼：

- abs(today_sold_ratio - recommended_reduce_ratio) <= 5 percentage points
- 或 today_sold_ratio >= recommended_reduce_ratio * 0.8
- 或股數換算後可證明已賣量接近建議減碼量。

符合後，原本同級 減碼 X% 主行動需轉為：

- 主行動: 減碼後觀察
- 原因: 今日已減碼約 Y%，接近原建議 X%，等待新訊號
- 不得在 summary / 持倉卡 / 明日清單 / 詳情再以同級 減碼 X% 當主行動。

### 2. 允許再次減碼的覆蓋條件

今日已賣後，只有以下情況可再次輸出減碼 / 賣出主行動：

- 跌破停損。
- 跌破警戒。
- 結構進一步惡化，例如原本 減碼 25% 升級為 減碼 50% 或 停損 / 清倉。
- 新觸發更高級風控，且風控級別高於今日已執行的減碼級別。
- 原本今日賣出比例明顯低於新建議比例，仍有未完成的增量風控差額。

再次減碼時，輸出必須說明是「增量風控」或「硬風控覆蓋」，不得像同級重複建議。

### 3. 今日買入與減碼衝突契約

今日已買入的持倉，預設主行動為：

- 主行動: 新倉風控觀察
- 原因: 今日剛買入，先觀察是否守住警戒 / 停損

今日買入後不得顯示一般性 減碼 25% / 減碼 50%，除非符合以下硬風控覆蓋條件：

- 買入後跌破停損。
- 買入後跌破警戒且策略定義為需立即降風險。
- 結構明顯惡化，且風控級別高於新倉觀察。
- PM/策略已有明確的當日反手風控規則。

若硬風控覆蓋今日買入，輸出必須包含觸發條件，例如：

- 硬風控：跌破停損，今日新倉仍需減碼 50%
- 不加碼，先風控：跌破警戒，觀察是否失守

不得只顯示 減碼 50% 而沒有新倉事件與觸發條件。

### 4. 主行動優先級

同一檔股票同一份報文只能有一個主行動。優先級如下：

1. 停損 / 清倉
2. 硬風控減碼
3. 增量減碼
4. 減碼後觀察
5. 新倉風控觀察
6. 續抱
7. 觀察
8. 不動作

若同時符合高分強勢與風控條件，風控優先；summary 必須說 不加碼，先風控。

## 驗收條件

1. 緯創 fixture: 今日已賣 40 股、約 27%，原始策略建議 減碼 25% 時，Telegram 不得再出現同級主行動 減碼 25%；應輸出 減碼後觀察。
2. 緯創覆蓋 fixture: 今日已賣約 27%，但後續跌破停損或風控升級至高於原建議時，Telegram 仍可輸出再次減碼 / 停損，且必須標示 硬風控 或 風控升級 原因。
3. 智原 fixture: 今日買入 40 股 後，若只有一般弱化或原始 reduce 訊號，Telegram 不得直接顯示 減碼 50%；應顯示 新倉風控觀察。
4. 智原硬風控 fixture: 今日買入後若跌破停損 / 跌破警戒 / 結構惡化至更高級風控，Telegram 可顯示減碼 / 停損，但同一行必須說明觸發條件。
5. Summary、持倉卡、明日清單、詳情中，同一股票不得出現互相衝突的主行動。
6. Header 版本必須顯示 v20.0.9，測試期望同步。
7. 未持倉分類、watchlist、DB payload、live Telegram、live Supabase、replay/backfill write path 不得改變。
8. QA 必須使用接近 Owner 報文情境的長報文 fixture，而不是只檢查單一欄位存在。
9. Tech 自檢需至少覆蓋策略 decision 與 Telegram formatter 直接輸出；QA 需補直接消費者與負面硬風控案例。
10. 若現有資料來源無法可靠取得今日買 / 賣事件，Tech 必須 blocked，不能用「今天賣過就永不賣」或硬編股票名稱處理。

## 範例或 fixture

### Fixture A: 緯創同級減碼已執行

輸入形狀：

股票: 緯創
目前持倉: 150 股
今日已賣: 40 股
今日已賣比例: 26.7%
原始策略建議: 減碼 25%
價格狀態: 未跌破停損、未跌破警戒、結構未進一步惡化

期望手機輸出形狀：

【05/27 盤後｜v20.0.9】

持倉先處理：
緯創：減碼後觀察｜今日已減碼約27%，接近原建議25%，等待新訊號

持倉詳情：
緯創｜主行動：減碼後觀察
事件：今日已賣40股（約27%）
追溯：原始建議減碼25%，已由今日交易完成，未觸發更高級風控

不得出現：

緯創：減碼25%
緯創：明日再減碼25%

### Fixture B: 緯創硬風控覆蓋

輸入形狀：

股票: 緯創
今日已賣比例: 26.7%
原始已執行建議: 減碼 25%
新狀態: 跌破停損 或 風控升級為減碼50% / 停損

期望手機輸出形狀：

持倉先處理：
緯創：硬風控減碼｜跌破停損，今日已減碼後仍需降低風險

持倉詳情：
緯創｜主行動：硬風控減碼
事件：今日已賣約27%
覆蓋原因：跌破停損 / 風控升級，高於原同級減碼

### Fixture C: 智原今日買入後一般減碼衝突

輸入形狀：

股票: 智原
今日已買: 40 股
原始策略建議: 減碼 50%
價格狀態: 未跌破停損、未跌破警戒、未觸發更高級風控

期望手機輸出形狀：

持倉先處理：
智原：新倉風控觀察｜今日剛買入，先看是否守住警戒

持倉詳情：
智原｜主行動：新倉風控觀察
事件：今日已買40股
追溯：原始減碼訊號未達硬風控覆蓋條件

不得出現：

智原：減碼50%
智原：今日買入後再減碼50%

### Fixture D: 智原今日買入後硬風控

輸入形狀：

股票: 智原
今日已買: 40 股
新狀態: 買入後跌破停損 或 跌破警戒且策略要求立即降風險

期望手機輸出形狀：

持倉先處理：
智原：硬風控減碼｜今日新倉跌破停損，先降低風險

持倉詳情：
智原｜主行動：硬風控減碼
事件：今日已買40股
覆蓋原因：跌破停損，高於新倉觀察

## 明確禁止事項

- 禁止 live Telegram。
- 禁止 live Supabase write。
- 禁止正式 backfill。
- 禁止改 DB schema / migration。
- 禁止改 core/watchlist.py。
- 禁止硬編 緯創、智原 作為特殊案例。
- 禁止用「今天賣過就永不賣」作為硬鎖。
- 禁止用「今天買過就永不賣」遮蔽停損 / 更高級風控。
- 禁止只在 formatter 隱藏減碼文字而不修 strategy decision / action contract。
- 禁止讓同一股票在 summary、持倉卡、明日清單、詳情出現相反主行動。
- 禁止擴張到未持倉漏斗、策略證據、watchlist、DB payload 或 unrelated cleanup。

## 阻塞條件

- 現有持倉 / 交易資料無法可靠提供今日買入、今日賣出、交易比例或交易日期，且本輪又禁止 DB schema 變更。
- 無法判斷 recommended reduce ratio 與今日已賣比例是否同級或接近。
- 策略層沒有可傳遞到 formatter 的主行動 / 風控原因欄位，導致只能改文案遮罩。
- Fixture 無法建立 Owner 報文情境，或測試只能覆蓋單欄位而不能覆蓋手機長報文。
- Tech 發現需要改 DB/watchlist/live payload 才能完成，必須停止並回報 Architect/Owner。
