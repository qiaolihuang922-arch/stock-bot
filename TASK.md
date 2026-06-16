# TASK: multi_day_rebound_retest_v21_1_20260616

## 任務狀態

- task_id: `multi_day_rebound_retest_v21_1_20260616`
- 任務類型: `risk_patch`
- 狀態: `QA passed, pending commit/push`
- 版本建議: 報文 header 維持 `v21.1`
- QA 分級: L2

## Owner 問題

Owner 貼出 06/16 盤中未持倉報文，指出旺宏已連漲三天，仍被顯示為 `淘汰｜弱反彈待確認`，判斷太死。Owner 問題不是要求直接買入，而是要求分類要合理：連漲修復後不應仍是淘汰，但也不能追高。

## 使用者可見結果

- 單日急彈仍顯示 `等回測｜急彈待回測`。
- 多日連漲修復的 `WEAK_REBOUND` 不再直接淘汰，改為 `等回測｜反彈修復待回測`。
- 可買條件仍保守：先站回突破區或回測區，再回測不破 + 非追高 + 量能有效。
- `decision=FAIL`、`FAILED_BREAKOUT`、`reject_family=突破失敗` 不得被連漲修復規則覆蓋，仍維持淘汰。
- 不做 live Telegram delivery。
- 不做 DB schema/write/backfill。

## 非目標

- 不新增買入訊號。
- 不改停損 / 減碼 / 持倉行動。
- 不修改 DB。

## 影響模組與直接消費者

- `core/generator.py`: 未持倉漏斗分類。
- `presentation/report.py`: 未持倉卡片文案。
- `tests/test_generator_report.py`: 多日反彈修復防回退。
- 直接消費者: official `generate_report(dry_run=True)` message list、runner/bot Telegram artifact。

## 輸出契約

若未持倉標的符合：

- `price_behavior` 或 `structure_phase` 為 `WEAK_REBOUND`
- 最近三段收盤 / 現價連續抬高
- 最近三段累計漲幅 >= 5%
- 不是單日急彈 `live_change >= 7%`
- 不是 `decision=FAIL` / `FAILED_BREAKOUT` / `reject_family=突破失敗`

則漏斗狀態為 `等回測`，卡片顯示：

- title: `等回測｜反彈修復待回測`
- 進場: `不買，等回測`
- 原因: `連漲修復待回測`
- 可買: `先站回突破區/回測區，再回測不破 + 非追高 + 量能有效`

## 驗收條件

- 旺宏 dry-run 從 `淘汰｜弱反彈待確認` 變成 `等回測｜反彈修復待回測`。
- 單日急彈測試仍顯示 `急彈待回測`。
- 突破失敗測試仍保留淘汰。
- full pytest 通過。

## 失敗標本與驗收路由

- 失敗標本: Owner 貼出的 06/16 盤中旺宏卡。
- 驗收路由:
  - `unheld_funnel_state`
  - `formatTelegramUnheldCard`
  - official `generate_report(dry_run=True)`

## 禁止事項與阻塞條件

- 禁止 live Telegram delivery。
- 禁止手寫 production DML。
- 若 production runner artifact 與 dry-run 不一致，下一輪必須先查 runner commit / deployment path。
