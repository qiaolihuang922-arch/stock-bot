# QA_REPORT: presentation_noise_reduction_v20_4_31

## 測試範圍

- 任務尺寸 / QA：normal_patch / L2。
- 驗證範圍：presentation/message list、手機閱讀順序、section visibility、卡片降噪、B5 split。
- 未執行：full pytest、production read-only smoke、replay、backfill、live Telegram delivery。

## 關聯風險掃描

- 可吸收 diff：`CHANGELOG.md`、`core/generator.py`、`presentation/report.py`、`tests/test_generator_report.py`。
- `core/generator.py` 只改 `format_cross_day_tracking_summary()` signature 與文案：`追蹤最強` -> `僅追蹤`。
- `presentation/report.py` 只改 summary 合併、卡片 history/backtest hidden helper、data basis abnormal visibility。
- 未碰 DB schema/write path、RR 公式、production backfill、live Telegram。
- VERSION 保持 `v20.4.31`。

## 跨區塊語意一致性

- 無有效進場時不再輸出 `追蹤最強` / `🔥 最強`，改為 `僅追蹤` 並標 `未達進場條件`。
- 市場/結論與原因/風險已合併；舊 `🧭 今日結論`、`🧭 原因`、`🔥 最強` 不再作為 summary 主輸出。
- 正常資料源：盤中與盤後簡報不顯示 `資料依據`。
- 異常資料源：盤後 source-error 顯示單一 `簡報＋資料依據`，`策略樣本：` count 為 1。
- B5：`隔日確認 1、等冷卻 1、等回測 1` 與卡片 `隔日確認 / 等冷卻 / 不可追高觀察` 一致。

## 使用者誤讀風險

- 無有效進場時不再出現偽推薦感的 `追蹤最強`。
- 交易執行仍保留短資訊，不把持倉風控整句重複成新增下單。
- 卡片不可用回測/歷史行被隱藏，避免逐卡 `不可用` 噪音。

## 質疑與反證

- `test_presentation_noise_intraday_no_valid_entry_uses_track_only_without_data_basis`
- `test_presentation_noise_afterhours_normal_sources_hide_data_basis`
- `test_presentation_noise_afterhours_source_error_shows_single_data_basis`
- `test_presentation_noise_card_history_unavailable_hidden_across_cards`
- `test_b5_tracking_split_matches_card_states_and_tracking_total`
- 結果：5 passed，13 warnings。
- 既有手機路徑 probes：3 passed，25 warnings。
- `git diff --check`：passed。

## 未測項目

- 未跑 full pytest。
- 未做 production read-only smoke、replay、backfill、live Telegram。
- 未驗未來新增 source status 名稱。

## QA 結論

通過
