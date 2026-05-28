# CHANGELOG:

## 修改內容

- Telegram formatter 可見版本由 `v20.1.0` 升至 `v20.1.1`。
- 收斂盤後明日計畫語意：持倉加碼項目改為 `待觸發加碼10/20/30`，不再把加碼歸為風控短句。
- 收斂持倉風控區：加碼持倉只保留 `風控：守警戒線，不追價`，避免與明日計畫重複完整加碼下一步。
- 收斂未持倉長卡買點句：等回測、等 RR、淘汰等不可買情境改為短句，先呈現 `不買 / 不可買 / 等條件`。
- 盤中隔日計畫不再使用未收盤假設語意；盤後路徑使用已知收盤語意 `收盤未修復，列入明日降級檢查`。
- 淘汰卡移除舊式產業 guard，改為單次短句 `產業：未判斷產業多空`。

## 修改檔案

- `core/generator.py`
- `tests/test_generator_report.py`
- `tests/test_market_theme_evidence.py`
- `tests/test_notifier.py`
- `CHANGELOG.md`

## 契約影響

- Telegram header / formatter 可見版本改為 `v20.1.1`。
- Telegram message list 仍維持原本結構：詳情訊息在前、summary 為最後一則，notifier `send_many()` 可照舊消費。
- 使用者可見文字有變更：summary / 明日計畫 / 持倉風控 / 未持倉卡 / 淘汰卡的文案更短，並移除本輪禁止語意。
- 未改 formatter 回傳型別、Telegram payload shape、DB payload、DB schema、策略 decision、watchlist 或 live delivery 行為。

## 版本同步

- `core/generator.py` 已同步 `VERSION = "v20.1.1"`。
- `tests/test_generator_report.py`、`tests/test_market_theme_evidence.py`、`tests/test_notifier.py` 已同步 header 期望為 `v20.1.1`。

## 直接消費者同步

- Telegram notifier / message sender：`tests/test_notifier.py` 已確認最後一則 summary 仍可由 `send_many()` 發送，且 header 為 `v20.1.1`。
- Owner 手機 Telegram 閱讀路徑：`tests/test_generator_report.py` 新增盤後加碼計畫 fixture，檢查 `待觸發加碼10`、持倉風控短句，以及禁止把加碼歸為風控與重複完整加碼下一步。
- Formatter message list / snapshot：既有 formatter tests 已同步不可買短句、淘汰產業 guard、盤中隔日計畫語意與版本字串。
- QA 使用的長報文形狀 fixture：`tests/test_generator_report.py` 中 v20 長報文情境已更新為短買點句與 `產業：未判斷產業多空`。

## 未影響模組

- 未改 `services/analysis.py` 策略 decision。
- 未改 `core/condition_engine.py` 條件映射。
- 未改行情來源、watchlist、scheduler / cron。
- 未新增 DB table / migration。
- 未改 DB write path / payload schema。
- 未改 replay/backfill。
- 未執行 live Telegram delivery。
- 未執行 live Supabase write。
- 未執行正式 backfill。

## 已跑自檢命令

- `arch -arm64 .venv/bin/python -m pytest tests/test_generator_report.py tests/test_market_theme_evidence.py tests/test_notifier.py`
  - 結果：`60 passed, 21 warnings`。
- `rg -n "v20\\.1\\.0|若收盤|不代表看空產業|明日風控｜加碼|買點：不買｜題材仍可追蹤|買點：不買｜.*技術觸發失效" core tests`
  - 結果：產品碼無命中；測試中僅保留 `assertNotIn` 禁止字串檢查。

## 殘留風險

- 本輪只收斂 Telegram formatter 呈現，不處理更上游的策略分類、持倉決策或證據鏈 provider。
- Summary 仍保留既有漏斗、索引、資料來源與部分舊版回歸區塊；本輪未做更大幅度的 message list 重排或刪段。
- 測試警告來自既有相依套件與 Python 版本 deprecation，非本輪新增失敗。
