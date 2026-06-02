# CHANGELOG: evidence_score enters decision score and funnel boundary

## 任務尺寸與風險

- 任務尺寸：major（Owner 已確認 evidence 進入決策分數與 funnel 邊界）。
- 風險判斷：改動 final confidence、排序、未持倉 funnel 邊界、manifest/report artifact 與使用者可見報文分數行。
- 未改 RR 公式、DB schema/write、live Telegram、Phase 3 runner 或 production backfill。

## 修改內容

- 新增 evidence score / modifier / final confidence 路徑：
  - `compute_evidence_score(report_context, name) -> tuple[float | None, str]`
  - `evidence_modifier = clamp(1 + 0.3 * (evidence_score - 0.5), [0.85, 1.15])`
  - evidence 不足時 modifier = 1.0，final confidence = technical confidence。
- `strategy_sample` 與 `market_theme` evidence payload 補 `decision_eligible` 與 `forbidden_effects`。
- `market_theme` strong eligibility 收窄：
  - 只有 `evidence_trend.status == confirmed_trend` 可作 confirmed strong evidence / `decision_eligible=True`。
  - `supporting_trend` 只作 supporting score，不得觸發 Phase 2b boundary adjustment。
  - `single_day` 仍不可 decision eligible。
- `pick_best_stock`、watchlist sort 與 execution ordering 使用 `final_confidence`，沒有 final confidence 時維持 fallback。
- 報文 score line 改為 `綜合 X｜技術 Y｜證據 +Z%（status）`；資料不足時顯示 `證據：不適用（資料不足）`。
- Phase 2b near-boundary adjustment：
  - 只允許 existing technical setup + strong confirmed evidence。
  - 只能調整到可準備，不得變可買。
  - 不放寬 RR / overheat / chase / risk-control hard blockers。
  - card 與 manifest 都保留 `evidence_adjustment_reason`。
- chase hard blocker 補強：
  - `LIMIT_LOCK` / `LIMIT_REBOUND` / `漲停不追` / `漲停反彈待確認` / `不可追高` 類 blocker 不得被 evidence boundary adjustment 放寬。
  - confirmed evidence + strategy ready + near-boundary setup 遇到 chase blocker 時仍維持不可追高觀察，不產生 adjustment reason。
- 修復 QA mixed-bucket 阻塞：
  - 同一份未持倉中，只有帶 `evidence_adjustment_reason` 的 adjusted prepare 計入 `可準備`。
  - 普通 prepare 仍計入 `不可追高觀察`。
  - Summary、交易執行提示、未持倉漏斗、detail index、card、manifest 使用同一 per-symbol 拆分。
  - manifest/report artifact 的 `stock.<name>.risk.value.funnel_state` 改為主顯示態；普通 prepare 直接顯示 `不可追高觀察`，並以 `strategy_funnel_state` 保留內部策略分類 `可準備`。
  - card label 同步：ordinary prepare 無 `evidence_adjustment_reason` 時，卡片主狀態也顯示 `不可追高觀察`，不再與 Summary/漏斗/manifest 出現 `待回測` 口徑分裂。
- 報文版本升為 `v20.4.30`。

## 修改檔案

- `core/generator.py`
- `presentation/report.py`
- `services/analysis.py`
- `tests/test_generator_report.py`

## 最小改動策略

- 沿用既有 strategy sample summary、market/theme trend、entry blockers、RR / overheat / chase hard blocker。
- 不新增 DB schema、不新增 write path、不手寫 production DML。
- 不改 core RR 公式或持倉狀態機。
- 只同步 evidence score 的直接消費者：分數 payload、排序、funnel 邊界、Telegram formatter、manifest/report artifact 與 regression tests。

## 契約影響

- 新增 public helper：`compute_evidence_score(report_context, name)`。
- result payload 新增 / 保留：
  - `technical_confidence`
  - `evidence_score`
  - `evidence_status`
  - `evidence_modifier`
  - `final_confidence`
- report_context evidence 新增：
  - `market_theme.decision_eligible`
  - `strategy_sample.decision_eligible`
  - `*.forbidden_effects`
- `market_theme.decision_eligible` 契約：只有 `confirmed_trend` 可為 true；supporting / single-day 不可作 strong boundary evidence。
- evidence_manifest：
  - `stock.<name>.score.value` 揭露 technical / evidence / modifier / final confidence。
  - 未持倉 `stock.<name>.risk.value.funnel_state` 是 artifact 主顯示態，與手機 card/detail 一致。
  - 未持倉 `stock.<name>.risk.value.strategy_funnel_state` 保留內部策略漏斗分類。
  - 未持倉 `stock.<name>.risk.value.evidence_adjustment_reason` 用於 artifact 驗證 boundary adjustment reason。
- 使用者可見報文：
  - score line 拆成綜合 / 技術 / 證據。
  - mixed prepare 場景拆成 `可準備 N` 與 `不可追高觀察 M`，避免整桶誤讀。

## 直接消費者同步

