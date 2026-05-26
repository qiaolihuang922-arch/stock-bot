# RESEARCH.md

本文件由 Architect 維護，用來承接研究型任務。PM、Tech、QA 可在各自區塊填寫摘要；Architect 最後只吸收結論，不接收完整聊天紀錄。

## Question

- 任務類型：跨角色研究
- 任務日期：2026-05-26
- 研究對象：v19.5 報文與策略體驗強化方向
- 背景：v19.4.1 已完成 Telegram 摘要最後推送與按鈕綁定修正。Owner 提供最新收盤報文，要求研究下一版強化方向。
- 核心問題：
  - v19.5 是否應把收盤報文從完整資料展示升級為決策壓縮與執行清單。
  - 如何減少持倉處理優先級、隔日追蹤、待確認候選之間的重複。
  - 如何讓持倉與未持倉的明日觸發更像可執行清單，而不是說明文。
  - 回測、RR、S、V 等資料應如何保留，但不干擾第一屏決策。
  - Tech 需評估是否可只在顯示 / 排序層完成，不改策略 action。
  - QA 需主動質疑 PM / Tech 可能漏掉的關聯與使用者誤判風險。

## Evidence

- v19.4.1 已能顯示：
  - R3 不新增原因。
  - 回測參考度與判讀。
  - 今日新倉浮虧風控語氣。
  - 減碼 / 停利 / 停損原因與下一步。
- Owner 最新貼文顯示 v19.4.1 已達成摘要最後推送。
- 報文仍偏長，且詳情與摘要間有語意重複。
- Owner 要求研究下一版強化方向，不直接開發。

## PM Findings

### PM 結論

v19.4.1 已完成「摘要最後推送」後，報文第一眼可見性已改善。v19.5 不應再只是新增區塊，而應解決 Owner 最新 v19.4.1 收盤報文暴露出的下一層問題：資訊仍然偏多、決策重點仍分散、持倉與未持倉的下一步雖然存在但還不夠像一張可執行交易清單。

v19.5 建議定位為「收盤決策壓縮與執行清單升級」。

核心目標：

1. 把收盤報文壓縮成「先看 30 秒就能決策」。
2. 把持倉變成可排序的處理隊列。
3. 把未持倉從資料清單變成候選漏斗。
4. 把明日觸發條件從說明文變成可掃讀的觸發卡。
5. 保留完整資料，但降低其對主閱讀流的干擾。

### 對 Owner 最新 v19.4.1 收盤報文的產品判斷

基於 v19.4.1 的產品形態，最新收盤報文已具備：

- 總覽摘要最後送出，Telegram 打開時優先看見摘要。
- 持倉處理優先級。
- 隔日追蹤。
- 待確認候選。
- 持倉 / 未持倉詳情保留。

但仍有四個產品問題：

1. 摘要區塊變多後，第一屏仍可能過長。
2. 持倉摘要、持倉處理優先級、持倉詳情存在語意重複。
3. 未持倉分組、隔日追蹤、待確認候選有重疊，使用者可能不知道以哪個為主。
4. 回測、RR、S、V、盤面等指標仍在詳情中佔據較多注意力，但不是所有標的都值得同等閱讀。

### v19.5 產品方向

v19.5 應新增「決策壓縮層」，把總覽摘要拆成三個可掃讀區塊：

```text
1. 今日結論
2. 明日執行清單
3. 詳情索引
```

使用者第一眼應看到：

```text
今天不新增 / 持倉優先 / 明天只追 3 檔 / 2 檔需風控
```

而不是先看到一串完整分類。

### 報文壓縮方式

#### 1. 新增「今日結論」單行

總覽摘要最上方新增一行交易結論：

```text
🧭 今日結論：R3 偏熱，不新增；持倉優先，明日只追 3 檔
```

或：

```text
🧭 今日結論：進攻仍在，但追價風險高；新倉只等回測
```

這行要取代部分冗長的市場解釋，不新增大量文字。

#### 2. 新增「明日執行清單」

將持倉處理優先級與隔日追蹤合併成一個更短的執行清單。

範例：

```text
✅ 明日執行清單
1. 智原｜新倉風控｜未修復降級
2. 英業達｜核心風控｜守警戒價
3. 光寶科｜等回測｜不破再評估
4. 建準｜等RR修復｜不追價
```

原本的 `📌 持倉處理優先級` 與 `🕒 隔日追蹤` 可在 v19.5 轉為執行清單的子來源，不必都完整展開在第一屏。

#### 3. 詳情層改為「只列需要看的」

詳情仍保留，但摘要應提供索引：

```text
📎 詳情索引：持倉 5 檔｜追蹤 3 檔｜淘汰 4 檔
```

