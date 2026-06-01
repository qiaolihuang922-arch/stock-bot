# QA_REPORT:

## 測試範圍

- 任務尺寸 / QA level：normal_patch / L2。
- 驗證範圍：Telegram formatter、未持倉卡片、強勢準備摘要、版本字串與相關測試。
- 讀取文件與 diff：`TASK.md`、`CHANGELOG.md`、`core/generator.py`、`presentation/report.py`、`tests/test_generator_report.py`、`tests/test_market_theme_evidence.py`。
- 未做 full pytest / replay / backfill；本輪禁止 live Telegram delivery。

## 關聯風險掃描

- `TASK.md`、`CHANGELOG.md`、實際 diff 一致：任務是縮量漲停未持倉風險提示。
- `core/generator.py` 只新增窄條件 helper：`volume_ratio < 1.0` 且既有 bucket 為 `漲停鎖價` 時回傳縮量提示。
- `presentation/report.py` 只在未持倉卡片主內容插入縮量提示，位置在數據行後。
- 未見 DB schema / RLS / grant / policy / role、production write、backfill、live Telegram delivery、持倉加減碼 / 停損停利策略 diff。

## 跨區塊語意一致性

- 卡片：`volume_ratio = 0.62` 的漲停鎖價卡片顯示 `縮量漲停，需開板回測確認，不等同攻擊量`，仍維持 `👀 可準備｜漲停鎖價`。
- 摘要：同一低量標的在強勢準備摘要中 action 改為縮量風險提示；攻擊量標的維持 `不可追高，待開板回測`。
- 負例：`volume_ratio = 1.71` 的漲停鎖價卡片不顯示縮量提示，且未降級。
- QA 補充邊界：`volume_ratio = 1.0` 的漲停鎖價不顯示縮量提示；`volume_ratio = 0.62` 但非漲停鎖價也不顯示縮量提示。

## 使用者誤讀風險

- 手機閱讀時，縮量提示在同一卡片內可見，不需要看 debug / log / metadata。
- 攻擊量漲停與縮量漲停不再完全同文案處理。
- 無可買語氣未回退：本輪測試仍確認可買為 0、可準備維持不可買語意。

## 質疑與反證

- Tech 測了 `0.62` 與 `1.71`；QA 補測 `1.0` 邊界與「非漲停低量」路徑。
- QA 命令：`arch -arm64 .venv/bin/python -m pytest -q tests/test_generator_report.py::GeneratorReportTest::test_low_volume_limit_up_prepare_card_and_summary_show_risk tests/test_generator_report.py::GeneratorReportTest::test_v20_2_4_r3_hot_prepare_overflow_counts_hidden_statuses tests/test_market_theme_evidence.py::MarketThemeEvidenceTest::test_readonly_smoke_cli_outputs_full_integrity_json_with_mocked_report`：3 passed，13 warnings。
- QA inline mobile-order boundary probe：passed。
- `git diff --check`：passed。

## 未測項目

- 未跑 full pytest；normal_patch / L2 範圍內不擴成 full matrix。
- 未做 production DB read-only smoke、replay、backfill、live Telegram delivery。
- 未驗證所有 price_behavior / blocker 組合，只驗本輪契約最相關的漲停鎖價、攻擊量邊界與非漲停低量負例。

## QA 結論

通過
