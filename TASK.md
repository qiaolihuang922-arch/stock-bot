# TASK: 持倉風控檢查完整列出全部持倉

## 任務狀態

- task_id: holdings-risk-list-no-truncation-20260602
- 任務類型: normal_patch
- 狀態: ready_for_tech
- 版本建議: 使用者可見 Telegram 報文變更，需檢查並同步報文版本字串
- QA 分級建議: L2

## Owner 問題

上一輪任務因 stale Tech worktree 阻塞，需要重跑。Telegram 第三則「持倉風控檢查」目前只列前 5 筆，之後顯示「另有 N 項持倉風控見詳情」之類截斷提示。Owner 要求：有幾個持倉就完整列幾個，不顯示截斷提示。

## 使用者可見結果

手機閱讀 Telegram 第三則「持倉風控檢查」時：

- 6 檔以上持倉全部列出。
- 不出現「另有」、「見詳情」等持倉風控列表截斷提示。
- 列表排序仍與持倉卡 / detail index 一致。

## 非目標

- 不改 strategy decision。
- 不改持倉排序規則。
- 不改主行動判斷。
- 不改 RR 計算或顯示語意。
- 不改 DB schema / write path。
- 不做 live Telegram delivery。
- 不改未持倉漏斗、可買 / 可準備 / 僅追蹤 / 淘汰邏輯。
- 不做報文全量重設或清理。

## 影響模組與直接消費者

- 影響模組: Telegram 報文第三則「持倉風控檢查」列表渲染上限、截斷文案、相關測試 / probe。
- 直接消費者: Owner 手機端閱讀 Telegram 報文第三則；QA 手機閱讀 probe；既有持倉卡 / detail index 對照測試。

## 輸出契約

- 「持倉風控檢查」列表應輸出全部持倉項目，筆數等於本次報文輸入的持倉數。
- 不得再依固定上限只顯示前 5 筆。
- 當持倉數大於 5 時，不得輸出「另有 N 項」、「見詳情」或等價截斷提示。
- 單筆持倉既有欄位、格式、主行動、風控語意不得變更。
- 列表排序必須沿用既有持倉卡 / detail index 順序，不新增排序規則。
- 已存在且不得回退的契約:
- 同一持倉在同一份報文只能有一個主行動。
- 持倉卡、持倉風控檢查、detail index 的同一持倉順序與索引語意需一致。
- 無關區塊不得新增空區塊、0-count 或下單占位。
- 使用者可見版本字串不得與實際報文內容不一致。

## 版本契約

- 這是使用者可見 Telegram 報文變更。
- Tech 必須確認報文 header / version constant 是否需要升版；若既有規則要求報文內容變更即升版，必須同步。
- 不得因「只改列表上限」而讓版本字串與實際報文契約不一致。

## 驗收條件

- 建立或更新可重跑手機閱讀 probe：輸入至少 6 檔持倉時，「持倉風控檢查」列出全部 6 檔以上持倉。
- Probe 需明確反證第三則不含「另有」與「見詳情」截斷提示。
- Probe 需驗證持倉風控檢查排序仍與持倉卡 / detail index 一致。
- 既有 Telegram 報文測試仍通過。
- 不得出現 strategy decision、主行動、RR、DB schema/write、未持倉漏斗相關 diff，除非只是測試 fixture 必要欄位且不改語意。

## 範例或 Fixture

手機閱讀示例形狀：

持倉風控檢查
1. AAPL ...
2. MSFT ...
3. NVDA ...
4. TSLA ...
5. AMD ...
6. META ...

不得出現：

另有 1 項持倉風控見詳情

Fixture 要求：

- 至少 6 檔持倉。
- 持倉卡 / detail index / 持倉風控檢查三者可比對同一順序。
- 不需要 live Telegram、不需要 production write。

## 明確禁止事項

- 禁止改 strategy decision、買賣 / 加減碼 / 停損停利判斷。
- 禁止改持倉排序規則。
- 禁止改主行動判斷。
- 禁止改 RR。
- 禁止改 DB schema、RLS、grant、policy、role、index / constraint 或 write path。
- 禁止 live Telegram delivery。
- 禁止改未持倉漏斗。
- 禁止把本輪擴成報文全量重構或清理任務。

## 阻塞條件

- 找不到「持倉風控檢查」第三則的可測渲染入口。
- 無法建立 6 檔以上持倉的可重跑 fixture / probe。
- 無法判定持倉卡 / detail index 的既有排序來源。
- 版本字串規則不明且會造成使用者可見契約不一致時，需交回 Architect 補充。

## 本輪停止條件

完成到以下範圍即停止：

- 第三則「持倉風控檢查」完整列出全部持倉。
- 6 檔以上 probe 通過，且無「另有」/「見詳情」截斷提示。
- 排序與持倉卡 / detail index 一致。
- 相關既有測試通過並完成 QA L2 驗收。

旁支問題只記待辦，不納入本輪：

- 其他 Telegram 區塊的文案整理。
- 未持倉漏斗或策略分類調整。
- 持倉卡格式重設。
- 報文整體清理或版本治理重構。
