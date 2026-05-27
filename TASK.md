# TASK: Telegram header 版本同步到 v20.0.9

## 任務狀態

- task_id: telegram-header-version-v20.0.9
- 任務類型: tiny_patch
- 狀態: ready_for_tech
- 版本建議: patch
- 版本契約: 本輪使用者可見 Telegram 報文 header 必須顯示 v20.0.9
- QA 分級建議: L1
- QA 升級原因: 不升級；本輪只改版本常量、使用者可見 header 測試期望與必要文件，不改策略、資料流、DB、watchlist 或 live delivery。

## Owner 問題

Owner 指出 Telegram 報文 header 仍顯示 v20.0.1，版本號沒有正常同步。Owner 要求所有使用者可見 Telegram 報文 header 與相關測試期望統一更新為 v20.0.9，避免手機上看到舊版本造成誤判目前部署狀態。

## 使用者可見結果

Owner 打開手機 Telegram 報文時，第一眼看到的報文 header 版本字串應為 v20.0.9。

手機閱讀路徑：

1. Owner 打開 Telegram。
2. 先看到最新 stock-bot 報文 header。
3. header 中版本號顯示 v20.0.9。
4. 報文後續 summary、持倉、未持倉、詳情內容維持既有邏輯與分類，不因本任務改變。

## 非目標

- 不改策略判斷。
- 不改買入、賣出、加碼、減碼、停損、停利邏輯。
- 不改報文分類、分組名稱、排序、summary 文案規則。
- 不改 Telegram payload shape。
- 不改 DB schema、DB write path、Supabase payload。
- 不改 watchlist。
- 不做 live Telegram delivery。
- 不做正式 backfill。
- 不做 replay/backfill 流程調整。
- 不清理無關檔案。
- 不重構 formatter。

## 影響模組

- 直接模組:
- Telegram 報文 formatter / generator 中的使用者可見版本常量或 header 組裝位置。
- 與 Telegram header 版本字串相關的測試期望、snapshot 或 fixture。
- 必要時同步固定交付文件中的本輪實作摘要。
- 不應影響模組:
- services/analysis.py
- core/condition_engine.py
- services/stock_api.py
- services/signal_store.py
- services/daily_snapshot_store.py
- core/signal_snapshot.py
- core/signal_validator.py
- services/position_store.py
- core/watchlist.py
- replay/backfill scripts
- Telegram live delivery path

## 直接消費者

- Owner 手機 Telegram 報文閱讀者。
- Telegram formatter 的 header 輸出呼叫方。
- 使用者可見報文 snapshot / formatter tests。
- 任何檢查 Telegram header 版本字串的測試 fixture 或期望輸出。

## 輸出契約

- 被改輸出: Telegram 報文 header 的版本字串。
- 版本字串必須由目前 header 輸出改為 v20.0.9。
- 不得殘留使用者可見 header 期望 v20.0.1。
- 報文 header 其他文字、日期、標題、分隔符、排序與 message list contract 不得因本任務改變。
- Telegram message list 的數量、順序與 payload shape 不得因本任務改變。
- 若存在共用版本常量，例如 VERSION 或等價欄位，Tech 必須同步到 v20.0.9，並確認 formatter 實際輸出使用該常量。

## 驗收條件

- Formatter 實際產出的 Telegram header 包含 v20.0.9。
- Formatter 實際產出的 Telegram header 不包含 v20.0.1。
- 使用者可見 header 測試期望、snapshot 或 fixture 已同步為 v20.0.9。
- 對使用者可見版本期望進行掃描後，不應再有 v20.0.1 作為 Telegram header 預期版本。
- 報文分類、summary、持倉、未持倉、詳情、DB payload、watchlist 與策略 decision 沒有修改。
- Tech 自檢需至少跑與 header formatter / snapshot 直接相關的最小測試。
- QA 必須實際產生或擷取一段 formatter output，核對手機第一眼 header 中包含 v20.0.9。
- QA 必須掃描不應殘留的使用者可見版本期望 v20.0.1，並說明掃描範圍。

## 範例或 fixture

示例輸出形狀，實際日期與其他欄位可依既有 formatter 決定：

台股訊號日報 v20.0.9
日期：2026-05-27

今日結論：
新倉：無有效進場，不可買
持倉：依既有規則顯示
追蹤：依既有規則顯示

手機閱讀檢查重點：

[第一屏最上方]
台股訊號日報 v20.0.9

不接受：

台股訊號日報 v20.0.1

## 明確禁止事項

- 禁止改策略分數、策略條件、持倉行動優先級。
- 禁止改報文分類或分組名稱。
- 禁止改 Telegram payload shape 或 message list 順序。
- 禁止改 DB schema、DB 寫入、Supabase function。
- 禁止改 watchlist。
- 禁止 live Telegram delivery。
- 禁止 live Supabase write。
- 禁止正式 backfill。
- 禁止用大範圍重構處理單一版本字串問題。
- 禁止為了測試方便改變日期、股票資料、策略 fixture 語意。
- 禁止刪除固定 8 份 Markdown 文件。

## 阻塞條件

- 找不到 Telegram formatter header 的實際版本來源，且無法證明哪個常量控制使用者可見 header。
- 現有測試環境無法執行 formatter 相關最小測試，且 runner 補環境後仍失敗。
- 掃描發現多個互相矛盾的使用者可見版本來源，無法在本 tiny patch 範圍內判斷唯一權威來源。
- 若修正 v20.0.9 需要改動策略、DB、watchlist、live delivery 或報文分類，Tech 必須停止並回報 blocked，不得擴大實作。
