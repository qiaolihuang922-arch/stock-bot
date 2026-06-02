# QA_REPORT:

  ## 測試範圍

  本輪驗收 risk_patch_score_source_status_display_gate_20260602，範圍限於 S 分數 / 強弱補源門控：

  - 讀取 TASK.md、CHANGELOG.md、git diff。
  - 檢查可吸收 diff：presentation/report.py、tests/test_generator_report.py、CHANGELOG.md。
  - 確認 worktree 無其他 tracked 殘留；未發現 core/generator.py、strategy、RR、DB schema/write、live Telegram 相關 diff。
  - 未做 full repo pytest、replay、backfill、production smoke，符合 risk_patch / L2 範圍。

  ## 風險預算與停止條件

  本輪最值得抓的風險：

  1. score.source_status 非 available/derived 時，持倉/未持倉卡仍顯示 S n/5 或高信心 盤面：突破確認 / 極強。
      - 驗證：Tech probes + QA missing score manifest probe。
      - 停止條件：任一卡同時出現 S 證據不足/S 不可用 與 S 5/5、盤面：突破確認 或 極強。
  2. score 不可用時誤把價格/RR/volume 一起藏掉，造成手機讀者誤以為 price/RR source missing。
      - 驗證：source-error / missing score manifest 下確認價格仍顯示；未持倉 RR 仍顯示。
      - 停止條件：price/RR 可用 fixture 輸出被改成 source missing 或整卡不可讀。
  3. available/derived 正常案例被誤降級。
      - 驗證：Tech regression available/derived card 保留 S 5/5 與 盤面：突破確認。
      - 停止條件：正常資料出現 S 證據不足 或 強弱證據不足。

  ## 關聯風險掃描

  TASK / CHANGELOG / diff 一致：本輪只改 presentation formatter 與 regression tests，未擴到策略、RR、DB、live delivery。

  重跑 Tech 測試：

  - arch -arm64 .venv/bin/python -m pytest -q tests/test_generator_report.py -k 'score_source or breakout_distance'
      - 6 passed, 105 deselected, 13 warnings
  - arch -arm64 .venv/bin/python -m pytest -q tests/test_generator_report.py
      - 111 passed, 221 warnings
  - arch -arm64 .venv/bin/python -m py_compile presentation/report.py tests/test_generator_report.py
      - passed
  - git diff --check
      - passed

  額外 QA probe：

  - 建立持倉與未持倉手機卡 fixture，price / daily_ohlcv / RR / volume 可用，但 stock.TEST.score manifest 缺失。
  - 結果：持倉與未持倉皆不含 S 5/5、S 4/5、極強、盤面：突破確認；皆顯示 S 證據不足 與 盤面：強弱證據不足｜待確認；價格保留；未持倉 RR 2.1 保留。

  ## 跨區塊語意一致性

  持倉卡：

  - 數據 行從 S 5/5 降為 S 證據不足。
  - 盤面 行同步降為 強弱證據不足｜待確認。
  - 價格行仍顯示，持倉非加碼 RR 仍維持既有 新倉 RR：不適用（既有持倉） 契約。

  未持倉卡：

  - source-error 與 missing score manifest 都不再顯示數值型 S 分數。
  - 盤面 不再顯示高信心突破確認。
  - price/RR/volume 可用資訊未被 score gate 誤藏。

  正常資料：

  - available/derived regression 保留 S 5/5 與 盤面：突破確認，未被降級。

  ## 使用者誤讀風險

  按手機閱讀順序檢查卡片主體：

  - 先看到標題與行動，再看到 盤面：score 不足時已改成低信心文字，不會先給 突破確認。
  - 再看到 數據：score 不足時顯示 S 證據不足 或 S 不可用，不會同列出現 S 5/5。
  - 後續價格/RR 可用時仍保留，避免讀者誤解成整體價格或 RR source missing。

  ## 質疑與反證

  主動反證 Tech 未覆蓋的缺 score manifest 路徑：stock.TEST.score 欄位完全缺失，但 price/RR/volume 仍可用。結果通過，證明缺欄位 fail closed 且不牽連 price/RR。

  另檢查 diff 未碰 core/generator.py、services、DB/migrations/supabase 路徑；未看到 strategy decision、RR 公式、DB schema/write、live Telegram 變更。

  ## 未測項目

  - 未驗其他 evidence gate 清單項，依 TASK 不納入本輪。
  - 未驗 production read-only smoke、Telegram live delivery、backfill/replay。
  - 無 report_context 的 legacy direct card wrapper 仍屬既有無 evidence manifest 呼叫形態；本輪 QA 只按 TASK 的手機 report/evidence_manifest 路徑驗收，若要把無 context 呼叫也強制視為 missing-source，需另開契約任務。

  ## QA 結論

  通過
