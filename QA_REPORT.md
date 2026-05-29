# QA_REPORT:

  ## 測試範圍

  任務：evidence_chain_production_closure_gap_20260529，risk_patch / QA L2+。本輪最小驗證範圍聚焦 production source-of-truth contract、no-schema-change evidence、read-only smoke fail-closed、以及無 live side effect；未擴
  成 full pytest、replay、backfill 或 live DB 驗證。

  已驗證命令：

  - arch -arm64 .venv/bin/python -m pytest tests/test_market_theme_evidence_handoff.py tests/test_market_theme_evidence.py -q：31 passed，17 warnings。
  - arch -arm64 .venv/bin/python scripts/smoke_market_theme_evidence_readonly.py：exit 2，符合缺 read-only env 時 fail-closed；輸出含 schema_decision: no-schema-change、telegram_confirmed: false。
  - git diff --check：passed。
  - QA 追加 one-off 反證：直接呼叫 load_confirmed_market_theme_evidence() 驗證 forbidden / allowed source_family。

  可吸收 diff 必須包含：

  - tracked：CHANGELOG.md
  - tracked：docs/handoff/evidence_chain_market_theme_ops_artifacts.md
  - tracked：scripts/smoke_market_theme_evidence_readonly.py
  - tracked：services/market_theme_evidence_store.py
  - tracked：tests/test_market_theme_evidence_handoff.py
  - untracked 但本輪交付必要：docs/handoff/evidence_chain_production_closure_gap_assessment.md

  不得只用 git diff / git diff --stat 吸收，否則會漏掉 untracked assessment doc。

  ## 風險預算與停止條件

  本輪最值得抓的風險：

  1. forbidden source_family=local/runtime/cache/worktree/report-derived/synthetic/default/test/fixture 被 loader 誤判 confirmed。
      - 驗證：pytest 覆蓋 + QA 追加 report_derived、test 等變體 one-off。
      - 結果：均 insufficient-data / confirmed=False / telegram_confirmed=False。
  2. allowed production_db、owner_approved_persistent、market_data 被過度封死。
      - 驗證：QA 追加直接 consumer probe。
      - 結果：單一合法 row 均 status=confirmed / confirmed=True。
  3. no-schema-change / manual boundary 被文件誤讀成 production 已上線或已 backfill。
      - 驗證：讀 assessment、ops handoff、SQL template、diff side-effect scan。
      - 結果：文件明確寫 repo-side only、Owner manual only、未 live write / backfill / RLS / Telegram。

  停止條件：完成上述 contract 測試、diff side-effect scan、schema evidence spot-check 後停止；不做 live Supabase、正式 backfill、RLS 實測、Telegram delivery、full pytest。

  ## 關聯風險掃描

  TASK.md、CHANGELOG.md 與 diff 大體一致：Tech 交付 no-schema-change assessment、smoke schema_decision、loader source-family guard、局部測試。schema evidence 可由既有 SQL schema、manual template、loader SELECT_FIELDS /
  confirmed condition 交叉核對。

  QA 追加發現一個非阻塞行為：若查回 rows 同時含 forbidden row 與 allowed row，目前 _validate_rows() 會因任一 forbidden row 直接 insufficient-data，即使後面有 allowed confirmed row。這是保守 fail-closed，不會 fake
  confirmed；但未來 production 若混入舊 local/test rows，可能造成合法 evidence 被壓掉。列為後續風險，不阻塞本輪「不得 fake confirmed」主目標。

  未看到本輪 diff 修改 core/generator.py、Telegram formatter、VERSION、strategy thresholds、SQL migration/backfill 執行入口或 notifier。

  ## 跨區塊語意一致性

  CHANGELOG、assessment doc、smoke output、SQL template 的語意一致：

  - schema_decision: no-schema-change
  - no live Supabase write
  - no formal backfill
  - no production RLS/grant change
  - no live Telegram delivery
  - production closure 尚未完成
  - Owner 仍需提供 read-only env / rows / manual approval

  core/generator.py 的 VERSION 仍是 v20.4.3，本輪未改 Telegram 使用者可見版本契約。

  ## 使用者誤讀風險

  Owner 手機 Telegram 路徑本輪不變；缺 production confirmed rows 或 forbidden source rows 時 smoke / loader 都不會輸出 telegram_confirmed=true。因此不會因 repo artifact 存在而讓 Telegram 變成「題材 confirmed」或「新倉可
  買」。

  文件 wording 未暗示 SQL 已執行、RLS 已完成、backfill 已上線；assessment 的「Not Done」段落足夠清楚。

  ## 質疑與反證

  反證一：forbidden source row 即使同時是 fresh + confirmed + supporting，load_confirmed_market_theme_evidence() 仍 fail closed。QA one-off 覆蓋 local、runtime、cache、worktree、report-derived、report_derived、
  synthetic、default、test、test_fixture、fixture。

  反證二：allowed persistent source row 可 confirmed。QA one-off 覆蓋 production_db、owner_approved_persistent、market_data，皆 confirmed。

  反證三：read-only smoke 缺 env 時不 fallback live write，不使用 Telegram；實測 exit 2 且 telegram_confirmed: false。

  ## 未測項目

  未測 live Supabase read-only env、production rows、RLS/grant 實際結果、正式 backfill、live Telegram delivery；這些都被 TASK 明確排除，需 Owner 單獨批准。

  未跑 full pytest / replay / backfill dry-run；依 L2+ 與本輪停止條件不擴大。

  ## QA 結論

  通過

  條件說明：Architect 吸收時必須把 untracked docs/handoff/evidence_chain_production_closure_gap_assessment.md 一併納入可吸收 diff；不能只合併 tracked git diff。混合 forbidden+allowed rows 的保守 fail-closed 行為建議列後
  續風險，但不阻塞本輪驗收。
