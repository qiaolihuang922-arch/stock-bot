# CHANGELOG:

  ## 任務尺寸與風險

  - 任務尺寸: process
  - 風險判斷: 只新增 read-only schema verification handoff SQL，不改產品程式、不改既有 schema artifact intent、不連 production DB、不執行 live write / backfill / Telegram。

  ## 修改內容

  - 新增一份 Owner / QA 可在 Supabase SQL editor 手動執行的只讀 metadata verification SQL。
  - SQL 覆蓋 TASK.md 要求的 verification matrix 所需結果：
      - table exists
      - columns / expected columns / column comparison
      - unexpected columns
      - check constraints
      - freshness / support_level / evidence_status allowed values
      - indexes / expected indexes / index comparison
      - latest confirmed partial index
      - table / column comments
  - 無安全只讀 production connection，因此未宣告 production schema pass；本輪交付的是可手動執行並回傳結果的 read-only SQL artifact。

  ## 修改檔案

  - docs/handoff/evidence_phase_4_market_theme_confirmed_evidence_readonly_verification.sql

  ## 最小改動策略

  - 只新增 handoff SQL artifact。
  - 未修改 db/sql/evidence_phase_4_market_theme_confirmed_evidence.sql，避免改動前一輪 SQL schema intent。
  - 未修改 Python app code、tests、formatter、strategy、DB writer、runner 或 Telegram 報文。
  - 未編輯 CHANGELOG.md；本回覆提供完整 CHANGELOG 內容供 runner 寫入。

  ## 契約影響

  - 不改函式回傳結構。
  - 不改 message list、payload、Telegram 報文分組或排序。
  - 不改 DB schema intent、不新增 migration、不新增 writer / loader。
  - 新增的 artifact contract: 手動執行後會產生多個只讀 result sets，供 QA / Owner 填入 TASK.md 指定 verification matrix。
  - Production schema 結論仍需依實際 Supabase 執行結果判定；目前不可宣告 pass。

  ## 直接消費者同步

  - Owner / operator: 可直接執行新增 SQL 並回傳全部 result sets。
  - QA: 可用新增 SQL 對照 TASK.md verification matrix，若 hard schema / constraints / indexes 有 fail row 應 blocked；comments 缺失僅 warning，除非 SQL contract 後續改變。
  - Architect: 可依回傳結果更新狀態與下一步。
  - 後續 Tech: 若 verification pass，後續 read-only loader 任務仍需另開，不得依本輪聊天推定 schema 已通過。

  ## 未影響模組

  - 未影響 Telegram formatter / core/generator.py / 版本字串。
  - 未影響 strategy decision。
  - 未影響 DB write path。
  - 未影響 replay / backfill。
  - 未影響 watchlist。
  - 未執行 live Supabase write。
  - 未執行 live Telegram delivery。
  - 未檢查或修改其他 production table。

  ## 已跑自檢命令

  - rg -n "\b(insert|update|delete|drop|truncate|create|alter|grant|revoke)\b|service_role|token|secret|connection string|postgres://|supabase_key" docs/handoff/
    evidence_phase_4_market_theme_confirmed_evidence_readonly_verification.sql
      - 結果: 無命中。
  - git diff --check -- docs/handoff/evidence_phase_4_market_theme_confirmed_evidence_readonly_verification.sql
      - 結果: 無 whitespace error。
  - git status --short
      - 結果: 只有新增 docs/handoff/evidence_phase_4_market_theme_confirmed_evidence_readonly_verification.sql。
  - python3 嘗試 pglast parser
      - 結果: pglast_unavailable: ModuleNotFoundError: No module named 'pglast'，未做 parser validation。
  - command -v psql || true; command -v docker || true; command -v podman || true
      - 結果: 本環境未找到可用 local Postgres parser/runtime 工具。

  ## 殘留風險

  - 未連 production DB，不能宣告 public.market_theme_confirmed_evidence schema 通過。
  - 本機缺 pglast / psql / Docker / Podman，新增 SQL 只做靜態自檢，未做 PostgreSQL parser validation。
  - Supabase 實際輸出格式可能需要 QA 依 result sets 做人工 matrix 填寫與判斷。

  ## 旁支待辦

  - 實際 production schema verification 需由 Owner / QA 在安全只讀環境執行新增 SQL 後判定。
  - read-only loader、confirmed evidence writer、backfill、RLS / grants / policies、query performance、Telegram 顯示 confirmed evidence 都不在本輪處理範圍。
