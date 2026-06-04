# QA_REPORT:

  ## 測試範圍

  本輪依 TASK.md 判定為 normal_patch / QA L2，驗證範圍收斂在 v20.4.36 06/04 Telegram 手機閱讀一致性、official message-list replay、formatter diff 與 handoff 一致性；未擴成 production runner artifact、live Telegram、DB、
  RR 公式或策略決策驗證。

  已讀取：TASK.md、CHANGELOG.md、git status --short、git diff --stat、core/generator.py diff、presentation/report.py diff、tests/test_generator_report.py diff。

  目前 worktree modified：

  - 可吸收產品 / 測試 diff：core/generator.py、presentation/report.py、tests/test_generator_report.py
  - handoff 文件殘留：CHANGELOG.md
  - 無 untracked 檔案；未建議整包合併。

  執行命令：

  - arch -arm64 ./.venv/bin/python -m pytest tests/test_generator_report.py -k '0604_v20_4_36_mobile_readability or v20_4_36_non_actionable or v20_4_36_failed_unheld or v20_4_36_single_backtest or
    structural_artifacts_cover_three_fail_closed_cases or presentation_noise' -q：9 passed
  - arch -arm64 ./.venv/bin/python -m py_compile core/generator.py presentation/report.py tests/test_generator_report.py：passed
  - git diff --check：passed
  - 額外 official formatTelegramMessages probe：passed

  ## 風險預算與停止條件

  本輪最值得抓的 3 個風險：

  1. TASK.md / CHANGELOG.md / diff 不一致，尤其上一輪 conditional pass 的 CHANGELOG 自述矛盾是否仍存在。
      - 驗證：比對 handoff、diff 檔案、版本聲明與未影響模組。
      - 停止條件：若 CHANGELOG 仍描述舊任務或 diff 不屬本輪，結論 blocked / conditional pass。
  2. 手機首屏與卡片由上往下閱讀時仍互相打架。
      - 驗證：focused official message-list replay 覆蓋六個 06/04 failure specimen。
      - 停止條件：若仍有裸「今日新建倉 3」、正常資料行刷屏、突破失敗被過熱覆蓋、建準回測偏弱缺解釋，結論 blocked。
  3. 降噪過度刪掉該保留的 execution memory / 高風險歷史。
      - 驗證：QA 額外用 official formatTelegramMessages 建立普通 observe 與已賣記憶對照；普通歷史需隱藏，execution memory 需保留。
      - 停止條件：若兩者都被隱藏或都刷屏，結論 blocked / conditional pass。

  ## 關聯風險掃描

  TASK.md 要求不改策略、RR、DB schema/write、live Telegram。diff 只落在 formatter、source-status/cross-day display、summary 文案與 replay 測試；未看到 services/analysis.py、DB、runner、Telegram live delivery 變更。

  版本契約一致：core/generator.py 仍為 VERSION = "v20.4.36"，CHANGELOG 也寫版本維持 v20.4.36。

  清理 / 瘦身 / refactor 證據表要求不適用；本輪不是清理任務。

  ## 跨區塊語意一致性

  official replay 覆蓋並通過：

  - 首屏含 今日已買 3｜風控中 2，不再裸寫 今日新建倉 3。
  - 正常持倉卡不再逐卡顯示 資料：持倉與現價已確認...。
  - 正常未持倉卡不再逐卡顯示 資料：現價與 OHLCV 已確認...。
  - 光寶科等量能卡顯示 RR -（量能不足） 與 證據：量能不適用。
  - 群創 / 技嘉淘汰突破失敗卡顯示風控不可用，不被過熱文案覆蓋。
  - 建準可買且回測偏弱時保留 回測（建準）：...，同卡補 回測僅輔助，分批小倉、不追價。

  CHANGELOG 現在描述本輪 06/04 手機閱讀收斂，已不再混入上一輪 trend_continuation monitor / data basis 任務內容；與 diff 一致。

  ## 使用者誤讀風險

  手機閱讀順序檢查結果可吸收：首屏先交代今日已買與風控數，再列新倉建議；卡片內 RR / 不適用原因 / 證據不適用原因 對量能不足與突破失敗維持同一主因。

  QA 額外反證：普通 observe / 修復中 / 連續觀察 1 天 / 權重 +1 已被隱藏；但 source_of_truth=position_events 且 previous_action=sold 的 execution memory 仍保留歷史行。這降低了「降噪把重要已賣/風控記憶一併消掉」的契約風
  險。

  ## 質疑與反證

  質疑 1：Tech 是否只測 helper？
  反證：新增測試與 QA 額外 probe 都使用 official generator.formatTelegramMessages final message list，不是 private helper-only。

  質疑 2：CHANGELOG 是否仍與本輪任務矛盾？
  反證：目前 CHANGELOG 標題、任務尺寸、修改檔案、契約影響、覆蓋層級都指向 06/04 mobile readability；不再描述舊 trend_continuation monitor 作為本輪修改。

  質疑 3：全量 tests/test_generator_report.py 有 26 failed 是否阻塞本輪？
  判斷：不阻塞本輪 L2。CHANGELOG 已明列 full generator suite 仍有 26 個 legacy 舊契約失敗，且本輪 focused replay / contract tests 通過。這是旁支 legacy 測試整理風險，不應擴成本輪 full-suite 修復；但 Architect 收口時不得
  把它描述成全量測試通過。

  ## 未測項目

  - 未取得 Owner 06/04 原始完整 production 報文；本輪使用等價 official message-list fixture。
  - 未跑 production runner artifact、live Telegram、DB read/write、backfill。
  - 未重跑全量 pytest；已知 tests/test_generator_report.py -q 仍有 26 個 legacy contract failures，列為後續風險。
  - 未驗 RR 數值合理性與策略 decision，符合 TASK 非目標。

  ## QA 結論

  通過

  本輪 TASK / CHANGELOG / diff 已一致；focused official message-list replay 與 QA 額外手機誤讀反證通過。可吸收範圍限 core/generator.py、presentation/report.py、tests/test_generator_report.py 的本輪 formatter / replay
  diff，以及 CHANGELOG.md handoff 修正；不要把已知 full generator legacy failures 宣稱為已解決。
