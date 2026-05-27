# QA_REPORT:

  ## 測試範圍

  依據：TASK.md、CHANGELOG.md、git status --short、git diff -- core/generator.py tests/test_generator_report.py CHANGELOG.md、core/generator.py formatter 呼叫鏈、services/notifier.py message list 直接消費者。

  實測範圍：

  - 核對 VERSION = "v20.0.9"，且 formatTelegramSummary()、generate_report() DB/evidence version 來源同一常量。
  - 核對 formatTelegramMessages() 回傳順序未因本 diff 改變：持倉、未持倉、summary；include_detail=True 時為 detail、持倉、未持倉、summary。
  - 掃描範圍：rg -n "v20\\.0\\.1|v20\\.0\\.9" -g '!CHANGELOG.md' -g '!TASK.md' -g '!DISPATCH.md' -g '!CURRENT_STATE.md' -g '!AGENTS.md' -g '!QA_REPORT.md'。
  - 測試命令：tests/test_generator_report.py + 補測直接消費者 tests/test_notifier.py，結果 36 passed, 21 warnings。
  - QA 補充 smoke：直接產生 formatter message list，確認最後一則 summary header 為 【05/27 盤後｜v20.0.9】，且不含 v20.0.1；include_detail=True 同樣最後一則為 v20.0.9 summary。

  可吸收 diff：

  - core/generator.py：只改 VERSION from v20.0.1 to v20.0.9。
  - tests/test_generator_report.py：只改兩個 header 版本期望。
  - CHANGELOG.md：本輪 Tech 交付摘要，標題符合 # CHANGELOG:。

  worktree 殘留：

  - git status --short 只有上述 3 個 tracked modified files，未見其他 tracked 殘留。
  - CLEANUP_PLAN.md 仍有歷史文字 v20.0.1 Evidence Readiness Message，但不在 git diff 中，且不是 Telegram header 程式常量或測試期望；不應作為本輪可吸收 diff 一起處理。
  - 本輪不是清理 / 瘦身 / refactor 任務，path / claim / evidence / risk / action 證據表要求不適用。

  ## 關聯風險掃描

  直接呼叫方：

  - formatTelegramSummary() 直接使用 VERSION 組 header。
  - formatTelegramMessages() 直接消費 formatTelegramSummary()，summary 仍放在 message list 最後一則。
  - generate_report() 也用同一 VERSION 傳給 record_daily_signals()、record_daily_snapshots()、record_strategy_evidence()；這是版本常量同步的下游影響，但 diff 未改 DB payload shape 或寫入流程。
  - services/notifier.send_many() 依 list 順序送出，最後一則才附 reply_markup；QA 補跑 notifier 測試確認 list 直接消費者未破壞。

  外部副作用：

  - 未執行 live Telegram delivery。
  - 未執行 live Supabase write。
  - 未執行 replay/backfill。
  - 測試以 stub config 執行，未讀取 .env 或密鑰。

  ## 跨區塊語意一致性

  此任務只改 header 版本字串，不改 summary、持倉、未持倉、漏斗、詳情分類與排序。

  手機閱讀順序檢查：

  - formatter 實際 message list 第一則是 【持倉標的】，最後一則是 summary header 【05/27 盤後｜v20.0.9】。
  - 依 send_many() 順序送出時，summary 是最後送出的訊息；Telegram 手機常見閱讀情境會先看到最新/最後送出的 summary，因此符合 TASK 的「第一眼 header v20.0.9」意圖。
  - 若 Owner 從聊天較上方開始讀歷史訊息，第一則仍是持倉詳情而非 header；這是既有 message list contract，不是本輪 diff 新增風險。

  ## 使用者誤讀風險

  主要誤讀風險是版本號仍顯示舊版，讓 Owner 誤判部署狀態。QA 檢查結果：

  - 程式與 formatter 測試中的 header 版本期望已同步為 v20.0.9。
  - 直接產生的 summary header 不含 v20.0.1。
  - 掃描只在 CLEANUP_PLAN.md 歷史狀態文字看到 v20.0.1，不是使用者可見 Telegram header 來源。

  本輪未改買、賣、加碼、停損、等待或追蹤文案；未發現由本 diff 引入的交易行動誤讀。

  ## 質疑與反證

  PM 是否漏需求：

  - PM 已列明直接消費者、輸出契約、版本契約與驗收條件；未發現本 tiny patch 必須補充的產品需求。

  Tech 是否漏同步：

  - Tech 同步了 VERSION 與兩處 formatter header 測試期望。
  - QA 額外質疑 formatTelegramMessages() 的直接消費者 send_many()，補跑 tests/test_notifier.py，確認 message list 消費契約未破壞。

  測試是否能證明沒有破壞直接消費者：

  - tests/test_generator_report.py 覆蓋 formatter。
  - tests/test_notifier.py 覆蓋 list 順序送出與最後一則 markup 行為。
  - QA smoke 覆蓋 include_detail=False 與 include_detail=True 下最後一則 summary header。

  QA 主動找到指定清單之外的風險：

  - 主動檢查了「header 在最後一則 summary，不在第一則 message」是否會破壞 Owner 手機第一眼路徑。反證結果：這是既有順序，且 notifier 照順序送出，最後一則 summary 仍是手機最新訊息；可接受。

  ## 未測項目

  - 未跑 full pytest：TASK QA 分級為 L1，且 diff 僅改版本常量與 header 測試期望。
  - 未跑 replay/backfill dry-run：非目標，且本輪不改 replay/backfill。
  - 未做 live Telegram delivery / live Supabase write：明確禁止。
  - 未驗 production DB 寫入結果：本輪不改 DB schema 或 write path；僅確認 generate_report() 使用同一 VERSION 常量。

  ## QA 結論

  通過
