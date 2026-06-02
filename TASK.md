# TASK: 修復證據加權框架空轉與 D2/B5 漏斗分類不一致

## 任務狀態

- task_id: evidence-wiring-and-funnel-consistency-20260602
- 任務類型: risk_patch
- 狀態: done
- 版本建議: 不升版，保持目前 VERSION
- QA 分級建議: L3
- 主 bug: 證據加權框架與正式報文路徑未正確消費既有歷史 / confirmed evidence，且 D2/B5 漏斗分類與卡片計數不一致。

## Owner 問題

證據加權框架已存在，但兩個證據源沒有真正進入正式決策 / 報文消費路徑：

1. services/strategy_evidence.py load_strategy_evidence_summary 目前用 version 過濾，導致跨版本有 outcomes 的歷史信號無法進入回測，狀態長期 not_applicable / insufficient_data。
2. core/generator.py 的市場題材 evidence wiring 在 market_summary 是字串時可能沒有傳入正確 trade_date，正式 generate_report 路徑沒有穩定消費 loader 回傳的 confirmed evidence_trend。
3. D2/B5 漏斗「等冷卻 / 隔日確認」計數與卡片分類仍不一致，手機閱讀時會看到 summary / 漏斗 / 卡片互相矛盾。
4. 調試期每天 bump VERSION 造成資料依版本散落；本輪修 wiring / filter 不得升版。

## 使用者可見結果

正式產生的 Telegram / 報文在手機閱讀時應看到：

- 策略證據狀態從空轉變為可用：當近 N 個交易日跨版本歷史有 outcomes 時，有效樣本數 > 0，狀態為 ready。
- 市場題材區顯示 confirmed evidence 與 8 天趨勢，不再在已有 confirmed evidence 時顯示「資料不足」。
- D2/B5 漏斗數字、分類標題、個股卡片狀態一致；同一檔股票不會在漏斗與卡片呈現不同分類。
- 報文版本字串保持目前版本，不因本輪修補而 bump。

手機閱讀示例形狀：

市場題材
- confirmed: <題材名稱>
- 8天趨勢: <up/down/flat 或既有格式>
- evidence: ready / confirmed

D2/B5 漏斗
- 等冷卻: 2
- 隔日確認: 1

卡片
[股票A] 狀態: 等冷卻
[股票B] 狀態: 隔日確認

實際文案與欄位名稱以既有報文格式為準，但不得再出現同一份報文中「漏斗計數為等冷卻、卡片卻歸到隔日確認」的矛盾。

## 非目標

- 不重設策略邏輯。
- 不改 RR 公式。
- 不改買賣 / 加減碼 / 停損停利核心決策規則。
- 不改 DB schema、RLS、grant、policy、role、index、constraint。
- 不做 live Telegram delivery。
- 不手寫 production DML。
- 不新增或修改 production 回寫 / backfill 行為。
- 不處理未追蹤 scripts/diagnose_evidence_sources.py；除非 Architect 另開任務納入範圍，本輪不得觸碰。
- 不做全量清理、重構或版本治理工程。

## 影響模組與直接消費者

影響模組：

- services/strategy_evidence.py
- load_strategy_evidence_summary
- core/generator.py
- market_theme_summary_evidence
- build_report_context
- 官方 generate_report 路徑中市場題材 evidence 消費 wiring
- D2/B5 漏斗與卡片分類相關 formatter / classifier / rendered message 測試
- 既有測試中對 strategy evidence、market theme evidence、D2/B5 funnel rendering 的 fixture / probe

直接消費者：

- 官方 generate_report 產生的 Telegram / 報文內容。
- build_report_context 的下游報文 formatter。
- build_market_theme_production_trend_consumption_check。
- D2/B5 漏斗 summary、分類卡片、手機閱讀路徑。
- strategy evidence 回測 / evidence weighting 狀態判斷。

## 輸出契約

### Strategy Evidence Loader

load_strategy_evidence_summary 必須：

- 以 trade_date 為基準，讀取近 N 個交易日歷史。
- 不再用 .eq('version', version) 限制 outcomes 歷史。
- 可跨版本消費已有 outcomes 的歷史信號。
- 保留既有回傳 payload shape；不得任意改名或刪除既有欄位。
- 當近 N 交易日有可用 outcomes 樣本時：
- effective_sample_count > 0 或既有等價樣本欄位為正數。
- evidence 狀態為 ready。
- 若 production / fixture 缺資料，仍要 fail closed 為 missing-source / source-error / insufficient-data，不得偽造 ready。

### Market Theme Evidence

market_theme_summary_evidence / build_report_context 必須：

- 呼叫 load_confirmed_market_theme_evidence 時傳入正確 trade_date。
- market_summary 是字串時也不得走無 trade_date 分支。
- 官方 generate_report 路徑必須消費 loader 回傳的 confirmed evidence 與 evidence_trend。
- build_market_theme_production_trend_consumption_check 必須顯示 uses_history=True。
- 有 confirmed history 時，使用者可見市場題材不得顯示「資料不足」。

### D2/B5 漏斗分類

D2/B5 相關輸出必須：

- 漏斗計數與卡片分類使用同一分類來源或同一分類器結果。
- 「等冷卻」與「隔日確認」不得在 summary / 漏斗 / 卡片之間互相矛盾。
- rendered message probe 必須覆蓋使用者實際會看的文字，而不只檢查 helper 回傳值。

### 版本契約

- 本輪不得 bump VERSION。
- 使用者可見 header / 常量 / 測試期望中的版本字串必須保持目前值。
- 不得新增依賴新版 version 才能讀到 evidence 的行為。

## 版本契約

