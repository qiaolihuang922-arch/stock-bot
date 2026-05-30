# TASK: 修復 evidence read-only smoke credential fallback

## 任務狀態

- task_id: fix-evidence-readonly-smoke-credential-fallback
- 任務類型: tiny_patch
- 狀態: ready_for_tech
- 版本建議: patch
- 版本契約: 本輪不改 Telegram / 策略 / 使用者報文版本；若專案有 CLI/script 版本 header，沿用目前版本，不為此 smoke fallback 單獨升版。
- QA 分級建議: L1

## Owner 問題

scripts/smoke_market_theme_evidence_readonly.py 目前只讀 SUPABASE_URL + SUPABASE_READONLY_KEY env。當本機 config.py 已有 SUPABASE_URL / SUPABASE_KEY，但 env 未提供 readonly key 時，script 會誤報 production DB env/
config missing，造成 evidence read-only smoke 在可安全讀取的本機設定下被錯誤阻塞。

## 使用者可見結果

- Owner / developer 執行 read-only smoke 時，憑證解析順序符合安全 fallback：
1. SUPABASE_URL: 優先 env，其次 config.SUPABASE_URL
2. key: 優先 env SUPABASE_READONLY_KEY
3. 其次 env SUPABASE_KEY
4. 再其次 config.SUPABASE_READONLY_KEY
5. 最後 config.SUPABASE_KEY
- 若仍缺 URL 或 key，script 必須 fail closed，清楚提示缺必要 DB read credential，但不得輸出任何 secret value、hash、partial/truncated value。
- 成功 fallback 時，script 可以建立 Supabase client，或在測試中以 fake client 驗證 credential resolution contract。

## 非目標

- 不改策略 decision。
- 不改 Telegram 報文、formatter、message list contract 或手機閱讀內容。
- 不改 DB schema / RLS / grant / policy / role。
- 不做 live write。
- 不做 backfill。
- 不改 market theme evidence 的資料模型、查詢語意或 production 資料內容。
- 不做全 repo credential refactor。
- 不清理其他 smoke scripts。

## 影響模組

- 直接模組:
- scripts/smoke_market_theme_evidence_readonly.py
- 對應的直接測試檔，位置由 Tech 依現有測試結構選擇。
- 直接消費者:
- 本機 / CI 手動執行 evidence read-only smoke 的 developer / Owner。
- Architect / QA 用來確認 production DB read-only evidence path 是否可讀的 smoke command。

## 輸出契約

- 單一主 bug: credential fallback resolution。
- 單一輸出契約:
- script 判斷 DB credential 時，必須使用以下 resolution order：
- URL: os.environ["SUPABASE_URL"] -> config.SUPABASE_URL
- key: os.environ["SUPABASE_READONLY_KEY"] -> os.environ["SUPABASE_KEY"] -> config.SUPABASE_READONLY_KEY -> config.SUPABASE_KEY
- 缺 URL 或 key 時回傳 fail closed，不建立 client，不進行 DB read。
- log / stderr / exception message 不得包含 secret value、hash、前後幾碼、長度推測或任何可識別 credential 的派生資訊。
- 已存在且不得回退的契約:
- 此 smoke 必須是 read-only smoke。
- 缺憑證不得 fallback 成 live write、backfill 或 DB mutation。
- 不得要求 Owner 手動執行 SQL。
- 不得改 Telegram / 策略 decision。
- 不得把 SUPABASE_SERVICE_ROLE_KEY 或其他高權限 secret 納入 fallback。

## 驗收條件

1. config fallback 可用:
- 在 env 沒有 SUPABASE_READONLY_KEY、但 config.SUPABASE_URL + config.SUPABASE_KEY 存在時，credential resolver 能選到 config fallback，並可建立 client，或以 fake client 驗證傳入的是 resolved URL/key。
2. fail closed 可用:
- env 與 config 都缺 URL 或 key 時，script 必須失敗並停止，不建立 client，不進行 DB read。
- 失敗訊息只能說明缺必要 read credential，不得包含任何 secret value/hash/truncated value。
3. priority 不回退:
- 若 env SUPABASE_READONLY_KEY 存在，必須優先於 env SUPABASE_KEY 與 config key。
- 若 env SUPABASE_KEY 存在且 readonly key 不存在，必須優先於 config key。
4. 範圍不擴張:
- diff 只應集中在 smoke credential resolution 與直接測試。
- 不得修改策略、Telegram、DB schema、RLS、grant、policy、backfill 或 live delivery path。

## 範例或 fixture

- fixture A: env SUPABASE_URL=https://example.supabase.co, env SUPABASE_READONLY_KEY=ro_env, env SUPABASE_KEY=anon_env, config.SUPABASE_KEY=config_key
- expected: resolver 使用 SUPABASE_READONLY_KEY
- expected output shape: readonly smoke credential source resolved 或等價安全訊息，不含 key 值。
- fixture B: env 無 Supabase key，fake config 有 SUPABASE_URL=https://example.supabase.co + SUPABASE_KEY=config_key
- expected: resolver 可建立 fake client / 呼叫 fake client factory。
- expected: 不誤報 production DB env/config missing。
- fixture C: env 與 config 都缺 key
- expected: fail closed。
- expected output shape: missing required Supabase read credentials 或等價安全訊息。
- forbidden output examples: config_key, conf...key, key hash, key length。

## 明確禁止事項

- 禁止輸出任何 secret value、hash、partial/truncated value、長度或 fingerprint。
- 禁止新增 live write、DB mutation、backfill、資料修復流程。
- 禁止改 DB schema / RLS / grant / policy / role。
- 禁止改 Telegram 報文、formatter header、message list、策略 decision、watchlist 或持倉狀態機。
- 禁止讀取或引用 .env、*.pem、~/.aws/credentials、~/.ssh/*、token 檔案。
- 禁止把 service role 或高權限 credential 加入 fallback。
- 禁止為此 tiny patch 擴成全量 credential 管理重構或全 repo smoke 清理。

## 阻塞條件

- 若現有 script 沒有可分離測試的 credential resolution seam，Tech 仍應只做最小可測抽取；若需要大規模重構才可測，先 blocked 回報。
- 若 config.py 中不存在 SUPABASE_READONLY_KEY 或 SUPABASE_KEY 的明確可讀 contract，且無法以 fake config module 驗證 fallback，Tech blocked 要求 Architect 補充現有 config 契約。
- 若測試環境無法安全 mock config/env/client factory，且會迫使測試讀真實 secret，必須 blocked。
- 若修復需要 DB schema、RLS、grant、policy 或 live credential 權限變更，必須 blocked，不納入本輪。

## 本輪停止條件

- 完成 credential fallback resolution。
- 補上直接測試覆蓋 config fallback 與缺憑證 fail closed。
- 驗證不輸出 secret 派生資訊。
- Tech 自檢只跑直接相關測試；QA 只做 L1 局部測試與一個負面 secret-output 反證。
- 發現其他 smoke script 同類問題、credential 命名不一致、CI secret 配置問題，只記為後續待辦，不納入本輪。
