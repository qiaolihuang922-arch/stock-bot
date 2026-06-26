# CHANGELOG: telegram_readability_risk_wording_20260626

## 修改內容與修改檔案

- `core/generator.py`
  - `holding_risk_next_step_text()` 新增 `data` 參數，依現價判斷是否已跌破警戒/停損。
  - 持倉 tomorrow/next-step 呼叫改傳入 `data`，讓 final 報文能用當下狀態文案。
- `presentation/report.py`
  - 盤中 execution 區塊標題改為 `今日盤中風控優先順序`。
  - 減碼持倉卡新增 `減碼基準` 行，顯示總倉、建議賣股數與目標剩餘。
  - 風險依據改分辨 `已低於警戒/停損` 與 `距警戒/停損`。
  - 過熱未持倉若被 `等量能` 搶主狀態，改回 `等冷卻`。
  - 突破失敗等待條件補 `不追` 與 `量能確認`。
  - brief 無新倉行補原因。
- `tests/test_generator_report.py`
  - 新增減碼股數與已跌破警戒 final card regression。
  - 更新突破失敗與今日買入 summary 可見文案預期。

## 契約影響

- 使用者可見 Telegram 報文更精準；策略 signal、payload shape、DB 寫入不變。
- `holding_risk_next_step_text()` public helper 兼容舊呼叫；未傳 `data` 時仍使用既有未跌破語氣。
- Message list 順序不變；summary 文字新增原因。

## 版本同步

- `v21.1` 維持不變。
- 本輪未修改 `generator.VERSION`。

## 直接消費者同步

- Telegram 持倉卡、未持倉卡、簡報 summary 均同步。
- QA 使用 final card/message tests 反證，不只驗 helper。

## 未影響模組

- 無 DB schema/write/backfill/delete。
- 無 live Telegram。
- 無 future-watch、MOPS、fundamentals 流程變更。

## 自檢命令與結果

- `python -m pytest tests/test_generator_report.py -k "holding_next_step_uses_risk_prices_not_breakout_zone or reduce_card_shows_share_basis or failed_breakout_card_does_not_show_attack_volume_as_positive or failed_breakout_within_reclaim_buffer_waits_reclaim_not_terminal_reject or overheat or today_buy"`
  - Result: `14 passed, 219 deselected`
- `python -m pytest tests/test_generator_report.py::GeneratorReportTest::test_reduce_card_shows_share_basis_and_current_warning_breach tests/test_generator_report.py::GeneratorReportTest::test_failed_breakout_card_does_not_show_attack_volume_as_positive tests/test_generator_report.py::GeneratorReportTest::test_today_buy_holding_overrides_add_level_in_all_summary_surfaces tests/test_generator_report.py::GeneratorReportTest::test_overheat_pullback_display_switches_from_cooling_to_retest`
  - Result: `4 passed`
- `python -m pytest tests/test_generator_report.py`
  - Result: `46 failed, 190 passed, 3 unhandled/uuu, 172 warnings`
  - 判讀: full file 仍有多個既有舊文案預期與本輪外的契約差異，未作為本輪通過證據。

## 覆蓋層級

- helper: `holding_risk_next_step_text`
- formatter: `formatTelegramPositionCard`, `formatTelegramUnheldCard`, `format_brief_data_evidence_message`
- official message list/final card: `formatTelegramMessages`
- production source: 未讀寫 production DB，未 live delivery

## 殘留風險

- `tests/test_generator_report.py` 全檔仍有既有舊文案預期失敗；本輪只覆蓋 Owner 指出的手機閱讀問題。
- CAO runner 因本機缺 `tmux` 無法啟動 PM stage；本輪改走本地等價流程並記錄 runner gap。
