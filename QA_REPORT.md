# QA_REPORT:

  ## 測試範圍

  本輪任務尺寸為 tiny_patch，QA level 為 L1。驗證範圍收斂在 scripts/smoke_market_theme_evidence_readonly.py 的 credential fallback、直接測試、直接消費者與 secret-output 風險；未擴成 full pytest / replay / backfill。

  可吸收 diff：

  - scripts/smoke_market_theme_evidence_readonly.py
  - tests/test_market_theme_evidence_handoff.py
  - CHANGELOG.md

  worktree 殘留：

  - git status --short --untracked-files=all 僅顯示上述 3 個 tracked 修改；未發現需合併的旁支殘留。QA 測試暫存使用 .qa_tmp/，未改 tracked file。

  已執行：

  - arch -arm64 .venv/bin/python -m pytest tests/test_market_theme_evidence_handoff.py -q：31 passed
  - PYTHONPYCACHEPREFIX=.qa_tmp/pycache arch -arm64 .venv/bin/python -m py_compile scripts/smoke_market_theme_evidence_readonly.py tests/test_market_theme_evidence_handoff.py：通過
  - git diff --check：通過
  - QA 補充負面反證：只有 SUPABASE_SERVICE_ROLE_KEY 時 resolver fail closed、不建立 client、不 fallback 到高權限 key：通過
  - QA 補充 secret derivative render 反證：fail-closed render 不含 secret / hash / fingerprint / length：通過

  備註：第一次 py_compile 未設 PYTHONPYCACHEPREFIX 時被 sandbox 擋在使用者 Cache 寫入，改用 .qa_tmp/pycache 後通過；不屬於程式失敗。

  ## 風險預算與停止條件

  本輪最值得抓的 3 個風險：

  1. credential resolution 順序錯，仍誤報缺 env/config。
      - 驗證：讀 diff、跑直接測試，確認 URL 與 key fallback 順序符合 TASK。
      - 停止條件：直接測試通過且 _build_readonly_client() 使用 resolver。
  2. 缺憑證時沒有 fail closed，或仍建立 client / 讀 DB。
      - 驗證：直接測試與 QA 補充 fake client negative，確認 missing credentials 不呼叫 client factory。
      - 停止條件：fake client calls 為空，status failed。
  3. secret 或高權限 key 被輸出 / 被納入 fallback。
      - 驗證：檢查 diff 無 SUPABASE_SERVICE_ROLE_KEY fallback；補測 service-role only case；檢查 fail-closed render 不含 secret 派生資訊。
      - 停止條件：service-role only 無 client、render 無 secret/hash/fingerprint/length。

  停止於 L1 局部契約驗證；其他 smoke script、CI secret 命名與 live Supabase read 不納入本輪。

  ## 關聯風險掃描

  TASK.md、CHANGELOG.md、git diff 一致：本輪只改 read-only smoke credential fallback 與直接測試，未見策略、Telegram、DB schema、RLS、grant、policy、backfill、live delivery path 變更。

  直接消費者掃描：

  - scripts/smoke_market_theme_evidence_readonly.py main() 仍透過 _build_readonly_client() 建 client，已接到新 resolver。
  - scripts/generate_evidence_approval_package.py 只引用 CLI command 字串，呼叫方式未變。
  - 測試新增 fake config / fake client 驗證，不讀真實 .env 或真實 secret。

  未發現清理 / 瘦身 / refactor 任務，因此不適用 path / claim / evidence / risk / action 證據表阻塞條件。

  ## 跨區塊語意一致性

  本輪不改 Telegram / summary / dashboard / formatter header / message list，無手機報文版面變更。

  CLI smoke fail-closed 語意一致：

  - TASK 要求缺 URL 或 key 時 fail closed。
  - diff 中 main 使用 missing required Supabase read credentials。
  - render 仍顯示 mode: read-only、write: disabled、status: fail-closed、telegram_confirmed: false。
  - 不會把缺憑證誤讀成已確認 production evidence。

  ## 使用者誤讀風險

  Owner / developer 執行 smoke 時，缺憑證輸出只提示缺必要 read credential，不會顯示 key 值、hash、截斷值或長度。這降低了把 secret 貼到 log / 聊天 / issue 的風險。

  成功 fallback 時，CLI 使用方式不變；主要風險是使用者不知道實際 key 來源，但 TASK 沒要求輸出 credential source，且輸出 source 可能增加 secret 誤讀或 debug 擴張風險。本輪接受不顯示 key source。

  ## 質疑與反證

  主動質疑 1：Tech 測試有覆蓋 readonly/env/config key，但是否漏掉「service-role 高權限 key 被誤用」？

  - 反證：QA 補測只有 SUPABASE_SERVICE_ROLE_KEY / config service role key 時 resolver 回 failed、credentials 為空、client factory 未被呼叫。通過。

  主動質疑 2：缺憑證輸出是否可能包含 secret 派生資訊？

  - 反證：QA 補測 render 不含 hash、fingerprint、length，直接測試也檢查 secret 字串不出現在 output。通過。

  主動質疑 3：這個 patch 是否回退 read-only contract？

  - 反證：diff 未新增 write/backfill/live Telegram；service role 未納入 read-only smoke fallback；write: disabled render contract 保留。可接受。

  ## 未測項目

  - 未用真實 Supabase credential 跑 live read-only smoke；本輪 TASK 明確允許 fake client 驗證 resolver contract，且避免讀取或輸出真實 secret。
  - 未跑 full pytest、replay、backfill dry-run；tiny_patch / L1 不需要。
  - 未驗證其他 smoke scripts 是否也有 env/config fallback 問題；TASK 停止條件要求列為後續風險，不納入本輪。

  ## QA 結論

  通過
