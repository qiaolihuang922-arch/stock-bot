# QA_REPORT:

## 測試範圍

- 任務尺寸：normal_patch，QA L2。
- 驗證聚焦：presentation/report 第一刀拆分、`formatTelegramMessages` 相容、三則 Telegram messages 順序、side-effect gate、maturity gate `v20.4.21`。
- 未擴大到 full pytest、replay、backfill、production DB write 或 live Telegram。

## 關聯風險掃描

- TASK.md 與 CHANGELOG.md 主範圍一致：只拆 Telegram presentation assembly，不改策略、RR、holding 狀態機、DB write path。
- CHANGELOG.md 已包含 refactor 任務要求的 `path / claim / evidence / risk / action` 表。
- `presentation/report.py` 與 `presentation/__init__.py` 實際存在且可 import。
- 可吸收 diff 限於：
  - `CHANGELOG.md`
  - `TASK.md`
  - `QA_REPORT.md`
  - `core/generator.py`
  - `presentation/__init__.py`
  - `presentation/report.py`
  - `tests/test_generator_report.py`
  - `tests/test_market_theme_evidence.py`
  - `tools/cao_agent/check_evidence_handoff_gate.sh`
- 不應吸收 `.qa_tmp/` 或其他未列工作樹內容。

## 跨區塊語意一致性

- TASK message order：messages[0] 持倉、messages[1] 未持倉、messages[2] 簡報＋資料依據，與 CHANGELOG 契約一致。
- 直接 consumer smoke：
  - MSG0: `【06/01 盤中｜v20.4.21】` / `【持倉標的】`
  - MSG1: `【06/01 盤中｜v20.4.21】` / `【未持倉標的】`
  - MSG2: `【06/01 盤中｜v20.4.21】` / `🧾 v20.4.21 簡報＋資料依據`
  - MSG3: `【Details Backup】...` only when `include_detail=True`
- `core/generator.py` 保留 `formatTelegramMessages(...)` public wrapper，改呼叫 `presentation.report.render_telegram_messages(...)`。
- `VERSION` 已升到 `v20.4.21`，測試與 maturity gate 同步。

## 使用者誤讀風險

- 已按 Owner 手機閱讀順序檢查：第一則持倉、第二則未持倉、第三則簡報＋資料依據。
- Regression 覆蓋無有效進場情境，保留「新倉：無有效進場」與不把「最強標的」誤讀成可下單推薦的檢查。
- `include_detail=True` 時 Details Backup 追加在最後，不插入前三則主訊息之前。

## 質疑與反證

- Side-effect 反證：`presentation/report.py` 未 import / call `record_daily_signals`、`record_strategy_evidence`、`get_supabase_client`、`record_daily_snapshots`。
- AST gate 反證：新 presentation module 不直接 mutate `results_map` / `result` / `holding_decision` roots。
- Maturity gate 反證：maturity_score=100、generator_version=`v20.4.21`、schema_change=false、data_write=false、live_telegram=false。
- QA 結論為 conditional pass，條件是 Architect 收口時必須明確吸收 `presentation/__init__.py` 與 `presentation/report.py` 兩個新檔；Architect git stage/commit 時必須滿足此條件。

## 已跑命令

- `py_compile core/generator.py presentation/report.py tests/test_generator_report.py`：passed。
- `pytest -q tests/test_generator_report.py tests/test_market_theme_evidence.py`：125 passed，177 warnings。
- `git diff --check`：passed。
- maturity report + handoff gate：passed。

## 未測項目

- 未跑 full repo pytest；符合 L2 範圍。
- 未做 production DB write、live Telegram delivery、replay/backfill。
- 未證明所有注入 formatter helper 都 immutable；本輪只驗證新 presentation module 無直接 side effect / direct root mutation。

## QA 結論

conditional pass
