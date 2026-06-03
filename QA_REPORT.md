# QA_REPORT: Render market/theme evidence freshness check 與幂等補寫

## 測試範圍

- 任務：`render_market_theme_evidence_freshness_20260603`
- QA 分級：L3。
- 範圍：
  - Render `/` route preflight 行為。
  - Phase3 freshness-only CLI。
  - market/theme completeness 與 read-after-write fail closed。
  - backfill CLI / workflow range contract。
  - 靜態語法與 diff hygiene。

## 關聯風險掃描

- DB schema：未變更。
- Production write path：仍走既有 `upsert_source_payloads()` / approved backfill script interface；未手寫 DML。
- Telegram live delivery：未觸發。
- Telegram 報文格式 / VERSION：未改。
- Strategy / RR / holding state：未改。
- Render high-frequency risk：preflight 失敗會 blocking dispatch，避免錯誤資料下仍發報文；這是 intentional fail closed。

## 跨區塊語意一致性

- `TASK.md` 要求 Render 每次啟動可呼叫 freshness check；`app.py` 已在 dispatch 前呼叫。
- `TASK.md` 要求已完整日期跳過不重寫；test 覆蓋 `already-complete` 且 backfill 未被呼叫。
- `TASK.md` 要求未到 14:00 只讀不寫；test 覆蓋 `skipped-before-safe-write-time` 且 backfill 未被呼叫。
- `TASK.md` 要求缺失且 14:00 後補寫並驗證；test 覆蓋 `backfilled-and-verified`。
- `TASK.md` 要求某日 read-after-write mismatch fail closed；test 覆蓋 `read-after-write-mismatch` 與非成功狀態。
- `TASK.md` 要求 backfill 不再 May-only；workflow / CLI tests 覆蓋 `--historical-range --start-date --end-date`。

## 使用者誤讀風險

- `MARKET_THEME_FRESHNESS_FAILED` log 帶 `trade_date / source / stage / reason / action=fail_closed`，可直接知道卡在哪一層。
- freshness report 帶 `version=market_theme_freshness_v1`，不混同 Telegram 報文版本。
- 已寫過但只寫一條 confirmed row 的情境不會被誤判完整；本輪新增反證，必須 9 個官方 TWSE 題材 key 齊全才跳過。

## 失敗標本反證

- Owner 標本：Render 每 5 分鐘啟動，不是手動 GitHub Action；6/1、6/2、6/3 因舊流程漏寫，market/theme 仍停在 5/29。
- 反證路徑：
  - Render route：freshness failure blocks workflow dispatch and already-sent tag。
  - Freshness helper：最近交易日已完整時跳過，不重寫。
  - Freshness helper：部分 confirmed rows 不算完整，會補寫。
  - Freshness helper：14:00 前不寫。
  - Freshness helper：14:00 後缺失會補寫並 read-after-write。
  - Freshness helper：read-after-write 仍缺 business key 時 fail closed。
  - Workflow：manual backfill step 傳入 `start_date/end_date`。

## 質疑與反證

- 質疑：Render 每 5 分鐘會不會無腦寫？
  - 反證：`already-complete` fixture 中 backfill calls 為空。
- 質疑：半寫入是否會被誤判已完成？
  - 反證：只有一條 confirmed row 的 fixture 會觸發 backfill。
- 質疑：未到安全時間是否會寫 DB？
  - 反證：13:55 fixture backfill calls 為空。
- 質疑：失敗後是否仍發 workflow？
  - 反證：`test_freshness_failure_blocks_dispatch_before_sent_tag` 確認 `already_sent` 與 workflow dispatch 都未執行。

## 已跑命令

- `arch -arm64 .venv/bin/python -m pytest tests/test_app_render_preflight.py tests/test_phase3_evidence_automation.py tests/test_market_theme_source_backfill.py tests/test_workflow_runtime_config.py`
  - 結果：45 passed。
- `PYTHONPYCACHEPREFIX=/private/tmp/stock_bot_pycache_main arch -arm64 .venv/bin/python -m py_compile app.py scripts/run_phase3_evidence_automation.py scripts/backfill_market_theme_sources.py`
  - 結果：passed。
- `git diff --check`
  - 結果：passed。

## 未測項目

- 未在 Render production runtime 實際跑 5 分鐘 endpoint。
- 未執行本輪新 freshness preflight 對 production DB 的 live write。
- 未跑 full pytest。
- 未驗證 Render timeout / memory / cold start 表現。

## QA 結論

conditional pass

理由：程式碼、helper、runner route、workflow/CLI contract 的 L3 反證已通過；但 production Render 部署後的實際 5 分鐘觸發 log 尚未取得，因此不能宣稱 production runtime 已完全驗收。程式 diff 可吸收，部署後需看一次 Render log 或 GitHub dispatch artifact，確認 freshness preflight 在真實環境輸出 `already-complete` 或 `backfilled-and-verified`。
