# QA_REPORT:

  ## 測試範圍

  - 任務尺寸 / QA level：risk_patch、L2+；未擴成 full pytest / replay / backfill / production smoke。
  - 讀取：TASK.md、CHANGELOG.md、git status、git diff、services/market_theme_evidence_store.py、tests/test_market_theme_evidence_handoff.py、相關 generator/provider 局部消費路徑。
  - 可吸收 diff：
      - services/market_theme_evidence_store.py
      - tests/test_market_theme_evidence_handoff.py
      - CHANGELOG.md
  - worktree 殘留：tests/test_market_theme_evidence_handoff.py 目前是 untracked；合併時需明確納入，不能只合併 tracked diff。

  ## 風險預算與停止條件

  本輪最值得抓的風險：

  1. fake/runtime/local/cache/worktree/report-derived/test fixture 旁路產生 confirmed 或 SQL。
      - 驗證：Tech 測試 + QA smoke 直接呼叫 builder 與 renderer。
      - 停止條件：invalid source confirmed=False、handoff_ready=False、rows=[]、sql=""。
  2. 直接 renderer 繞過 builder validator。
      - 驗證：render_market_theme_evidence_handoff_sql([])、None、runtime/local/report-derived rows。
      - 停止條件：全部回空字串、不拋例外、不產生 SQL。
  3. handoff artifact 被誤讀為 live write 或 fresh runner local state。
      - 驗證：靜態掃描只見 loader .execute() read path，無 insert/upsert/update/delete；generator 仍只讀 production loader。
      - 停止條件：無 live write API、無 Telegram/header diff、殘留 production backfill/RLS/smoke 明確標為 manual/follow-up。

  ## 關聯風險掃描

  - TASK.md / CHANGELOG.md / diff 一致：本輪實作確實只新增 non-live handoff builder、SQL renderer、測試；未改 strategy threshold、Telegram formatter、runner、watchlist、schema/RLS。
  - 直接 renderer 無旁路：invalid rows 會套 _validate_handoff_row()；[] 與 None 回 ""。
  - fake source 反證：QA smoke 覆蓋 runtime、runtime-cache、local、local-cache、cache、worktree、test、test-fixture、test_fixture、report_derived、report-derived、synthetic、fixture、default，均不產生 SQL。
  - handoff no live write：新增 helper 只回傳 SQL 字串，live_write=False；未發現新增 Supabase write API。
  - fresh runner：core/generator.py 仍呼叫 load_confirmed_market_theme_evidence()，無本地 handoff 狀態依賴；無 DB/env 時 fail closed 為 missing-source / source-error。
  - DB matrix：CHANGELOG.md 已區分 consumed、reference-only、write-only/reference-only、manual-owner-step；沒有把 market_daily_bars、signal_runs/items/outcomes 說成 generator 直接策略來源。

  ## 跨區塊語意一致性

  - CHANGELOG.md 同時聲明 non-live handoff、manual SQL、no agent live write、production ingestion/backfill/RLS/smoke follow-up，與 diff 行為一致。
  - 關係圖從 raw true source -> builder -> manual SQL -> production table -> loader -> provider -> generator -> Telegram evidence block，狀態標示沒有把 handoff SQL 誤標為已寫入 production。
  - core/generator.py 版本仍為 v20.4.3；本輪未改 Telegram 使用者可見報文，版本契約可接受。

  ## 使用者誤讀風險

  - Owner 手機閱讀順序檢查：本輪未改 Telegram message list；既有缺 source 文案仍是「證據：production 來源不足，不作確認。」而不是 confirmed 或可買。
  - confirmed 文案只應來自 production table fresh rows；handoff builder 自身固定 confirmed=False，不會讓 Owner 在未手動寫 DB 前看到 confirmed。
  - 殘留風險已標明 production write/backfill/RLS/smoke 未完成，不應被解讀為已上線或已完成正式 ingestion。

  ## 質疑與反證

  - 質疑：Tech 測試只靠 builder 是否可能漏掉 renderer 直接呼叫？
      - 反證：測試與 QA smoke 均直接呼叫 renderer；invalid/empty/None 不產生 SQL。
  - 質疑：report-derived 變體是否可能繞過禁止清單？
      - 反證：report_derived 與 report-derived 都被 QA smoke 驗證為無 SQL；後者即使不是明確 forbidden，也因不在 allowlist 被拒絕。
  - 質疑：handoff SQL 是否讓 fresh runner 不經 production DB 就 confirmed？
      - 反證：generator/provider 消費仍走 production loader；handoff helper 沒被 generator 呼叫，且 builder 回傳 confirmed=False。

  測試命令：

  - arch -arm64 .venv/bin/python -m pytest tests/test_market_theme_evidence_handoff.py tests/test_market_theme_evidence.py -q：25 passed，17 warnings。
  - QA smoke：14 種 fake/local/runtime/report-derived source + renderer empty/None + no DB fresh-run fail closed，通過。

  ## 未測項目

  - 未連 production DB。
  - 未驗證 RLS/read-only role。
  - 未做 formal backfill / replay。
  - 未執行 live Supabase write。
  - 未執行 live Telegram delivery。
  - 未做 full pytest；符合本輪 L2+ 停止條件。

  ## QA 結論

  通過。

  本結論只代表本輪可吸收 diff 通過：non-live handoff builder、direct renderer fail-closed、fake source 不產生 confirmed/SQL、fresh runner 不依賴 local handoff。不得解讀為 production ingestion/backfill/RLS/smoke 已完成或
  已上線。