- `pick_best_stock()` 使用 final confidence。
- `sort_watchlist_grouped()` 與 execution ordering 使用 final confidence。
- `formatTelegramUnheldCard()` 顯示 adjusted card 的可準備狀態與 evidence boundary reason。
- `today_conclusion_text()`、`format_execution_checklist()`、`format_unheld_funnel()`、`detail_index_text()` 同步 per-symbol prepare count。
- `presentation/report.py` 的資料依據摘要同步使用 prepare split helper。
- tests 覆蓋 missing evidence、confirmed no setup、near-boundary adjustment、RR/overheat hard blocker、sample <10、single_day market/theme、pick/sort final confidence、mixed adjusted + ordinary prepare。
- mixed manifest probe 覆蓋 adjusted risk 主顯示態 `可準備` + reason，以及 ordinary risk 主顯示態 `不可追高觀察` + reason None + `strategy_funnel_state=可準備`。
- mixed card probe 覆蓋 ordinary card 主狀態 `不可追高觀察`，與 Summary/漏斗/detail/manifest 一致。
- supporting trend probe 覆蓋 `supporting_trend + strategy sample ready + near-boundary setup` 不產生 adjustment reason、不輸出 `產業主題 confirmed`、不調成 evidence-adjusted 可準備。
- chase hard blocker probe 覆蓋 `LIMIT_LOCK / 漲停不追 + confirmed_trend + strategy ready + near-boundary setup` 不產生 adjustment reason、不顯示 adjusted 可準備。

## 未影響模組

- 未改 RR 公式。
- 未改 DB schema / RLS / grant / policy / role / index / constraint。
- 未新增 production write、backfill 或 live Telegram delivery。
- 未改 Phase 3 automation。
- 未把 evidence 做成 standalone BUY source。
- 未放寬 chase / overheat / RR / risk controls。

## 已跑自檢命令

- `PYTHONPATH=. PYTHONPYCACHEPREFIX=/private/tmp/stock_tech_pycache arch -arm64 .venv/bin/python -m pytest -q tests/test_generator_report.py -k 'evidence or mixed or final_confidence or overheat or sample or single_day'`
  - 結果：22 passed，105 deselected，37 warnings。
- `PYTHONPATH=. PYTHONPYCACHEPREFIX=/private/tmp/stock_tech_pycache arch -arm64 .venv/bin/python -m pytest -q tests/test_generator_report.py -k 'evidence or market_theme_single_day or pick_best_stock'`
  - 結果：14 passed，114 deselected，33 warnings。
- `PYTHONPATH=. PYTHONPYCACHEPREFIX=/private/tmp/stock_tech_write_pycache arch -arm64 .venv/bin/python -m pytest -q tests/test_generator_report.py -k 'evidence or mixed or final_confidence or overheat or sample or single_day'`
  - 結果：18 passed，111 deselected，33 warnings。
- `PYTHONPATH=. PYTHONPYCACHEPREFIX=/private/tmp/stock_tech_pycache arch -arm64 .venv/bin/python -m pytest -q targeted 4 tests`
  - 結果：4 passed。
- `PYTHONPATH=. PYTHONPYCACHEPREFIX=/private/tmp/stock_tech_pycache arch -arm64 .venv/bin/python -m pytest -q tests/test_generator_report.py::GeneratorReportTest::test_mixed_evidence_adjusted_and_ordinary_prepare_split_counts_and_labels`
  - 結果：1 passed，13 warnings。
- `PYTHONPATH=. PYTHONPYCACHEPREFIX=/private/tmp/stock_tech_pycache arch -arm64 .venv/bin/python -m pytest -q tests/test_generator_report.py -k 'evidence or final_confidence or mixed'`
  - 結果：14 passed，113 deselected，33 warnings。
- `PYTHONPATH=. PYTHONPYCACHEPREFIX=/private/tmp/stock_tech_pycache arch -arm64 .venv/bin/python -m pytest -q tests/test_generator_report.py`
  - 結果：128 passed，225 warnings。
- `PYTHONPATH=. PYTHONPYCACHEPREFIX=/private/tmp/stock_tech_write_pycache arch -arm64 .venv/bin/python -m pytest -q tests/test_generator_report.py`
  - 結果：129 passed，225 warnings。
- `PYTHONPATH=. PYTHONPYCACHEPREFIX=/private/tmp/stock_tech_pycache arch -arm64 .venv/bin/python -m py_compile core/generator.py presentation/report.py services/analysis.py tests/test_generator_report.py`
  - 結果：passed。
- `git diff --check`
  - 結果：passed。
- 補充：未使用 `arch -arm64` 的本機 pytest 曾因 x86_64 Python 載入 arm64 `pydantic_core` collection failed；改用既有 arm64 執行方式後通過。

## 殘留風險

- 未跑 full pytest / replay / production data matrix；本輪驗證集中在 generator/report 的使用者可見契約。
- strategy sample 仍沿用現有樣本門檻與 source path，未新增更細 per-stock evidence source-of-truth。
- 若外部 artifact consumer 假設 `stock.<name>.risk.value` 永遠是純字串，需另開 manifest schema 收斂任務；本輪 repo tests 與 QA artifact probe 依 dict payload 驗證。

## 旁支待辦

- per-stock strategy evidence 更細分桶需另開資料契約任務。
- production evidence 資料品質需走 read-only artifact 任務驗證。
- Phase 3 runner / trading-day gate 已在前一輪完成，不在本輪重改。
