# TASK: trade_state_machine_v21_20260608

## 任務狀態
- task_id: `trade_state_machine_v21_20260608`
- 任務類型: `minor`
- 狀態: `conditional_pass`
- 版本建議: `v21.0`
- QA 分級: `L3`

## Owner 問題
Owner 指出資料已放入 DB，但系統仍像報文判斷器，無法清楚回答「什麼時候真的能買、什麼時候能賣」。Owner 要求版本號升到 `21.0`，開始做交易狀態機。

## 使用者可見結果
- 使用者可見版本升到 `v21.0`。
- 正式報文每檔卡片新增一行 `交易狀態`，由 read-only 狀態機輸出：
  - 持倉可顯示 `停損`、`減碼`、`停利`、`今日進場`、`續抱`、`不可行動`。
  - 未持倉可顯示 `可買`、`可準備`、`等量能`、`等回測`、`等RR修復`、`等冷卻`、`觀察`、`不可行動`。
- 狀態機輸出包含單一 state、action、trigger、previous_state/transition、reason。
- v1 不擴 DB schema、不寫 DB、不 live Telegram delivery。

## 非目標
- 不改 DB 欄位、RLS、grant、policy、role、index。
- 不寫 production state snapshot。
- 不重寫完整 entry/exit 策略核心。
- 不把等待類標的升格成現在可買。

## 影響模組與直接消費者
- `core/trade_state_machine.py`: v21.0 read-only 狀態機核心。
- `core/generator.py`: 版本、狀態機套用、artifact helper。
- `presentation/report.py`: TG 卡片顯示狀態機線。
- `tests/test_trade_state_machine.py`: 狀態機契約測試。
- `tests/test_generator_report.py`, `tests/test_market_theme_evidence.py`: 版本同步。
- 直接消費者：official `generate_report(dry_run=True)` message list。

## 輸出契約
- 每檔最多一個主狀態。
- 狀態機輸出必須標記 `schema_version=v21.0`、`source=derived-readonly`、`db_write=False`、`schema_change=False`。
- 資料來源不足只能阻止 `READY/BUYABLE` 升格；不得把 `等量能/等回測` 直接壓成不可行動。
- 持倉 exit action 優先於一般續抱。
- 報文可見版本必須是 `v21.0`。

## 驗收條件
- `tests/test_trade_state_machine.py` 通過。
- focused generator replay 通過，並顯示 `交易狀態` 線。
- official `generate_report(dry_run=True)` 產生 v21.0 報文，不 live Telegram。
- 若 full `tests/test_generator_report.py` 因舊精準字串/既有口徑不全綠，QA 必須標明 conditional，不得宣稱全通。

## 失敗標本與驗收路由
- 失敗標本：Owner 指出系統只有報文判斷，沒有交易狀態機。
- 驗收路由：
  - helper: `evaluate_unheld_state` / `evaluate_position_state`。
  - formatter: TG 卡片 `交易狀態` 線。
  - official generator: `generate_report(dry_run=True)`。

## 禁止事項與阻塞條件
- 禁止 live Telegram delivery。
- 禁止 production DB write / schema change。
- 若狀態機會把等待類標的誤判成可買，必須 blocked。