如果 Telegram 長度壓力大，未持倉弱勢淘汰只列摘要，不必每檔都完整卡片。

### 持倉決策可讀性

v19.5 持倉應改成「處理狀態 + 明日檢查 + 失效條件」三段式。

持倉摘要建議格式：

```text
英業達｜核心風控｜守 59.0｜跌破升級風控
智原｜新倉風控｜站回 211.5｜否則降級
緯創｜洗盤續抱｜守警戒｜跌破轉風控
```

產品規則：

- `續抱` 不能單獨出現，需搭配原因或下一步。
- `核心續抱` 應說明守什麼價或什麼條件轉弱。
- `新倉風控` 必須顯示成本 / 買點 / 警戒其中一個明確參考。
- `減碼後觀察` 必須顯示修復條件。

### 未持倉決策可讀性

v19.5 未持倉應從「分組展示」升級成「候選漏斗」。

建議漏斗：

```text
未持倉漏斗：
可買：0
可準備：2
等回測：1
等RR修復：2
淘汰：4
```

並只把前 3-5 檔列入明日執行清單。其餘只保留統計或詳情。

未持倉標題建議：

```text
【可準備】股票｜明日觸發：...
【等回測】股票｜回測不破再評估
【等RR修復】股票｜RR不足，不追
【淘汰】股票｜弱勢 / 遠離觸發
```

產品規則：

- `不買` 不應作為主標題反覆出現。
- `不買` 可以保留在買點行，但標題應顯示等待類型。
- `弱勢淘汰` 不應佔用主決策版面。

### 策略體驗強化方向

v19.5 不建議直接改大策略門檻，但可以研究「策略體驗層」：

1. `可準備分數`
   - 不等於買入分數。
   - 用於明日追蹤排序。
   - 由 RR 接近度、過熱降溫、回測位置、回測參考度組成。

2. `持倉風控分級`
   - R1：正常續抱
   - R2：洗盤續抱
   - R3：新倉風控 / 核心風控
   - R4：減碼後觀察 / 轉弱
   - R5：停損 / 清倉

3. `明日觸發類型`
   - 價格觸發：站回 / 跌破 / 回測不破
   - 風報觸發：RR 修復
   - 量能觸發：量能回升或不失控
   - 風險觸發：過熱降溫

這些可以先作為顯示與排序層，不直接改交易 action。

### Edge Cases

- 沒有任何隔日追蹤標的時，顯示：

```text
✅ 明日執行清單：僅處理持倉，無新追蹤
```

- 沒有持倉時，執行清單應以候選為主：

```text
✅ 明日執行清單：無持倉，僅追蹤 3 檔待確認
```

- 有停損 / 減碼 / 停利時，必須排在執行清單最前面。

- 合格可買出現時，必須覆蓋等待狀態，進入執行清單第一組：

```text
1. 股票｜可買｜分批，不追價
```

- 回測參考度低的標的不能因為相對略優排到高優先級。

- 弱勢淘汰若數量很多，只顯示統計，不展開詳情：

```text
弱勢淘汰：5 檔｜主因：市場弱、遠離觸發
```

- 如果 Telegram 多段訊息仍過長，總覽摘要必須優先完整，詳情可拆分。

### v19.5 建議新增使用者可見區塊

必做：

```text
🧭 今日結論
✅ 明日執行清單
未持倉漏斗
📎 詳情索引
```

可選：

```text
⚠ 風控焦點
📉 淘汰統計
```

不建議：

```text
再新增完整長卡片
再新增另一組星等
把所有回測細節拉到摘要
```

### v19.5 報文範例

```text
【05/26 收盤｜v19.5】
📊 市場：進攻偏熱｜R3
🧭 今日結論：不新增，持倉優先；明日只追 3 檔
🧭 原因：強勢股多過熱，RR不足，不追高

✅ 明日執行清單
1. 智原｜新倉風控｜站回 211.5，否則降級
2. 英業達｜核心風控｜守 59.0，跌破升級風控
3. 光寶科｜等回測｜回測不破且降溫再評估
4. 建準｜等RR修復｜不追價

未持倉漏斗：
可買 0｜可準備 0｜等回測 1｜等RR修復 2｜淘汰 4

📎 詳情索引：持倉 5｜追蹤 3｜淘汰 4
```

### v19.5 是否要改策略門檻

PM 建議：

- 不在 v19.5 直接放寬 BUY / STOP / TAKE_PROFIT 硬門檻。
- 可以新增「可準備分數」與「風控分級」，但只能用於排序、壓縮與追蹤，不直接產生交易 action。
- 若 Owner 要真正調整 RR / 過熱 / 加碼門檻，應另開 v20 或 v19.6 策略研究。

