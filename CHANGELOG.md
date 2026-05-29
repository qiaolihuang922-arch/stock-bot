# CHANGELOG: 修正 Supabase SQL artifact 結尾語法錯誤

  ## 任務尺寸與風險

  - 任務尺寸: tiny_patch
  - 風險判斷: 僅修 SQL artifact 可複製性與 handoff notes；不改產品 Python、策略、Telegram、runtime DB read/write path。
  - QA 分級對應: L1

  ## 修改內容

  - 在 db/sql/evidence_phase_4_market_theme_confirmed_evidence.sql header 補明整段複製執行與 ERROR 42601 syntax error at end of input 的常見原因。
  - 在 SQL 尾端新增一個唯讀 validation marker statement，讓最後一個有效 statement 明確以 ; 結尾。
  - 新增最小 handoff 文件，說明此 SQL artifact 的用途、整段複製方式、不可 production 驗證、不可 backfill、不可加入 credential。

  ## 修改檔案

  - db/sql/evidence_phase_4_market_theme_confirmed_evidence.sql
  - docs/handoff/evidence_phase_4_market_theme_confirmed_evidence.md

  ## 最小改動策略

  - 保留原本 schema intent、table name、欄位、constraint、index 與 comment contract。
  - 不新增 destructive DML / DDL。
  - 不新增 grants、credential、production connection 設定。
  - 不擴大到其他 SQL artifact 或 migration framework。

  ## 契約影響

  - SQL artifact contract: 仍是單一可複製 SQL block；尾端現在有明確唯讀 select ... as sql_artifact_validation_marker; 作為完整性標記。
  - Schema contract: 未改 table 欄位、index、constraint、comment 語意。
  - Telegram / CLI / payload / message list / formatter contract: 未改。
  - DB runtime read/write path: 未改。

  ## 直接消費者同步

  - Owner / operator: handoff 文件補明需整段複製，不要局部複製，不要由 agent 連 production 驗證。
  - Supabase SQL editor / Postgres parser: SQL 尾端增加明確有效 statement terminator，降低尾段漏貼或 parser ambiguous 的風險。
  - QA: 可用 SQL 檔與 handoff 文件做 static scan；本地 parser 若可用再做非 production syntax validation。

  ## 未影響模組

  - 未改產品 Python / app code。
  - 未改策略、watchlist、Telegram formatter、scheduler。
  - 未執行 live Telegram。
  - 未連 production Supabase。
  - 未做正式 backfill。
  - 未改 runtime DB read/write path。

  ## 已跑自檢命令

  - git diff --check: 通過。
  - rg -n -i "\b(drop\s+table|truncate|delete\s+from|update\s+public\.|insert\s+into|grant\s+|service_role|password|secret|token|connection string|supabase db|psql|curl|wget)\b" db/sql/
    evidence_phase_4_market_theme_confirmed_evidence.sql docs/handoff/evidence_phase_4_market_theme_confirmed_evidence.md || true: 無命中。
  - tail -n 8 db/sql/evidence_phase_4_market_theme_confirmed_evidence.sql: 確認最後有效 statement 以 ; 結尾。
  - perl 靜態粗檢: paren_open=25 paren_close=25 dollar_quote_markers=0。
  - perl 去除 SQL line comments 後檢查最後有效字元: ;。
  - git diff --no-index --check /dev/null docs/handoff/evidence_phase_4_market_theme_confirmed_evidence.md || true: 無 whitespace error。
  - command -v psql || echo psql_not_found: psql_not_found。
  - command -v docker || echo docker_not_found: docker_not_found。

  ## 殘留風險

  - 本 worktree 沒有 psql 或 local Postgres container / Docker，未跑真正 Postgres parser validation。
  - 未連 production，符合任務禁止事項；SQL 是否能在 Owner production schema 狀態下成功執行仍需 Owner 手動 review production 是否已有同名但不完整 table。

  ## 旁支待辦

  - 其他 SQL artifact 風格一致性不在本輪處理。
  - 正式 migration framework、rollback 策略、production schema drift audit、全量 SQL lint 不在本輪處理。
  - SQL 執行後的 read-only loader / writer / backfill / RLS policy 需另開任務並取得批准。
