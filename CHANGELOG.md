# CHANGELOG: v20.4.36 06/04 報文手機閱讀一致性收斂

  ## 任務尺寸與風險

  - 任務尺寸：normal_patch
  - 風險：使用者可見 Telegram message-list formatter 變更；不改策略、RR、DB schema/write、live Telegram。
  - 版本：維持 v20.4.36，未改 core/generator.py 的 VERSION。

  ## 修改內容

  - 正常 source 狀態不再逐卡顯示「持倉與現價已確認」或「現價與 OHLCV 已確認」。
  - 普通 cross-day observe / 修復中 / 連續觀察 1 天 / 權重 +1 歷史行不再逐卡刷屏；仍保留高風險或 execution memory 類歷史。
  - 未持倉原因優先級改為淘汰 / 突破失敗 / 風控優先於過熱；量能不足顯示 證據：量能不適用。
  - 建準類 BUY 若單檔回測偏弱 / 無明顯優勢 / 樣本不足，卡片補短句：回測僅輔助，分批小倉、不追價。
  - 首屏今日買入摘要在今日已買數大於 0 時改為 今日已買 N｜風控中 M，避免裸寫 今日新建倉 3。
  - 新增 06/04 official formatTelegramMessages message-list replay，覆蓋六個 failure specimen。

  ## 修改檔案

  - core/generator.py
  - presentation/report.py
  - tests/test_generator_report.py

  ## 最小改動策略

  - 僅改 formatter/source-status/cross-day display 與 message-list replay 測試。
  - 未改 strategy decision、RR 公式、payload 來源、DB write path、runner 或 Telegram live delivery。
  - `CHANGELOG.md` 由 Tech handoff 產生並由 Architect 收口同步；不屬產品 formatter diff。

  ## 契約影響

  - 使用者可見 message list 文字局部變更。
  - 回測單檔格式保留 回測（建準）：...。
  - 正常資料提示由逐卡顯示改為異常才顯示。
  - 未改函式回傳結構、DB payload、策略 decision payload。
  - 版本維持 v20.4.36。

  ## 直接消費者同步

  - presentation/report.py formatter 已同步 official generator 消費路徑。
  - tests/test_generator_report.py 以 official formatTelegramMessages final message list replay 驗證，非 helper-only。

  ## 未影響模組

  - 未改 services/analysis.py。
  - 未改 RR 公式。
  - 未改 DB schema / RLS / grant / policy / role / index / constraint。
  - 未改 DB write path。
  - 未執行 production backfill、production write 或 live Telegram。

  ## 已跑自檢命令

  - ./.venv/bin/python -m pytest ...：blocked by architecture mismatch，pydantic_core arm64 wheel 被 x86_64 Python 載入失敗。
  - arch -arm64 ./.venv/bin/python -m pytest tests/test_generator_report.py -k '0604_v20_4_36_mobile_readability or v20_4_36_non_actionable or v20_4_36_failed_unheld or v20_4_36_single_backtest or
    structural_artifacts_cover_three_fail_closed_cases or presentation_noise' -q：9 passed。
  - arch -arm64 ./.venv/bin/python -m pytest tests/test_generator_report.py -q：139 passed / 26 failed；失敗集中在既有舊測仍期待 0-count 噪音或舊非行動分數顯示，與目前 v20.4.36 降噪契約不一致。
  - git diff --check：passed。
  - PYTHONPYCACHEPREFIX=/private/tmp/tech_write_pycache arch -arm64 ./.venv/bin/python -m py_compile core/generator.py presentation/report.py tests/test_generator_report.py：passed。

  ## 殘留風險

  - 未取得 production runner artifact 或 Owner 06/04 原始完整報文，只用等價 official message-list fixture 覆蓋。
  - 全量 tests/test_generator_report.py 仍有 26 個舊契約斷言失敗；本輪未擴大更新整批 legacy 測試。
  - QA 仍需沿同一 message-list replay 補手機誤讀或契約風險反證。

  ## 旁支待辦

  - 另開任務整理 legacy generator tests 中 0-count / 舊分數顯示斷言與 v20.4.36 降噪契約的衝突。
  - 若 Owner 要驗正式 06/04 runner 報文，需另由 Architect/QA 取得 read-only artifact；本輪未做 live delivery。
