# CHANGELOG:

## 任務尺寸與風險

- 任務尺寸：risk_patch。
- 風險判斷：使用者可見 Telegram 持倉卡與盤後簡報口徑修正，涉及 message list 文字契約與版本字串。
- 邊界：不改 DB schema、不做 live Telegram、不改 production write/backfill、不重設策略方向。

## 修改內容

- 對今日買入持倉且盤後當前不滿足買點的持倉卡，新增說明行，明確區分：
  - `strategy_intraday`：今日已執行，盤後已不在買點，不代表可繼續買。
  - `manual_or_ledger`：來源為手動/ledger，非當前策略買點。
  - `unknown`：來源未確認，且盤後不在買點，不得視為當前可買。
- 新增 formatter helper 判斷今日買入來源與 current can buy 狀態；來源不足時 fail closed 為 unknown。
- 使用者可見報文版本由 `v20.4.21` 升為 `v20.4.22`，並同步測試期望。
- 補上 2301 光寶科同型 fixture，覆蓋 50 股今日買入、弱勢、普通、遠離突破 5.43%、三種買入來源。
- 補上策略 probe：distance > 4 且弱勢 / 遠離突破不可通過 can_buy。

## 修改檔案

- `core/generator.py`
  - VERSION 升為 `v20.4.22`。
  - 新增 today buy source / current can buy helper 並注入 presentation deps。
- `presentation/report.py`
  - 持倉卡盤後路徑消費今日買入說明 helper。
- `tests/test_generator_report.py`
  - 覆蓋手機閱讀路徑：持倉卡、盤後簡報、禁止呈現為當前可買。
- `tests/test_analysis_engine.py`
  - 覆蓋 distance > 4 / weak / far-from-breakout 不可通過 can_buy。
- `tests/test_market_theme_evidence.py`
  - 同步版本契約。

## 最小改動策略

- 只在既有 Telegram presentation deps 增加今日買入來源說明 helper。
- 只在持倉卡盤後路徑插入一行說明，不重排 message list、不重構整體報文。
- 策略層只補 probe，未修改 can_buy 實作，因現有邏輯已擋 distance > 4。
- 測試版本字串為配合 VERSION 升版的直接同步。

## 契約影響

- 使用者可見報文版本：`v20.4.21` -> `v20.4.22`。
- 持倉卡輸出新增一行 `說明：...`，只限盤後、今日買入持倉、且當前不滿足買點。
- 第三則盤後簡報已沿用前一任務修正：今日已買持倉不再被寫成「今日無有效新倉」。
- message list 順序未改。
- payload shape 未改。
- DB schema / RLS / grant / policy / role / index / constraint 未改。
- DB write path、live Telegram delivery、backfill 未改。

## 直接消費者同步

- `presentation/report.py` 的持倉卡 renderer 已消費新的說明 helper。
- `formatTelegramMessages()` 盤後 message list 透過既有 deps 自動消費新行為。
- `tests/test_generator_report.py` 覆蓋 Owner 手機閱讀路徑。
- `tests/test_analysis_engine.py` 覆蓋策略 distance gate 不回退。

## 未影響模組

- 未改交易策略 ranking。
- 未改停損 / 停利 / 加減碼狀態機。
- 未改持倉資料讀取、production ledger 寫入或 DB 結構。
- 未改 Telegram delivery consumer。
- 未改未持倉漏斗分組邏輯。

## 已跑自檢命令

- `PYTHONPATH=. PYTHONPYCACHEPREFIX=/private/tmp/stock_tech_pycache arch -arm64 .venv/bin/python -m py_compile core/generator.py presentation/report.py tests/test_generator_report.py tests/test_analysis_engine.py tests/test_market_theme_evidence.py`：passed。
- `PYTHONPATH=. PYTHONPYCACHEPREFIX=/private/tmp/stock_tech_pycache arch -arm64 .venv/bin/python -m pytest -q tests/test_generator_report.py tests/test_analysis_engine.py tests/test_market_theme_evidence.py`：166 passed, 201 warnings。
- `git diff --check`：passed。

## 殘留風險

- 今日買入來源若上游未提供明確 buy_source，formatter 只能用既有 today_action 與 position_events 保守判斷；不足時會顯示 unknown fail closed。
- 未做 production read 或 live Telegram 驗證；本輪僅提供可重跑 fixture/probe 自檢。

## 旁支待辦

- 若需要更精準區分 runner strategy order 與手動 ledger order，需另開任務補上游持久 source-of-truth 欄位或 read-only artifact。
- 其他股票同型今日買入來源缺口未全量盤點，本輪只覆蓋 TASK 指定的 2301 類誤讀路徑。
