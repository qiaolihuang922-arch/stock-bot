# CHANGELOG: telegram_all_cards_institutional_trading_20260626

## 修改內容與修改檔案

- `presentation/report.py`
  - 新增三大法人買賣超 formatter helper。
  - 持倉卡固定插入 `昨日三大法人買賣超：...`。
  - 未持倉卡固定插入 `昨日三大法人買賣超：...`。
  - 支援 top-level / `result` 內多種三大法人 payload key 與中英文欄位別名。
- `tests/test_generator_report.py`
  - 新增持倉/未持倉無資料仍硬輸出 `資料不足` 的 final card 測試。
  - 新增有三大法人資料時格式化外資/投信/自營/合計的 final card 測試。

## 契約影響

- 所有股票卡片增加一行 `昨日三大法人買賣超：...`。
- 缺資料時 fail closed 為 `資料不足`。
- 不改策略 signal、payload shape、DB 寫入或 live delivery。

## 版本同步

- 使用者可見版本仍為 `v21.1`。
- 未修改 `generator.VERSION`。

## 直接消費者同步

- Telegram 持倉卡與未持倉卡同步。
- Summary / future-watch 不新增此欄位。

## 未影響模組

- 無 production DB schema/write/backfill/delete。
- 無 live Telegram。
- 無三大法人資料抓取器新增。

## 自檢命令與結果

- `python -m pytest tests/test_generator_report.py::GeneratorReportTest::test_all_stock_cards_hard_output_yesterday_institutional_trading tests/test_generator_report.py::GeneratorReportTest::test_institutional_trading_line_formats_three_major_values tests/test_generator_report.py::GeneratorReportTest::test_reduce_card_shows_share_basis_and_current_warning_breach tests/test_generator_report.py::GeneratorReportTest::test_failed_breakout_card_does_not_show_attack_volume_as_positive`
  - Result: `4 passed`
- `python -m pytest tests/test_generator_report.py -k "institutional_trading or reduce_card_shows_share_basis or failed_breakout_card_does_not_show_attack_volume_as_positive or today_buy_holding_overrides_add_level_in_all_summary_surfaces or overheat_pullback_display_switches_from_cooling_to_retest"`
  - Result: `6 passed, 229 deselected`

## 覆蓋層級

- formatter helper: 三大法人買賣超 line parser/formatter。
- final card: `formatTelegramPositionCard`, `formatTelegramUnheldCard`。
- production source: 未讀寫 production DB，未 live delivery。

## 殘留風險

- 專案目前沒有正式三大法人資料抓取源；有資料時可顯示，無資料時只會顯示 `資料不足`。
- CAO runner 仍因缺 `tmux` 無法啟動正式 agent flow，本輪沿用本地等價流程。
