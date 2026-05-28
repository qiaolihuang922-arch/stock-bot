# TASK: Telegram Holding Risk / Tomorrow Plan Noise Reduction v20.1.3

## 任務狀態

- task_id: telegram-holding-risk-tomorrow-plan-dedupe-v20-1-3
- 任務類型: tiny_patch
- 狀態: ready
- 版本建議: patch，使用者可見 Telegram 報文變更，版本升為 v20.1.3
- QA 分級建議: L1
- 理由: 只改 Telegram formatter / tests，不改策略 decision、資料來源、DB payload 或排程。
- L1 必須包含 formatter snapshot、接近真實手機長報文 fixture、Telegram message list / notifier 直接消費者 smoke、手機閱讀順序檢查。
- 不升 L2，除非 Tech 實作碰到策略 action、持倉 decision 來源、payload shape 或非 formatter 公用契約。

## Owner 問題

Owner 在 v20.1.2 Telegram 報文中看到同一檔持倉的同一個降級 / 風控行動跨區塊重複：

- 持倉風控檢查 已寫：智原 / 緯創 明日未修復降級
- 隔日計畫 又寫：收盤未修復，列入明日降級檢查

手機閱讀時這兩段表達同一個行動，造成噪音，且讓 隔日計畫 看起來像沒有提供新資訊。

本輪要降低 Telegram 手機報文噪音：同一檔同一風控 / 降級行動只能出現一次；明日相關區塊只保留真正不同於風控檢查的待觸發事項。

## 使用者可見結果

Owner 手機打開 Telegram 後，閱讀順序應是：

1. Header 顯示 v20.1.3
2. Summary 先看今日結論 / 新倉是否可買
3. 再看今日交易紀錄或已執行項
4. 再看 持倉風控檢查
- 智原 / 緯創這類「未修復降級」只在這裡出現一次
5. 最後才看 明日計畫
- 只放真正不同的待觸發事項，例如技嘉 待觸發加碼10
- 若沒有非風控的明日事項，整個 明日計畫 區塊不輸出

Owner 不應再看到同一檔股票在 持倉風控檢查 與 隔日計畫 / 明日計畫 中用不同話術重複同一個降級檢查。

## 非目標

- 不改策略 decision。
- 不改持倉 action 判斷來源。
- 不改加碼 / 減碼 / 停損 / 降級規則。
- 不改 DB schema、DB payload、cache、watchlist。
- 不改 market theme evidence provider / source family 判定。
- 不做 live Telegram delivery。
- 不做 live Supabase write。
- 不做 replay / backfill。
- 不重新設計整份 Telegram 報文結構。

## 影響模組

- 直接模組:
- Telegram formatter / summary 組裝邏輯
- 報文區塊生成 helper
- formatter snapshot / regression tests
- 可能涉及但只能作為直接消費者 smoke:
- Telegram message list 產生器
- notifier last-message / send payload 測試

## 直接消費者

- Owner 手機 Telegram 報文。
- Telegram message list contract。
- notifier / Telegram payload 直接消費者。
- formatter snapshot tests。
- QA 手機閱讀 fixture。

## 輸出契約

### 版本契約

- 本輪必須升為 v20.1.3。
- Telegram header / formatter VERSION 或等價使用者可見版本常量必須同步。
- 測試期望中的 header 版本也必須同步。
- 不得回退到 v20.1.1 或 v20.1.2 header。

### 區塊契約

- 不再輸出獨立標題 隔日計畫。
- Canonical tomorrow section 使用 明日計畫。
- 持倉風控檢查 承擔持倉風控 / 降級 / 未修復檢查。
- 明日計畫 只承擔非重複的待觸發事項，例如：
- 待觸發加碼10
- 待觸發加碼20
- 待觸發加碼30
- 其他不是同一檔同一風控 / 降級行動的明日觸發項
- 若 明日計畫 沒有非重複事項，整個區塊不輸出。

### 去重契約

同一檔股票在同一份報文中：

- 若 持倉風控檢查 已輸出 明日未修復降級、未修復降級檢查、收盤未修復降級 或同義風控行動，明日計畫 不得再次輸出同一行動。
- 不得用改寫話術規避去重，例如：
- 明日未修復降級
- 收盤未修復，列入明日降級檢查
- 明日降級檢查
以上對同一檔視為同一風控 / 降級行動。
- 非同一行動可以保留，例如同一檔若有 PM 明確定義的非風控待觸發加碼事項，才可進 明日計畫；本輪不得自行新增這種策略含義。

### 不得回退既有契約

本輪不得破壞 v20.1.1 / v20.1.2 已修契約：