### 可直接放入 TASK.md 的產品文案

```text
# TASK: v19.5 收盤決策壓縮與執行清單升級

## 需求目標

v19.5 要把 v19.4.1 的交易閉環報文壓縮成更像「收盤後執行清單」的產品。

使用者打開 Telegram 最下面的摘要時，30 秒內要知道：
- 今天是否新增。
- 明天最重要的 3-5 件事。
- 哪些持倉要處理。
- 哪些未持倉值得追蹤。
- 哪些標的只是淘汰統計，不需要細看。

## 新增 / 調整區塊

1. 新增 `🧭 今日結論`
2. 新增 `✅ 明日執行清單`
3. 新增 `未持倉漏斗`
4. 新增 `📎 詳情索引`
5. 壓縮弱勢淘汰與低優先級未持倉詳情

## 報文範例

【05/26 收盤｜v19.5】
📊 市場：進攻偏熱｜R3
🧭 今日結論：不新增，持倉優先；明日只追 3 檔
🧭 原因：強勢股多過熱，RR不足，不追高

✅ 明日執行清單
1. 智原｜新倉風控｜站回 211.5，否則降級
2. 英業達｜核心風控｜守 59.0，跌破升級風控
3. 光寶科｜等回測｜回測不破且降溫再評估
4. 建準｜等RR修復｜不追價

未持倉漏斗：
可買 0｜可準備 0｜等回測 1｜等RR修復 2｜淘汰 4

📎 詳情索引：持倉 5｜追蹤 3｜淘汰 4
```

### 可直接放入 TASK.md 的驗收標準

```text
v19.5 驗收標準：

1. 總覽摘要新增 `🧭 今日結論`。
2. 總覽摘要新增 `✅ 明日執行清單`。
3. 總覽摘要新增 `未持倉漏斗`。
4. 總覽摘要新增 `📎 詳情索引`。
5. 明日執行清單最多顯示 5 項。
6. 停損 / 減碼 / 停利 / 新倉風控必須排在執行清單前面。
7. 未持倉只有高優先級追蹤標的進入執行清單。
8. 弱勢淘汰預設只統計，不佔用主摘要。
9. 持倉摘要不得只顯示 `續抱`，必須有處理狀態或下一步。
10. 未持倉標題不得大量重複 `不買`，需顯示等待類型。
11. 回測只能影響追蹤排序，不得直接產生 BUY。
12. 總覽摘要仍最後送出，維持 v19.4.1 Telegram 順序。
13. 持倉詳情與未持倉詳情仍保留，但低優先級標的可壓縮。
14. 不改 DB schema。
15. 不擴大股票池。
16. 不直接放寬 RR / 過熱 / 加碼 / 停利 / 停損硬門檻。
```

## Tech Findings

- Tech 結論：PM 提出的 v19.5「收盤決策壓縮與執行清單升級」具備高可行性，第一版可以主要落在 `core/generator.py` 的顯示 / 排序 / derived summary layer，不需要改 `services/analysis.py` 的交易 action，不需要改 DB schema，不需要改 replay/backfill。真正需要控管的是：壓縮後不能讓使用者漏看硬風控、不能把「追蹤 / 可準備」誤解成「可買」、不能讓弱勢淘汰資料從可追溯層消失。

### 1. 現有實作支援度

- 目前 `core/generator.py` 已具備 v19.5 所需的大部分基礎 helper：
  - `formatTelegramSummary()`：總覽摘要入口。
  - `format_position_priority()`：持倉處理優先級。
  - `format_next_day_tracking()` / `next_day_tracking_items()`：隔日追蹤清單。
  - `format_pending_candidates_grouped()`：待確認候選。
  - `classify_watchlist_group()` / `sort_watchlist_grouped()`：未持倉分組與排序。
  - `formatTelegramPositionCard()` / `formatTelegramUnheldCard()`：詳情卡片。
  - `compact_backtest_line()`：回測壓縮行。
  - `split_message()` 與 v19.4.1 的多段推送順序：總覽摘要可保持最後送出。
- 因此 v19.5 不需要從零重寫 Telegram reporter；建議新增少量 formatter helper，重組摘要內容：
  - `format_today_conclusion()`
  - `format_execution_checklist()`
  - `format_unheld_funnel()`
  - `format_detail_index()`
  - `execution_item_from_holding()` / `execution_item_from_watch()`

### 2. 是否能只在顯示 / 排序層完成

