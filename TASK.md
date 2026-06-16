# TASK: approach_distance_gap_v21_1_20260616

## 任務狀態

- task_id: `approach_distance_gap_v21_1_20260616`
- 任務類型: `normal_patch`
- 狀態: `QA passed, pending commit/push`
- 版本建議: 報文 header 維持 `v21.1`
- QA 分級: L2

## Owner 問題

Owner 貼出 06/16 盤前/盤中未持倉報文，指出 `等接近` 仍顯示 `個股弱勢`，且 `缺口：需解除後重新評估 / 可買：主條件解除後重新評估` 太空泛，沒有按策略顆粒度說明。

## 使用者可見結果

- `等接近` 卡片 title label 必須是 `遠離觸發`，不得被 `個股弱勢` 搶走。
- `等接近` 缺口必須說清楚距離問題，例如 `距突破 22.05%，仍未進入觸發區`。
- `等接近` 可買條件必須說明 `接近觸發區，或出現趨勢延續/回測承接買點型態`。
- 保留 `距突破` 獨立顯示。
- 不做 live Telegram delivery。
- 不做 DB schema/write/backfill。

## 非目標

- 不重算策略模型。
- 不改持倉風控。
- 不修改 DB。

## 影響模組與直接消費者

- `presentation/report.py`: 未持倉卡片 title / gap / unlock。
- `tests/test_generator_report.py`, `tests/test_trade_state_machine.py`: 防回退標本。
- 直接消費者: official `generate_report(dry_run=True)` message list、runner/bot Telegram artifact。

## 輸出契約

- 若 `funnel_state == 等接近`:
  - title label: `遠離觸發`
  - 進場原因: `還沒到買點區`
  - 缺口: `距突破 X%，仍未進入觸發區`
  - 可買: `接近觸發區，或出現趨勢延續/回測承接買點型態`
- 不得再落到 blockers[0] 的泛用文字 `需解除後重新評估`。

## 驗收條件

- official dry-run 的緯創/仁寶/技嘉/群創等接近卡片不再出現 `個股弱勢` 作為 title label。
- 等接近卡片不再出現 `缺口：需解除後重新評估`。
- full pytest 通過。

## 失敗標本與驗收路由

- 失敗標本: Owner 貼出的 06/16 盤前/盤中未持倉報文。
- 驗收路由:
  - formatter: `tests/test_generator_report.py`
  - state/report integration: `tests/test_trade_state_machine.py`
  - official dry-run: `generate_report(dry_run=True)`

## 禁止事項與阻塞條件

- 禁止 live Telegram delivery。
- 禁止手寫 production DML。
- 若 production runner artifact 與 dry-run 不一致，下一輪必須先查 runner commit / source path。
