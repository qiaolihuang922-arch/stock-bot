# QA_REPORT: v20.4.41 盤後未持倉 gate attribution 可讀性修正

## 測試範圍

- QA 風險預算：tiny_patch / L1，只驗 formatter / message-list replay、版本、禁止變更面，不擴成 full pytest / production replay / DB smoke。
- 本輪最值得抓的風險：
  - 距突破 gate 修正不完整：RR不足 distance=2 或其他 blocker distance=2 仍外露。
  - 手機閱讀誤讀：可買 / trend_continuation / 盤後準備 / 過熱 / 突破失敗卡片主因被次因稀釋。
  - 契約越界：策略、RR、can_buy / is_valid_entry、DB / live Telegram 被改動。
- 停止條件：TASK / CHANGELOG / diff 不一致、official message-list replay 無法執行、版本不一致，或任一 blocker 復現即 blocked。

## 關聯風險掃描

- 已讀 TASK.md、CHANGELOG.md、git diff。
- 可吸收 diff：
  - core/generator.py：版本 v20.4.40 -> v20.4.41。
  - presentation/report.py：未持倉卡 formatter attribution / 盤後文案 / enum 顯示轉換。
  - tests/test_generator_report.py：focused official formatTelegramMessages replay assertion。
  - CHANGELOG.md：本輪 Tech 摘要。
- worktree 殘留：目前只有上述 tracked modified，未見本輪外無關 tracked diff。
- 靜態掃描 diff 未見策略計算、RR 計算、can_buy、is_valid_entry、DB schema / read-write、live Telegram delivery 變更。

## 跨區塊語意一致性

- Tech focused replay 通過：4 passed。
- py_compile 通過。
- git diff --check 通過。
- 版本確認：generator.VERSION == v20.4.41。
- replay 覆蓋結果：
  - RR不足且 distance=2 卡只顯示 RR gap，不顯示 距突破 2%/需<=4%。
  - RR不足且 distance=6 仍顯示 距突破 6%/需<=4%，不是全域刪除。
  - 真正可買與 trend_continuation 小倉 BUY 不顯示 到達可買差距。
  - FAILED_BREAKOUT 不顯示 RR 0/需>=1.5，改顯示突破失敗需重新轉強。
  - post-market ordinary prepare 顯示 盤後訊號 / 需開盤後重新確認，且卡片內不顯示 證據：資料不足。
  - EXTREME / HOT 只保留降溫主因，不列 RR / entry quality 次因。
  - replay output 不外露 EXTREME / HOT / LIMIT_LOCK / LIMIT_REBOUND / WEAK_REBOUND raw enum。

## 使用者誤讀風險

- 依手機閱讀順序檢查 summary -> 未持倉卡：summary 的新倉 / 可準備 / 僅追蹤 / 淘汰統計與卡片狀態一致，未把不可買卡寫成可立即買。
- 盤後 prepare 卡從標題、買點、到達可買差距、數據原因都指向「需開盤後重新確認」，沒有混入 RR不足或資料不足語意。
- 過熱與突破失敗卡片主因明確，未被 RR 0 或 entry quality 次因干擾。

## 質疑與反證

- 補驗 Tech 未覆蓋的反例：official route 建立 source missing 且 distance=2 的 BUY payload。結果卡片只顯示 missing-source / 需可用，HAS_DISTANCE_2=False，未復現上一輪 blocker。
- 主動質疑 _unheld_buy_gap_line 是否仍可能因 source blocker 帶出近距離突破；official message-list route 中 source missing 會使距離不可用，使用者可見輸出未外露 距突破 2%/需<=4%。
- 旁支風險：若未來有 source blocked 但仍保留有效 dist 的新路徑，應補一個 focused test；本輪現有 official route 未觸發，不阻塞。

## 未測項目

- 未跑 full pytest，符合 tiny_patch / L1 風險預算。
- 未跑 production runner artifact、read-only production smoke、DB read/write、live Telegram。
- 未驗證真實 2026-06-04 production payload 全矩陣，只驗等價 official message-list replay fixture。

## QA 結論

通過。TASK、CHANGELOG、diff 與 focused replay 證據一致；上一輪 blocker 已反證，未見策略 / RR / can_buy / is_valid_entry / DB / live Telegram 越界。
