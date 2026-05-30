# TASK: write CLI Supabase credentials env/config fallback

## 任務狀態

- task_id: write-cli-supabase-config-fallback
- 任務類型: normal_patch
- 狀態: ready_for_tech
- 任務尺寸判斷: normal_patch
- 主 bug: write CLI / evidence store 只看 env，未 fallback 到既有 config.py。
- 不升級為 risk_patch: 不改 DB schema、不 live write、不改策略 decision、不改 Telegram 報文。
- 版本建議: 本輪不升版，沿用目前 VERSION
- QA 分級建議: L1
- 原因: CLI/config resolution 局部修復，需覆蓋直接 CLI 與 store consumer、負面缺配置、env 優先順序、secret 不外洩。

## Owner 問題

Owner 要修正 write CLI 的 Supabase credential resolution：本專案已有 config.py 配置，write path 不應只依賴 SUPABASE_URL / SUPABASE_SERVICE_ROLE_KEY env，否則在既有 config 可用但 env 缺失時會錯誤 fail。

## 使用者可見結果

- 執行 scripts/write_market_theme_confirmed_evidence.py --execute 時：
- 若 env 有值，優先使用 env。
- 若 env 缺失，fallback 到既有 config.py。
- 若 env 與 config 都缺必要配置，fail closed，並只顯示缺哪些配置名。
- CLI / log / error 不得輸出任何 secret value，只能輸出來源狀態與缺失配置名稱。
- 本輪不改 Telegram、策略結果、DB schema、正式寫庫流程或版本字串。

## 非目標

- 不改 market theme 策略判斷。
- 不改 evidence 資料 schema、table、RLS、grant、policy、role。
- 不新增 live write 行為，不執行 production 寫入。
- 不改 Telegram 報文、formatter、VERSION。
- 不做全量清理、全 repo refactor、credential 管理重設。
- 不引入新的 secrets storage 機制。

## 影響模組

- scripts/write_market_theme_confirmed_evidence.py
- services/market_theme_evidence_store.py
- 直接相關測試 fixture / unit tests

## 直接消費者

- CLI 使用者: 執行 scripts/write_market_theme_confirmed_evidence.py 的 Owner / runner。
- evidence store caller: CLI 內部呼叫 services.market_theme_evidence_store 建立 Supabase client / write path。
- 測試消費者: 既有 dry-run、forbidden write、credential 缺失相關測試。

## 輸出契約

- Credential resolution precedence:
1. env SUPABASE_URL
2. fallback config.SUPABASE_URL
3. env SUPABASE_SERVICE_ROLE_KEY
4. fallback config.SERVICE_ROLE_KEY
5. fallback config.SUPABASE_SERVICE_ROLE_KEY
- SERVICE_ROLE_KEY config alias 必須兼容。
- SUPABASE_SERVICE_ROLE_KEY env 與 config.SUPABASE_SERVICE_ROLE_KEY 必須兼容。
- env 存在時必須優先於 config，不得被 config 覆蓋。
- 缺配置時必須 fail closed，不得建立 partial client 或進入 write。
- CLI / error / debug output 只可顯示：
- 使用來源狀態，例如 url_source=env、key_source=config.SERVICE_ROLE_KEY
- 缺失配置名稱，例如 missing: SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY|SERVICE_ROLE_KEY
- CLI / error / debug output 不得顯示：
- Supabase URL value
- service role key value
- key 前後綴、長度、遮罩片段或可反推 secret 的內容

## 已存在且不得回退的契約

- dry-run 預設不得寫入。
- forbidden / no-live-write 測試不得回退。
- --execute 仍須明確 opt-in 才能進入 write path。
- 缺必要 credential 時必須 fail closed。
- 不得輸出 secret value。
- 不得改 DB schema 或 production payload schema。
- 不得改策略分類、Telegram 報文、VERSION。

## 驗收條件

1. 無 env、fake config module 提供 SUPABASE_URL + SERVICE_ROLE_KEY 時，--execute 可走 fake Supabase client path 並通過，不因 env 缺失 fail。
2. 無 env、無可用 config 時，CLI / store fail closed，明確列出缺失配置名稱，且不建立 client、不寫入。
3. env 與 config 同時存在時，實際使用 env 值；測試需能辨識 env 優先於 config。
4. 兼容 config.SUPABASE_SERVICE_ROLE_KEY 作為 service key fallback。
5. 所有錯誤、狀態輸出、測試 captured output 不包含 URL value 或 service key value。
6. 既有 dry-run / forbidden write tests 維持通過，不得為了本修復放寬 write guard。

## 範例或 fixture

- fixture A: env 缺失，fake config 成功
- env: unset SUPABASE_URL, unset SUPABASE_SERVICE_ROLE_KEY
- fake config: SUPABASE_URL="https://fake.supabase.co", SERVICE_ROLE_KEY="fake-service-key"
- expected: fake client factory 被呼叫；狀態只顯示 url_source=config.SUPABASE_URL, key_source=config.SERVICE_ROLE_KEY；不輸出實際 URL/key。
- fixture B: env 優先
- env: SUPABASE_URL="env-url", SUPABASE_SERVICE_ROLE_KEY="env-key"
- fake config: SUPABASE_URL="config-url", SERVICE_ROLE_KEY="config-key"
- expected: fake client 收到 env sentinel；輸出來源為 env；不輸出 sentinel value。
- fixture C: 全缺 fail closed
- env: unset
- fake config: absent or missing relevant attrs
- expected: non-zero / raised controlled error；message 包含缺失配置名；不寫入、不建立 client、不輸出 secret。

## 明確禁止事項

- 禁止 live write production Supabase。
- 禁止 live Telegram delivery。
- 禁止改 DB schema / migration / RLS / grant / policy / role。
- 禁止改策略、watchlist、market theme classification。
- 禁止改 VERSION 或 Telegram formatter header。
- 禁止在 log、exception、test assertion failure 中輸出 secret value。
- 禁止把缺 credential fallback 成 dummy production client。
- 禁止擴大成全 repo credential refactor。

## 阻塞條件

- 若 Tech 無法定位既有 config.py import pattern，必須 blocked，要求 Architect 補充允許讀取的局部檔案或既有 config contract。
- 若現有 tests 無法隔離 env/config，必須新增局部 fixture；不得用真 env 或 production config 驗收。
- 若 fake client 無法避免 live write 風險，必須 blocked，不得執行 --execute 對真 Supabase。
- 若發現現有 dry-run / forbidden write 契約本身不明確，先只記待辦，不納入本輪修復，除非阻塞上述驗收。

## 本輪停止條件

- 完成 credential resolution fallback、env precedence、fail-closed、secret redaction 四類局部驗收。
- 通過直接 CLI / store 相關測試與既有 dry-run / forbidden write tests。
- 停止於本 bug；任何 credential 架構整理、config 命名統一、production write workflow 改造、Telegram 顯示調整，均只記待辦，不進本輪。
