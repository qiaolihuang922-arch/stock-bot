# TASK: explicit_approach_zone_wording_v21_1_20260616

## 任務狀態

- task_id: `explicit_approach_zone_wording_v21_1_20260616`
- 任務類型: `tiny_patch`
- 狀態: `implemented + full pytest passed`
- 版本建議: 報文 header 維持 `v21.1`
- QA 分級: L1

## Owner 問題

Owner 指出未持倉卡片中的：

- `進場：不買，等接近觸發區｜原因：還沒到買點區`
- `缺口：距突破 15.23%，仍未進入觸發區`

語意太抽象，不知道「買點區 / 觸發區」到底是哪個區。

## 使用者可見結果

- `等接近` 卡片會明確顯示突破區價位：
  - `進場：不買，等接近突破區 399~400.99`
  - `缺口：距突破 15.23%，尚未接近突破區 399~400.99`
  - `可買：接近突破區 399~400.99，或出現趨勢延續/回測承接買點型態`
  - `明日觸發：接近突破區 399~400.99 後重新評估買點型態`
- 若 payload 沒有突破區價位，fallback 為 `突破區/回測支撐`，不再顯示抽象 `買點區`。

## 非目標

- 不修改策略判斷。
- 不修改距突破計算。
- 不修改 DB schema/write/backfill/prune。
- 不做 live Telegram delivery。

## 影響模組與直接消費者

- `presentation/report.py`
  - `等接近` 的 entry / gap / unlock / trigger 文案。
- `tests/test_generator_report.py`
- `tests/test_trade_state_machine.py`
- 直接消費者:
  - 未持倉 Telegram card。

## 輸出契約

- 禁止在 `等接近` 使用抽象原因 `還沒到買點區`。
- 優先顯示 `突破區 low~high`。
- 沒有價位資料時才使用 `突破區/回測支撐` fallback。

## 驗收條件

- 技嘉 dry-run card 顯示 `突破區 399~400.99`。
- 等接近 regression 不再包含 `還沒到買點區` / `仍未進入觸發區`。
- Targeted tests 與 full pytest 通過。

## 失敗標本與驗收路由

- 失敗標本:
  - Owner 貼出的技嘉 `等接近｜遠離觸發` 卡片。
- 驗收路由:
  - `generate_report(dry_run=True)`
  - official unheld message。

## 禁止事項與阻塞條件

- 禁止只把文字換成另一個抽象詞。
- 禁止更動策略門檻。
- 禁止 live Telegram delivery。
