# CHANGELOG:

## 修改內容

- 修正盤中報文持倉 detail card 的 `下一步` 舊時間語意：`新倉風控觀察` / `續抱觀察` 相關路徑不再輸出 `隔日未修復，降低優先級`，改為 `盤中先觀察，未修復再降級`。
- 補強 generator 測試，確認持倉 detail card 與整份盤中 message 的持倉詳情都不含 `明日未修復` / `隔日未修復`。
- 保持 `v20.0.11`，未更動策略、DB、watchlist、Telegram payload shape 或 message list 順序。

## 修改檔案

- `core/generator.py`
- `tests/test_generator_report.py`
- `CHANGELOG.md`

## 契約影響

- 使用者可見 Telegram 文案改變：持倉 detail card 的 `下一步` 不再使用 `明日未修復` / `隔日未修復` 舊語意。
- 未改函式回傳結構、message list 順序、Telegram payload shape、報文分組或 public helper signature。
- `隔日計畫` 區塊標題與 `若收盤仍未修復：...列入隔日降級檢查` 條件句維持既有契約；本輪只移除 summary/detail card 內的舊長句噪音。

## 版本同步

- `core/generator.py` 既有 `VERSION = "v20.0.11"` 維持不變。
- 本輪未升版也未回退，符合 Architect 指令「保持 v20.0.11」。

## 直接消費者同步

- `formatTelegramPositionCard()` 直接消費者已同步：Owner 手機 Telegram 持倉 detail card 經由 `formatTelegramMessages()` 產生時會套用新 `下一步` 文案。
- `tests/test_generator_report.py::GeneratorReportTest::test_new_position_risk_watch_takes_precedence_over_add_signal` 已同步直接 card 斷言，確認 `下一步：盤中先觀察，未修復再降級` 且不含舊字樣。
- `tests/test_generator_report.py::GeneratorReportTest::test_intraday_v20_0_11_followup_review_contract` 已同步長報文 fixture，確認 summary 與持倉 message 均不含 `明日未修復` / `隔日未修復`。

## 未影響模組

- 未改 `services/analysis.py` 策略決策。
- 未改 `core/condition_engine.py` 條件映射。
- 未改 DB schema / migrations / Supabase write path。
- 未改 watchlist。
- 未改 replay/backfill。
- 未執行 live Telegram delivery。
- 未執行 live Supabase write。
- 未執行正式 backfill。

## 已跑自檢命令

- `PYTHONPATH=/private/tmp/stockbot_test_config:$PWD arch -arm64 .venv/bin/python -m pytest tests/test_generator_report.py -q`
  - 結果：`44 passed, 21 warnings`
- `.venv/bin/python -m pytest tests/test_generator_report.py -q`
  - 結果：失敗於 collection，原因是 `.venv` 指向主 repo arm64 虛擬環境，但目前 shell 的 Python 需要 x86_64 `pydantic_core`；已依既有 QA/runner 模式改用 `arch -arm64` 重跑並通過。

## 殘留風險

- 未執行 full pytest、replay/backfill dry-run、live Telegram delivery 或 live Supabase write；依本輪禁止事項未執行。
- `holding_tomorrow_trigger()` 仍保留內部判斷用的 `明日未修復降級` 字串，用於產生有條件的 `隔日計畫` 候選；summary 已清洗為 `盤中觀察修復狀況` / `隔日計畫` 條件句，detail card 已改為盤中語意。
