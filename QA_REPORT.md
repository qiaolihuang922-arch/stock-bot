# QA_REPORT:

## 測試範圍

- 任務：`tg-evidence-short-ux-v20.4.13`
- 任務尺寸 / QA：`tiny_patch / L1`，驗證範圍限於第三則 Telegram short/evidence、三則訊息順序、版本字串、missing-source fail-closed；未擴成 full replay / backfill / production write。
- 讀取：`TASK.md`、`CHANGELOG.md`、git diff、`core/generator.py`、相關測試檔。
- 可吸收 diff：`core/generator.py`、`tests/test_generator_report.py`、`tests/test_market_theme_evidence.py`、`TASK.md`、`CHANGELOG.md`、`QA_REPORT.md`；均與本任務範圍相關。

## 風險預算與停止條件

- 風險 1：第三則仍洩漏 raw/debug evidence。驗證：掃 diff、跑禁止詞測試、補 sector-only market/theme probe。停止條件：第三則不含指定 raw terms。
- 風險 2：第三則順序或手機閱讀路徑被改壞。驗證：完整三則 messages index 檢查。停止條件：持倉 first、未持倉 second、簡短證據摘要 third。
- 風險 3：missing-source 被自然語言包裝成推薦。驗證：策略樣本 unavailable / price missing cases、sector-only WAIT sample。停止條件：仍 fail-closed、無可買文案、策略 decision 不被升級。

## 關聯風險掃描

- `TASK.md`、`CHANGELOG.md`、diff 口徑一致：版本升 `v20.4.13`，只改第三則 short/evidence 與必要測試；未見 DB schema/write、策略 decision、payload shape 擴大。
- `core/generator.py` 主要改動：`VERSION = "v20.4.13"`；第三則 Evidence Compact 改為自然語言「簡短證據摘要」；`format_telegram_short_report_message()` 過濾 `Source：核心價格`、`證據日期：`、`來源：`、`趨勢：` 與 `latest_trade_date/lookback_range/source_of_truth/db_table`。
- `formatTelegramMessages()` 仍 append：持倉、未持倉、short/evidence；`include_detail=True` 時 Details Backup 仍在最後。
- `git diff --check`：passed。
- `py_compile core/generator.py services/notifier.py`：passed。

## 跨區塊語意一致性

- 主倉測試：`PYTHONPATH=. PYTHONPYCACHEPREFIX=/private/tmp/stock_main_pycache arch -arm64 .venv/bin/python -m pytest -q tests/test_generator_report.py tests/test_market_theme_evidence.py tests/test_notifier.py`：119 passed，169 warnings。
- QA 獨立測試：`arch -arm64 .venv/bin/python -m pytest -q tests/test_generator_report.py tests/test_market_theme_evidence.py`：116 passed，169 warnings。
- QA 補充反證 probe：手造 market/theme 只有 `sector_index` 的 sample；raw summary 原本可產生 `證據日期`、`來源：sector_index`、`latest_trade_date`、`Source：核心價格`，第三則輸出禁止詞命中為空。
- 順序：第 1 則 `【持倉標的】`、第 2 則 `【未持倉標的】`、第 3 則含 `簡短證據摘要`。
- 原 sample decision 維持 WAIT/action 0，未出現可買、建議買入或立即進場。

## 使用者誤讀風險

- 手機閱讀順序符合 TASK：持倉 first、未持倉 second、short/evidence third。
- 第三則保留決策短訊與自然語言證據摘要，不要求 Owner 從 table/file/key/date 流水自行推理。
- 前兩則卡片內既有 `Source：price/OHLCV/RR...` 屬 card-level source 契約，本輪非目標；QA 未把它當第三則 raw evidence 洩漏。

## 質疑與反證

- 質疑：只移除 Evidence Compact heading，但 summary 前半仍可能帶 raw market/theme 來源行。反證：sector-only probe 證明 raw summary 有 `來源：sector_index/latest_trade_date`，第三則經 formatter 後無命中。
- 質疑：策略樣本 unavailable 但 payload 內仍是 BUY/action 0.1，formatter 可能造假成可買。反證：測試與 probe 均顯示第三則 `新倉無有效進場`，rendered messages 無可買推薦文案。
- 質疑：改第三則時影響前兩則或 message list。反證：完整三則與 detail 模式測試均檢查 messages index；前兩則仍各自為持倉 / 未持倉。

## 未測項目

- 未做 live Telegram delivery。
- 未做 production DB write、backfill、全量 replay。
- 未跑 full repo pytest；依 `tiny_patch / L1` 只跑 task 直接相關 tests 與補充 formatter probe。
- 未驗證 Telegram 實機渲染；本輪以 message text 順序與內容契約驗收。

## QA 結論

通過
