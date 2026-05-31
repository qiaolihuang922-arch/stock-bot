# QA_REPORT:

  ## 測試範圍

  - QA 風險預算：risk_patch / L2。本輪只讀驗證 Tech 修復上一份 QA 阻塞點後的候選 diff，不擴大到 full replay、backfill、production DB live read/write 或 live Telegram。
  - 本輪最值得抓的 3 個風險：
      1. source_status=ready 且 previous_action=take_profit / dedupe_guard=prior_take_profit_completed，但 execution_memory 缺失或 sold_shares=0 時，2356 是否仍輸出「第二段停利 本次建議 56 股」或進明日計畫。
      2. 有 -112/-75 execution memory 時，2356 是否仍顯示已執行不重複，而不是被新的 blocked 分支誤擋。
      3. market/theme evidence 日期是否不只顯示 same_trade_date，且 strategy sample 0 不否定 market/theme production evidence。
  - 對應驗證：
      - 已讀 TASK.md、CHANGELOG.md、上一份 QA 阻塞報告、git status、git diff。
      - 已檢查 core/generator.py、services/cross_day_context.py、core/market_theme_evidence.py、services/market_theme_evidence_store.py、services/strategy_evidence.py 與對應 tests。
      - 已跑 touched-path tests，並補一段 QA 自建 fixture 按手機閱讀順序檢查 Summary / card / 明日計畫。
  - 停止條件：
      - TASK / CHANGELOG / diff 若矛盾且影響交付，阻塞。
      - 2356 缺 execution memory 或 sold_shares=0 仍出現 56 股或進明日計畫，阻塞。
      - 正常 -112/-75 execution memory 被誤判 blocked，阻塞。
      - 必要 L2 測試不可執行且無可用 runner 環境，阻塞。

  ## 風險預算與停止條件

  - 任務尺寸匹配：TASK.md 標示 risk_patch，QA 建議 L2；Tech 未觸及 DB schema / write path / live delivery，本輪不升級到 full matrix。
  - 可吸收 diff：
      - core/generator.py：版本升 v20.4.7，補 execution memory insufficient-data fail-closed，並同步 Summary / card / execution item / detail formatter。
      - services/cross_day_context.py：讀取 shares_before/shares_after，新增 latest execution memory 組裝。
      - core/market_theme_evidence.py、services/market_theme_evidence_store.py：補 actual/latest trade date 與 trend lookback_range 顯示，lookback rows 提高到 240。
      - services/strategy_evidence.py：strategy sample 層說明不影響 market/theme production confirmed evidence。
      - tests/test_generator_report.py、tests/test_market_theme_evidence.py：覆蓋正向、負向與日期顯示。
  - worktree 殘留：
      - tracked modified files 僅上述 8 個含 CHANGELOG.md；未看到其他 untracked 殘留。
      - QA 未修改 tracked file；只用 .qa_tmp 作測試暫存環境。
  - 停止條件未觸發。

  ## 關聯風險掃描

  - 上一份 QA 阻塞點已被針對性修正：core/generator.py 現在把 source_status=ready、已有 prior take-profit guard、但 execution_memory.sold_shares <= 0 的 second-stage take-profit 視為 blocked，文案為 execution memory
    insufficient-data｜不輸出重複停利股數。
  - services/cross_day_context.py 的 positive path 仍會把同一 latest trade date 的賣出 delta 組成 sell_deltas=[-112,-75]、sold_shares=187，供 generator 顯示已執行。
  - market/theme trend 查詢路徑仍有 .lte("trade_date", trade_date)，移除 trend 內部 4 日 gap filter 不會把 05/31 報文引入未來日期；本輪不擴成所有日期矩陣。
  - TASK.md 有重複拼接痕跡，但核心契約與 CHANGELOG.md、diff 一致，未構成本輪阻塞。

  ## 跨區塊語意一致性

  - 測試結果：
      - 初次用預設 Python 跑測試因 shell / venv 架構不一致失敗：pydantic_core arm64、當前需要 x86_64。
      - 改用 Tech 自檢同款 arch -arm64 後通過：
          - tests/test_generator_report.py -q：71 passed。
          - tests/test_market_theme_evidence.py tests/test_cross_day_context.py -q：39 passed。
          - git diff --check：通過。
  - QA 補充 fixture：
      - execution_memory=None：action 為 停利記憶不足，不含「本次建議 56 股」，Summary 無「明日計畫」，2356 未進明日計畫。
      - execution_memory.sold_shares=0：同上。
      - execution_memory.sell_deltas=[-112,-75]：action 為 第二段停利後觀察，Summary 顯示「已執行 1 項不重複」，card 顯示 production latest_trade_date=2026-05-29｜已賣出 -112、-75｜...｜第二段已執行，不含 56 股且不進明日
        計畫。
  - 手機閱讀順序檢查結果符合 TASK：Summary、持倉卡片、今日交易 / 已執行、持倉風控、明日計畫未再互相矛盾。

  ## 使用者誤讀風險

  - 2356 缺 memory 時，使用者不會看到明確賣出股數，也不會看到明日再賣第二段；改為「停利記憶不足」與「先補 production execution memory」。
  - 有 memory 時，使用者會看到 latest trade date、賣出 deltas、剩餘股數與第二段已執行，能理解不是 05/31 假日當天新賣出。
  - market/theme evidence fixture 顯示：
      - 證據日期：latest_trade_date=2026-05-29；report_date=2026-05-31 uses latest trading day evidence
      - lookback_range=2026-05-26~2026-05-29
      - 不再只有 same_trade_date。
  - strategy evidence 開頭明確寫明 strategy sample 層不影響 market/theme production confirmed evidence；樣本 0 不會否定 market/theme evidence。

  ## 質疑與反證

  - Tech 自檢已覆蓋負向案例，但 QA 另補了手機閱讀路徑反證，特別檢查「明日計畫」整段是否仍含 2356。結果 missing / zero memory 兩種情境均 HAS_TOMORROW_PLAN=False。
  - QA 也反證 positive path：-112/-75 execution memory 沒有被 insufficient-data 分支誤擋，仍走已執行不重複。
  - QA 另檢查 evidence 日期與 strategy sample 文案；未發現 sample 層覆蓋 production confirmed evidence 的輸出風險。

  ## 未測項目

  - 未跑 full pytest、full replay、backfill、production DB live read/write、live Telegram；符合本輪 L2 邊界。
  - 未逐檔驗證其他股票的 historical execution memory；同一路徑會自然套用，但逐檔資料 audit 屬旁支。
  - 未驗證所有 report date 的 trend lookback 組合；本輪只驗 2026-05-31 假日報文風險。

  ## QA 結論

  通過

  本輪候選 diff 可吸收；不要把 worktree 外的任何其他殘留當成本次合併內容。
