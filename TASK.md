# TASK: 修復 GitHub workflow Supabase service-role runtime config wiring

## 任務狀態

- task_id: workflow-supabase-service-role-runtime-config
- 任務類型: tiny_patch
- 狀態: ready_for_tech
- 版本建議: 不升使用者可見版本；本輪只修 GitHub runner runtime config wiring，不改 Telegram / CLI 報文內容。
- QA 分級建議: L1
- 任務尺寸判斷: tiny_patch
- 本輪主 bug: GitHub workflow 產生的 runtime config.py 未注入 SUPABASE_SERVICE_ROLE_KEY / SERVICE_ROLE_KEY alias，導致 fresh runner 執行 evidence write script 時找不到 service-role credential。

## Owner 問題

Owner 發現 .github/workflows/stock-bot.yml 的 Create runtime config 目前只寫入 SUPABASE_URL / SUPABASE_KEY，但 scripts/write_market_theme_confirmed_evidence.py --execute 需要以下任一來源：

- env SUPABASE_SERVICE_ROLE_KEY
- config.SERVICE_ROLE_KEY
- config.SUPABASE_SERVICE_ROLE_KEY

GitHub fresh run 若只依 workflow 生成 runtime config.py，可能無法執行 Supabase evidence write path。

## 使用者可見結果

- GitHub Actions fresh run 在有 secrets.SUPABASE_SERVICE_ROLE_KEY 時，runtime config.py 會產生 service-role alias。
- 既有 SUPABASE_KEY 仍保留給讀取路徑使用，不被 service-role key 覆蓋。
- validation / log 只能顯示欄位是否存在，不得輸出任何 secret 值。
- 若舊的 STOCK_CONFIG secret 仍被使用，既有行為不得被破壞。

## 非目標

- 不改 DB schema。
- 不新增表、欄位、RLS、grant、policy、role。
- 不改 Supabase evidence 寫入邏輯本身。
- 不執行 live write。
- 不發 live Telegram。
- 不重設策略、不改報文分類、不改 watchlist。
- 不做 workflow 全面重構或 secrets 命名大遷移。
- 不移除 SUPABASE_KEY 既有讀路徑契約。
- 不要求 L3 full pytest / replay / backfill。

## 影響模組

- 直接檔案:
- .github/workflows/stock-bot.yml
- 可能需要的最小驗證檔:
- 既有 workflow/static validation 測試，若 repo 已有相關測試則優先補在原位置。
- 若無既有測試，可補最小靜態檢查，驗證 workflow 產生 runtime config 的 alias 與 no-secret logging contract。

## 直接消費者

- GitHub Actions runner 的 Create runtime config step。
- runtime 生成的 config.py。
- scripts/write_market_theme_confirmed_evidence.py --execute 的 credential fallback path。
- 既有 Supabase read path，仍使用 SUPABASE_URL / SUPABASE_KEY。

## 輸出契約

### 單一輸出契約

GitHub workflow 生成 runtime config.py 時，必須同時保留 read key 與 service-role alias：

- SUPABASE_URL 仍由既有來源生成。
- SUPABASE_KEY 仍由既有來源生成，供既有讀路徑使用。
- 新增或修正 service-role aliases:
- SUPABASE_SERVICE_ROLE_KEY
- SERVICE_ROLE_KEY
- service-role alias 必須優先來自 secrets.SUPABASE_SERVICE_ROLE_KEY。
- 若 workflow 仍支援 STOCK_CONFIG 舊 secret，不能破壞其原有 config 注入行為。
- validation 可以檢查 key 是否 present / missing，但不得 print secret value、截斷 secret、hash secret 或輸出可逆資訊。

### 已存在且不得回退的契約

- SUPABASE_KEY 不得被移除。
- SUPABASE_KEY 不得被 service-role key 取代。
- STOCK_CONFIG 舊 secret 使用路徑不得被破壞。
- scripts/write_market_theme_confirmed_evidence.py --execute 既有 fallback 契約不得回退：
- env SUPABASE_SERVICE_ROLE_KEY
- config.SERVICE_ROLE_KEY
- config.SUPABASE_SERVICE_ROLE_KEY
- 本輪不得把缺 service-role key 包裝成成功寫入；缺 key 時應維持既有 fail-closed / validation failure 行為。

