# TASK: telegram_all_cards_institutional_trading_20260626

## 任務狀態

- task_id: `telegram_all_cards_institutional_trading_20260626`
- 任務類型: `normal_patch`
- 狀態: `implemented_QA_conditional_pass_pushed`
- 版本建議: `v21.1`
- QA 分級: `L2`

## Owner 問題

Owner 要求報文中每一檔股票都硬輸出昨日三大法人買賣超；修正範圍不是只有買檔，而是持倉與未持倉所有股票卡片。

## 使用者可見結果

- 每張持倉卡與未持倉卡都顯示 `昨日三大法人買賣超：...`。
- 若 payload 有三大法人資料，顯示外資、投信、自營與合計。
- 若 payload 沒有資料，仍硬輸出 `昨日三大法人買賣超：資料不足`，不得默默省略或偽裝為 0。

## 非目標

- 不新增 production DB schema。
- 不寫 production DB。
- 不發 live Telegram。
- 不在本輪新增三大法人抓取/backfill；只定義與呈現報文欄位。

## 影響模組與直接消費者

- `presentation/report.py`: 持倉與未持倉 Telegram card formatter。
- `tests/test_generator_report.py`: final card regression。
- 直接消費者: Owner 手機 Telegram 報文。

## 輸出契約

- 每張股票卡必須有一行以 `昨日三大法人買賣超：` 開頭。
- 支援 payload keys: `institutional_trading`, `three_major`, `three_major_institutional`, `institutional_investors`, `legal_person_trading`。
- 同名 key 可在 top-level 或 `result` 內。
- 支援欄位別名：
  - 外資: `foreign`, `foreign_investor`, `foreign_net`, `外資`, `外資買賣超`
  - 投信: `investment_trust`, `trust`, `trust_net`, `投信`, `投信買賣超`
  - 自營: `dealer`, `dealer_net`, `proprietary`, `自營`, `自營商`, `自營商買賣超`
  - 合計: `total`, `total_net`, `net_total`, `合計`, `三大法人合計`
- 若沒有合計且三項皆為 numeric，formatter 可自動加總。
- 預設單位為 `張`；payload 可用 `unit` 覆蓋。

## 版本契約

- 使用者可見版本維持 `v21.1`。
- 本輪只改報文顯示契約，不改策略版本。

## 驗收條件

- 持倉 final card 無資料時仍顯示 `昨日三大法人買賣超：資料不足`。
- 未持倉 final card 無資料時仍顯示 `昨日三大法人買賣超：資料不足`。
- 未持倉 final card 有資料時顯示外資/投信/自營/合計。
- 既有報文 readability focused regression 不被破壞。

## 範例或 fixture

- 無資料 fixture: 持倉技嘉、未持倉建準，兩者都顯示資料不足。
- 有資料 fixture: 建準 `foreign=1200`, `investment_trust=-300`, `dealer=50`，輸出合計 `+950張`。

## 失敗標本與驗收路由

- Owner correction: `是每一檔股票`。
- 驗收路由: final `formatTelegramPositionCard` / `formatTelegramUnheldCard` output。

## 禁止事項與阻塞條件

- 缺資料時不得輸出 0 或空白。
- 不得只在買檔/可買檔輸出。
- 不得 live Telegram。