- 可以。PM 的必做項大多是「資訊重排與壓縮」，不要求改變策略結果：
  - `🧭 今日結論` 可由現有 `market_summary`、market state、風險理由、持倉數、追蹤數推導。
  - `✅ 明日執行清單` 可合併既有持倉優先級與隔日追蹤，最多取 3-5 項。
  - `未持倉漏斗` 可由 `tomorrow_watch_state()` / `classify_watchlist_group()` 類型統計產生。
  - `📎 詳情索引` 可由 holding / tracking / rejected counts 產生。
- 建議 v19.5 明確保持以下不變：
  - 不改 `decision`。
  - 不改 `action`。
  - 不改 `is_tradeable`。
  - 不改 `is_best_candidate`。
  - 不改 RR / 過熱 / 漲停 / 停損 / 停利 / 加碼硬門檻。
- 若只做第一版，應把 `可準備分數` 實作成 `display_priority` 或 `tracking_priority`，不得寫回 strategy result，也不得進 DB snapshot。

### 3. 影響模組

- 主要影響：
  - `core/generator.py`
    - 摘要 formatter。
    - 執行清單排序。
    - 未持倉漏斗統計。
    - 詳情索引。
    - 可能壓縮低優先級未持倉卡片的呈現方式。
  - `tests/test_generator_report.py`
    - 新增 / 更新 formatter snapshot-like assertions。
    - 驗證摘要最後送出仍成立。
    - 驗證硬 action 不被顯示層覆蓋。
- 可能受影響但第一版不建議改：
  - `services/analysis.py`：不改策略門檻。
  - `services/daily_snapshot_store.py` / `services/signal_store.py`：不改寫入 payload。
  - `services/position_store.py`：若只用當日 `position_events`，不需改；若要跨日事件狀態，才需要另開 read-only loader。
  - `services/notifier.py`：v19.4.1 已處理 summary last + reply_markup last；v19.5 不應再改發送契約。

### 4. 建議技術落地方式

- 不建議在 `formatTelegramSummary()` 裡直接堆大量字串判斷；應先建立一個摘要 view model：
  - `build_report_decision_summary(results_map, market_summary, best, score)`
  - 回傳：
    - `today_conclusion`
    - `execution_items`
    - `unheld_funnel`
    - `detail_index`
    - `risk_reason`
- `execution_items` 建議使用結構化資料，不要只用字串：
  - `name`
  - `kind`: `holding` / `watch`
  - `state`: `STOP` / `REDUCE` / `TAKE_PROFIT` / `NEW_POSITION_RISK` / `CORE_RISK` / `WAIT_PULLBACK` / `WAIT_RR` / `WAIT_VOLUME` / `CONFIRM_NEXT_DAY`
  - `priority`
  - `trigger`
  - `display_text`
- 最後再由 formatter 轉成最多 5 行文字。這樣 QA 可以直接測排序與分類，不必靠全文比對。

### 5. 持倉執行清單可行性

- 可由現有持倉 helper 推導：
  - `position_summary_action()`
  - `position_priority_rank()`
  - `holding_tomorrow_trigger()`
  - `holding_next_step_line()`
  - `ensure_holding_decision()`
  - `stock_pnl()`
- 風控 / 停利 / 減碼 / 停損應使用最高優先級，維持 PM 規則。
- `續抱` 不應單獨出現在摘要；技術上可在 execution item 轉換時強制將其展開為：
  - `洗盤續抱｜守警戒`
  - `核心風控｜守警戒價`
  - `新倉風控｜站回 / 守停損`
  - `減碼後觀察｜修復才恢復優先級`
- 這是顯示層語意展開，不改 `holding_decision.level`。

### 6. 未持倉漏斗可行性

- 可直接從現有未持倉狀態推導：
  - `is_valid_entry()` -> `可買`
  - `tomorrow_watch_state()` / `entry_blockers()` / `heat_state` / `trade_state` -> `可準備 / 等回測 / 等RR修復 / 等量能 / 隔日確認`
  - `classify_watchlist_group()` 或弱勢條件 -> `淘汰`
- 建議漏斗分類不要完全等同目前分組名稱，應建立 v19.5 專用 helper：
  - `classify_unheld_funnel_state(name, data)`
- 原因：
  - 目前 `classify_watchlist_group()` 服務的是「未持倉摘要分組」。
  - v19.5 漏斗服務的是「明日執行與閱讀優先級」。
  - 兩者混用會讓未來 QA 很難判斷是產品分組變了，還是追蹤排序變了。

### 7. 詳情保留與壓縮方式

- PM 提到「低優先級未持倉詳情可壓縮」。技術上可行，但需明確產品邊界：
  - 不得直接刪除標的。
  - 不得讓弱勢淘汰完全不可追溯。
  - 可把弱勢淘汰集中成統計行，並在同一段保留簡短列表，例如：`淘汰 4：旺宏、...｜主因：市場弱、遠離觸發`。
