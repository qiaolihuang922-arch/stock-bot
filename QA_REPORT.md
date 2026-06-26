# QA_REPORT: telegram_readability_risk_wording_20260626

## 測試範圍

- 持倉減碼 final card。
- 已跌破警戒/停損 next-step 語氣。
- 未持倉過熱與突破失敗 final card。
- brief summary 無新倉原因。
- 今日買入覆蓋加碼的 summary/card 一致性。

## 關聯風險掃描

- 減碼股數來自既有 `holding_decision["shares"]` 與 `holding["shares"]`，未改策略。
- 未傳 `data` 的 helper 呼叫仍保留舊語氣，避免破壞外部舊呼叫。
- 過熱只在 `title_label == 過熱觀察` 且 state 被顯示成 `等量能` 時改主狀態，不影響正常量能等待。
- 突破失敗仍是等待站回，不轉成可買。

## 跨區塊語意一致性

- 持倉卡片、風險依據、盤中處理一致使用已跌破/未跌破語氣。
- Summary 補充無新倉原因，和未持倉卡片的等待/淘汰狀態一致。
- 盤中風控清單標為優先順序，避免與持倉卡順序被誤讀為矛盾。

## 使用者誤讀風險

- 已降低：`減碼 50%` 現在可直接看到建議賣出股數。
- 已降低：已跌破警戒不再看起來像還沒跌破。
- 已降低：過熱標的不再因量能 gate 被誤讀為只差量能即可買。
- 已降低：突破失敗明確需站回加量能確認。

## 失敗標本反證

- Owner 建準類型 failure specimen 已用 final position card fixture 反證：
  - `減碼基準：總倉 550股｜建議賣 275股（50%）｜目標剩 275股`
  - `已跌破警戒 143.23，先減碼；跌破停損 138.71 停損`
  - 不含 `跌破警戒 143.23 續減`
- Owner 旺宏/聯電類型 failure specimen 已用 final unheld card 反證：
  - `重新站回突破區 175.5~176.38 + 量能確認後再評估`
- 過熱等待 regression 保持 `等冷卻` / `等回測`，不顯示可買語氣。

## 質疑與反證

- 質疑: 是否只改 helper，final 報文沒變？
  - 反證: tests 直接檢查 `formatTelegramPositionCard` / `formatTelegramUnheldCard` / `formatTelegramMessages` 輸出。
- 質疑: 是否改了策略？
  - 反證: 僅改文案分流與 formatter 顯示，沒有修改 signal 產生或 DB path。
- 質疑: 是否 full regression 全過？
  - 反證: 未宣稱。全檔 `tests/test_generator_report.py` 仍失敗，列為既有舊文案預期與本輪外風險。

## 未測項目

- 未發 live Telegram。
- 未讀寫 production DB。
- 未跑全套通過；`tests/test_generator_report.py` full file 尚有舊預期失敗。
- CAO PM/Tech/QA runner 未能啟動，原因是本機缺 `tmux`。

## QA 結論

conditional pass。

條件：本輪 Owner 指出的手機閱讀問題已由 focused final-output tests 覆蓋並通過；全檔舊文案預期與 CAO runner gap 需另輪清理。
