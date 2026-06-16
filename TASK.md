# TASK: rebound_retest_anchor_wording_v21_1_20260616

## 任務狀態

- task_id: `rebound_retest_anchor_wording_v21_1_20260616`
- 任務類型: `tiny_patch`
- 狀態: `implemented + targeted QA passed`
- 版本建議: 報文 header 維持 `v21.1`
- QA 分級: L1

## Owner 問題

Owner 指出未持倉卡片：

- `等回測｜反彈修復待回測`
- `缺口：等待回測最近修復支撐 53.3 附近不破`

看起來像系統已經識別出有效支撐，但實際策略來源是 DB `daily_price` 的最近跨日收盤序列。若只取最近收盤，不得稱為已驗證支撐，否則會讓 Owner 懷疑是假資料或假記憶。

## 使用者可見結果

- 反彈修復待回測卡片改為：
  - `缺口：等待回測最近反彈收盤 53.3 附近不破`
  - `可買：回測最近反彈收盤 53.3 附近不破 + 非追高 + 量能有效`
- 不再使用 `最近修復支撐`。
- `等回測` 仍只代表等待下一次回測確認，不代表已經完成回測。

## 非目標

- 不修改策略門檻。
- 不修改跨日判斷邏輯。
- 不修改 DB schema / write / backfill / prune。
- 不做 live Telegram delivery。

## 影響模組與直接消費者

- `presentation/report.py`
  - multi-day rebound retest anchor wording。
- `tests/test_generator_report.py`
  - official formatter regressions。
- 直接消費者:
  - 未持倉 Telegram card。

## 輸出契約

- 若使用 `recent_daily_price_points` 的最後一筆日收盤作回測錨點，只能稱為 `最近反彈收盤`。
- 禁止稱為 `支撐`，除非策略實際計算 swing low / 均線 / 成交密集區等支撐來源。
- `等回測` 必須保持不可買語氣。

## 驗收條件

- 群創 / 旺宏官方 dry-run card 顯示 `最近反彈收盤`。
- 報文與 tests 不再出現 `最近修復支撐`。
- Targeted official formatter tests 通過。
- Full pytest 通過後才能 commit/push。

## 失敗標本與驗收路由

- 失敗標本:
  - Owner 貼出的群創 `等待回測最近修復支撐 53.3 附近不破` 卡片。
- 驗收路由:
  - `generate_report(dry_run=True)` official unheld message。
  - `tests/test_generator_report.py` official formatter tests。

## 禁止事項與阻塞條件

- 禁止用 runtime dict / agent memory 解釋跨日狀態。
- 禁止把最近收盤誇大成已確認支撐。
- 禁止 live Telegram delivery。
