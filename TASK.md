# TASK: Next Evidence Chain Development

## 任務狀態

- task_id: `next_evidence_chain_development`
- 任務類型: `risk_patch`
- 狀態: `ready_for_pm`
- 版本建議: 若使用者可見報文文案或結構變更，升 patch version。
- QA 分級: L2；若改 DB write path、策略核心或 schema，升 L3。

## Owner 問題

證據鏈已能讀 production market/theme evidence，但使用者仍需要它在報文中產生「看得懂、可執行但不誤導」的策略輔助效果。

## 已完成前置

- 05/31 假日报文重複第二段停利已修。
- production market/theme 2026-05 history 已存在並通過 audit。
- generator 已消費 production `market_theme_confirmed_evidence` history。
- `策略證據 v20.0` 已和 market/theme evidence 分層。

## 本輪目標

PM 需先定義下一階段 evidence chain 的使用者可見契約：

- market/theme evidence 要如何影響 Summary / 強勢準備 / 風險提示 / 題材說明。
- evidence confirmed 只能作背景與排序提示，不得直接放寬買點。
- report 要清楚區分：
  - 市場/題材 production evidence。
  - strategy sample / classification backtest evidence。
  - 個股買點、持倉與風控決策。

## 非目標

- 不新增 DB schema，除非 Owner 先審 SQL。
- 不 live Telegram。
- 不把 evidence confirmed 直接變成 BUY。
- 不用 runtime/local/worktree 假資料補 confirmed。
- 不回頭處理 05/31 重複停利，除非 regression。

## 驗收方向

- 手機閱讀順序：Summary -> 強勢準備/可準備 -> 持倉風控 -> evidence blocks。
- 沒有可買時仍明確寫「新倉：無有效進場」。
- evidence 文案能回答：
  - 市場/題材是否支持？
  - 支持來自哪個 trade_date / lookback_range？
  - 支持是否足以追高？答案必須保守。
- QA 必須補一個使用者誤讀反證：production confirmed 不能被讀成「現在可買」。
