# CHANGELOG: per-stock evidence reliability closeout

## 任務尺寸與風險

- 任務尺寸：major / L3。
- 風險：改 evidence score、evidence modifier、final confidence、使用者可見資料依據文案與 version；未改 RR 公式、DB schema/write、live Telegram。

## 修改內容

- `core/generator.py`
  - 版本升至 `v20.4.31`。
  - `compute_evidence_score(report_context, name)` 改為優先使用逐股 `per_stock_evidence`。
  - `build_report_context()` 收集每檔 `market_theme_evidence`、`strategy_sample_evidence`、`backtest_context`。
  - `market_theme` evidence 先判 source_status；`missing-source / source-error / insufficient-data / unresolved-conflict` 直接 fail closed 為 `unavailable / score=None`，再判 supporting / weak / mixed。
  - market/theme confirmed 門檻與資料依據可靠度同口徑：需 `confirmed_trend` 且 observed/support/streak 達標，才可滿額 confirmed / decision eligible。
  - strategy sample 支援逐股 `strategy_sample_evidence / backtest_context`；逐股 payload 有 source_status 時優先使用，不再被 report-level `evidence.strategy_sample` manifest 缺失誤判 unavailable。
  - market/theme 逐股模式 fail closed：只要 `report_context.per_stock_evidence` 已存在，且該股缺少逐股 `market_theme` payload，就不得 fallback 到報表級 confirmed market/theme；該股 market/theme evidence 回傳 `unavailable / score=None / decision_eligible=False`。
  - strategy_sample 逐股模式 fail closed：只要 `report_context.per_stock_evidence` 已存在，且該股缺少逐股 `strategy_sample / backtest_context / setup-specific strategy` payload，就不得 fallback 到報表級 strategy sample；該股 strategy evidence 回傳 `unavailable / score=None / decision_eligible=False`。
  - 單一來源、supporting、partial evidence 皆加 modifier cap；supporting 不到 1.15，confirmed 才可到 ceiling。
  - `unheld_tracking_only_count()` 納入 `隔日確認`，讓 `僅追蹤` aggregate、漏斗拆分、卡片實際數量同口徑。
  - Summary / execution checklist 避免在 `僅追蹤` 已包含 `隔日確認` 後重複追加 `N 檔隔日確認`。
  - `stock.<name>.score` manifest value 補 `evidence_score / evidence_status`。
- `presentation/report.py`
  - reliability 為資料不足時，資料依據改為 `市場 / 題材背景：短期背景資料不足，僅供觀察。`
- `tests/test_generator_report.py`
  - 補 per-stock 不同 evidence modifier / final confidence。
  - 補 per-stock strategy sample 不依賴 report-level manifest 的反證。
  - 補 per-stock strategy_sample 缺 payload 時不 fallback 報表級 available strategy sample 的 QA blocker 反證。
  - 補 per-stock market/theme 缺 payload 時不 fallback 報表級 confirmed 的 QA blocker 反證。
  - 補 source-error + supporting-looking payload fail closed。
  - 補 supporting modifier cap、insufficient 不得 +15%、score manifest evidence status、D1 文案與卡片 / 漏斗一致回歸。
  - 更新 `隔日確認` tracking-only 測試契約：拆分加總 = `僅追蹤` aggregate = card actual。
- `tests/test_market_theme_evidence.py`
  - 同步 v20.4.31 與資料不足文案。
  - 覆蓋 market/theme reliability / source / stale / confirmed theme 不產生 BUY 的既有 guard。
- Phase 3
  - 未改碼；本輪用既有 `tests/test_phase3_evidence_automation.py` 與 `tests/test_workflow_runtime_config.py` 證明 daily evidence scheduled path、approved CLI、calendar guard、stale alert/no live Telegram guard 仍成立。

## 修改檔案

- `core/generator.py`
- `presentation/report.py`
- `tests/test_generator_report.py`
- `tests/test_market_theme_evidence.py`

## 最小改動策略

- 只改 evidence score / reliability / formatter 文案與直接 regression tests。
- 不重做 Phase 1/2/2b 架構，不重做 Phase 3 automation。
- 不改 RR 公式、策略 hard blocker、DB schema/write、live Telegram、正式 backfill。

## 契約影響

- `compute_evidence_score(report_context, name)` 呼叫方式不變，但結果改為逐股 evidence 優先。
- `compute_evidence_score(report_context, name)` 在 named per-stock mode 下，該股缺逐股 market/theme payload 時不再吃 report-level market/theme 加分；若 strategy 也不可用，回傳 `(None, "unavailable")`，modifier 維持 `1.0`。
- `compute_evidence_score(report_context, name)` 在 named per-stock mode 下，該股缺逐股 strategy payload 時不再吃 report-level strategy sample 加分。
- `evidence_modifier_for_score(evidence_score, evidence_status=None)` 增加 optional status 參數；既有單參數呼叫仍相容。
- `unheld_tracking_only_count(funnel)` 現在包含 `隔日確認`；使用者可見 `僅追蹤` 總數與漏斗拆分採同一口徑。
- `result` payload 持續輸出 `technical_confidence / evidence_score / evidence_status / evidence_modifier / final_confidence`。
- `stock.<name>.score` manifest value 新增 `evidence_score / evidence_status`。
- 使用者可見報文版本升至 `v20.4.31`。
- 資料不足文案改為 `短期背景資料不足，僅供觀察`。

