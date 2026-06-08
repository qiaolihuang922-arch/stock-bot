# TASK: historical_analogy_granularity_20260608

## 任務狀態
- task_id: `historical_analogy_granularity_20260608`
- 任務類型: `normal_patch`
- 狀態: `qa_passed`
- 版本建議: `v20.4.52`
- QA 分級: `L2`

## Owner 問題
Owner 要求強化 `歷史類比`，目前顆粒度太粗，只有籠統相似度與少量特徵。

## 使用者可見結果
- 歷史類比由單行粗摘要改為多行：
  - 最像事件 / 相似度 / 型態 / 壓力級別。
  - 相似點：跌幅、高檔回落、盤中震盪、量能、5日位置。
  - 不相似/限制：說明為何不能直接當崩盤預測。
  - 下一步觀察：隔日低點、量能、高檔回落等具體條件。
  - 資料：TWSE近幾日與樣本庫大小。
- generic historical source 也補 `相似點` / `不相似/限制` / `下一步觀察` 行。

## 非目標
- 不改交易決策、買賣建議、DB schema、DB write、live Telegram delivery。
- 不新增外部歷史資料庫；本輪使用既有 TWSE source 與內建台股急跌樣本庫。

## 影響模組與直接消費者
- `core/future_watch.py`: historical analogy scoring / formatter。
- `core/generator.py`: 使用者可見版本。
- `tests/test_generator_report.py`: future-watch regression。

## 輸出契約
- 第 4 則 `歷史類比` section 保持在 `未來30日法說會` 前。
- `歷史類比` 可輸出多行，但不改 message order。
- dry-run only，不觸發 Telegram send。

## 驗收條件
- focused pytest 通過。
- `py_compile` 通過。
- official `generate_report(dry_run=True)`：
  - header 為 `v20.4.52`。
  - 歷史類比包含 `相似點`、`不相似/限制`、`下一步觀察`、`資料`。

## 失敗標本與驗收路由
- Owner 指出 v20.4.51 歷史類比顆粒度不足。
- 驗收路由：official generator `generate_report(dry_run=True)` 最終 message list。

## 禁止事項與阻塞條件
- 禁止 live Telegram delivery。
- 禁止 production DB write / schema change。
- 若 official dry-run 無法產生 message list，結論只能 blocked。