- 如果 Owner 仍要求「所有標的完整卡片都在 Telegram 內」，則 v19.5 只能壓縮摘要，不能壓縮詳情。
- 若允許詳情壓縮，建議第一版只壓縮「未持倉弱勢淘汰」卡片，不壓縮：
  - 持倉。
  - 可買。
  - 可準備。
  - 等回測 / 等RR / 等量能。
  - 漲停 / 過熱高風險。

### 8. 回測資料的使用邊界

- 目前 `compact_backtest_line()` 已可顯示樣本、參考度、勝率、相對報酬與判讀。
- v19.5 可讓回測參考度進 `display_priority`，但只限排序：
  - `參考度低`：不提高優先級。
  - `參考度中 / 高` 且相對略優：可在同類候選內排序提前。
  - 相對偏弱：同類候選內排序降低。
- 不得讓回測：
  - 產生 BUY。
  - 覆蓋 RR 不足。
  - 覆蓋過熱 / 漲停不追。
  - 覆蓋停損 / 減碼 / 停利。
  - 改 strongest candidate。

### 9. 技術風險

- 語意壓縮風險：
  - `今日結論` 太短可能讓使用者忽略持倉風控。
  - 解法：執行清單中停損 / 減碼 / 新倉風控永遠排前面。
- 分類誤導風險：
  - `可準備` 容易被理解成可買。
  - 解法：文案固定帶 `不可買 / 等觸發`，並在買點行維持 `不買`。
- 資料缺失風險：
  - 如果壓縮弱勢淘汰詳情，QA 需確認所有股票仍在摘要或詳情索引中可追溯。
- Telegram 長度風險：
  - 摘要最後送出後若變長，仍需確保 summary 不被 split 到難讀。
  - 若 summary 有 split 風險，需讓 summary chunks 仍在最後且最後 chunk 保留核心結論，或限制執行清單最多 5 項。
- 回歸風險：
  - `formatTelegramMessages()` 訊息順序與 `reply_markup` 最後綁定不能回退。
- 測試風險：
  - 若只測全文片段，容易漏掉排序錯誤；建議新增 helper 層 unit tests。

### 10. 建議 v19.5 任務切分

- v19.5 可以作為 minor，但建議限定為「報文體驗與決策壓縮」，不要混入策略門檻。
- MVP 範圍：
  - 新增 `🧭 今日結論`。
  - 新增 `✅ 明日執行清單`，最多 5 項。
  - 新增 `未持倉漏斗`。
  - 新增 `📎 詳情索引`。
  - 保持總覽摘要最後送出。
  - 保持 `reply_markup` 綁定最後摘要段。
- 延後項：
  - 跨日 tracking table。
  - 跨日「昨日追蹤完成 / 失效」持久化。
  - 策略門檻調整。
  - DB schema 變更。
  - 正式 backfill。

### 11. 建議 QA 驗證方向

- Formatter / summary：
  - 摘要包含 `今日結論`、`明日執行清單`、`未持倉漏斗`、`詳情索引`。
  - 摘要仍是 `messages[-1]`。
  - `reply_markup` 仍附在最後一段摘要。
- 執行清單排序：
  - 停損 / 減碼 / 停利 / 新倉風控優先於一般追蹤。
  - 最多 5 項。
  - 合格 BUY 必須進前段，不被等待狀態覆蓋。
- 未持倉漏斗：
  - `可買`、`等回測`、`等RR修復`、`等量能`、`淘汰` 計數正確。
  - 弱勢淘汰不佔用主執行清單。
- 不變性：
  - 不改 strategy action。
  - 不改 DB payload。
  - 不改 snapshot/replay/backfill。
  - 回測只影響排序，不產生 BUY。

### 12. Tech 結論

- v19.5 可以進入 PM 正式 TASK，但應明確限制為「顯示 / 排序 / 摘要 view model」。
- 第一版不需要改 `services/analysis.py`、DB schema、股票池、replay/backfill。
- 技術上最重要的不是新增更多文案，而是建立結構化 summary view model，避免 formatter 字串堆疊失控。
- 若 Owner 要把「可準備分數」真正納入交易決策，應另開 v19.6 或 v20 策略研究；v19.5 只做閱讀與執行體驗升級。

## QA Findings

- QA 結論：v19.5 可以進入正式 PM `TASK.md`，但必須被定義為「顯示 / 排序 / 摘要 view model」版本，不能混入策略門檻、DB schema、replay/backfill 或跨日持久化。QA 對 PM / Tech 方向給 conditional approval：產品方向合理，技術落點可行，但摘要壓縮會引入新的閱讀風險與發送契約風險，必須在驗收標準中明確防回退。

