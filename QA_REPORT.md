# QA_REPORT:

  ## 測試範圍

  本輪 QA 風險預算判定：normal_patch / L2-lite。驗證限於 Telegram formatter、summary、未持倉漏斗、詳情索引、版本字串與直接消費者 smoke；未擴成 full pytest / replay / backfill / DB payload。

  已檢查文件與 diff：

  - TASK.md：v20.2.5 盤後 Telegram 手機噪音與語義衝突修正。
  - CHANGELOG.md：描述範圍與 diff 一致。
  - git diff：tracked diff 只含 CHANGELOG.md、core/generator.py、tests/test_generator_report.py、tests/test_notifier.py、tests/test_market_theme_evidence.py。

  已跑命令：

  - arch -arm64 .venv/bin/python -m pytest tests/test_generator_report.py tests/test_notifier.py tests/test_market_theme_evidence.py
      - 結果：79 passed, 21 warnings
  - git diff --check
      - 結果：通過
  - QA 自補手機閱讀順序 smoke：
      - 05/29 盤後 fixture：可準備 8、僅追蹤 0、淘汰 2、英業達已執行賣出 187 股、無新增交易建議。
      - 結果：通過。

  ## 風險預算與停止條件

  本輪最值得抓的風險：

  1. 今日無新增建議與已執行交易並存時，Owner 誤讀為「今天沒有交易」。
      - 驗證：檢查 summary 連續順序為 今日交易 / 新增交易建議：無 後接 已執行（不重複下單）。
      - 結果：通過。
  2. 僅追蹤 0 時仍輸出零計數拆分，造成手機噪音。
      - 驗證：檢查不得出現 其中僅追蹤 0 檔拆分、等冷卻 0、等回測 0、等RR修復 0、等量能 0。
      - 結果：通過。
  3. 可準備 8 被混稱為未持倉追蹤 8，讓 Owner 誤判可準備與僅追蹤。
      - 驗證：檢查漏斗與索引顯示 可準備 8 檔，不列入交易執行、可準備 8｜淘汰 2，且不出現 未持倉追蹤 8。
      - 結果：通過。

  停止條件已達成：05/29 類似 fixture 通過手機閱讀驗收、版本為 v20.2.5、formatter / summary / funnel / index 相關測試通過、diff 未碰策略 / DB / watchlist / live / backfill。

  ## 關聯風險掃描

  core/generator.py diff 只改：

  - VERSION = "v20.2.5"
  - format_unheld_funnel
  - detail_index_text
  - formatTelegramSummary 今日交易文案

  未看到策略門檻、分類邏輯、evidence provider、DB schema / payload、Supabase write path、watchlist、replay / backfill 相關 diff。

  直接消費者檢查：

  - formatTelegramMessages 最後一則 summary 帶新版 header 並承接 formatter 改動。
  - tests/test_notifier.py 已同步 notifier 保留最後一則 summary header 的版本契約。
  - tests/test_market_theme_evidence.py 已同步相關 summary header 版本期望。

  可吸收 diff：

  - core/generator.py
  - tests/test_generator_report.py
  - tests/test_notifier.py
  - tests/test_market_theme_evidence.py
  - CHANGELOG.md 作為 Tech 交付摘要

  worktree 殘留：

  - git status --short 僅顯示上述 5 個 tracked 修改。
  - .qa_tmp/config.py 存在於測試暫存目錄，未出現在 tracked status；不應作為本輪合併內容。

  ## 跨區塊語意一致性

  手機閱讀順序 smoke 驗證的 summary 順序：

  【05/29 盤後｜v20.2.5】 → 今日交易 / 新增交易建議：無 → 已執行（不重複下單） → 未持倉漏斗（非執行） → 可準備 8 檔，不列入交易執行 → 詳情索引：持倉 1｜可準備 8｜淘汰 2

  跨區塊數量一致：

  - 漏斗：可買 0｜可準備 8（不可買）｜僅追蹤 0｜淘汰 2
  - 補充行：可準備 8 檔，不列入交易執行
  - 索引：可準備 8｜淘汰 2

  未發現 summary、漏斗、索引互相混稱 可準備 / 僅追蹤 / 淘汰 的問題。

  ## 使用者誤讀風險

  本輪主要誤讀路徑已被修掉：

  - 不再用 今日交易紀錄：無新增 混淆已執行交易。
  - 新增交易建議：無 與 已執行（不重複下單） 分段顯示，手機上可區分「沒有新建議」與「今天已有交易」。
  - 僅追蹤為 0 時沒有拆分零計數行。
  - 可準備 8 沒有被總稱為 未持倉追蹤 8。

  殘留觀察：detail_index_text 在沒有淘汰時仍會輸出 淘汰 0，但本輪驗收 fixture 是 淘汰 2，且 TASK 主問題聚焦在僅追蹤 0 拆分與可準備 8 混稱；此項不阻塞本輪，可列後續手機噪音收斂。

  ## 質疑與反證

  主動質疑 1：Tech 是否只改文案，實際偷改策略分類？

  - 反證：git diff -- core/generator.py 只涉及 formatter 函式與 VERSION；未改 unheld_funnel_state、策略門檻、DB / live / watchlist 路徑。

  主動質疑 2：測試是否只驗單一欄位存在，沒有驗手機連續閱讀？

  - 反證：QA 額外跑不落地 smoke，檢查 summary 區塊先後順序與禁用文案；通過。

  主動質疑 3：版本是否只改測試、未同步實際 header？

  - 反證：core/generator.py 的 VERSION 已為 v20.2.5，相關 formatter / notifier / market evidence 測試同步通過。

  ## 未測項目

  未跑 full pytest、replay、backfill、DB payload、live Telegram delivery、Supabase write。原因：TASK 明確指定 L2-lite，且本輪非策略、DB、live path 變更。

  未驗證證據鏈補強、可準備排序品質、R3 熱度判斷、更多未持倉分類重設、完整報文重構；均屬 TASK 指定旁支待辦。

  ## QA 結論

  通過
