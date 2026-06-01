# QA_REPORT:

## 測試範圍

- 任務：`telegram-evidence-human-readable-v20.4.17`
- 任務尺寸 / QA：`normal_patch / L2`
- 驗證範圍：Telegram 第三則「簡報＋資料依據」人話化、版本 `v20.4.17`、完整三則 message list、formatter / sample 測試。
- 未做 DB write、live Telegram、replay、backfill、full pytest。

## 關聯風險掃描

- `TASK.md / CHANGELOG.md / diff` 一致：只改第三則資料依據、版本與測試；未見策略 decision、候選分類、DB schema/write path、live delivery 修改。
- `formatTelegramMessages` 仍輸出三則主體順序：持倉 -> 未持倉 -> 簡報＋資料依據；`include_detail=True` 才追加備份訊息。
- 第三則資料依據三段成立：市場 / 題材背景、策略樣本、持倉 / 價格 / 候選資料。
- `git diff --check`：passed。
- `py_compile core/generator.py services/notifier.py`：passed。
- Scoped tests：`tests/test_generator_report.py tests/test_market_theme_evidence.py tests/test_notifier.py`：120 passed，169 warnings。

## 跨區塊語意一致性

- 第一、二則仍保留持倉 / 未持倉主體；第三則承擔資料依據用途。
- 第三則 market/theme 文案包含可靠度與限制，例如資料不足時「只作觀察，不作買點」，有支持時覆蓋「不等於買點」。
- strategy sample 不可用時，第三則使用人話「可靠度低，未納入買賣判斷」，不再輸出 raw status 或 backtest source。
- 持倉 / 候選資料文案說明可支持風控 / 分類，以及缺資料標的保守處理，不輸出 raw source/status。

## 使用者誤讀風險

- 已按手機閱讀順序檢查完整三則：持倉 -> 未持倉 -> 簡報＋資料依據。
- 第三則沒有把市場 / 題材背景寫成「推薦理由」或「有效進場」；決策簡報仍可出現「新倉：無有效進場」。
- QA 自補負面樣本把 full_msg 與 market/strategy input 塞入 raw 工程語、ISO timestamp、不可用 strategy sample；第三則仍通過 forbidden-term / ISO scan，且未出現可買。

## 質疑與反證

- 反證：完整三則 sample 中，第三則不含 `production`、`runtime`、`production DB`、`classification backtest`、`source-of-truth`、`available`、`derived`、`as_of`、`source_status`、`missing-source`、`source-error`、`insufficient-data`、`fail-closed` 或 ISO timestamp。
- 反證：strategy sample 明確不可用時，第三則只顯示未納入買賣判斷，不顯示 backtest/source-of-truth/fail-closed raw 語。
- 反證：market/theme 缺可靠來源時第三則顯示背景不足與不作買點，未生成新倉可買語意。

## 未測項目

- 未做 production DB read-only smoke，因本輪驗收可由 formatter sample / fixtures 覆蓋，且不需要 DB/write/live Telegram。
- 未跑 full pytest、replay、backfill；依 `normal_patch / L2` 不擴大。
- 未檢查其他非第三則區塊是否仍有既有工程診斷文字；本輪只約束第三則。

## QA 結論

通過