### 關聯風險掃描

#### 直接消費者與資料流

- `core/generator.py`
  - `generate_report()` 回傳 `messages, execution_reply_markup(results_map)`。
  - `formatTelegramMessages()` 目前回傳 list：持倉詳情、未持倉詳情、總覽摘要。
  - `formatTelegramSummary()` 是 v19.5 壓縮摘要的主要入口。
- `main.py`
  - 直接消費 `generate_report()` 的 tuple，並呼叫 `send_many(messages, reply_markup=reply_markup)`。
- `services/notifier.py`
  - `send_many()` 對 list 訊息只把 `reply_markup` 附在最後一段。
  - 單段 string 則直接附 `reply_markup`。
- 測試契約
  - `tests/test_generator_report.py` 已覆蓋 summary last、formatter 順序與部分策略顯示不變性。
  - `tests/test_notifier.py` 已覆蓋 reply_markup 綁最後一段與單段字串原行為。

QA 判斷：v19.5 只要改摘要分段、summary split、messages list 順序或低優先級詳情壓縮，就會影響 `main.py -> send_many()` 這條直接發送契約。即使不改 `services/notifier.py`，QA 仍必須把 `messages[-1]` 是總覽摘要、且 `reply_markup` 附在最後摘要段列為必測。

#### 可能漏掉的間接依賴

- `generate()` 會把 `generate_report()[0]` 若為 list 就 join 成文字；v19.5 若改 messages 結構為 object / view model，不可破壞這個 fallback。
- Telegram `send()` 會把單段超過 3500 字截斷；若 v19.5 摘要壓縮失敗導致 summary 過長，最重要的結論可能被截斷。
- `split_message()` 目前只用於完整詳情備份；若 v19.5 讓摘要 split，需重新定義「最後一段摘要」與 `reply_markup` 應附在哪個 summary chunk。
- `execution_reply_markup(results_map)` 仍依全結果產生按鈕；若低優先級標的詳情被壓縮，按鈕與可見標的的關係可能讓使用者困惑。

### 質疑與反證

#### 1. PM 是否漏需求

PM 已定義 `今日結論`、`明日執行清單`、`未持倉漏斗`、`詳情索引`，但仍需要補三個硬性需求：

- 風控不可被壓縮掉：停損、減碼、停利、新倉風控、核心風控必須在摘要可見；不能只存在詳情。
- 低優先級可壓縮但不可消失：弱勢淘汰可統計化，但必須可追溯到股票名稱、主因與原始詳情位置。
- 等待類型必須明確不是可買：`可準備`、`等回測`、`等RR修復`、`等量能` 必須固定帶 `不可買 / 等觸發 / 不追價` 之一，不能只用正向詞彙。

QA 反證標準：若一份 v19.5 報文中使用者只看最後摘要，看不到任何風控標的、看不出等待標的不可買、或找不到淘汰標的名稱，則 PM 需求不完整。

#### 2. Tech 是否漏同步

Tech 正確指出 MVP 可主要落在 `core/generator.py`，但仍需同步三個契約：

- `formatTelegramMessages()` 的 list 順序不得回退，summary 必須仍是 `messages[-1]`。
- `send_many()` 的 `reply_markup` last-message contract 必須新增 v19.5 integration test，不只保留 notifier unit test。
- 如果建立 `build_report_decision_summary()` view model，必須有 helper-level tests 驗證排序與分類；不能只靠全文 `assertIn`。

QA 反證標準：若 Tech 只改 `formatTelegramSummary()` 並讓現有片段測試通過，但沒有測 `generate_report() -> send_many()` 的末段摘要與按鈕契約，QA 應判定 conditional pass 或 blocked。

#### 3. 測試是否能證明沒有破壞直接消費者

不能只靠 formatter snapshot。v19.5 至少要證明：

- `formatTelegramMessages()` 產出的最後一段是總覽摘要。
- `generate_report()` 回傳的 messages list 保持可被 `send_many()` 消費。
- `send_many(messages, reply_markup)` 仍將 inline keyboard 綁到最後摘要段。
- 單段 string 行為沒有回退。
- 摘要長度不會觸發 `send()` 3500 字截斷；或若摘要 split，仍有明確的最後 summary chunk 規則。

### 指定風險檢查

#### 摘要壓縮是否造成風控漏看

高風險。PM 建議最多 3-5 項執行清單，若持倉風控超過 5 項，低順位風控可能被擠掉。

QA 要求：
- STOP / REDUCE / TAKE_PROFIT / 新倉風控 / 核心風控必須優先於所有未持倉追蹤。
- 若風控項超過 5 項，摘要不得靜默截斷，必須顯示 `另有 N 檔風控見詳情` 或等效索引。
- `今日結論` 不得只寫「不新增」，必須帶出是否有持倉風控。

