# QA_REPORT:

  ## 測試範圍

  本輪判定為 risk_patch / L2，驗證範圍對齊 TASK：只驗 cross-day source boundary、generator 直接消費者、header 與手機報文誤讀風險；未擴大到 full pytest / replay / backfill / production DB live read。

  已檢查：

  - TASK.md、CHANGELOG.md、git diff --stat、相關 diff。
  - core/generator.py
  - services/cross_day_context.py
  - tests/test_cross_day_context.py
  - tests/test_generator_report.py
  - tests/test_market_theme_evidence.py

  有效驗證命令：

  - pytest tests/test_cross_day_context.py tests/test_generator_report.py tests/test_market_theme_evidence.py tests/test_notifier.py：92 passed。
  - 定點 blocker tests：5 passed。
  - 額外 QA 反證腳本：pure DB 啟用；mixed local / missing source 對 sort、prepare、dedupe、detail 全部 fail closed。
  - git diff --check：通過。
  - forbidden diff 掃描：未見 schema / migration / SQL / backfill / watchlist / live Supabase write / live Telegram delivery 變更；掃描只命中測試 payload update() 與 formatter 呼叫假陽性。

  ## 風險預算與停止條件

  本輪最值得抓的 3 個風險：

  1. mixed source 假裝 ready：["position_events", "local_position_events"] 不能影響 sorting / summary / detail / prepare / dedupe。
      - 驗證：新增 mixed-source generator test、QA 額外腳本。
      - 結果：fail closed。
  2. DB missing / source-error 被 local today event 補成跨日記憶。
      - 驗證：test_local_today_events_do_not_become_cross_day_memory、test_source_error_fails_closed_even_with_partial_rows_and_local_events。
      - 結果：previous_action/date、連續天數、weight、dedupe 都歸零或 unknown；same-run guard 只留在 same_run_*。
  3. v20.4.0 高級風控優先被歷史 dedupe 回退。
      - 驗證：test_v20_4_cross_day_reduce_history_does_not_suppress_hard_risk_reduce。
      - 結果：REDUCE_50 硬風控仍輸出，不被歷史 reduce dedupe 壓掉。

  停止條件已達成：fresh DB event、DB missing/source-error、local-only negative、mixed-source blocker、header v20.4.1、禁止項掃描均完成。

  ## 關聯風險掃描

  TASK.md、CHANGELOG.md、diff 一致：CHANGELOG 宣稱只修 source boundary 與版本同步，diff 實際也集中在 cross_day_ready()、build_cross_day_contexts() 與相關測試。

  可吸收 diff：

  - core/generator.py
  - services/cross_day_context.py
  - tests/test_cross_day_context.py
  - tests/test_generator_report.py
  - tests/test_market_theme_evidence.py
  - CHANGELOG.md 作為 Tech 交付文件

  worktree 殘留：

  - git status 僅上述 6 個 tracked modified，未見 unrelated untracked / extra diff；不建議「整包合併」超出這些候選 diff。

  未發現需要擴 table / field / schema。現有實作只讀既有白名單 source 與既有 select 欄位；若後續要新增 Owner-approved persistent source，需另開任務同步白名單。

  ## 跨區塊語意一致性

  generator 的 cross-day 直接消費者已收斂到 cross_day_ready()：

  - sort adjustment
  - repair label
  - detail history line
  - prepare promotion
  - duplicate action
  - tracking summary

  QA 額外反證結果：

  - pure DB position_events：ready=True，sort/prepare/dedupe/detail 生效。
  - mixed position_events + local_position_events：ready=False，sort=0、prepare=False、dedupe=None、detail=None。
  - missing source：同樣 fail closed。

  手機輸出抽查：

  - header 顯示 【05/29 盤中｜v20.4.1】。
  - mixed local source 不出現 追蹤最強 假歷史、不出現 連續觀察 5 天、前次 eliminated、權重 +2、歷史：。

  ## 使用者誤讀風險

  Owner 手機閱讀順序檢查：

  1. Summary 先看到 v20.4.1 header 與今日結論。
  2. mixed/local-only 情境下，summary 沒有把 local runtime 資訊包裝成「追蹤最強」或「連續觀察」。
  3. detail 沒有顯示假 previous state/action/date 或假權重。
  4. DB event same-level dedupe 仍可讓 Owner 看到「歷史停利已完成，同級不重複」。
  5. 高級風控仍優先，不會讓 Owner 因歷史 reduce 誤以為今日硬風控不用做。

  ## 質疑與反證

  主動質疑：如果 source_status=ready 但 source list 混入 local，舊邏輯可能 any() 通過，導致報文排序與 summary 假記憶。反證顯示新邏輯要求所有 source 都在 persistent whitelist，mixed source 已 fail closed。

  主動質疑：same-run today events 是否仍偷改 previous_action/date 或 dedupe。反證顯示 today events 被保留在 same_run_*，不再進 source_of_truth，不足源時 cross-day 欄位歸 unknown。

  主動質疑：歷史 dedupe 是否壓掉 v20.4.0 高級風控。反證顯示 REDUCE_50 硬風控仍輸出，沒有回退。

  ## 未測項目

  - 未跑 full pytest，符合 L2 / risk_patch 停止條件。
  - 未做 replay/backfill dry-run，TASK 明列非目標。
  - 未讀 production DB、未做 live Supabase write、未做 live Telegram delivery。
  - 未驗 Phase 2 source precedence / schema mapping，屬旁支待辦。

  ## QA 結論

  通過。
