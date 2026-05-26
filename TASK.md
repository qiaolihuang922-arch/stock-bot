# TASK: 修復 Telegram 短報文未持倉漏斗數量誤讀

## 任務狀態

- task_id: telegram_short_unheld_funnel_count_fix_20260526
- 任務類型: patch / Telegram formatter 顯示 bug
- 狀態: ready_for_tech
- 版本建議: patch
- QA 分級建議: L1，因涉及 Telegram 短報文輸出契約與使用者誤讀風險，QA 必須補手機閱讀路徑與直接消費者檢查

## Owner 問題

Telegram 短報文的「未持倉漏斗（非執行）」目前可能把「僅追蹤總數」與其內部子分類拆分同時視覺上加總，造成 Owner 在手機上誤讀為未持倉數量超過實際 watchlist 剩餘檔數。

具體問題場景：

- watchlist 共 12 檔
- 已持倉 5 檔
- 未持倉實際應為 7 檔
- 短報文若顯示成類似 僅追蹤 7 + 冷卻 3 + 回測 2 + RR 1 + 量能 1，會讓人誤以為未持倉可加總為 14 檔
- 正確語意應是：未持倉總數 7 檔，其中 7 檔再拆成冷卻 / 回測 / RR / 量能等子分類

## 使用者可見結果

Owner 在手機 Telegram 打開短報文時，看到的「未持倉漏斗（非執行）」必須先清楚看到：

1. 已持倉與未持倉總數不會超過 watchlist 總數
2. 未持倉總數是一個總量
3. 冷卻 / 回測 / RR / 量能是未持倉總數底下的拆分，不是額外可加總項
4. 短報文不會暗示有超過 12 檔股票可被執行或加碼

手機閱讀路徑：

- 第一眼先看到今日是否有新倉可買
- 接著看到持倉處理優先級
- 再看到未持倉漏斗，該區塊必須以「未持倉 N 檔」作為總數
- 子分類必須用縮排、括號、破折號或其他清楚格式表達「其中拆分」
- 不得讓 Owner 需要心算才能知道冷卻 / 回測 / RR / 量能是否包含在未持倉總數內

## 非目標

本輪不做：

- 不改策略判斷
- 不改買入 / 賣出 / 加碼 / 淘汰規則
- 不改 DB schema
- 不改 Supabase 寫入
- 不改 watchlist 來源或 12 檔清單
- 不改行情來源
- 不改 replay / backfill 流程
- 不做 live Telegram delivery
- 不做 live Supabase write
- 不改長報文語意，除非短報文 helper 共用格式時需同步避免同一 bug

## 影響模組

直接影響模組：

- core/generator.py
- Telegram short summary / short report formatter 相關測試

可能關聯但本輪不應改變策略輸出的模組：

- services/analysis.py
- core/condition_engine.py
- core/watchlist.py

## 直接消費者

直接消費者：

- Telegram 短報文生成流程
- Owner 手機 Telegram 閱讀短報文
- 任何依賴短報文文字 snapshot / formatter helper 的測試

Tech 必須確認 formatter 變更後，直接呼叫短報文生成的路徑仍能取得相同 message list / payload 結構；本輪只允許改文字呈現，不允許改變 Telegram payload 外層結構。

## 輸出契約

本輪只改「未持倉漏斗（非執行）」的顯示語意。

必要契約：

- 已持倉數 + 未持倉總數 不得顯示成超過 watchlist 總數
- 僅追蹤 或等價總分類若代表未持倉總數，不得再與冷卻 / 回測 / RR / 量能並列成可加總同層項
- 冷卻 / 回測 / RR / 量能必須顯示為未持倉總數底下的子分類拆分
- 子分類數量合計應等於未持倉總數；若存在其他未持倉狀態，需顯示 其他 N 或等價拆分，避免合計失真
- 可買 / 準備 / 僅追蹤 / 不可行動仍須分開，不得混在同一行
- 不得把 等冷卻 顯示為 等回測，或把任何子分類放到錯誤分組
- 不得新增看似推薦買入的文案

可接受的短報文形狀之一：

未持倉漏斗（非執行）
未持倉 7 檔，僅追蹤不可買
其中：等冷卻 3、等回測 2、等RR修復 1、等量能 1

不可接受形狀：

未持倉漏斗（非執行）
僅追蹤 7｜等冷卻 3｜等回測 2｜等RR修復 1｜等量能 1

原因：這會讓手機閱讀者把 7 與子分類數字並列加總，誤讀成超過實際未持倉 7 檔。

## 驗收條件

1. 在 fixture 為 watchlist 12 檔、已持倉 5 檔、未持倉 7 檔時，短報文不得出現可被解讀為 7 + 子分類 的同層並列格式。
2. 同一 fixture 中，短報文必須清楚顯示未持倉總數為 7 檔。
3. 同一 fixture 中，冷卻 / 回測 / RR / 量能子分類合計必須等於 7，或若有其他狀態，必須有明確 其他 N 拆分。
4. Telegram short report 的 message list / payload 外層結構不得改變。
5. 策略輸出、分類判斷、watchlist、DB 寫入與 live Telegram/Supabase 路徑不得改變。
6. 測試需覆蓋「已持倉 5、未持倉 7」的誤讀回歸案例。
7. QA 必須用接近真實手機長度的短報文檢查閱讀順序，確認 Owner 不會把未持倉子分類加總成超過 12 檔。

## 範例或 fixture

建議 fixture：

- watchlist_total: 12
- held_count: 5
- unheld_total: 7
- unheld_breakdown:
- 等冷卻: 3
- 等回測: 2
- 等RR修復: 1
- 等量能: 1
- buyable_new_positions: 0

期望短報文示例輸出形狀：

今日新倉：無有效進場，不可買
持倉：5 檔，先看停損 / 減碼 / 加碼提示

未持倉漏斗（非執行）
未持倉 7 檔，僅追蹤不可買
其中：等冷卻 3、等回測 2、等RR修復 1、等量能 1

詳情見下方個股卡片

若子分類超過手機單行可讀長度，可接受換行：

未持倉漏斗（非執行）
未持倉 7 檔，僅追蹤不可買
其中：
等冷卻 3｜等回測 2
等RR修復 1｜等量能 1

## 明確禁止事項

- 禁止改策略邏輯
- 禁止改 DB schema 或 DB payload
- 禁止改 watchlist
- 禁止 live Telegram delivery
- 禁止 live Supabase write
- 禁止正式 backfill
- 禁止把冷卻 / 回測 / RR / 量能當成未持倉總數外的額外分類
- 禁止用「僅追蹤 N」與子分類同層並列造成可加總誤讀
- 禁止刪除 8 份固定 Markdown 工作流文件
- 禁止 Tech 自行擴大到長報文重設計或策略分類調整

## 阻塞條件

若 Tech 發現以下任一情況，必須 blocked 並回報，不得自行補產品決策：

- 現有短報文沒有可辨識的未持倉總數來源
- 子分類可能重疊，無法保證合計等於未持倉總數
- 同一股票可能同時落入冷卻 / 回測 / RR / 量能多個分類，導致無法用拆分方式呈現
- formatter 目前無法取得 held_count / watchlist_total / unheld_total 任一必要數字
- 修改短報文必須連帶改變 strategy output、DB payload 或 Telegram payload 外層結構
