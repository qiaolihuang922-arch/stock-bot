# CHANGELOG: 20260603_strategy_evidence_report_risk_patch

## 任務尺寸與風險

- 任務尺寸：risk_patch。
- 風險原因：本輪同時影響 strategy evidence 歷史取樣、Telegram 使用者可見報文分組，以及同日建倉 hard_stop / 快速止損風控顯示與主行動。

## 修改內容

- A1：`load_strategy_evidence_summary(limit=60)` 移除 `version` filter，改為跨版本歷史取樣。
- A1：`limit=60` 的語意改為最近 60 個 distinct `trade_date`，不是 60 rows；以 `range(start,end)` 分頁讀取 ordered rows，直到資料涵蓋超過 `limit` 個 distinct trade dates 或資料耗盡，再裁切成最近 60 個交易日。
- B1：`今日盤中交易執行` 只保留已執行 / 持倉動作；未持倉可買改列 `新倉建議`，並標示 `尚未買入`、`建議分批`。
- B2：Summary 的 `原因` / `風險` 拆成持倉與新倉對象，避免持倉和未持倉共用同一段長句。
- B3：未持倉非執行追蹤行抽成共用 formatter，盤中 / 盤後同步降噪；空交易執行不再顯示 `無新增下單`。
- B4：partial evidence modifier = 1.0 時顯示 `僅輔助參考`，不顯示 `+0%`。
- C：同日建倉若跌破 hard_stop、跌破入場價 3%，或跌破入場 K 棒低點，允許進入當日減碼；只破警戒但未達 hard_stop / 快速止損時維持新倉風控觀察。
- 版本同步：使用者可見報文版本升為 `v20.4.32`。

## 修改檔案

- `services/strategy_evidence.py`
- `core/generator.py`
- `presentation/report.py`
- `tests/test_strategy_evidence.py`
- `tests/test_generator_report.py`
- `tests/test_market_theme_evidence.py`

## 最小改動策略

- 沿用既有 evidence summary / report formatter / holding decision helper，只新增必要的分頁取樣 helper、新倉建議 helper、未持倉非執行行 helper、同日建倉風控 helper。
- A1 只修 history loading 契約，不改 scoring model、DB schema、DB write path 或 production backfill。
- B/C 只修使用者可見分組、原因風險拆分、partial 顯示與同日建倉 hard risk guard；不改 RR 公式。

## 契約影響

- `load_strategy_evidence_summary()` 回傳結構不變，但 public `limit` 語意由 row count 修正為 distinct `trade_date` history window。
- Telegram message list / 報文分組有變更：未持倉可買從 `今日盤中交易執行` 移到 `新倉建議`；空交易執行區塊不顯示無動作文案。
- 報文版本 header / artifact version 同步為 `v20.4.32`。
- Payload / DB：無新增 DB 欄位，無 schema / write 變更。

## 直接消費者同步

- `presentation/report.py` 已同步新倉建議、交易執行、原因 / 風險、未持倉非執行行。
- `tests/test_generator_report.py` 覆蓋盤中 / 盤後、新倉建議、partial evidence、同日建倉 hard_stop / 入場價 3% / 入場 K 棒低點 / 警戒緩衝。
- `tests/test_strategy_evidence.py` 覆蓋 `.range()` 分頁、無 `version` eq、高 row density 下最近 60 distinct trade dates。
- `tests/test_market_theme_evidence.py` 同步 `v20.4.32` 與新報文文案。

## 未影響模組

- 未改 RR 計算公式。
- 未改 DB schema、RLS、grant、policy、role、index、constraint。
- 未新增 production DB write path。
- 未執行 live Telegram delivery。
- 未做 production backfill。
- 未實作 D1 光寶科同日淘汰 -> 可買翻轉；維持 deferred。

## 已跑自檢命令

- `.venv/bin/python -m pytest tests/test_strategy_evidence.py`：13 passed。
- `arch -arm64 .venv/bin/python -m pytest tests/test_strategy_evidence.py tests/test_generator_report.py tests/test_market_theme_evidence.py`：201 passed，241 warnings。
- `PYTHONPYCACHEPREFIX=/private/tmp/tech_write_pycache arch -arm64 .venv/bin/python -m py_compile core/generator.py presentation/report.py services/strategy_evidence.py tests/test_generator_report.py tests/test_market_theme_evidence.py tests/test_strategy_evidence.py`：passed。
- `git diff --check`：passed。

## 殘留風險

- 一般 `.venv/bin/python` 在部分 shell 會用 x86_64 執行並撞到 arm64 `pydantic_core`；含 Supabase import 的 targeted tests 需使用 `arch -arm64 .venv/bin/python`。
- 若未來需支援非 Supabase-compatible query object，需另補明確 pagination contract；production Supabase path 預期支援 `.range()`。
- 未跑 full pytest、production smoke、正式 replay/backfill 或 live Telegram。

## 旁支待辦

- D1 光寶科同日淘汰 -> 可買翻轉另開任務確認真 bug、資料來源與使用者可見契約。
- 可另開 read-only artifact 驗證 production daily_signal_snapshot / daily_price 的實際 row density 與 pagination 成本。
