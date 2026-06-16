# TASK: cross_day_source_truth_v21_1_20260616

## 任務狀態

- task_id: `cross_day_source_truth_v21_1_20260616`
- 任務類型: `risk_patch`
- 狀態: `in_progress`
- 版本建議: 報文 header 維持 `v21.1`
- QA 分級: L2

## Owner 問題

Owner 指出「最近四個價格點不查數據庫怎麼來的」，並要求全局檢查類似跨日判斷是否用本次 payload / runtime 假裝 DB 記憶。真正要修的是資料來源契約：跨日狀態、連續修復、歷史權重與多日價格點必須來自 production DB 或明確持久 source-of-truth；Yahoo/TWSE payload 只能作同 run 技術指標，不得升格為跨日記憶。

## 使用者可見結果

- 多日弱反彈修復不再直接讀 `data["closes"]` / `data["price"]` 判斷。
- 多日修復升為 `等回測｜反彈修復待回測` 必須有 `daily_price` DB 價格點。
- DB 價格點不足時，維持原保守分類，不假裝連續修復。
- `closes/volumes` 仍可用於同 run 技術指標：均線、距突破、量比、當日策略運算。
- 不做 live Telegram delivery。
- 不做 DB schema/write/backfill。

## 非目標

- 不新增買入條件。
- 不改持倉停損 / 減碼 / 停利。
- 不改 DB schema。
- 不清理或刪除 production DB 資料。

## 影響模組與直接消費者

- `services/cross_day_context.py`: 讀取 `daily_price` 作為持久價格點 source。
- `core/generator.py`: 多日反彈升級只接受 persistent DB 價格點。
- `tests/test_cross_day_context.py`: 驗證 `daily_price` 價格點會進 cross-day context。
- `tests/test_generator_report.py`: 驗證沒有 DB 價格點時不允許 payload closes 觸發多日修復；有 DB 價格點時才觸發。
- 直接消費者: official `formatTelegramMessages` / `generate_report(dry_run=True)` message list、runner/bot Telegram artifact。

## 輸出契約

- `cross_day_context.source_of_truth` 可包含 `daily_price`。
- `cross_day_context.recent_daily_price_points` 必須只包含 production DB `daily_price` 讀出的 `{trade_date, close, source}`。
- `multi_day_rebound_needs_retest(data)` 僅在以下情況為 true：
  - `WEAK_REBOUND`
  - 非單日強彈
  - 非 hard fail / failed breakout
  - `cross_day_context` ready
  - `source_of_truth` 包含 `daily_price`
  - 至少 4 個 DB close points
  - 最近三段價格抬高且累計反彈 >= 5%

## 驗收條件

- 沒有 `cross_day_context.daily_price` 的 payload，即使 `closes[-4:]` 連漲，也不得升為 `等回測｜反彈修復待回測`。
- 有 `daily_price` 最近價格點且符合條件時，才升為 `等回測｜反彈修復待回測`。
- `daily_price` 讀取錯誤時 fail closed。
- 既有趨勢延續 / 回測 / 歷史樣本測試不能回退。
- full pytest 通過。

## 失敗標本與驗收路由

- 失敗標本: Owner 對「最近四個價格點來源」的質疑，以及前一輪旺宏多日反彈卡片。
- 驗收路由:
  - `services.cross_day_context.build_cross_day_contexts`
  - `core.generator.multi_day_rebound_needs_retest`
  - `core.generator.unheld_funnel_state`
  - official formatter / dry-run message list。

## 禁止事項與阻塞條件

- 禁止 live Telegram delivery。
- 禁止手寫 production DML。
- 禁止把 Yahoo/TWSE payload、local cache、agent 記憶標成跨日 source-of-truth。
- 若 DB source 不足，必須 fail closed，不得用重複 last close 或 runtime fallback 補成跨日記憶。
