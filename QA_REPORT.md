# QA_REPORT:

  ## 測試範圍

  本輪任務尺寸為 normal_patch、QA level 為 L2。我沒有擴成 full pytest / replay / backfill；驗證集中在 read-only audit JSON contract、fail-closed gate、直接消費者與 Owner 可見 dry-run 輸出誤讀風險。

  已檢查：

  - TASK.md
  - CHANGELOG.md
  - git status
  - git diff --stat
  - services/market_theme_evidence_store.py
  - scripts/smoke_market_theme_evidence_readonly.py
  - tests/test_market_theme_evidence_handoff.py

  已跑命令：

  - arch -arm64 .venv/bin/python -m pytest tests/test_market_theme_evidence_handoff.py -q -> 34 passed
  - arch -arm64 .venv/bin/python -m pytest tests/test_market_theme_evidence.py -q -> 21 passed
  - git diff --check -> passed
  - scripts/smoke_market_theme_evidence_readonly.py --trade-date 2026-05-29 --production-source-audit-json -> exit code 2，輸出 blocked JSON，未洩漏 secret/hash/fingerprint
  - 追加直接消費者 smoke：mock production source rows 可產生 approved_payload_preview，且 fake client 未觸發 insert/update/upsert/delete

  ## 風險預算與停止條件

  最值得抓的 3 個風險：

  1. 把個股 snapshot / signal item row count 誤升級成 market/theme confirmed evidence。
      - 驗證：測試與 diff 顯示需具備 market_index / sector_theme_key / watchlist_breadth / evidence_value / support_level / lineage 並通過 validator 才能 preview。
      - 結果：local contract 通過。
  2. dry-run audit 變成 live write 或產出可誤執行 payload。
      - 驗證：JSON 固定 write_execution=disabled、live_write=false；追加 fake client 阻擋 write method。
      - 結果：未見 write path 被呼叫。
  3. Owner 讀 dry-run output 時誤以為 production source row count 已被完整確認。
      - 驗證：實跑 CLI。
      - 結果：本環境 production read 失敗；輸出 blocked，但 signal_runs source-error 時 signal_items 顯示 rows: 0，可能讓 Owner 誤讀成 signal_items 已查且為 0。

  停止條件：不做 live production write、不做 backfill、不做 full repo 測試；production row count 只能在允許 read-only Supabase network 的 runner 完成。

  ## 關聯風險掃描

  TASK.md、主要 code diff、測試方向大致一致：新增 read-only audit helper、CLI flag、局部 tests，不改策略、Telegram、DB schema 或 write CLI。

  需注意兩個不一致/殘留：

  - CHANGELOG.md 說「未直接編輯 CHANGELOG.md」，但 git status / git diff --stat 顯示 CHANGELOG.md 已修改。這是交付文件描述不精準，不影響產品 code contract，但 Architect 吸收時不能把整包 diff 當成產品可合併 diff。
  - 可吸收產品 diff 應限於：
      - services/market_theme_evidence_store.py
      - scripts/smoke_market_theme_evidence_readonly.py
      - tests/test_market_theme_evidence_handoff.py
  - worktree 殘留/交付文件 diff：
      - CHANGELOG.md 僅作 handoff 摘要，不應被當成產品實作範圍。

  ## 跨區塊語意一致性

  本輪不是 Telegram / UI 任務，無手機報文版本或 formatter header 需驗證。

  Owner 可見 JSON 的閱讀順序檢查：

  - 開頭能看到 mode=read-only-production-audit
  - 能看到 write_execution=disabled、live_write=false
  - 能看到 can_generate_approved_payload=false 與 status=blocked
  - blocked 時 approved_payload_preview=null
  - missing_source_semantics 有列出需要 Owner/PM 補的 source semantics

  語意風險：當上游 production read 失敗時，source_tables 裡部分表有 status=source-error，但 signal_items 在無 run_ids 時被填成 ok/rows=0。這會削弱「來源表 row count」的可追溯語意。

  ## 使用者誤讀風險

  主要誤讀風險不是買賣建議，而是 Owner 可能把 signal_items rows=0 解讀為 production 已查無資料。實際上，當 signal_runs 讀取失敗或沒有可用 run id 時，程式沒有直接查 signal_items，而是用空結果代替。

  此風險不會造成 approved payload 被產出，因為整體仍 blocked；但會影響 Owner 對 production source availability 的判斷。

  ## 質疑與反證

  Tech 已覆蓋 snapshot rows 不可升級、explicit contract columns 才 preview、缺 credentials fail closed。QA 追加反證：

  - 直接消費者：mock safe mapping row 產生 preview，preview 欄位可被 validator 接受，且未觸發 write method。
  - 負面/誤讀案例：實跑 CLI 在 production read 失敗時 blocked 且 redacted，但 signal_items row count 可能被誤讀為已查。
  - 契約風險：TASK.md 要求至少回報指定 production tables 是否有 2026-05-29 資料；目前 sandbox 無法完成真實 production row count，因此不能給完全通過。

  ## 未測項目

  - 未驗證真實 production DB row count，因 CLI 在目前 sandbox 讀 production 發生 source-error。
  - 未做 live write、upsert、insert、update、delete。
  - 未做 backfill / replay。
  - 未做 full pytest。
  - 未驗證 Supabase read-only runner 實際 credential 權限是否符合 production。

  ## QA 結論

  conditional pass

  本地 code contract、fail-closed、dry-run only、局部直接消費者驗證通過；但 production row count 驗收未能在目前環境完成，且 signal_runs 失敗時 signal_items rows=0 有 Owner 誤讀風險。建議 Architect 僅吸收產品 code/test
  diff，不要整包合併 handoff 文件；正式完成前需在可連 production read-only 的 runner 重跑 audit CLI，並修正或接受 signal_items skipped/rows=0 的語意風險。