## 直接消費者同步

- Telegram 手機報文：資料不足不再顯示「仍支持目前背景觀察」。
- `apply_evidence_confidence()` 使用 per-stock evidence score 與 status cap。
- pick/sort/execution ordering 沿用 final confidence；final confidence 現在可因逐股 evidence 不同而不同。
- manifest consumer 可讀 `stock.<name>.score.value.evidence_score/evidence_status`。
- Phase 3 scheduled runner / GitHub Actions 未改碼，但 guard tests 納入本輪驗證。

## 未影響模組

- 未改 `services/analysis.py`。
- 未改 RR 公式與 RR blocker。
- 未改 overheat / chase / LIMIT_LOCK hard blocker 定義。
- 未改 DB schema / RLS / grant / policy / role / index / constraint。
- 未執行 live Telegram、live Supabase write、正式 backfill。
- 未改持倉風控排序與持倉卡 / detail index 同序契約。

## 已跑自檢命令

- `git diff --check`
  - 結果：passed。
- `PYTHONPATH=. PYTHONPYCACHEPREFIX=/private/tmp/tech_write_pycache .venv/bin/python -m py_compile core/generator.py presentation/report.py tests/test_generator_report.py tests/test_market_theme_evidence.py`
  - 結果：passed。
- `PYTHONPATH=. PYTHONPYCACHEPREFIX=/private/tmp/tech_write_pycache arch -arm64 .venv/bin/python -m pytest tests/test_generator_report.py -k "...evidence..."`
  - 結果：13 passed。
- `PYTHONPATH=. PYTHONPYCACHEPREFIX=/private/tmp/tech_write_pycache arch -arm64 .venv/bin/python -m pytest tests/test_market_theme_evidence.py -k "...integrity/source/stale/theme..."`
  - 結果：5 passed。
- `PYTHONPATH=. PYTHONPYCACHEPREFIX=/private/tmp/tech_write_pycache arch -arm64 .venv/bin/python -m pytest tests/test_generator_report.py -k "...maturity/funnel/card..."`
  - 結果：5 passed。
- `PYTHONPATH=. PYTHONPYCACHEPREFIX=/private/tmp/stock_tech_pycache arch -arm64 .venv/bin/python -m pytest -q tests/test_generator_report.py -k 'market_theme_source_error_supporting_payload_fails_closed_before_supporting or per_stock_market_theme_missing_does_not_fallback_to_report_level_confirmed or per_stock_evidence_uses_stock_theme_and_setup_not_report_level_shared_score or per_stock_strategy_sample_status_does_not_depend_on_report_level_manifest'`
  - 結果：4 passed。
- `PYTHONPATH=. PYTHONPYCACHEPREFIX=/private/tmp/stock_tech_pycache arch -arm64 .venv/bin/python -m pytest -q tests/test_generator_report.py -k "per_stock_strategy_sample_missing or per_stock_market_theme_missing or unheld_funnel_counts_next_day_confirmation or unheld_next_day_confirmation_card_and_funnel_counts_match"`
  - 結果：4 passed。
- `PYTHONPATH=. PYTHONPYCACHEPREFIX=/private/tmp/stock_tech_pycache arch -arm64 .venv/bin/python -m pytest -q tests/test_generator_report.py`
  - 結果：135 passed，225 warnings。
- `PYTHONPATH=. PYTHONPYCACHEPREFIX=/private/tmp/stock_tech_pycache arch -arm64 .venv/bin/python -m pytest -q tests/test_market_theme_evidence.py`
  - 結果：36 passed，13 warnings。
- `PYTHONPATH=. PYTHONPYCACHEPREFIX=/private/tmp/stock_tech_pycache arch -arm64 .venv/bin/python -m pytest -q tests/test_generator_report.py tests/test_market_theme_evidence.py`
  - 結果：170 passed，225 warnings。
- `PYTHONPATH=. PYTHONPYCACHEPREFIX=/private/tmp/stock_tech_pycache arch -arm64 .venv/bin/python -m pytest -q tests/test_phase3_evidence_automation.py tests/test_daily_snapshot_store.py tests/test_workflow_runtime_config.py`
  - 結果：29 passed，13 warnings。
- Tech 前一輪 combined targeted suite：
  - `tests/test_generator_report.py tests/test_market_theme_evidence.py tests/test_phase3_evidence_automation.py tests/test_workflow_runtime_config.py`
  - 結果：188 passed，225 warnings。

## 殘留風險

- per-stock market/theme evidence 依賴 payload 中已有逐股 `market_theme_evidence`；production 若沒有更細 theme mapping，仍會 fallback report-level 或 fail closed。
- Phase 3 本輪只驗 guard，不重改 runner；若 Owner 要 production evidence data quality matrix，需另開 read-only artifact 任務。
- warnings 來自第三方 deprecation / Python 版本警告，非本輪改動。

## 旁支待辦

- 若 Owner 要更完整的 per-stock theme granularity，需要另開資料治理 / mapping 任務。
