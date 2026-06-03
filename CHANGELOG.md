# CHANGELOG: research_trend_continuation_phase1

## 任務尺寸與風險

- 任務類型：research。
- 風險原因：本輪讀 production DB 產出策略研究結論，但不改正式策略、報文或 DB。
- 未碰：`services/analysis.py`、`core/condition_engine.py`、`core/generator.py`、DB schema/write path、live Telegram。

## 修改內容

- 新增 `scripts/research_trend_continuation.py`
  - 只讀 `daily_price`，用 OHLCV 本地計算 ma5 / ma10 / ma20、vol_ratio、1/3/5/10 日 forward returns、MFE / MAE。
  - 分組輸出 `pullback_continuation` 與 `extended_spike` 1.08 / 1.15 / 1.22 對照組。
  - DB 憑證缺失、表不可讀、欄位缺失或資料不足時 fail closed，輸出 `status: blocked` 或 `insufficient-data`，不產生假 metrics。
- 新增 `tests/test_research_trend_continuation.py`
  - 覆蓋 pullback continuation fixture 分類與報告渲染。
  - 覆蓋缺 DB env fail closed。
  - 覆蓋缺必要欄位 fail closed。
  - 覆蓋 DB fetch 只使用 `select / order / range / execute`。
- 新增 research artifacts：
  - `reports/research/trend_continuation_20260603.txt`
  - `reports/research/trend_continuation_20260603.json`
- 更新 `RESEARCH.md`
  - 記錄資料來源、重跑命令、核心 metrics、結論與限制。

## 修改檔案

- `scripts/research_trend_continuation.py`
- `tests/test_research_trend_continuation.py`
- `reports/research/trend_continuation_20260603.txt`
- `reports/research/trend_continuation_20260603.json`
- `RESEARCH.md`
- `TASK.md`

## 最小改動策略

- 只新增獨立研究腳本與 focused tests。
- 不接正式買入路徑，不更改 scoring / funnel / report formatter。
- 研究結論只來自 production DB read-only `daily_price` 實跑輸出，fixture 只用於測試分類與 fail closed。

## 契約影響

- 新增 CLI research contract：
  - `arch -arm64 .venv/bin/python scripts/research_trend_continuation.py`
  - `--json` 可輸出 machine-readable JSON。
  - `--no-config` 可驗缺憑證 fail closed。
- 不改 public strategy contract、Telegram message list、DB contract、RR formula。

## 直接消費者同步

- Owner / Architect：讀 `RESEARCH.md` 與 `reports/research/*` 判斷是否進入階段二。
- QA：可重跑腳本、focused tests、mutation scan。
- 後續 Tech：若 Owner 另行授權階段二，需以本輪 research artifact 作為前置證據；本輪結論不支持直接實裝。

## 未影響模組

- 未改 `services/analysis.py`。
- 未改 `core/condition_engine.py`。
- 未改 `core/generator.py`。
- 未改 DB schema / RLS / grant / policy / role / index / constraint。
- 未改 production write / backfill / live Telegram。

## 已跑自檢命令

- `PYTHONPYCACHEPREFIX=/private/tmp/trend_research_pycache arch -arm64 .venv/bin/python -m py_compile scripts/research_trend_continuation.py tests/test_research_trend_continuation.py`
  - 結果：passed。
- `arch -arm64 .venv/bin/python -m pytest tests/test_research_trend_continuation.py -q`
  - 結果：4 passed。
- `rg -n "table\\([^\\n]+\\)\\.(insert|upsert|update|delete)|\\.(upsert|update|delete|rpc)\\(|\\b(create|alter|drop|truncate)\\s+table\\b|send_telegram" scripts/research_trend_continuation.py`
  - 結果：no matches。
- `arch -arm64 .venv/bin/python scripts/research_trend_continuation.py`
  - 結果：completed；`pullback_continuation_edge=insufficient-data`。

## 研究輸出摘要

- `daily_price` source rows：516。
- `pullback_continuation`：樣本 5，5 日勝率 20.00%，5 日平均收益 -3.89%，結論 `insufficient-data`。
- `extended_spike >=1.08`：樣本 78，5 日勝率 65.38%，5 日平均收益 +6.23%。
- `extended_spike >=1.15`：樣本 46，5 日勝率 65.22%，5 日平均收益 +7.45%。
- `extended_spike >=1.22`：樣本 30，5 日勝率 63.33%，5 日平均收益 +6.17%。
- 階段二狀態：不應啟動。當前 pullback continuation 定義沒有通過「樣本足夠、勝率 >50%、平均收益為正」門檻。

## 覆蓋層級

- production source：covered by read-only `daily_price` run。
- script output：covered，txt/json artifact 已產出。
- fixture/helper：covered by focused tests。
- 未覆蓋：未消費 `signal_outcomes`，未讀 `daily_signal_snapshot` 作 setup source；本輪結論只覆蓋 `daily_price` OHLCV 計算路徑。

## 殘留風險

- `pullback_continuation` 樣本只有 5，不能據此實裝策略。
- extended spike 對照組表現為正，但本輪只是對照，不代表授權追高買入；仍受既有不可追高邊界約束。
- 若 Owner 要重新研究，應先擴大樣本來源、納入 `signal_outcomes` 或調整 pullback 定義，再重跑同層研究。

## 旁支待辦

- 可另開研究任務：納入 `signal_outcomes` 與 `daily_signal_snapshot` 的 setup/outcome mapping，確認是否能增加樣本與可靠度。
- 若未來研究通過，再另開 major 策略設計任務，並由 Owner 明確授權是否放開 RESEARCH.md 既有硬邊界。
