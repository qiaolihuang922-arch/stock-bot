# QA_REPORT:

## 測試範圍

- 依據 `TASK.md`、`CHANGELOG.md`、候選 diff 驗證本輪 patch：Telegram header / `VERSION` 由 `v20.0.12` 升到 `v20.0.13`，並保留 evidence blocker 負面語意。
- 可吸收候選 diff：
  - `core/generator.py`
  - `tests/test_generator_report.py`
  - `tests/test_notifier.py`
  - `CHANGELOG.md`
- 實測命令：
  - `arch -arm64 .venv/bin/python -m pytest tests/test_generator_report.py::GeneratorReportTest::test_intraday_v20_0_12_separates_mainline_from_execution tests/test_generator_report.py::GeneratorReportTest::test_intraday_v20_0_12_hot_market_without_ai_evidence_uses_neutral_mainline tests/test_generator_report.py::GeneratorReportTest::test_intraday_v20_0_13_legacy_market_summary_cannot_confirm_theme tests/test_notifier.py -q`
  - 結果：`6 passed, 13 warnings`
- 補充 Owner 手機閱讀順序 smoke：直接呼叫 `formatTelegramMessages()`，驗證最後一則 summary header 為 `【05/28 盤中｜v20.0.13】`，前 9 行未出現 forbidden confirmed bullish 文案；結果通過。
- broader related smoke：`arch -arm64 .venv/bin/python -m pytest tests/test_generator_report.py tests/test_notifier.py -q`
  - 結果：`47 passed, 3 failed, 21 warnings`
  - 3 個失敗為既有 / 殘留 phase-sensitive 測試，未固定 `get_market_phase()` 時輸出 `明日觸發` / `明日未修復`，舊斷言期待 `盤中觸發` / `盤中觀察修復狀況`。

## 關聯風險掃描

- `core/generator.py`：
  - `VERSION = "v20.0.13"`，符合本輪 patch 版本契約。
  - `ai_supply_chain_mainline_supported()` 新增 explicit evidence token gate；只有題材 keyword 加 explicit token 才能輸出 `主線：AI / 電子供應鏈仍偏多。`
- `tests/test_generator_report.py`：
  - header 期望已同步 `v20.0.13`。
  - 新增 legacy market summary 負面 fixture，驗證無 explicit source 時不能 confirmed。
- `tests/test_notifier.py`：
  - 新增 `send_many()` 直接消費者測試，確認 summary 作為最後一則送出且保留 `v20.0.13` header。
- 未見 DB schema、watchlist、scheduler、live Telegram sender、Supabase write path diff。
- 本輪不是清理 / 瘦身 / refactor 任務，path / claim / evidence / risk / action 證據表不適用。

## 跨區塊語意一致性

- Owner 手機閱讀順序檢查：
  - 最後一則 summary 第一行為 `【05/28 盤中｜v20.0.13】`。
  - 市場段落顯示 `進攻偏熱｜R3`，但主線降級為 `市場偏多但買點未成立`。
  - 執行段落顯示 `新增買點未成立，等觸發，不追高`。
  - 新倉段落顯示 `無有效進場`。
  - `🔥 最強` 顯示 `無有效進場標的`。
- 負面 fixture 中未出現：
  - `AI / 電子供應鏈仍偏多`
  - `AI 題材偏多`
  - `電子供應鏈偏多`
  - `v20.1.0`
- summary、header、notifier last message 的版本語意一致；未看到把「追蹤 / 等待」誤包成「可買」的本輪新增問題。

## 使用者誤讀風險

- 本輪目標風險已被控制：無 explicit evidence 時，Owner 不會在手機 summary 第一屏看到 AI / 電子供應鏈 confirmed bullish。
- Header 顯示 `v20.0.13`，避免同一可見版本停在舊行為。
- 殘留風險：
  - `market_theme_evidence:confirmed`、`source:`、`來源:`、`confirmed`、`證據確認` 目前是字串 token gate，不是真正 evidence payload/schema。
  - 本輪不能被解讀成已建立 `v20.1.0` 題材證據鏈或正式 evidence provider。
  - broader formatter suite 的 3 個 phase-sensitive failures 涉及「盤中 / 明日」文案；非本輪修改，但屬使用者可見語意，建議另開任務固定 phase。

## 質疑與反證

- PM 是否漏需求：本輪 TASK 限定 patch、版本契約、notifier 直接消費者、evidence 負面 fixture，未要求 full evidence provider；可接受。
- Tech 是否漏同步：`core/generator.py` 版本常量為 `v20.0.13`，相關 formatter / notifier 測試已同步，未發現程式測試仍期待 `v20.0.12`。
- 測試是否能證明沒有破壞直接消費者：已補 notifier `send_many()` last-message 消費者測試與直接 `formatTelegramMessages()` 手機閱讀 smoke，不只重跑 Tech 單一 formatter assertion。
- QA 主動反證路徑：使用舊 `market_summary="AI / 電子供應鏈仍偏多"` 且無 explicit token 的高熱市場 fixture 檢查 summary，確認不會輸出 AI / 電子供應鏈 confirmed bullish，也不會把不可買誤讀成可買。

## 未測項目

- 未執行 full pytest、replay/backfill dry-run、live Telegram delivery、live Supabase write；符合 TASK 禁止事項與 L1 停止條件。
- 未驗證真正 evidence provider / schema / cache，因本輪不是 `v20.1.0` 新能力發布。
- 未修 broader formatter suite 的 3 個 phase-sensitive failures；QA 只標記為殘留，不視為本輪可吸收 diff 的阻塞。

## QA 結論

conditional pass

條件：可吸收本輪限定 diff（`core/generator.py` 版本與 evidence gate、相關 formatter / notifier tests、`CHANGELOG.md`），但不得宣告 broader formatter suite 全綠；3 個既有 / 殘留 phase-sensitive 測試失敗需另開任務處理或由 Architect 明確接受為本輪非阻塞殘留。
