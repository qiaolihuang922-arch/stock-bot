# QA_REPORT: future_watch_remove_history_events_20260626

## 測試範圍

- Future-watch source construction.
- Future-watch payload construction.
- Future-watch formatter.
- Official dry-run report path.
- Adjacent report readability regression.

## 關聯風險掃描

- 確認不是只隱藏輸出：`default_future_watch_sources()` 不再查 historical/global builders。
- 確認未誤刪法說會與財報。
- 確認 summary 前三則仍不混入 future-watch。
- 確認既有 low-repair/actionability regression 仍通過。

## 跨區塊語意一致性

- 未來30日關注現在只保留可追蹤資訊：法說會、關注標的財報。
- 不再把低相似歷史類比放在 future-watch 第一段。
- 不再顯示無行動價值的台股事件空狀態。

## 使用者誤讀風險

- 已降低：手機閱讀不再把「歷史類比」誤讀成市場判斷。
- 已降低：不再出現「未查到官方事件」這種無行動價值結尾。

## 失敗標本反證

- Owner 06/26 報文中的兩個目標區塊已反證：
  - `HAS_HISTORY=False`
  - `HAS_TW_EVENTS=False`
- Official dry-run 仍保留:
  - `HAS_FUTURE_WATCH=True`
  - `HAS_MOPS=True`
  - `HAS_FUND=True`

## 質疑與反證

- 質疑: 是否只是 formatter 不顯示但仍查？
  - 反證: 新增測試 patch historical/global live builders 為 `AssertionError`，`default_future_watch_sources()` 不觸發。
- 質疑: 是否把整個未來30日關注刪掉？
  - 反證: dry-run `HAS_FUTURE_WATCH=True`，且法說會/財報仍存在。
- 質疑: 是否影響既有報文一致性？
  - 反證: combined focused regression `20 passed, 212 deselected`。

## 未測項目

- 未跑 full suite。
- 未發 live Telegram。
- 未寫 production DB。

## QA 結論

通過。
