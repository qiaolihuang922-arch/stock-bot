# QA_REPORT:

  ## 測試範圍

  本輪判定為 normal_patch / QA L1。驗證集中在 write CLI 與 services.market_theme_evidence_store 的 credential resolution，不擴成 full pytest、replay、backfill 或 production write。

  已檢查：

  - TASK.md
  - CHANGELOG.md
  - git status --short
  - git diff --stat / 相關 diff
  - 直接消費者：scripts/write_market_theme_confirmed_evidence.py、build_market_theme_write_client、validate_market_theme_write_env
  - 使用者可見 CLI JSON 輸出

  已跑命令：

  - git diff --check：通過
  - pytest tests/test_market_theme_evidence_handoff.py -q：25 passed
  - pytest tests/test_market_theme_evidence.py tests/test_market_theme_evidence_handoff.py -q：46 passed, 17 warnings
  - QA 額外反證：payload validation 失敗時 credential validation 必須 skipped 且不洩漏 secret：通過
  - QA 額外反證：env URL + config key 混合來源只輸出 sanitized source，不輸出值：通過

  ## 風險預算與停止條件

  本輪最值得抓的風險：

  1. env/config precedence 錯誤，導致 env 被 config 覆蓋。
      - 驗證：讀 diff、跑既有 env precedence test、補 mixed source sanitized validation。
  2. 缺配置或 payload 失敗時沒有 fail closed，誤入 write path。
      - 驗證：缺 env/config test、payload invalid + --execute 額外反證。
  3. CLI / error / JSON 輸出洩漏 URL 或 service key。
      - 驗證：檢查 sanitized output path，測試 stdout 不含 sentinel secret。

  停止條件：

  - 覆蓋 fallback、env precedence、fail-closed、secret redaction。
  - 直接 CLI/store tests 通過。
  - 確認無 Telegram、策略、DB schema、VERSION diff。
  - 不驗 production Supabase live write，因 TASK 明確禁止。

  ## 關聯風險掃描

  TASK.md、CHANGELOG.md、git diff 一致：改動集中於：

  - services/market_theme_evidence_store.py
  - scripts/write_market_theme_confirmed_evidence.py
  - tests/test_market_theme_evidence_handoff.py
  - CHANGELOG.md

  rg 顯示 validate_market_theme_write_env / build_market_theme_write_client 的產品呼叫方限於 write CLI，CHANGELOG 的直接消費者說法成立。

  可吸收 diff：

  - write credential fallback
  - CLI execute JSON 的 sanitized env_validation
  - 直接測試更新

  worktree 殘留：

  - git status 僅上述 4 個 modified，未見 untracked 殘留。
  - 不建議整包合併超出上述 diff；本輪不包含任何 Telegram、策略、schema、watchlist、replay/backfill 改動。

  ## 跨區塊語意一致性

  CLI JSON 的 mode、write_execution、payload_validation、env_validation 語意一致：

  - dry-run 仍不寫入。
  - payload validation 失敗時 env_validation.status=skipped，不暗示 credential 已可寫。
  - env/config 通過時只顯示 url_source / key_source，不顯示 URL/key value。
  - rows_written 只在 execute 成功時反映 upsert rows。

  Telegram / summary / dashboard 不在本輪 diff，未改 formatter、VERSION、message list 或報文分組。

  ## 使用者誤讀風險

  Owner 執行 CLI 後最先看到的是 JSON：

  - write_execution=blocked 或 executed 清楚。
  - 缺配置時只列 missing 名稱，不暴露 secret，也不把缺 key 包裝成可寫。
  - fallback 成功時顯示來源，例如 config.SERVICE_ROLE_KEY，不顯示值。

  未發現會讓 Owner 誤判已 live write、已改策略、已改 Telegram 或已升版的輸出。注意：若本機 config.py 內有 placeholder/test credentials，--execute 且無 env 會依任務要求 fallback 並嘗試建立 client；這是本輪需求範圍內行為，
  仍受 --execute opt-in 保護，未在 QA 中做 live write。

  ## 質疑與反證

  主動質疑 1：payload 本身不合法時，CLI 是否仍讀 credential 並輸出 source，讓 Owner 誤以為已可寫？

  - 反證：用 forbidden runtime payload + fake config secrets 跑 --execute，結果 return code 2、write_execution=blocked、env_validation.status=skipped，stdout 不含 URL/key。

  主動質疑 2：mixed source 情境是否會洩漏 env/config value？

  - 反證：env 只給 URL、config 給 SERVICE_ROLE_KEY，validate_market_theme_write_env 只回傳 url_source=env、key_source=config.SERVICE_ROLE_KEY，不含 secret value。

  主動質疑 3：Tech 是否把任務擴成其他 Supabase consumer 或 read-only loader？

  - 反證：diff 未改 read-only _build_client、策略、Telegram、DB schema；rg 未發現其他產品呼叫方需同步。

  ## 未測項目

  - 未執行 production Supabase --execute live write，符合 TASK 禁止事項。
  - 未跑 full pytest、replay、backfill，因本輪為 L1 normal_patch，且無策略/Telegram/schema diff。
  - 未驗證正式 secret 管理命名統一；CHANGELOG 已列為後續 cleanup，不屬本輪。

  ## QA 結論

  通過