#### 等待標的是否被誤解為可買

中高風險。`可準備` 是產品上有用的詞，但交易語意容易被使用者理解成可進場。

QA 要求：
- `可準備` 不得與 `可買` 同色 / 同語氣 / 同排序標籤。
- 等待類標題必須包含 `等`、`不可買`、`不追價` 或具體觸發條件。
- 買點行仍必須明確顯示 `不買`，除非 `is_valid_entry()` 成立。
- 合格 BUY 必須覆蓋等待狀態；等待狀態不得覆蓋 BUY，也不得生成 `is_tradeable=True`。

#### 低優先級標的是否不可追溯

高風險。PM / Tech 都允許弱勢淘汰壓縮，但如果只剩統計數，Owner 後續無法檢查某檔股票為何被淘汰。

QA 要求：
- 弱勢淘汰可不展開完整卡片，但必須至少保留股票名稱清單與主因統計。
- `詳情索引` 必須能回答：持倉幾檔、追蹤幾檔、淘汰幾檔、低優先級名稱在哪裡看。
- 12 檔 watchlist 不得因壓縮而在報文中完全消失；若有任何標的不出現在摘要或詳情，QA 應判定 blocked。

#### Telegram summary / reply_markup 契約是否回退

高風險。v19.4.1 剛修正摘要最後送出與按鈕綁定，v19.5 正好會改 summary 結構，最容易回退。

QA 要求：
- 預設 messages 順序仍需保證最後一段是總覽摘要。
- `include_detail=True` 時完整詳情 chunk 仍必須在摘要之前。
- `reply_markup` 必須綁在最後摘要段，不可回到第一段詳情。
- 若 summary split 成多段，必須定義 `reply_markup` 綁到最後 summary chunk，且最後 chunk 不得只是殘餘低價值文字。
- 必須保留 `tests/test_notifier.py`，並新增 formatter-to-notifier contract smoke。

### v19.5 QA 驗證矩陣建議

| 編號 | 場景 | 風險 | 最小預期 | 建議測試 |
| --- | --- | --- | --- | --- |
| V19.5-QA-01 | 摘要最後送出 | Telegram 契約回退 | `messages[-1]` 包含 `v19.5`、`今日結論`、`明日執行清單` | formatter test |
| V19.5-QA-02 | reply_markup 綁定 | 按鈕跑到詳情段 | `send_many()` 只對最後摘要段帶 markup | notifier + contract smoke |
| V19.5-QA-03 | 多風控持倉 | 風控漏看 | STOP / REDUCE / TAKE_PROFIT / 新倉風控優先進執行清單；超量有索引 | summary view model unit |
| V19.5-QA-04 | 風控超過 5 項 | 靜默截斷 | 顯示前 5 項且提示另有 N 項見詳情 | summary formatter test |
| V19.5-QA-05 | 合格 BUY | 等待狀態覆蓋買點 | BUY 進執行清單前段；不顯示為等回測 / 可準備 | derived state unit |
| V19.5-QA-06 | RR 不足但強勢 | 等待被誤解成可買 | 顯示 `等RR修復 / 不追價 / 買點：不買` | formatter test |
| V19.5-QA-07 | 過熱強勢股 | 追高風險 | 顯示等冷卻 / 等回測，不進可買 | formatter test |
| V19.5-QA-08 | 弱勢淘汰多檔 | 不可追溯 | 漏斗顯示淘汰數，詳情或統計行保留名稱與主因 | formatter test |
| V19.5-QA-09 | 低優先級壓縮 | 12 檔消失 | 全部 watchlist 標的可在摘要 / 詳情 / 壓縮列表追溯 | snapshot-like test |
| V19.5-QA-10 | 回測略優 | 回測產生 BUY | 只影響同類排序，不改 decision / is_tradeable / best candidate | strategy invariance test |
| V19.5-QA-11 | 摘要長度 | Telegram 截斷 | summary 低於 3500 字，或有明確 split 規則 | length smoke |
| V19.5-QA-12 | 無持倉 | 空狀態誤導 | 明日執行清單以候選為主，仍說明無持倉 | formatter test |
| V19.5-QA-13 | 無追蹤候選 | 空狀態誤導 | 顯示僅處理持倉 / 無新追蹤 | formatter test |
| V19.5-QA-14 | position_events 缺失 | 新倉 / 減碼誤判 | 安全回退，不硬判新倉或減碼後 | formatter fixture |
| V19.5-QA-15 | generate fallback | 下游格式破壞 | `generate()` 仍可 join list，`generate_report()` tuple 不變 | contract test |

### 最小測試分層建議