- 未持倉短買點句仍要短，先呈現 不買 / 不可買 / 等條件。
- 盤後明日加碼語意仍為 待觸發加碼10/20/30，不得回到 明日風控｜加碼10。
- 盤後報文不得再出現未收盤語意 若收盤。
- 淘汰 / 不可買文案不得回到 不代表看空產業。
- 不得輸出 明日風控｜加碼10。
- market theme evidence 行仍必須在新倉結論後。
- report-derived only evidence 不得變成 confirmed。
- confirmed market theme 不得放寬個股買點或讓不可買變可買。

## 驗收條件

1. v20.1.3 報文 header 正確顯示。
2. 智原 / 緯創類 fixture 中，持倉風控檢查 已有 明日未修復降級 時，明日計畫 不得再出現同一檔的 收盤未修復，列入明日降級檢查 或同義句。
3. 若所有明日項目都只是持倉風控重複項，明日計畫 區塊不輸出。
4. 若有真正不同的明日待觸發事項，例如技嘉 待觸發加碼10，明日計畫 仍輸出且只包含該類非重複事項。
5. 手機閱讀順序中，Owner 不需要在兩個區塊比對同一檔同一降級行動。
6. 持倉風控檢查 與 明日計畫 的分類名稱、數量、股票名單不得互相矛盾。
7. Telegram message list / notifier 直接消費者仍能取得最後一則完整報文，不因移除空區塊而破壞 payload。
8. 已修契約不得回退：短買點句、待觸發加碼10、無 若收盤、無 不代表看空產業、無 明日風控｜加碼10、market theme evidence 在新倉結論後、report-derived only 不得 confirmed。
9. 不改策略 decision、DB/schema/cache、watchlist、live Telegram/Supabase、backfill。

## 範例或 fixture

### Fixture A: 只有重複風控項

輸入語意：

- 智原: 持倉，未修復，需明日降級檢查
- 緯創: 持倉，未修復，需明日降級檢查
- 沒有非風控明日待觸發事項

期望輸出形狀：

【05/28 盤後｜v20.1.3】

...今日結論 / 新倉結論...

持倉風控檢查
- 智原：明日未修復降級
- 緯創：明日未修復降級

...詳情...

不得出現：

隔日計畫
- 智原：收盤未修復，列入明日降級檢查
- 緯創：收盤未修復，列入明日降級檢查

也不得出現空的：

明日計畫

### Fixture B: 風控項 + 真正明日觸發項

輸入語意：

- 智原: 持倉，未修復，需明日降級檢查
- 緯創: 持倉，未修復，需明日降級檢查
- 技嘉: 持倉，非風控待觸發加碼10

期望輸出形狀：

【05/28 盤後｜v20.1.3】

...今日結論 / 新倉結論...

持倉風控檢查
- 智原：明日未修復降級
- 緯創：明日未修復降級

明日計畫
- 技嘉：待觸發加碼10

...詳情...

不得把智原 / 緯創重複放進 明日計畫。

## 明確禁止事項

- 禁止修改策略 decision、持倉 action 優先級、加碼 / 降級判斷規則。
- 禁止修改 DB schema、DB payload、cache、watchlist。
- 禁止新增 live Telegram delivery、live Supabase write、正式 backfill。
- 禁止改 market theme evidence confirmed 條件。
- 禁止讓 report-derived only evidence confirmed。
- 禁止回退 v20.1.1 / v20.1.2 手機降噪與 evidence contract。
- 禁止把 明日計畫 當成風控檢查的第二份摘要。
- 禁止用同義句跨區塊重複同一檔同一風控 / 降級行動。
- 禁止為了通過測試刪掉必要的非重複明日觸發事項，例如技嘉 待觸發加碼10。

## 阻塞條件

- Tech 發現去重需要改策略 decision 或 action 來源，而不只是 formatter 分流時，必須 blocked。
- Tech 發現現有資料無法區分「風控降級」與「非風控明日觸發」時，必須 blocked，回報需要的欄位或分類契約。
- 若版本常量位置不明，或 Telegram header 不是由 formatter 控制，必須 blocked。
- 若測試 fixture 無法覆蓋接近真實手機長報文，QA 不得通過。
- 若移除 隔日計畫 會導致真正不同的明日待觸發事項消失，必須 blocked 或 conditional pass，不能直接吸收。

## PM 自檢

- 已列使用者可見結果: 是。
- 已列非目標: 是。
- 已列影響模組: 是。
- 已列直接消費者: 是。
- 已列輸出契約: 是。
- 已列版本契約: 是，升為 v20.1.3。
- 已列手機閱讀路徑與示例輸出形狀: 是。
- 已列驗收條件: 是。
- 已列禁止事項與阻塞條件: 是。
- 公開來源: 本任務為 Owner 指定的既有 Telegram 報文降噪 patch，未使用新增公開網路資料。
