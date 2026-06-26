# TASK: telegram_mobile_readability_consolidation_20260626

## 任務狀態

- task_id: `telegram_mobile_readability_consolidation_20260626`
- 任務類型: `normal_patch`
- 狀態: `implemented_QA_pending_git`
- 版本建議: `v21.1`
- QA 分級: `L2`

## Owner 問題

Owner 貼出盤後完整報文並要求從使用者角度全部修復。主要痛點是手機閱讀仍太長、MOPS source-error 擋住第一眼、future-watch 財報區滑動太多、三大法人只有數字沒有判讀、盤後 summary 沒直接列出明日要賣多少股。

## 使用者可見結果

- MOPS source-error 不再顯示在未來30日關注訊息中；沒有可見資料時不產生空 future-watch message。
- `關注標的財報` 每檔壓成兩行：
  - `2356 英業達｜EPS 2026Q1 0.68｜營收 2026/05 +35.3%`
  - `昨日法人偏買：外+2,736｜投-102｜自-480｜合+2,153張`
- 三大法人加入 `偏買 / 偏賣 / 分歧` 判讀。
- 盤後 summary 新增 `明日優先`，直接列停損/減碼股數。
- 持倉風控檢查在盤後改成短股數口徑。
- 今日買入說明縮短，例如 `今日買入：手動/ledger，非策略買點`。

## 非目標

- 不改策略判斷。
- 不改資料來源與 DB。
- 不發 live Telegram。
- 不改持倉狀態機。

## 影響模組與直接消費者

- `core/future_watch.py`: future-watch formatter、法人判讀。
- `core/generator.py`: 今日買入短句、盤後持倉風控 checklist 股數口徑。
- `presentation/report.py`: 盤後 summary `明日優先`。
- `tests/test_generator_report.py`: owner specimen 對應 regression。
- 直接消費者: Telegram 持倉卡、盤後簡報、未來30日關注。

## 輸出契約

- Future-watch 不顯示 source-error 佔位。
- Future-watch 財報每檔最多兩行。
- 法人行格式：`昨日法人偏買/偏賣/分歧：外...｜投...｜自...｜合...張`。
- 盤後 summary 若有持倉風控，顯示 `明日優先：...`。
- 盤後持倉風控檢查顯示停損/減碼股數。

## 版本契約

- 使用者可見版本維持 `v21.1`。

## 驗收條件

- Future-watch / institutional / afterhours focused regression 通過。
- MOPS source-error 不出現在 output。
- 三大法人行有偏買/偏賣判讀。
- Summary 包含明日優先股數。
- 今日買入說明為短句。

## 範例或 fixture

- Owner specimen:
  - 建準、英業達停損；技嘉減碼。
  - Future-watch 12 檔財報與三大法人。
- Regression fixtures:
  - `test_afterhours_brief_does_not_call_all_risk_today_buys_established_new_positions`
  - `test_future_watch_institutional_trading_line_is_mobile_compact`
  - live-source related future-watch focused tests。

## 失敗標本與驗收路由

- Owner full afterhours report is the failure specimen.
- 驗收路由:
  - `formatTelegramMessages` -> summary/evidence message。
  - `formatTelegramPositionCard` -> 今日買入短句。
  - `format_future_watch_message` -> future-watch final message。

## 禁止事項與阻塞條件

- 不得用 source-error 佔位污染手機報文。
- 不得讓 future-watch 財報回到每檔 4 行以上。
- 不得把缺資料輸出成 0。
- 不得 live Telegram。
