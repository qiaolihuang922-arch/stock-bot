# RESEARCH.md

保存最新研究任務的高信號摘要，不保留完整聊天紀錄。

## Current Research Context

- 主題：DB / evidence chain 如何影響策略報文。
- 結論：DB 不是直接替代即時策略引擎；它優先承擔「記憶、證據、排序提示、去重、追溯」。
- 邊界：market/theme evidence confirmed 不能單獨把不可買改成可買，不能放寬追高限制。

## Data Roles

- `positions`：持倉 source-of-truth。
- `position_events`：已買 / 已賣 / 已停利 / 已減碼的 execution ledger；跨日防重必須用它。
- `daily_signal_snapshot`：每日當時版本留存，用於追溯，不要求舊月份回填 current version。
- `market_theme_confirmed_evidence`：production market/theme evidence，已用于報文中的市場/題材背景。
- `market_theme_index_daily_bars`：market/theme index source table，供 evidence / audit 使用。
- `sector_theme_members`：mapping，不是 daily history。

## Latest Evidence Chain State

- 2026-05 market/theme history 已入庫並通過 audit。
- generator 已消費 production `market_theme_confirmed_evidence`，不是 runtime/local 假資料。
- 05/31 假日报文已修：execution memory 與 evidence display 分層。

## Next Research / Product Question

下一步不是再證明資料表存在，而是定義 evidence 如何「有用但不誤導」：

- 怎樣把 market/theme trend 轉成 Summary / 強勢準備 / 風險提示？
- 怎樣讓使用者看到題材偏多，但仍知道不可追高？
- 怎樣區分 market/theme evidence、strategy sample evidence、個股買點？
- 需要哪些 QA 反證來避免 production confirmed 被讀成 BUY？
