# QA_REPORT: research_trend_continuation_phase1

## 測試範圍

- 任務：`research_trend_continuation_phase1`
- QA 分級：L2。
- 已驗：
  - 研究腳本可執行。
  - production DB read-only `daily_price` 實跑輸出。
  - 缺憑證 / 缺欄位 fail closed。
  - mutation / live Telegram 禁令。
  - 未改正式策略核心檔案。

## 關聯風險掃描

- DB schema / write path：未改。
- DB write：未發現 `insert / upsert / update / delete / rpc` 或 schema mutation。
- Telegram live delivery：未發現 send path。
- Strategy decision：未改 `services/analysis.py`、`core/condition_engine.py`、`core/generator.py`。
- Research source：正式結論來自 production DB read-only `daily_price`，不是 fixture。

## 跨區塊語意一致性

- `TASK.md` 要求階段一只做研究；diff 只新增研究腳本、研究測試、研究 artifact 與 handoff 文件。
- `RESEARCH.md`、`CHANGELOG.md`、artifact 結論一致：`pullback_continuation_edge=insufficient-data`。
- `CHANGELOG.md` 明確說本輪未消費 `signal_outcomes` / `daily_signal_snapshot`，避免把覆蓋範圍誇大成三表完整研究。

## 使用者誤讀風險

- 研究結論不是「趋势延續可以買」，而是「目前定義不支持進入階段二」。
- extended spike 對照組數字為正，但 QA 判定它只是對照，不構成追高買入授權。
- 樣本數不足與 5 日負 edge 同時存在；不可用來放開 RESEARCH.md 的硬邊界。

## 失敗標本反證

- 缺憑證負面案例：
  - `--no-config` path 回傳 `status: blocked`、`reason: missing-production-db-credentials`、`no_synthetic_data: true`。
- 缺欄位負面案例：
  - test fixture 移除 `low` 欄位後 `normalize_bars()` raise `ResearchBlocked(reason="missing-column")`。
- 只讀案例：
  - fake client test 只觀察到 `table / select / order / range / execute`。
  - mutation regex scan 無命中。

## 質疑與反證

- 質疑：Tech fixture 是否被當成正式研究？
  - 反證：artifact 由 `scripts/research_trend_continuation.py` 實跑 production read-only 生成，`RESEARCH.md` 也明確 fixture 只驗分類與 fail closed。
- 質疑：是否偷偷改策略核心？
  - 反證：`git diff --name-only` 未包含 `services/analysis.py`、`core/condition_engine.py`、`core/generator.py`。
- 質疑：研究是否足以進階段二？
  - 反證：`pullback_continuation` 樣本 5 < min_sample 30，且 5 日勝率 20.00%、平均收益 -3.89%；不符合 Owner 門檻。

## 已跑命令

- `PYTHONPYCACHEPREFIX=/private/tmp/trend_research_pycache arch -arm64 .venv/bin/python -m py_compile scripts/research_trend_continuation.py tests/test_research_trend_continuation.py`
  - 結果：passed。
- `arch -arm64 .venv/bin/python -m pytest tests/test_research_trend_continuation.py -q`
  - 結果：4 passed。
- `arch -arm64 .venv/bin/python scripts/research_trend_continuation.py`
  - 結果：completed，產出 research report。
- `rg ... scripts/research_trend_continuation.py`
  - 結果：no DB write / schema mutation / live Telegram matches。

## 未測項目

- 未跑 full pytest。
- 未實裝階段二。
- 未消費 `signal_outcomes` 或 `daily_signal_snapshot` 作正式 outcome / setup source。
- 未 live Telegram。
- 未 DB write。

## QA 結論

conditional pass

理由：階段一研究腳本、只讀約束、fail closed 與 production DB read-only output 已驗；但本輪未覆蓋 `signal_outcomes / daily_signal_snapshot` 三表完整研究，且研究結論是 insufficient-data，不支持進入階段二。
