# CHANGELOG:

## 任務尺寸與風險

- 任務類型：mixed_patch。
- 風險分級：trend_continuation 觸發驗證與只讀監控屬 risk_patch；資料依據隱藏、QA probe 改讀 manifest、回測行降噪屬 normal_patch。
- 版本契約：維持 `v20.4.36`，不回退也不升版；本輪沒有改 header 版本常量。
- 明確未碰：RR 公式、DB schema / write path、live Telegram、既有持倉風控主決策。

## 修改內容

- 新增 `tests/test_trend_continuation.py`：
  - 正向回踩延續 fixture：正式 `strategy()` 產生 `decision_type="trend_continuation"` / BUY / 小倉 `<=15%`。
  - official generator / report 路由顯示「趨勢延續」與「小倉」。
  - extended spike 無回踩不開 trend_continuation BUY。
  - 負證據不開 BUY，降級 `trend_observation` / WAIT。
  - 同一 OHLCV fixture 驗 research helper 與 production detector 命中一致。
- 新增 `scripts/monitor_trend_continuation.py`：
  - 只讀比對 production trend_continuation live hits 與 5 日 outcomes。
  - 輸出 hit count、evaluated count、live win rate、backtest baseline、diff、連續低於閾值筆數與 alert。
  - 缺 read credentials / source-of-truth 時 fail closed 為 `source-error` 或 `insufficient-data`，不產生假勝率。
- `presentation/report.py`：
  - 新增 `SHOW_DATA_BASIS = False`，預設隱藏第三則「資料依據」文字段。
  - `SHOW_DATA_BASIS=True` 時可恢復可見資料依據。
  - 只隱藏文字，不刪 `report_context`、manifest、source_status、evidence_status、compute_evidence_score 或 fail-closed gate。
- `core/generator.py`：
  - evidence maturity / structural artifacts 的 pass 條件改讀 `evidence_manifest` source/status/use/limit/conflict，不再依賴可見「資料依據」文案。
  - ledger conflict 情境允許 `stock.智原.risk` 在 manifest 中呈現 `unresolved-conflict`，並繼續要求報文不可輸出確認執行語氣。
  - 未持倉回測行按同 `setup_key` 去重；相同 setup_key 只顯示一次，不同 setup_key 保留。
- `tests/test_generator_report.py`：
  - 原本依賴可見「資料依據」文案的 structural / maturity probe 改讀 manifest。
  - trend_continuation official report 測試改為確認 summary 預設不露資料依據，同時 manifest / context 仍保留來源狀態。

## 修改檔案

- `TASK.md`
- `CHANGELOG.md`
- `core/generator.py`
- `presentation/report.py`
- `scripts/monitor_trend_continuation.py`
- `tests/test_generator_report.py`
- `tests/test_trend_continuation.py`

## 最小改動策略

- 不改 trend_continuation 已有策略門檻，只補可重跑觸發驗證與監控。
- 不改 RR 計算公式。
- 不改 DB schema / RLS / grant / policy / role / index / constraint。
- 不新增 production write 或 live Telegram。
- 資料依據只改可見文字預設，不改內部 evidence / manifest payload。
- 回測行只做同 setup_key 可見去重，不刪 backtest payload。

## 契約影響

- 新增 CLI：`scripts/monitor_trend_continuation.py`。
  - stdout JSON fields 包含 `status`、`trade_date`、`source`、`setup_key`、`live_hit_count`、`evaluated_trade_count`、`live_win_rate_5d`、`backtest_win_rate_5d`、`backtest_avg_return_5d`、`win_rate_diff`、`consecutive_below_threshold`、`alert_threshold_win_rate`、`alert_after_trades`、`alert`。
  - 缺 production read source 時 exit 2，且 JSON status 為 `source-error` 或 `insufficient-data`。
- 報文第三則：
  - 預設標題為 `🧾 v20.4.36 簡報`，不顯示「資料依據」段。
  - `SHOW_DATA_BASIS=True` 可恢復「簡報＋資料依據」。
- QA / artifact：
  - visible data basis 不再是驗證來源完整度的 contract；manifest/source_status/evidence_status 才是 contract。
- 未持倉卡片：
  - 同 setup_key 的重複回測行降噪；不同 setup_key 仍顯示。

## 直接消費者同步

- Owner 手機報文：預設少一段長資料依據噪音；trend_continuation 卡片與 summary 仍可讀。
- official generator / report：仍建構完整 `report_context` 與 `evidence_manifest`。
- QA probe：改讀 manifest/source_status/evidence_status，不再依賴隱藏文字。
- 監控消費者：可定期只讀跑 `scripts/monitor_trend_continuation.py`，由 stdout / artifact 判斷是否 alert。

## 未影響模組

- 未改 `services/analysis.py` 的 strategy decision 結果。
- 未改 `core/condition_engine.py`。
- 未改 `core/signal_snapshot.py`。
- 未改 RR 公式。
- 未改 DB schema / write path。
- 未改 live Telegram delivery。
- 未做 production DB write / backfill。

## 已跑自檢命令

- `PYTHONPYCACHEPREFIX=/private/tmp/tech_validate_pycache python3 -m py_compile services/analysis.py core/generator.py presentation/report.py scripts/research_trend_continuation.py scripts/monitor_trend_continuation.py tests/test_trend_continuation.py tests/test_generator_report.py`
  - 結果：passed。
- `arch -arm64 ./.venv/bin/python -m pytest tests/test_trend_continuation.py tests/test_generator_report.py -k 'trend_continuation or v20_4_18_structural_artifacts or v20_4_20_maturity_report' -q`
  - 結果：13 passed，154 deselected，41 warnings。
- `python3 scripts/monitor_trend_continuation.py --no-config --trade-date 2026-06-03`
  - 結果：exit 2，JSON `status="source-error"`，原因為缺 Supabase read credentials；fail-closed 符合契約。
- `git diff --check`
  - 結果：passed。

## 覆蓋層級

- strategy：正向 fixture 確認正式 `strategy()` 可觸發 trend_continuation BUY；負證據 / spike 反例不開 BUY。
- research / production parity：同一 OHLCV fixture 的 research helper 與 production detector 命中一致。
- official generator / report：趨勢延續小倉卡片、隱藏資料依據、manifest 保留、回測行去重。
- structural artifact：maturity / structural coverage 改讀 manifest，ledger conflict 仍 fail closed。
- monitor：缺 source fail closed JSON。

## 殘留風險

- 未跑 full pytest。
- 未跑正式 runner artifact。
- 未讀 production DB，也未做 production write。
- monitor 目前驗證了缺憑證 fail-closed；真實 live win rate 需有 production read credentials 與已成熟 outcomes 才會從 `insufficient-data` 進入 `ok/alert`。
- `SHOW_DATA_BASIS=False` 隱藏的是手機文字，不代表來源證據被刪；後續 debug 若需要可臨時開 `SHOW_DATA_BASIS=True`。

## 旁支待辦

- 若 Owner 要正式 runner 定期跑 monitor，需要另開 runner / schedule 任務。
- 若 Owner 要缺 OHLCV 時所有非 trend_continuation BUY 也 fail closed，需要另開全域 source gate 任務；本輪只驗 trend_continuation。
