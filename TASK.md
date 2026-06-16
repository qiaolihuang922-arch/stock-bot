# TASK: rebound_retest_source_gate_v21_1_20260616

## 任務狀態

- task_id: `rebound_retest_source_gate_v21_1_20260616`
- 任務類型: `risk_patch`
- 狀態: `implemented + full pytest passed + pushed`
- 版本建議: 報文 header 維持 `v21.1`
- QA 分級: L2

## Owner 問題

Owner 貼出 06/16 盤中報文，指出：

- 旺宏、群創連漲修復後仍曾被打成 `淘汰｜弱反彈待確認`，不像真實交易狀態機。
- 聯電 `距突破 4~5%` 附近時不應顯示遠離/淘汰，且 source 缺失不應被包裝成策略淘汰。
- 報文過去把「回測」全部寫成回到突破區 / 前高，對反彈修復不合理。
- 多日反彈、量能、風險報酬與資料來源必須依真實資料路徑，不得用對話記憶或假資料。

## 使用者可見結果

- `can_buy` 距離門檻同步為 `>5%` 才拒絕突破買點區，與 v21.1 `<=5% 接近突破` 契約一致。
- 連漲修復 / 多日反彈等待回測時，不再要求「先站回前高/突破區」；改為等待最近 DB-backed 修復支撐附近回測不破。
- 急彈追價仍維持等回測，不放寬成可買。
- source-only 缺失時從 `淘汰` 改為 `等資料` / `不可行動`，fail closed 但不誤導為策略淘汰。
- 資料來源或策略樣本不可用時，不再展示可行動風險報酬數字。
- 等資料卡片去除冗餘交易狀態、診斷原因與不可用數據行，保留決策必要資訊。
- 不做 live Telegram delivery。
- 不做 DB schema/write/backfill/prune。

## 非目標

- 不新增 live 下單或 Telegram 推送。
- 不修改持倉停損 / 減碼 / 停利核心規則。
- 不新增 DB 欄位或改 schema。
- 不把連漲修復直接升格為可買；仍需回測不破、非追高、量能有效。

## 影響模組與直接消費者

- `services/analysis.py`: `can_buy` 距離門檻。
- `core/generator.py`: source-only gate 的未持倉 funnel。
- `presentation/report.py`: 未持倉 entry contract、source label、風險報酬與資料行顯示。
- `tests/test_analysis_engine.py`: 距離門檻 regression。
- `tests/test_generator_report.py`: official message list / user-visible card regression。
- 直接消費者: `generate_report(dry_run=True)`、`formatTelegramMessages`、runner/bot artifact。

## 輸出契約

- 突破距離:
  - `<=5%`: 接近突破 / 可進一步評估，不因距離本身淘汰。
  - `>5%`: 遠離突破，但若是多日修復，狀態可為等回測而非淘汰。
- 多日修復回測:
  - 缺口: `等待回測最近修復支撐 X 附近不破`
  - 可買: `回測最近修復支撐 X 附近不破 + 非追高 + 量能有效`
  - X 只能來自 DB-backed `cross_day_context.recent_daily_price_points`，沒有資料時不補假價。
- 急彈 / 過熱:
  - 漲停或過熱維持 `等冷卻`。
  - 急彈追價維持 `等回測`，不得直接買。
- source gate:
  - source-only 缺失不顯示 `淘汰`。
  - 風險報酬顯示 `-（不可行動）` 或直接省略，不得用可買證據呈現。

## 驗收條件

- 旺宏等價 replay：多日反彈修復顯示 `等回測｜反彈修復待回測`，不得顯示 `淘汰｜弱反彈待確認`。
- 反彈修復缺口使用最近修復支撐，不再硬寫 `先站回突破區`。
- 聯電 source 缺失等價 replay 顯示 `等資料`，不得顯示 `⛔ 淘汰`。
- source-error 卡片不得展示可用風險報酬數字當作買點證據。
- official `generate_report(dry_run=True)` 可見報文符合上述結果。
- full pytest 通過。

## 失敗標本與驗收路由

- 失敗標本:
  - 聯電 `⛔ 淘汰｜觀察` + 接近突破 / source 缺失混在一起。
  - 旺宏 / 群創連漲修復後仍 `淘汰｜弱反彈待確認`。
  - 回測條件要求先回到前高突破區，導致反彈修復永遠等不到可執行回測。
- 驗收路由:
  - `services.analysis.can_buy`
  - `core.generator.unheld_funnel_state`
  - `presentation.report._unheld_entry_contract`
  - `presentation.report.formatTelegramUnheldCard`
  - official `generate_report(dry_run=True)` message list。

## 禁止事項與阻塞條件

- 禁止 live Telegram delivery。
- 禁止 DB schema/write/backfill/prune。
- 禁止用 local cache / 對話記憶假裝跨日資料。
- source 缺失必須 fail closed。
