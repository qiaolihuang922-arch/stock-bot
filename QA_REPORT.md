# QA_REPORT:

  ## 測試範圍

  本輪任務尺寸為 normal_patch，QA level 為 L2。我沒有擴成 full pytest / replay / backfill / live DB 驗證；驗證集中在 TASK 指定的 generator/report consumption、fresh-run 等價反證、source 邊界與手機閱讀誤讀風險。

  已檢查文件與 diff：

  - TASK.md、CHANGELOG.md
  - git diff --stat / git diff --name-only
  - core/generator.py
  - scripts/smoke_market_theme_evidence_readonly.py
  - tests/test_market_theme_evidence.py
  - 直接消費者：formatTelegramSummary()、formatTelegramMessages()、ai_supply_chain_mainline_supported()、read-only smoke CLI

  可吸收候選 diff 限於：

  - CHANGELOG.md
  - core/generator.py
  - scripts/smoke_market_theme_evidence_readonly.py
  - tests/test_market_theme_evidence.py

  worktree 殘留：

  - 未看到其他 tracked file 變更。
  - .qa_tmp/ 只作為本輪測試暫存使用，不應視為產品 diff。

  執行命令：

  - git diff --check：通過
  - arch -arm64 .venv/bin/python -m pytest tests/test_market_theme_evidence.py -q：29 passed
  - arch -arm64 .venv/bin/python -m pytest tests/test_generator_report.py -q：69 passed
  - arch -arm64 .venv/bin/python scripts/smoke_market_theme_evidence_readonly.py --trade-date 2026-05-29 --production-trend-consumption-check-json：exit 2，fail-closed 為 source-error，原因為本 QA 沙盒下讀取外部 source
    受限，未宣告 consumed。
  - 額外 inline 反證：runtime/local source row 不會讓 fresh_runner_rebuild passed；手機 summary header 仍為 v20.4.6，且 evidence trend 不在新倉行動前誤導買入。

  ## 風險預算與停止條件

  本輪最值得抓的 3 個風險：

  1. fresh_runner_rebuild=passed 是否其實靠 local/runtime/cache
     驗證：用 mocked persistent rows 驗 passed；再用 source_family=runtime row 反證 blocked。
     停止條件：runtime/local row 不得 passed，且 uses_runtime_or_local_cache_as_history=false。
  2. diagnostic JSON 是否把 daily_signal_snapshot 包裝成 market/theme trend source
     驗證：檢查新增測試與 fake client table access；daily_signal_snapshot 存在但未被查詢。
     停止條件：只讀 market_theme_confirmed_evidence，uses_only_daily_signal_snapshot=false。
  3. 使用者可見 Telegram/report 是否被本輪偷偷改壞
     驗證：檢查 VERSION 未改；跑 tests/test_generator_report.py；用手機閱讀順序檢查 summary。
     停止條件：header 維持 v20.4.6，新倉決策先於 evidence 背景，evidence trend 不產生「今日可買」誤讀。

  ## 關聯風險掃描

  TASK / CHANGELOG / diff 整體一致：

  - TASK 要求新增 fresh-run consumption verification report；diff 新增 build_market_theme_production_trend_consumption_check() 與 smoke CLI flag。
  - TASK 禁止 DB schema、data write、live Telegram；diff 未碰 schema / write path / Telegram delivery。
  - TASK 禁止修改 Telegram/report 文案與 header；diff 未改 VERSION = "v20.4.6"，formatter 文案未改。
  - TASK 要求 sector_theme_members=latest-only-blocked、market_theme_index_daily_bars=not-consumed；新增 report 固定保持此狀態。
  - CHANGELOG 宣稱未改策略、watchlist、持倉狀態機；diff 符合。

  需要標明邊界：

  - 新增 consumption check 的 entrypoint 是 core.generator.market_theme_summary_evidence，屬於正式 formatter 會使用的等價 evidence helper smoke，不是完整跑一次 production Telegram generator。
  - 真實 production DB / GitHub runner credentials 未在本 QA 沙盒完成讀取；CLI 正確 fail-closed 為 blocked/source-error，未被誤報 consumed。

  ## 跨區塊語意一致性

  JSON contract 檢查結果一致：

  - 成功路徑：mocked persistent DB rows 可得到 fresh_runner_rebuild=passed、uses_market_theme_confirmed_evidence_history=true、trend days > 0。
  - 缺 source / source error 路徑：CLI exit 2，fresh_runner_rebuild=blocked，未宣告 consumed。
  - runtime/local row 反證：fresh_runner_rebuild=blocked、uses_history=false，不把 runtime row 當 production history。
  - daily_signal_snapshot 反證：即使 fake client 有 snapshot row，也沒有被查詢為 market/theme trend source。

  ## 使用者誤讀風險

  手機閱讀順序檢查：

  - Summary 第一行仍是 【05/29 盤中｜v20.4.6】，本輪未偷升/降版。
  - 🧭 新倉：無有效進場。 出現在 evidence confirmed / trend 行之前。
  - evidence 行顯示為背景追溯，仍包含「限制：題材可追蹤，不代表可買」。
  - 未出現 今日可買 或 可買：台積電 這類會把 trend 誤讀成買進建議的文字。

  結論：本輪新增 diagnostic 不會改 Owner 手機上的買賣判斷順序；現有報文仍把 market/theme trend 放在背景追溯，而不是交易指令。

  ## 質疑與反證

  主動反證 Tech 未完全覆蓋的路徑：

  - 反證 source_family=runtime 的 confirmed-like row：結果仍 blocked，沒有 passed。
  - 反證目前 QA 沙盒不能讀 production DB：CLI 回 source-error / blocked，沒有把 source-error 降級成 consumed。
  - 反證手機誤讀：confirmed trend summary 不會產生可買文字，且新倉無進場先於 evidence 背景。

  未發現 TASK / CHANGELOG / diff 不一致到需要 blocked 的問題。

  ## 未測項目

  - 未讀真實 production Supabase rows；目前 QA 沙盒執行 read-only CLI 得到 source-error，只能確認 fail-closed。
  - 未跑 full pytest、replay、backfill dry-run，因 TASK 尺寸為 normal_patch / L2，且本輪非 write/backfill/schema 任務。
  - 未驗證 GitHub runner 真實 secret/env 是否存在；本輪只驗證 mocked persistent DB rows 可 fresh-run 重建，以及缺 source 時不誤報 consumed。

  ## QA 結論

  通過

  本輪可吸收候選 diff 與 TASK 範圍一致；核心 consumption check、fresh-run 等價反證、daily_signal_snapshot 邊界、Telegram 手機誤讀風險均已覆蓋。真實 production DB / GitHub env 仍是後續 read-only 環境確認項，不構成本輪
  blocked，因程式在缺 source/error 時已 fail closed。