- L1 必跑：
  - `tests/test_generator_report.py`
  - `tests/test_notifier.py`
  - 新增 summary view model unit tests。
  - formatter-to-notifier contract smoke。
- L2 條件觸發：
  - 若新增 read-only loader 或跨日追蹤讀取，跑對應 store / loader tests。
  - 若調整 snapshot payload 或 signal fields，跑 snapshot / validator tests。
- L3 條件觸發：
  - 只有改到 `services/analysis.py`、DB payload、replay/backfill scripts、正式寫庫流程，才做 full pytest + replay/backfill dry-run。

### QA 對 PM / Tech 結論的修正建議

- PM 的 `明日執行清單最多 5 項` 需要補上「超過 5 項時如何追溯」。
- PM 的 `弱勢淘汰預設只統計` 需要補上「名稱與主因不可消失」。
- PM 的 `可準備分數` 應改名或加註為 `不可買的準備度`，避免被理解成買入建議。
- Tech 的 view model 方向正確，但必須讓 QA 可直接測 `execution_items`、`unheld_funnel`、`detail_index`，不要只輸出字串。
- Tech 不應在 v19.5 修改 `services/notifier.py`，除非 summary split 規則需要；若修改，必須升級契約驗證。

### QA 結論

- v19.5 可進入正式 TASK，但 QA 建議標記為 minor + 預設 L3；若 Architect 明確限定不改策略 / DB / replay，可將實測收斂為「L2 顯示不變性 + contract」。
- QA 不接受只做 formatter 片段測試。v19.5 的核心風險是摘要壓縮後的誤讀與 Telegram 發送契約回退，必須加入直接消費者 contract tests。
- QA 對 PM / Tech 方向給 conditional approval：可以做，但 TASK 必須把風控不可漏看、等待不可誤解、低優先級可追溯、summary/reply_markup 不回退列為硬驗收。

## Architect Conclusion

- PM / Tech / QA 已完成 v19.5 報文與策略體驗強化研究。Architect 判斷：研究階段足夠，下一步可交 PM 正式改寫 `TASK.md`。

### Owner 補充約束

Owner 指出 v19.4.1 的短摘要 / 持倉處理區少了目前收益情況，導致無法一眼看到每檔持倉目前是賺是虧。這不是可壓縮資訊，v19.5 必須修正。

硬性要求：

- `✅ 明日執行清單` 中的所有持倉項必須保留目前收益百分比。
- 收益顯示格式沿用既有摘要語意，例如：`英業達｜+20.04%｜核心風控｜守 59.0`。
- 新倉風控、減碼後觀察、核心風控、洗盤續抱、續抱觀察都必須帶收益百分比。
- 未持倉項不需要收益百分比，但必須保留等待 / 不買語意。
- 壓縮摘要不得刪除持倉盈虧，因為盈虧是持倉處理優先級的重要判斷上下文。

### Architect 判斷

- v19.5 定位：`收盤決策壓縮與執行清單升級`。
- v19.5 可進入正式 TASK，但必須限定為顯示 / 排序 / summary view model，不改策略 action。
- 必做能力：
  - `🧭 今日結論`
  - `✅ 明日執行清單`
  - `未持倉漏斗`
  - `📎 詳情索引`
  - 持倉執行清單保留目前收益百分比
- 不可變更：
  - 不改 `services/analysis.py` 的交易 action。
  - 不改 RR / 過熱 / 漲停不追 / 加碼 / 停利 / 停損硬門檻。
  - 不改 DB schema。
  - 不擴大股票池。
  - 不改 replay/backfill。
- QA 要求需納入 TASK：
  - 風控不可漏看。
  - 等待標的不可被誤解為可買。
  - 低優先級標的不可完全消失。
  - summary 必須仍是 `messages[-1]`。
  - `reply_markup` 必須仍綁在最後摘要段。
  - 持倉執行清單必須保留收益百分比。
- 測試等級：v19.5 是 minor，預設 L3；若 Owner 明確限定不改策略 / DB / replay，實測可收斂為 `L2 顯示不變性 + Telegram contract`，但不得低於 L2。

## Next Action

- 轉 PM 正式改寫 `TASK.md`。
- `TASK.md` 必須使用 PM Findings 的產品方向，並合併 Tech / QA / Owner 補充約束。
- `TASK.md` 必須明確寫入：
  - 持倉執行清單保留收益百分比。
  - 最多 5 項時，若風控超量需顯示另有 N 項見詳情。
  - 弱勢淘汰可壓縮但名稱與主因不可消失。
  - `可準備` / `等回測` / `等RR修復` 必須保持不可買語意。
  - summary last 與 reply_markup last contract 不可回退。
