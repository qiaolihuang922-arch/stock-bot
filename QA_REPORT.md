# QA_REPORT.md

本文件由 QA 維護，提交給 Architect。只做差異測試、snapshot test、formatter test，不全 repo 掃描，不 refactor。本文件不得刪除，任務更新時只改寫內容。

## 任務狀態

- 狀態：QA 驗證完成
- 對應 TASK / CHANGELOG：`TASK.md`、`CHANGELOG.md`
- 提交日期：2026-05-26
- 版本：v19.3.4

## 測試範圍

依最新 `TASK.md` 與 `CHANGELOG.md`，本次只驗證 v19.3.4 報文解釋力修正。

驗證重點：
- 報文版本顯示為 `v19.3.4`。
- 回測行顯示樣本數、參考度、3 日勝率、相對報酬、判讀結果。
- R3 且不新增時，摘要顯示 `🧭 原因`。
- 今日新倉浮虧顯示 `新倉風控觀察` 或 `洗盤警戒`，不回退普通 `續抱觀察`。
- 持倉詳情卡片包含 `下一步：...`。
- 停利 / 減碼 / 停損詳情包含 `原因` 與 `下一步`。
- 停利 / 減碼 / 停損不改變原本交易 action。
- 價格行右括號仍完整。
- 報文大版型維持 v19.3.x 形式。

測試類型：
- 局部 formatter test。
- Snapshot / card rendering test。
- 報文解釋力文案 regression。

未執行全局測試、全 repo 掃描、refactor。

## 執行命令

```bash
.venv/bin/python -m pytest tests/test_generator_report.py
```

## 測試結果

結果：通過。

```text
29 passed, 21 warnings in 1.61s
```

驗收項結果：
- v19.3.4 版本顯示：通過。
- 回測參考度與判讀結果：通過。
- R3 不新增原因行 `🧭 原因`：通過。
- 今日新倉浮虧風控語氣：通過。
- 持倉詳情 `下一步`：通過。
- 停利 / 減碼 / 停損詳情 `原因` 與 `下一步`：通過。
- 交易 action 未被 formatter 改寫：通過。
- 價格行右括號完整：通過。
- 大版型未回退：通過。

警告說明：
- 21 個 warnings 來自既有第三方套件 / Python 版本 deprecation。
- 未見本次 v19.3.4 formatter / snapshot 驗證失敗。

## 未測項目

依 QA 職責與 `CHANGELOG.md` 範圍未執行：
- full pytest。
- 全 repo 掃描。
- replay / backfill。
- historical simulation。
- live Telegram delivery。
- live Supabase read/write。
- TWSE / Yahoo live data fetch。
- DB schema / persistence regression。
- `services/analysis.py` 策略門檻 regression。
- RR / 過熱 / 加碼 / 減碼 / 停利 / 停損策略判斷條件調整測試。
- v19.4 策略方向測試。

## 殘留風險

- 本次驗證只覆蓋 `TASK.md` / `CHANGELOG.md` 指定的報文解釋力與 formatter 修正，未覆蓋非本任務改動。
- 本次未執行 live Telegram delivery；真實 Telegram 客戶端渲染仍需 Architect 決定是否另行手動驗收。
- 本次未驗證 replay / backfill / DB，因任務明確不涉及 DB schema、daily snapshot、正式寫入或回測流程。
- 新倉浮虧判定依賴 `position_events.bought_shares`；若今日交易事件未入庫，報文無法判定今日新倉。
- R3 `🧭 原因` 是 formatter 摘要解釋，不是新的策略阻斷條件。
- 回測 `參考度 / 略優 / 偏弱` 只解讀既有 backtest context，不代表新增回測資料或策略分數。

## QA 結論

可交回 Architect 更新狀態。

QA 判定：
- v19.3.4 報文解釋力修正的局部 formatter / snapshot 驗證已通過。
- 本輪可作為 v19.3.4 顯示層解釋力修正驗收依據。