## 驗收條件

1. Workflow static contract
- .github/workflows/stock-bot.yml 的 runtime config 產生步驟會寫入 SUPABASE_SERVICE_ROLE_KEY 與 SERVICE_ROLE_KEY alias。
- alias 來源包含 secrets.SUPABASE_SERVICE_ROLE_KEY。
- SUPABASE_KEY 仍存在且未被改名或刪除。
2. No secret leakage
- workflow validation / shell output 不輸出 secret 原值。
- 測試或靜態驗證需覆蓋：log 只允許 present/missing 類訊息，不允許 echo config secret value。
3. Backward compatibility
- 若 STOCK_CONFIG 舊 secret 仍存在並被使用，原本可生成的 config 欄位不被覆蓋或刪除。
- 若 STOCK_CONFIG 不存在但 secrets.SUPABASE_SERVICE_ROLE_KEY 存在，fresh runner 仍能生成 service-role alias。
4. Evidence write consumer compatibility
- 靜態或最小單元驗證需證明 write_market_theme_confirmed_evidence.py --execute 可從 runtime config.SERVICE_ROLE_KEY 或 config.SUPABASE_SERVICE_ROLE_KEY 取得 service-role key。
- 不需要真的連 Supabase、不做 live write。

## 範例或 fixture

### 期望 runtime config 形狀

SUPABASE_URL = "..."
SUPABASE_KEY = "..."  # existing read path key

SUPABASE_SERVICE_ROLE_KEY = "..."  # from secrets.SUPABASE_SERVICE_ROLE_KEY
SERVICE_ROLE_KEY = SUPABASE_SERVICE_ROLE_KEY

### 期望 validation log 形狀

runtime config: SUPABASE_URL present
runtime config: SUPABASE_KEY present
runtime config: SUPABASE_SERVICE_ROLE_KEY present
runtime config: SERVICE_ROLE_KEY alias present

不得出現：

SUPABASE_SERVICE_ROLE_KEY=eyJ...
SERVICE_ROLE_KEY=eyJ...

## 明確禁止事項

- 禁止修改 DB schema / migration / RLS / grant / policy / role。
- 禁止執行 scripts/write_market_theme_confirmed_evidence.py --execute 對 production 做 live write。
- 禁止 live Telegram delivery。
- 禁止把 service-role key 寫入 repo tracked file。
- 禁止在 log、測試 snapshot、CHANGELOG 或 QA_REPORT 中輸出 secret 值。
- 禁止刪除或改名 SUPABASE_KEY。
- 禁止把 SUPABASE_KEY 改成 service-role key。
- 禁止順手清理 workflow 其他 job、排程、策略、報文或 runner 行為。
- 禁止擴大成全量 Supabase credential 重構。

## 阻塞條件

- repo 中實際 workflow 已不再有 Create runtime config step，或已改由其他集中 runner 生成 config，Tech 必須 blocked 並回報實際 source-of-truth。
- scripts/write_market_theme_confirmed_evidence.py 的 credential fallback 已與 Owner 描述不一致，Tech 必須 blocked，要求 Architect 重新確認契約。
- 無法在不輸出 secret 的前提下驗證 workflow，Tech / QA 必須 blocked，不得以人工看 log 取代。
- 若修復需要新增或修改 GitHub secrets 名稱以外的 production 設定，必須 blocked 交 Architect/Owner 確認。

## 本輪停止條件

- 完成 .github/workflows/stock-bot.yml runtime config alias wiring。
- 完成最小可驗證測試或靜態驗證，覆蓋 alias 生成、保留 SUPABASE_KEY、不輸出 secret。
- QA 以 L1 驗證 workflow/static contract 與 evidence write credential fallback 相容即可停止。

以下旁支問題只記待辦，不納入本輪：

- Supabase evidence write 資料內容正確性。
- evidence table schema 或 RLS 設計。
- replay/backfill dry-run。
- Telegram 報文呈現。
- secrets 管理全面重構。
- GitHub Actions job 全面整理。
