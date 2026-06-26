# TASK: telegram_readability_risk_wording_20260626

## 任務狀態

- task_id: `telegram_readability_risk_wording_20260626`
- 任務類型: `normal_patch`
- 狀態: `implemented_QA_conditional_pass_pushed`
- 版本建議: `v21.1`
- QA 分級: `L2`

## Owner 問題

Owner 貼出的 06/26 盤中 v21.1 完整報文有手機閱讀誤判風險：持倉減碼 50% 未說明賣出股數/基準、已跌破警戒仍寫成未來「跌破警戒續減」、未持倉過熱卻顯示「等量能｜過熱觀察」、突破失敗看起來仍可準備、summary 未說明無新倉原因。

## 使用者可見結果

- 減碼卡片顯示總倉、建議賣出股數、減碼比例與目標剩餘股數。
- 已低於警戒/停損時，盤中處理改用「已跌破」語氣，不再寫成未來條件。
- 過熱未持倉卡片主狀態優先顯示 `等冷卻｜過熱觀察`。
- 突破失敗觸發條件加入「不追」與量能確認。
- summary 的無新倉行補上原因：持倉風控優先、未持倉僅追蹤/淘汰。
- 盤中風控清單標題標明是「風控優先順序」，避免與持倉卡片順序誤讀。

## 非目標

- 不改持倉策略、加減碼判斷、停損停利核心。
- 不改 DB schema / DB write / backfill。
- 不發 live Telegram。
- 不重寫 full `tests/test_generator_report.py` 既有舊文案預期。

## 影響模組與直接消費者

- `core/generator.py`: 持倉 next-step 文案依即時價格分流。
- `presentation/report.py`: Telegram summary、持倉卡、未持倉卡 formatter。
- `tests/test_generator_report.py`: final-card/message regression。
- 直接消費者: Owner 手機 Telegram 報文、official formatter/message list。

## 輸出契約

- `REDUCE_25/REDUCE_50` 卡片須可見 `減碼基準：總倉 X股｜建議賣 Y股（25%/50%）｜目標剩 Z股`。
- 現價低於警戒時，減碼處理須輸出 `已跌破警戒 ...，先減碼`，不得輸出同價位 `跌破警戒 ... 續減`。
- 現價低於停損時，處理須輸出 `已跌破停損 ...，優先停損`。
- 過熱 blocker 與 `等量能` 同時存在時，標題主狀態須以 `等冷卻` 為主。
- 突破失敗等待須顯示站回區間後仍需量能確認，不得像可買訊號。
- brief summary 若無新倉，須保留 `新倉：無有效進場` 並補原因。

## 版本契約

- 使用者可見版本維持 `v21.1`。
- 本輪是可見報文契約修正，不升策略版本、不改 DB contract。

## 驗收條件

- Owner failure specimen 對應矛盾可由 final-card/message tests 反證。
- Focused regression 必須通過：
  - 減碼股數/已跌破警戒 final position card。
  - 突破失敗 unheld final card。
  - 今日買入覆蓋加碼 summary/card。
  - 過熱等待 card。
- 若 full `tests/test_generator_report.py` 因既有舊文案預期失敗，必須明確列為未測/殘留風險，不得宣稱 full suite passed。

## 範例或 fixture

- 建準 fixture：550股、今日買30股、REDUCE_50 建議賣275股、價格142.25、警戒143.23、停損138.71。
- 旺宏 fixture：FAILED_BREAKOUT，站回區 175.5~176.38，需量能確認。

## 失敗標本與驗收路由

- Failure specimen: Owner 06/26 盤中完整報文。
- 驗收路由: `formatTelegramMessages` / `formatTelegramPositionCard` / `formatTelegramUnheldCard` final output，不得只驗 helper。

## 禁止事項與阻塞條件

- 不得用 synthetic helper 結果宣稱手機報文完成。
- 不得更動 live Telegram 或 production DB。
- 若減碼股數來源缺失，不得硬造股數；缺資料時應不顯示基準或 fail closed。
