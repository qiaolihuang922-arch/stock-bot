# CHANGELOG:

## 修改內容

- Telegram formatter 可見版本由 `v20.1.2` 升至 `v20.1.3`。
- 盤後 summary 手機閱讀順序改為先輸出 `持倉風控檢查`，再輸出有非重複事項時的 `明日計畫 N`。
- `智原` / `緯創` 這類持倉未修復降級只保留在 `持倉風控檢查`，不再以 `隔日計畫` 或同義降級句重複輸出。
- `技嘉｜待觸發加碼10` 這類非重複明日觸發事項仍保留在 `明日計畫`。
- 盤後沒有非重複明日事項時，不輸出 `明日計畫 0`、`明日計畫：無新增下單`、`明日計畫\n無新增下單` 或 `隔日計畫`；詳情索引也不再顯示 `明日計畫 0`。
- 移除已無直接呼叫方的舊 `format_next_day_plan()` helper，避免舊 `隔日計畫` / 降級重複句型被重新接回輸出。

## 修改檔案

- `core/generator.py`
- `tests/test_generator_report.py`
- `tests/test_market_theme_evidence.py`
- `tests/test_notifier.py`
- `CHANGELOG.md`

## 契約影響

- Telegram header / formatter 可見版本改為 `v20.1.3`，未回退 `v20.1.1` / `v20.1.2`。
- Telegram summary 文字順序改變：盤後持倉風控檢查必須早於 `明日計畫 N`。
- Telegram summary 分組契約改變：不再輸出獨立 `隔日計畫`；`明日計畫` 只承載非重複 pending items，例如 `待觸發加碼10`。
- Telegram 詳情索引契約收斂：盤後 `pending_trade_items == 0` 時省略 `明日計畫 0`，避免空計畫被手機閱讀成隔日行動。
- 未改 Telegram message list 型別、notifier payload shape、DB payload、策略 decision、watchlist 或交易建議邏輯。

## 版本同步

- `core/generator.py` 已同步 `VERSION = "v20.1.3"`。
- `tests/test_generator_report.py`、`tests/test_market_theme_evidence.py`、`tests/test_notifier.py` 已同步 header 期望為 `v20.1.3`。

## 直接消費者同步

- Owner 手機 Telegram summary：新增盤後長 fixture，覆蓋 `智原` / `緯創` 持倉未修復降級先出現在 `持倉風控檢查`，且不進 `明日計畫`。
- Telegram message list contract：`formatTelegramMessages()` 仍維持 summary 為最後一則；只調整最後 summary 內區塊順序與空明日計畫輸出。
- Telegram notifier / sender：`tests/test_notifier.py` 已同步最後 summary header 為 `v20.1.3`，`send_many()` 消費方式不變。
- Formatter regression tests：保留 `技嘉｜待觸發加碼10` 進 `明日計畫`，並新增只有持倉風控時不得出現空 `明日計畫` / `隔日計畫` 的負面檢查。

## 未影響模組

- 未改 `services/analysis.py` 策略 decision。
- 未改 `core/condition_engine.py` 條件映射。
- 未改持倉 action 判斷來源、加碼 / 減碼 / 停損 / 降級規則。
- 未改 market theme evidence provider / source family 判定。
- 未改行情來源、watchlist、scheduler / cron。
- 未新增 DB table / migration / cache。
- 未改 DB write path / payload schema。
- 未改 replay/backfill。
- 未執行 live Telegram delivery。
- 未執行 live Supabase write。
- 未執行正式 backfill。

## 已跑自檢命令

- `arch -arm64 .venv/bin/python -m pytest tests/test_generator_report.py tests/test_market_theme_evidence.py tests/test_notifier.py`
  - 結果：`64 passed, 21 warnings`。
- `rg -n "v20\\.1\\.2|v20\\.1\\.1|隔日計畫|明日計畫 0|明日計畫：無新增下單|明日風控｜加碼|若收盤|不代表看空產業|收盤未修復，列入明日降級檢查|盤中觀察修復：.*收盤未修復" core tests`
  - 結果：產品碼未殘留舊版 header、舊 `隔日計畫` 輸出或禁止語意；命中皆為測試中的 `assertNotIn` 禁止檢查。
- `rg -n "format_next_day_plan" core tests`
  - 結果：無命中，舊 helper 已無呼叫方且已移除。

## 殘留風險

- 本輪只修 Telegram formatter 手機閱讀順序、空 `明日計畫` 輸出與直接測試；未做 QA 的完整驗收矩陣。
- 測試警告來自既有相依套件與 Python 版本 deprecation，非本輪新增失敗。
