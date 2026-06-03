# QA_REPORT:

  ## 測試範圍

  - QA 風險預算：本輪為 risk_patch / QA L3，最值得抓的風險限縮為 3 項：
      - A1 高 row density 下只取到 60 rows 而非 60 distinct trade_date；驗證 .range() 分頁、無 version eq、80 天 x 25 檔與跨頁邊界；停止條件：少於 60 distinct dates、混入第 61 日、存在 version filter。
      - B1-B4 / C 手機閱讀順序誤讀；驗證盤中 / 盤後 summary、新倉建議、交易執行、原因 / 風險、partial modifier、同日建倉風控；停止條件：未持倉可買進交易執行、+0% 殘留、同一標的主行動與原因風險矛盾。
      - 範圍外誤納入；驗證無 RR 公式、DB schema/write、production backfill、live Telegram、D1 實作；停止條件：diff 出現上述越界或 TASK/CHANGELOG/diff 不一致。
  - 已讀：TASK.md、CHANGELOG.md、git status --short、git diff --stat、相關 diff。
  - 已跑：
      - arch -arm64 .venv/bin/python -m pytest tests/test_strategy_evidence.py tests/test_generator_report.py tests/test_market_theme_evidence.py：201 passed，241 warnings。
      - arch -arm64 .venv/bin/python -m py_compile ...：passed。
      - git diff --check：passed。
      - QA 補充高密度跨頁 probe：61 天 x 17 檔，單一 trade_date 跨 page boundary，保留最近 60 distinct dates / 1020 rows，無 version eq：passed。

  ## 風險預算與停止條件

  - 本輪未擴成 full pytest / replay / production smoke / backfill，因 TASK 指定 L3 targeted 驗收，且 CHANGELOG 明列未跑 full pytest。
  - 若發現 TASK/CHANGELOG/diff 任一不一致、版本未升、D1 被實作、或 DB/write/live delivery 越界，直接阻塞。
  - 未觸發停止條件。

  ## 關聯風險掃描

  - 可吸收 diff：services/strategy_evidence.py、core/generator.py、presentation/report.py、三個測試檔與 CHANGELOG.md，均對應 TASK A1/B1-B4/C 與版本同步。
  - worktree 殘留：git status --short 只有上述 7 個 modified tracked files；未見 unrelated tracked diff。.qa_tmp/ 只作 QA 暫存，未進 tracked status。
  - A1：實作改為 .range(start,end) 分頁，limit=60 轉為最近 60 distinct trade_date；掃描未見 load_strategy_evidence_summary 對 version .eq()。
  - B/C：diff 未涉及 RR raw formula、DB schema/RLS/grant/policy/role/index/constraint、production write path、backfill 或 live Telegram。
  - D1：未見光寶科同日淘汰 -> 可買翻轉的新策略實作；維持 deferred。

  ## 跨區塊語意一致性

  - TASK.md、CHANGELOG.md、diff 一致：A1 分頁與無 version filter；B1-B4 報文分組 / 降噪 / partial 顯示；C 同日建倉 hard risk guard；D1 deferred。
  - 版本一致：core/generator.py VERSION = v20.4.32，測試同步檢查 Telegram header、brief/evidence header、artifact generator_version / telegram_header_version。
  - 盤中 / 盤後路徑均在 targeted tests 中覆蓋；未持倉可買移至「新倉建議」，交易執行只保留持倉 / 已執行動作。

  ## 使用者誤讀風險

  - 手機閱讀順序已反證：summary 中市場結論後拆成「原因」與「風險」，再進交易執行 / 新倉建議 / 非執行漏斗。
  - 未持倉可買不再被列在「今日盤中交易執行」，且新倉建議含「尚未買入」「建議分批」。
  - 空交易執行不顯示「無新增下單」占位；無有效新倉時顯示「新倉：無有效進場」，避免推薦語氣。
  - partial evidence modifier = 1.0 顯示「僅輔助參考」，未見 +0% 回退。

  ## 質疑與反證

  - QA 補充 Tech 未明確覆蓋的負面邊界：page size 1000 下同一 trade_date 被切在兩個 page，仍保留完整最近 60 天資料，未丟失跨頁日期 rows。
  - 同日建倉反證覆蓋 hard_stop、入場價 -3%、入場 K 棒低點、僅破警戒降級觀察；聯電 -3.86% + 突破失敗落入減碼，不是剛買入豁免。
  - 第一次 QA probe 因 QA 自身日期預期誤算失敗，修正預期後同一 probe 通過；不構成產品阻塞。

  ## 未測項目

  - 未跑 full pytest。
  - 未跑 production read-only smoke。
  - 未跑正式 replay / backfill。
  - 未做 live Telegram delivery。
  - 未驗證 production 實際 row density 與 pagination 成本；CHANGELOG 已列為旁支待辦。

  ## QA 結論

  通過
