# QA_REPORT:

  ## 測試範圍

  依據 TASK.md、CHANGELOG.md、git diff --stat、core/generator.py 與 tests/test_generator_report.py 驗證 Tech retry 後候選 diff。

  可吸收候選 diff 僅限：

  - core/generator.py
  - tests/test_generator_report.py
  - CHANGELOG.md

  worktree 狀態只顯示上述 3 個 tracked modified file；未看到與本任務無關的 tracked 殘留。不建議整包合併，Architect 應只審這 3 個候選 diff。

  實測命令：

  - git diff --check：通過，無 whitespace error。
  - arch -arm64 .venv/bin/python -m pytest tests/test_generator_report.py tests/test_notifier.py -q：44 passed, 21 warnings
  - focused 回歸：test_intraday_v20_0_10_execution_contract、旺宏弱反彈、tests/test_notifier.py：4 passed
  - 已執行停利相關回歸：test_post_profit_watch_card_does_not_repeat_same_level_take_profit、test_post_reduce_watch_card_uses_sold_shares_fallback_without_sell_pct：2 passed
  - 補充 helper 反證：action=0.6 輸出 首筆最多 30%，總上限 60%；action=0.3 保留 30%倉；直接盤中呼叫可輸出 盤中觸發。

  補充說明：直接用 .venv/bin/python 曾因 arm64/x86_64 架構不合載入 pydantic_core 失敗；改用 runner/Tech 使用的 arch -arm64 .venv/bin/python 後測試可執行並通過，不作為產品阻塞。

  ## 關聯風險掃描

  TASK.md、CHANGELOG.md 與 diff 核心一致：版本升到 v20.0.10、盤中 summary/執行清單改為今日盤中語意、光寶科 60% 詳情卡改為首筆 30/總上限 60、英業達已停利不再二次停利、旺宏保留弱反彈淘汰原因。

  直接消費者掃描：

  - production 呼叫 formatTelegramUnheldCard() 的路徑只有 formatTelegramMessages()，且已傳入 report_phase。
  - 測試中另有直接 helper 呼叫；不帶 report_phase 仍保留 明日觸發，與 CHANGELOG.md 殘留風險一致，未影響 Owner 手機 Telegram message list。
  - tests/test_notifier.py 通過，message list/notifier 直接消費者未被 formatter 參數變更破壞。

  非本輪變更：

  - 未看到 services/analysis.py、core/condition_engine.py、DB、watchlist、replay/backfill、live delivery diff。
  - 本輪不是清理/瘦身/refactor 任務，path / claim / evidence / risk / action 證據表硬規則不適用。

  ## 跨區塊語意一致性

  按 Owner 手機閱讀順序檢查長報文 fixture：

  1. Header：summary 含 【05/28 盤中｜v20.0.10】，未殘留目前版本 v20.0.9。
  2. 今日結論：顯示 今日盤中執行 2 項，持倉 1、可買 1。
  3. 執行清單：標題為 ✅ 今日盤中執行清單（持倉優先），不再是 明日執行清單。
  4. 英業達：summary 顯示 已執行｜今日已停利 25%｜停利後觀察，未顯示 停利 25% 或待執行停利。
  5. 光寶科：summary/執行清單明示 可買｜首筆最多 30%，總上限 60%｜分批，不追價，未被 另 N 項見詳情 隱藏。
  6. 未持倉詳情卡：光寶科顯示 可買｜首筆最多 30%，總上限 60% 與 買點：可買｜首筆最多 30%，總上限 60%｜分批，不追價，未出現 可買｜60%倉、買點：可買｜建議 60%倉、建議 60%倉。
  7. 旺宏：詳情卡顯示 淘汰｜弱反彈待確認 與 買點：不買｜弱反彈待確認，避免把 +7.23% 誤讀成被無理由淘汰。
  8. 盤中詳情卡觸發：message list 內未持倉詳情卡顯示 盤中觸發。

  ## 使用者誤讀風險

  上一輪阻塞的主要誤讀路徑已修：光寶科不再像一次下單 60%，而是清楚拆成首筆最多 30%、總上限 60%、分批不追價。

  可交易項壓縮風險已反證：format_execution_checklist() 先保留 actionable items，再壓縮 passive items；測試 fixture 中光寶科可買項直接出現在執行清單，不被 另 N 項見詳情 蓋住。

  仍需 Architect 注意的非阻塞殘留：TASK.md 內有重複任務卡段落，但兩段核心契約一致，未和 CHANGELOG.md / diff 形成實質矛盾。

  ## 質疑與反證

  - PM 是否漏需求：本輪驗收點涵蓋版本、盤中語意、已執行停利、可買項壓縮、光寶科倉位、旺宏淘汰原因；未發現 diff 與需求缺口。
  - Tech 是否漏同步：上一輪漏掉的 formatTelegramUnheldCard() 已同步；rg 反查 production 直接呼叫方只有 formatTelegramMessages()，已傳 report_phase。
  - 測試是否證明直接消費者未破壞：tests/test_generator_report.py tests/test_notifier.py 全部通過，並補跑 notifier consumer。
  - QA 主動新增反證：額外檢查 helper 邊界，確認 action=0.6 走首筆 30/總上限 60，action=0.3 不被誤改成 60% 文案；同時確認直接不帶 phase 的舊 helper 呼叫仍是非盤中預設，符合 Tech 已列殘留風險。

  ## 未測項目

  - 未跑 full pytest；TASK.md 建議 L2 且本輪未改策略核心公共 contract，已跑 formatter/generator/notifier 相關範圍。
  - 未跑 replay/backfill dry-run、live Telegram、live Supabase write；均屬本輪禁止或非必要項。
  - 未開前端預覽頁；本輪 diff 未改前端，且前端若消費同一 message list，已由 generator/notifier consumer 測試覆蓋主要輸出契約。

  ## QA 結論

  通過
