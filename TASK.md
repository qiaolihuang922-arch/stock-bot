# TASK: future_watch_remove_history_events_20260626

## 任務狀態

- task_id: `future_watch_remove_history_events_20260626`
- 任務類型: `normal_patch`
- 狀態: `QA_passed_pushed`
- 版本建議: `v21.1`
- QA 分級: `L2`

## Owner 問題

Owner 貼出的 06/26 盤中完整報文顯示，未來30日關注訊息包含「歷史類比」與「未來30日台股影響事件」。手機閱讀時這兩段偏噪音，且 Owner 明確要求直接移除，連查詢都不要查。

## 使用者角度分析

- 持倉區已經有 2 檔減碼、1 檔新倉觀察，簡報也強調今日風控；使用者主注意力應放在風控，不應被未來關注中的宏觀類比分散。
- 未持倉區已有 9 檔狀態與觸發條件；未來30日關注再加歷史類比/台股事件，閱讀負擔過高。
- 歷史類比低相似卻仍佔第一段，容易被誤讀成市場主結論。
- 「未查到未來30日官方事件」是無行動價值的空訊息，手機上應移除。

## 使用者可見結果

- 未來30日關注保留法說會與關注標的財報。
- 未來30日關注不顯示「歷史類比」。
- 未來30日關注不顯示「未來30日台股影響事件」與空狀態。
- Live/default future-watch source 不再查 historical TWSE 類比 source，也不再查 global event source。

## 非目標

- 不改持倉/未持倉策略。
- 不改 DB schema / DB write。
- 不發 live Telegram。
- 不恢復 WSL/CAO UI。

## 影響模組與直接消費者

- `core/future_watch.py`: future-watch payload/source/message。
- `tests/test_generator_report.py`: future-watch 報文與 default source 反證。
- 直接消費者: Telegram 未來30日關注訊息、dry-run report、Owner 手機閱讀。

## 輸出契約

- `【未來30日關注】` 可存在。
- `未來30日法說會` 可存在。
- `關注標的財報` 可存在。
- `歷史類比` 不得存在於 future-watch 報文。
- `未來30日台股影響事件` 不得存在於 future-watch 報文。
- default live source 不得呼叫 historical/global event builders。

## 驗收條件

- Future-watch focused tests pass。
- Adjacent report readability regression remains pass。
- Official `generate_report(dry_run=True)` shows:
  - `HAS_HISTORY=False`
  - `HAS_TW_EVENTS=False`
  - `HAS_FUTURE_WATCH=True`
  - `HAS_MOPS=True`
  - `HAS_FUND=True`

## 失敗標本與驗收路由

- Owner 06/26 盤中完整報文是 failure specimen。
- 驗收路由: `default_future_watch_sources` -> `build_future_watch_payload` -> `format_future_watch_message` -> `generate_report(dry_run=True)`。

## 禁止事項與阻塞條件

- 不得只隱藏輸出但仍做 historical/global event 查詢。
- 不得移除法說會與關注標的財報。
- 若 default source 還查 historical/global events，QA 必須阻塞。
