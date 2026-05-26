# QA_REPORT.md

本文件由 QA 維護，提交給 Architect。只做差異測試、snapshot test、formatter test，不全 repo 掃描，不 refactor。本文件不得刪除，任務更新時只改寫內容。

## 任務狀態

- 狀態：QA 驗證完成
- 對應 TASK / CHANGELOG：`TASK.md`、`CHANGELOG.md`
- 提交日期：2026-05-26
- 版本：v19.3.3

## 測試範圍

依最新 `TASK.md` 與 `CHANGELOG.md`，本次只驗證 v19.3.3 formatter 一致性修正。

驗證重點：
- 合格未持倉 `BUY` 在摘要顯示 `【可買 N】...`，不可進入 `可觀察但不可買`。
- 合格未持倉 `BUY` 詳情顯示 `🟢 可買｜買點成立`，買點行顯示建議倉位與 `現在可分批`。
- `ADD_10 / ADD_20 / ADD_30` 在持倉摘要、詳情標題、決策行顯示加碼語意。
- `TAKE_PROFIT_*` 顯示停利，不被壓成續抱。
- `REDUCE_*` 顯示減碼，不被壓成續抱。
- `STOP_100` 顯示停損，不可只顯示減碼。
- 停利 / 減碼 / 停損詳情決策行直接呈現策略 action。
- `RR不足 / 過熱觀察 / 市場弱 / 量能不足 / 遠離觸發` 的摘要、標題、買點行主因一致。
- 報文大版型維持 v19.3.2 形式。
- 不修改策略門檻。

測試類型：
- 局部 formatter test。
- Snapshot / card rendering test。
- Strategy-output-to-card 一致性 test。

未執行全局測試、全 repo 掃描、refactor。

## 執行命令

```bash
.venv/bin/python -m pytest tests/test_generator_report.py
```

## 測試結果

結果：通過。

```text
27 passed, 21 warnings in 1.72s
```

驗收項結果：
- 合格未持倉 `BUY` 摘要 `【可買 N】...`：通過。
- 合格未持倉 `BUY` 未進入 `可觀察但不可買`：通過。
- 合格未持倉 `BUY` 詳情 `🟢 可買｜買點成立`：通過。
- `ADD_10 / ADD_20 / ADD_30` 加碼語意：通過。
- `TAKE_PROFIT_*` 停利語意：通過。
- `REDUCE_*` 減碼語意：通過。
- `STOP_100` 停損語意，不壓成減碼：通過。
- 停利 / 減碼 / 停損詳情決策行直接呈現策略 action：通過。
- 阻擋原因摘要 / 詳情一致性：通過。

警告說明：
- 21 個 warnings 來自既有第三方套件 / Python 版本 deprecation。
- 未見本次 v19.3.3 formatter / snapshot 驗證失敗。

## 未測項目

依 QA 指令與 `CHANGELOG.md` 範圍未執行：
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

- 本次驗證只覆蓋 `TASK.md` / `CHANGELOG.md` 指定的 formatter 一致性修正，未覆蓋非本任務改動。
- 本次未執行 live Telegram delivery；真實 Telegram 客戶端渲染仍需 Architect 決定是否另行手動驗收。
- 本次未驗證 replay / backfill / DB，因任務明確不涉及 DB schema、daily snapshot、正式寫入或回測流程。
- Formatter 現已能正確呈現策略已有 action，但不代表策略會更頻繁產生 `BUY / ADD / STOP / TAKE_PROFIT / REDUCE` 訊號。
- 若後續策略層新增 action level 或改變 blocker 命名，仍需同步補 formatter snapshot cases。

## QA 結論

可交回 Architect 更新狀態。

QA 判定：
- v19.3.3 formatter 一致性修正的局部 formatter / snapshot / strategy-output-to-card 驗證已通過。
- 本輪可作為 v19.3.3 顯示層一致性修正驗收依據。