已存在且不得回退的契約：

- 正式報文仍由官方 generate_report 路徑產生。
- Telegram / 報文仍以既有 message list / formatter 結構輸出。
- 市場題材仍沿用既有 confirmed evidence / evidence trend 欄位語意。
- strategy evidence loader 仍應在資料不足時 fail closed，不得把缺資料包裝成 ready。
- D2/B5 漏斗與卡片仍保持既有使用者可見分類名稱；只修正分類來源一致性。
- VERSION 保持目前值，不因本輪修補升版。

若 Tech 發現上述任一契約在程式中不存在或名稱不一致，必須 blocked 並回報實際現有契約，不得自行創造新 contract。

## 驗收條件

1. Strategy evidence 歷史樣本驗收：
- 在有 outcomes 的跨版本歷史 fixture / safe read-only artifact 下，load_strategy_evidence_summary 不用 version filter 後能讀入近 N 交易日樣本。
- 有效樣本數 > 0。
- 狀態為 ready。
- 測試需能反證舊行為：若仍用 version filter，該案例會回到 not_applicable / insufficient_data。
2. Market theme official path 驗收：
- generate_report 官方路徑使用帶 trade_date 的 load_confirmed_market_theme_evidence 結果。
- market_summary 為字串的 fixture 也能傳入正確 trade_date。
- 報文市場題材區顯示 confirmed / 8 天趨勢，不顯示「資料不足」。
- build_market_theme_production_trend_consumption_check 驗證 uses_history=True。
3. D2/B5 rendered message 驗收：
- 補 rendered message probe，檢查手機閱讀文字中的漏斗計數與卡片分類一致。
- 至少覆蓋「等冷卻」與「隔日確認」同時存在或容易混淆的 fixture。
- 同一檔股票在同一份 rendered message 中只能落在一個 D2/B5 主分類。
4. 版本不升級驗收：
- VERSION 沒有被本輪改動。
- 報文 header / 常量 / 測試期望沒有因本輪修補改成新版本。
- evidence 讀取不依賴新增 version。
5. QA L3 驗收：
- QA 必須反證官方 generate_report 路徑，不得只測 helper。
- QA 至少補一個 Tech 未覆蓋的正式報文 / rendered message 風險 probe。
- QA 結論只能是 通過、conditional pass 或 阻塞，並列出未測項目。

## 範例或 Fixture

Tech 應使用或新增最小 fixture，避免擴成資料工程：

trade_date: 2026-06-02
history_window_days: N
strategy_evidence_history:
- trade_date: 2026-05-28
version: old_version
signal: B5
outcome: win_or_loss
- trade_date: 2026-05-29
version: another_old_version
signal: D2
outcome: win_or_loss

expected:
effective_sample_count: >0
status: ready

Market theme fixture：

trade_date: 2026-06-02
market_summary: "<string summary>"
confirmed_market_theme_evidence:
confirmed: true
evidence_trend: "<8-day trend payload in existing format>"

expected rendered message:
contains confirmed evidence
contains 8-day trend
does not contain 資料不足
production_trend_check.uses_history == true

D2/B5 rendered message fixture：

candidates:
- symbol: AAA
expected_group: 等冷卻
- symbol: BBB
expected_group: 隔日確認

expected:
funnel count 等冷卻 == rendered cards in 等冷卻
funnel count 隔日確認 == rendered cards in 隔日確認
no duplicated primary D2/B5 action per symbol

## 明確禁止事項

- 禁止修改 RR 公式。
- 禁止修改 DB schema / RLS / grant / policy / role / index / constraint。
- 禁止 live Telegram。
- 禁止手寫 production DML。
- 禁止新增未經 Owner 確認的 production write / backfill。
- 禁止觸碰未追蹤 scripts/diagnose_evidence_sources.py。
- 禁止 bump VERSION。
- 禁止把 helper 測試通過當作 official generate_report 通過。
- 禁止以 local cache、runtime dict、agent 對話作為跨日 evidence source-of-truth。
- 禁止在缺資料、缺權限、source-error 時宣告 ready 或通過。

## 阻塞條件

- 找不到既有 confirmed market theme evidence loader 或其回傳 contract，且無法確認正確消費欄位。
- 找不到 strategy evidence outcomes 的可信 fixture / safe read-only artifact，無法證明有效樣本數 >0。
- 現有 DB / artifact 欄位不足以區分 trade_date、outcome、signal 或 evidence_trend。
- 官方 generate_report 路徑無法在測試環境執行，且無替代 rendered message artifact 能反證使用者可見結果。
- 修復需要 DB schema / RLS / grant / policy / role 變更。
- 修復需要 live Telegram 或 production write。
- 必須觸碰 scripts/diagnose_evidence_sources.py 才能完成本輪，則 blocked 等 Architect/Owner 另行納入範圍。

## 本輪停止條件

完成條件：

- strategy evidence 跨版本 outcomes 歷史進入 loader，驗收有效樣本數 >0 且狀態 ready。
- official generate_report 路徑能呈現 confirmed market theme / 8 天趨勢，且 uses_history=True。
- D2/B5 rendered message probe 證明漏斗計數與卡片分類一致。
- VERSION 未改。
- QA L3 對 official path 反證通過或給出 conditional pass 的具體殘留風險。

不納入本輪、只記待辦：

- 策略勝率模型重設。
- RR 或 scoring formula 調整。
- DB schema / production backfill 設計。
- live Telegram 發送。
- 全量報文文案重構。
- 清理未追蹤 scripts 或診斷工具。
- 非 D2/B5 的其他漏斗分類問題，除非直接阻塞本輪 rendered message 一致性驗收。
