# CHANGELOG:

## 修改內容

- Telegram formatter 可見版本由 `v20.1.1` 升至 `v20.1.2`。
- `formatTelegramSummary()` 的 market theme evidence 行改到今日結論、主線/執行、新倉語意之後，避免手機第一屏先看到題材偏多。
- 新增 `build_market_theme_evidence_provider()` 作為 production formatter provider / adapter；existing `market_theme_evidence` dict 會重新拆回 source family 後由 `build_market_theme_evidence()` 驗證，不再直接信任 `confirmed` 欄位。
- `ai_supply_chain_mainline_supported()` 改走 normalized evidence，避免 malformed report-derived only dict 讓主線句輸出 `AI / 電子供應鏈仍偏多`。
- market theme evidence object 補上 `level`、`as_of`、`source_family_details`、`supports_claims`，保留既有 `theme_status` / `confirmed` / `source_families` 欄位供現有測試與 formatter 消費。
- 保留 v20.1.1 手機降噪契約：短買點句、`待觸發加碼10`、移除 `若收盤`、移除 `不代表看空產業`、禁止 `明日風控｜加碼10`。

## 修改檔案

- `core/market_theme_evidence.py`
- `core/generator.py`
- `tests/test_market_theme_evidence.py`
- `tests/test_generator_report.py`
- `tests/test_notifier.py`
- `CHANGELOG.md`

## 契約影響

- Telegram header / formatter 可見版本改為 `v20.1.2`。
- Telegram summary 文字順序有變更：market theme evidence 行仍在 summary，但位於今日結論、主線/執行、新倉之後。
- `build_market_theme_evidence_provider()` 新增 public helper；輸出仍是 structured evidence object，且 malformed existing dict 只能被重新驗證為 weak / absent / stale，不可只靠既有 `confirmed: true` 成為 confirmed。
- `format_market_theme_summary_lines()` 使用手機短句：confirmed 顯示 `市場題材：...證據偏多，但買點仍看個股條件`；weak 顯示 `市場題材：來源不足，僅追蹤`。
- 未改 Telegram message list 型別、notifier payload shape、DB payload、策略 decision、watchlist 或交易建議邏輯。

## 版本同步

- `core/generator.py` 已同步 `VERSION = "v20.1.2"`。
- `tests/test_generator_report.py`、`tests/test_market_theme_evidence.py`、`tests/test_notifier.py` 已同步 header 期望為 `v20.1.2`。

## 直接消費者同步

- Owner 手機 Telegram summary：`tests/test_market_theme_evidence.py` 與 `tests/test_generator_report.py` 已檢查 evidence 行出現在 `🧭 新倉：無有效進場。` 之後。
- Formatter message list：`formatTelegramSummary()` / `formatTelegramMessages()` 維持 summary 為最後一則，僅調整 summary 內 market theme evidence 位置與文案。
- Telegram notifier / sender：`tests/test_notifier.py` 已同步最後 summary header 為 `v20.1.2`，`send_many()` 消費方式不變。
- Market theme direct consumer：`ai_supply_chain_mainline_supported()` 已同步改走 `market_theme_summary_evidence()` normalizer，避免主線句繞過 provider。
- QA fixture / snapshot：新增 malformed existing evidence dict 測試，確認 report-derived only malformed dict 不會 confirmed。

## 未影響模組

- 未改 `services/analysis.py` 策略 decision。
- 未改 `core/condition_engine.py` 條件映射。
- 未改行情來源、watchlist、scheduler / cron。
- 未新增 DB table / migration / cache。
- 未改 DB write path / payload schema。
- 未改 replay/backfill。
- 未執行 live Telegram delivery。
- 未執行 live Supabase write。
- 未執行正式 backfill。

## 已跑自檢命令

- `arch -arm64 .venv/bin/python -m pytest tests/test_generator_report.py tests/test_market_theme_evidence.py tests/test_notifier.py`
  - 結果：`62 passed, 21 warnings`。
- `rg -n "v20\\.1\\.1|若收盤|不代表看空產業|明日風控｜加碼|今日可追主線買進|AI / 電子供應鏈 confirmed 偏多|市場偏多，所以放寬買點|題材偏多，所以 RR" core tests`
  - 結果：產品碼與測試未殘留 `v20.1.1` 或禁止輸出語意；測試中只保留 `assertNotIn` 類禁止語意檢查。

## 殘留風險

- 本輪只修 QA 指出的 summary 順序與 provider normalizer，不新增 DB schema、cache、外部 provider 或 production history。
- Structured source family 的新鮮度仍以現有 runtime 傳入欄位判斷；缺欄位或 malformed source 會降級，但不主動補外部資料。
- 測試警告來自既有相依套件與 Python 版本 deprecation，非本輪新增失敗。
