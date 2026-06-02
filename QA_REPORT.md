# QA_REPORT: evidence_gate_p1_p2_p4_20260602

  ## 測試範圍

  - 依 TASK.md 驗收 P1 / P2 / P4；任務尺寸 risk_patch、QA level 至少 L2。
  - 已讀 TASK.md、CHANGELOG.md、git diff，並抽查 core/generator.py、presentation/report.py、tests/test_generator_report.py。
  - 本輪沒有驗 P3/P5/P6/P7/P8，沒有做 replay/backfill/full repo pytest。
  - 可吸收 diff：CHANGELOG.md、core/generator.py、presentation/report.py、tests/test_generator_report.py。
  - worktree 殘留：.qa_tmp/ 內有既存 / 測試暫存檔，但未出現在 git status --short；QA 未修改 tracked file。

  ## 風險預算與停止條件

  - 風險 1：strategy_sample source-error 被誤寫成 price/OHLCV/RR source failure，或把可用價格藏掉。驗證：重跑 Tech probe 並補手機閱讀反證；停止條件為卡片仍顯示價格與 RR，但不進可買 / 觸發。
  - 風險 2：ledger / positions 不足時，持倉卡仍顯示精確股數、均價、今日買賣。驗證：重跑 P2 regression；停止條件為只顯示執行記憶不足，不與精確欄位並存。
  - 風險 3：RR 不可用 / 過熱或證據不足時，未持倉仍進可買 / 可準備 / 進場觸發，或完整證據正常案例被誤降級。驗證：重跑 renderer 回歸與補正常可買對照；停止條件為不足 fail-closed、完整證據仍可買。

  ## 關聯風險掃描

  - git diff 只改報文 context / renderer / tests / changelog；未見 services/analysis.py、DB schema、migration、Supabase write path、notifier/live Telegram 變更。
  - core/generator.py 版本常量仍為 v20.4.25，符合 CHANGELOG「未改 header 格式、不升版」說明。
  - git diff -U0 抽查未命中 calc_rr、def strategy、DB write、Telegram send 相關實質新增；未發現改 strategy decision、RR 公式、DB schema/write、live delivery。
  - 不是清理 / 瘦身 / refactor 任務，不適用 path / claim / evidence / risk / action 清理表阻塞條件。

  ## 跨區塊語意一致性

  - P1/P4：strategy_sample source-error 時，summary 顯示「新倉：無有效進場」、漏斗顯示 可買 0，未持倉卡為「不可行動｜策略樣本來源異常」，觸發為「無有效進場」，資料依據說策略樣本不納入買賣判斷；四者一致。
  - P2：ledger / execution memory insufficient 時，持倉卡顯示「今日執行：執行記憶不足，暫不顯示精確執行欄位」，測試確認不含 倉位：70股、均價、今日 買；資料依據包含「執行記憶：資料不足」。
  - 完整 strategy_sample evidence 對照案例仍顯示「新倉：可行動候選 1 檔」、可買 1、未持倉卡「可買」、S 5/5，未被誤降級。

  ## 使用者誤讀風險

  - 已按手機閱讀順序檢查 summary -> 未持倉漏斗 -> 卡片 -> 資料依據。
  - 補充反證：同一 BUY payload、price/OHLCV/RR available、strategy_sample source-error 時，不出現 price/OHLCV/RR source 或 價格：不可用（source missing），仍顯示 價格：100.0（+1.20%） 與 數據：RR 2.1｜S 證據不足｜V
    1.5x。
  - 同一 payload 換成完整 strategy evidence 後仍可買，避免使用者把本輪門控誤讀為「所有完整證據買點都被降級」。

  ## 質疑與反證

  - 重跑 Tech 焦點命令：3 passed, 105 deselected, 17 warnings。
  - 重跑完整 tests/test_generator_report.py：108 passed, 221 warnings。
  - 重跑 py_compile：core/generator.py presentation/report.py tests/test_generator_report.py passed。
  - git diff --check passed。
  - QA 補充手機閱讀 counter-probe passed：source-error 阻斷可行動分類，不歸咎 price/OHLCV/RR，不隱藏價格；完整證據正常可買案例不降級。

  ## 未測項目

  - 未測 P3/P5/P6/P7/P8。
  - 未做 production read-only smoke、正式 replay、backfill、live Telegram delivery。
  - 未跑全 repo pytest；本輪 L2 範圍集中在 tests/test_generator_report.py shared renderer / message list regression。

  ## QA 結論

  通過
