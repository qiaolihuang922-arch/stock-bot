# CHANGELOG:

  ## 任務尺寸與風險

  - 任務尺寸：normal_patch
  - 風險判斷：改 correction audit 的 JSON / CLI 輸出語義與 next_action 判讀，但不碰 DB write、backfill、schema、策略 decision、Telegram 報文或 live delivery。

  ## 修改內容

  - 修正 correction audit 對 daily_signal_snapshot 的判讀：
      - 新增全版本五月歷史 coverage 判斷：daily_signal_snapshot.history_coverage。
      - 將 current core/generator.py VERSION 五月 rows 改為 run-health diagnostic：daily_signal_snapshot.current_version_run_health。
      - current VERSION 舊五月 0 rows 現在輸出 diagnostic=current_version_old_month_zero_rows 且 blocks_history_coverage=false，不再加入 blocked_reason。
  - 保持 market/theme historical coverage blocked：
      - market_theme_confirmed_evidence / market_theme_index_daily_bars latest-only 仍不放行。
      - sector_theme_members mapping-only 仍不當作五月 daily history。
  - 調整 next_action：
      - market/theme 不完整時輸出 market_theme_historical_fetch_required。
      - duplicate evidence 時輸出 market_theme_dedupe_followup_required。
      - source-error 時輸出 source_error_blocked。
      - 不再因 daily_signal_snapshot current VERSION 五月 0 rows 輸出 blocked_current_version_snapshot_missing 或 generic backfill action。
  - 同步 missing-source CLI fallback，避免缺 Supabase read source 時暗示要補 current VERSION 舊五月 snapshot。

  ## 修改檔案

  - services/market_theme_evidence_store.py
  - scripts/smoke_market_theme_evidence_readonly.py
  - tests/test_market_theme_evidence_handoff.py

  ## 最小改動策略

  - 只改 correction audit report builder、CLI missing-source fallback 與既有 handoff 測試。
  - 未新增 market/theme 抓取、dedupe、backfill、schema guard 或 Telegram 行為。
  - 保留既有 legacy key daily_signal_snapshot_may_current_version_coverage，但內容同步擴充 run-health 欄位，降低直接消費者斷裂風險。

  ## 契約影響

  - 新增 JSON 欄位：
      - daily_signal_snapshot.history_coverage
      - daily_signal_snapshot.current_version_run_health
      - market_theme_historical_coverage
  - daily_signal_snapshot_may_current_version_coverage 仍存在，但新增：
      - generator_version
      - may_row_count_for_current_version
      - diagnostic
      - blocks_history_coverage
  - blocked_reason 不再把 current VERSION 舊五月 0 rows 當 historical coverage blocker。
  - next_action 不再要求 daily_signal_snapshot 舊五月 current VERSION backfill。
  - DB 寫入、CLI live 行為、Telegram 報文與版本字串：無變更。

  ## 直接消費者同步

  - Owner / Architect：可由 history_coverage.conclusion=covered 與 current_version_run_health.blocks_history_coverage=false 判斷 snapshot 歷史 coverage 與 current VERSION run-health 已分離。
  - QA：測試已覆蓋 current VERSION 舊五月 0 rows 但全版本歷史存在時，不因 current VERSION 0 rows blocked；market/theme latest-only / mapping-only 仍 blocked。
  - CLI fallback：--correction-audit-json missing-source contract 同步新增新欄位，並移除 current VERSION backfill 暗示。

  ## 未影響模組

  - 未改 production DB write / insert / update / delete。
  - 未改 market/theme historical fetch。
  - 未改 confirmed evidence dedupe 實作。
  - 未改 DB schema、RLS、grant、policy、role、index、constraint。
  - 未改策略 decision、持倉建議、watchlist、交易狀態機。
  - 未改 Telegram 報文版本、文案或 live delivery。

  ## 已跑自檢命令

  - python -m pytest tests/test_market_theme_evidence_handoff.py -k 'correction_audit or may_coverage'
      - 結果：blocked by environment，python: command not found。
  - python3 -m pytest tests/test_market_theme_evidence_handoff.py -k 'correction_audit or may_coverage'
      - 結果：blocked by environment，No module named pytest。
  - PYTHONPATH=. UV_CACHE_DIR=/private/tmp/uv-cache-stock-tech uv run pytest tests/test_market_theme_evidence_handoff.py -k 'correction_audit or may_coverage'
      - 結果：14 passed。
  - PYTHONPATH=. UV_CACHE_DIR=/private/tmp/uv-cache-stock-tech uv run pytest tests/test_market_theme_evidence_handoff.py
      - 結果：51 passed。
  - PYTHONPYCACHEPREFIX=/private/tmp/pycache-stock-tech PYTHONPATH=. UV_CACHE_DIR=/private/tmp/uv-cache-stock-tech uv run python -m compileall -q services/market_theme_evidence_store.py scripts/
    smoke_market_theme_evidence_readonly.py tests/test_market_theme_evidence_handoff.py
      - 結果：passed。
  - git diff --check
      - 結果：passed。

  ## 殘留風險

  - 自檢使用既有 fixture，未讀 production DB；不能宣告 production market/theme 三表五月資料完整。
  - legacy constants blocked_current_version_snapshot_missing / followup_backfill_task_needed 仍留在 module 中供其他路徑相容，但 correction audit 本輪路徑不再輸出它們。
  - QA 仍需反證 Owner 讀取 JSON 時不會誤判 market/theme 已完成或 snapshot 需要 current VERSION backfill。

  ## 旁支待辦

  - 下一張任務再處理 market/theme historical fetch。
  - 下一張任務再處理 market_theme_confirmed_evidence duplicate / dedupe。
  - 若後續要完全移除 legacy next_action constants，需另開契約清理任務並盤點所有消費者。
