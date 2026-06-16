# TASK: near_breakout_tracking_contract_v21_1_20260616

## 任務狀態

- task_id: `near_breakout_tracking_contract_v21_1_20260616`
- 任務類型: `risk_patch`
- 狀態: `implemented + QA passed + full pytest passed + pushed`
- 版本建議: 報文 header 維持 `v21.1`
- QA 分級: L2

## Owner 問題

Owner 貼出聯電樣本：`距突破：4.25%｜遠離突破`，同一張卡又顯示 `⛔ 淘汰｜觀察`。真正問題不是單一股票，而是 v21.1 距離策略與報文狀態契約不一致：

- 策略已把 `0~5%` 視為突破買點區 / 接近突破。
- 顯示層仍用 `<4%` 才叫接近，導致 `4.25%` 被誤標遠離。
- 部分 RR / hidden reason 仍用 `>4%` 當遠離觸發。
- `隔日確認 / 觀察` 類中間態在部分路徑沒有被 funnel 接住，會掉到預設淘汰。

## 使用者可見結果

- `4.25%` 這類 `<=5%` 距突破顯示為 `接近突破`，不再顯示 `遠離突破`。
- 接近突破區內、非硬失敗、品質 C 的觀察狀態，不再因中間態掉底而變成 `淘汰`。
- 真正硬失敗仍維持淘汰：`FAIL`、`突破失敗`、`FAILED_BREAKOUT`、`DISTRIBUTION`。
- 弱反彈不因距離近自動放寬；仍需 DB-backed 跨日修復證據或既有策略條件。
- 不做 live Telegram delivery。
- 不做 DB schema/write/backfill/prune。

## 非目標

- 不新增可買條件。
- 不修改持倉停損 / 減碼 / 停利。
- 不改跨日 DB source-of-truth。
- 不放寬弱反彈、突破失敗或資料缺失的 fail-closed 原則。

## 影響模組與直接消費者

- `presentation/report.py`: 距突破顯示 label。
- `core/generator.py`: 未持倉結構淘汰、RR 隱藏原因、funnel 中間態。
- `tests/test_generator_report.py`: 官方 message list 層回歸。
- 直接消費者: `formatTelegramMessages`、`generate_report(dry_run=True)`、runner/bot Telegram artifact。

## 輸出契約

- 距突破 label:
  - `<0`: `已突破`
  - `<1`: `臨界突破`
  - `<=5`: `接近突破`
  - `>5`: `遠離突破`
- `PRE_BREAKOUT` / `BREAKOUT_CONFIRM` 且非硬失敗時，不用 `弱勢/遠離` 軟阻擋直接升級淘汰。
- 保護只適用於非弱反彈的接近突破觀察；`弱反彈待確認` 不被距離近放寬。
- `entry_quality == C`、`market_grade != D/E`、接近突破、非硬失敗時，funnel 可維持 `隔日確認` / 追蹤，不掉入預設淘汰。

## 驗收條件

- 聯電等價 replay：`breakout_distance=4.25`、`entry_quality=C`、非硬失敗時，卡片包含 `距突破：4.25%｜接近突破`。
- 同一 replay 不得包含 `⛔ 淘汰`、`遠離突破`、`遠離觸發`。
- `7%` 仍顯示 `遠離突破`。
- 弱反彈真淘汰、突破失敗真淘汰、遠離觸發追蹤既有測試不回退。
- 大範圍報文 / 策略測試通過。

## 失敗標本與驗收路由

- 失敗標本: Owner 貼出的聯電卡片：
  - `【聯電 2303】⛔ 淘汰｜觀察`
  - `距突破：4.25%｜遠離突破`
  - `缺口：買點品質未過（目前 C，需 B 以上）`
- 驗收路由:
  - `presentation.report._breakout_distance_label`
  - `core.generator._unheld_structural_reject`
  - `core.generator.unheld_funnel_assessment`
  - `core.generator.rr_display_text / hidden_rr_reason`
  - official `formatTelegramMessages` message list。

## 禁止事項與阻塞條件

- 禁止 live Telegram delivery。
- 禁止 DB write / schema / backfill / prune。
- 禁止只改文案而不改策略狀態來源。
- 若資料來源缺失，仍須 fail closed，不得顯示有效進場。
