# QA_REPORT:

## 測試範圍

- 任務：`strategy-support-stop-candidate-20260601`，normal_patch / QA L2。
- 狀態：QA runner timeout / stream disconnected before final sentinel，沒有形成正式可吸收 QA 結論。
- 捕獲輸出已讀：`.cao_agent_context/outputs/20260601_203135_9901_stock_qa_code_readonly.txt`。

## 關聯風險掃描

- Tech candidate diff 位於 tech worktree，主 repo 未吸收產品 diff。
- Tech candidate 修改：
  - `services/analysis.py`
  - `tests/test_analysis_engine.py`
- 主 repo 目前只保留 handoff 文件，不吸收 strategy formula diff。

## 跨區塊語意一致性

- PM / Tech 對公式方向大致一致：有效 support 且 `0 < support < price` 時用 `max(baseline_stop, support)`，否則 fallback。
- QA 捕獲輸出顯示 focused tests / probes 方向通過，但 QA 未輸出完整 final answer 與 sentinel。

## 使用者誤讀風險

- 捕獲輸出指出阻塞點：TASK 版本契約要求若使用者可見報文內容或策略版本字串會呈現 RR / 止損變化，需同步升版。
- support stop candidate 會改變 `strategy()` 產出的 `stop / risk / rr`，而報文存在 RR 顯示路徑。
- VERSION 仍為 `v20.4.21`，本輪未獲得 Owner 對「不升版但改可見 RR/stop 口徑」的放行。

## 質疑與反證

- QA 已補 support >= price / support > price / support None fallback probe，捕獲輸出顯示 fallback baseline passed。
- QA 已補直接消費者 probe，捕獲輸出顯示 snapshot raw_result / rr shape 未破壞。
- 但 QA 未能完整收口；因此不能宣告通過。

## 未測項目

- 未形成完整 QA_REPORT final。
- 未跑 full pytest、production replay、DB smoke、live Telegram。
- 未完成版本契約決策。

## QA 結論

阻塞
