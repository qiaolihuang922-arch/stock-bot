# TASK: Codex 修復指令清單第 4/5/6/7/9/12 收口與第 8/10/11 回歸

## 任務狀態

- task_id: 20260602-risk-codex-fixlist-closeout-4-12
- 任務尺寸: risk_patch
- 狀態: ready_for_tech
- QA 分級建議: L3
- 流程要求: 必須走 PM -> Tech -> QA；不得由 Architect 或 PM 直接改產品代碼。
- 本輪實作: 第 4、5、6、7、9、12 項。
- 本輪回歸: 第 8、10、11 項。
- 已完成且不得回退: 第 1、2、3 項。

## Owner 問題

Owner 要求不要再拆，把 Codex 修復指令清單中「尚未完成且可直接修」的項目一次收口，並對既有已修噪音 / 空占位 / 持倉排序與主行動一致性做全量回歸。

本輪不是策略重設，而是修正報文與 evidence 表達的可靠性：

- strategy_sample 狀態不得靠中文渲染文本 grep 反推。
- 資料依據不得重複、硬編碼可靠度或輸出誤導確認語氣。
- 跨日來源不足時，previous_state / dedupe_guard 必須 fail closed。
- stock_api fallback 到 LAST_OHLCV 時必須標 stale 與 data date。
- 手機閱讀不得被同義 🧭、空占位、重複長句、互斥主行動或負百分比干擾。

## 使用者可見結果

Owner 在手機 Telegram / 報文閱讀時應看到：

- Summary 只回答決策：今天能不能買、持倉先處理什麼、未持倉哪些只是追蹤。
- 無可買時，全篇只保留必要一次「新倉：無有效進場」或等價不可買表述。
- 多個同義 🧭 / 簡報行壓縮為 1-2 行。
- 卡片層不逐卡重複「策略樣本不可用」「資料已確認」類長句；資料依據層合併說明一次。
- 僅追蹤 0、交易執行 0、無新增下單 等 0-count / 空占位預設不顯示。
- 同一持倉在卡片、風控檢查、簡報 / 索引中排序一致，且只有一個主行動詞。
- 已突破（-21.6%） 這類反直覺格式改成人話或隱藏負百分比。
- LAST_OHLCV fallback 可辨識為非當日 stale 資料，不得被讀成即時或當日日線。

手機閱讀示例形狀：

今日結論
新倉：無有效進場。
持倉：先處理停損 / 減碼項；其餘續抱或觀察。

🧭 可買 / 可準備 / 僅追蹤 / 不可行動已分組，詳情見下方。

資料依據
策略樣本：source-error，未用於確認結論。
行情：2330 使用 LAST_OHLCV 2026-05-29，非當日資料。
市場 / 主題可靠度：資料不足，保守看待。

持倉
1. 2356｜主行動：減碼｜理由...
2. 2376｜主行動：續抱｜理由...

## 非目標

- 不改 strategy decision 結果。
- 不改 RR 公式。
- 不改 DB schema、RLS、grant、policy、role、index、constraint。
- 不改 DB write path。
- 不做 production DML / backfill。
- 不 live Telegram delivery。
- 不新增跨日 source-of-truth。
- 不用假結構化來源或新文字 grep 包裝第 4 項。
- 不重寫整份報文架構。
- 不處理第 1、2、3 項以外的新旁支問題；除非阻塞本輪驗收，否則只記 follow-up。

## 影響模組

- core/generator.py
- _strategy_sample_status()
- cross_day_context / previous_state / dedupe_guard 消費路徑
- message list / summary / cards / risk check / index 輸出路徑
- presentation/report.py
- strategy sample 資料依據呈現
- market/theme 可靠度呈現
- 簡報 / 資料依據去重與降噪
- services/stock_api.py
- 即時 / 日線失敗後 fallback LAST_OHLCV 的結果 payload
- 既有報文 / Telegram formatter、fixture、probe、測試檔

## 直接消費者

- Owner 手機 Telegram 報文閱讀。
- presentation/report.py 產出的簡報 / 報文資料依據區塊。
- core/generator.py 產出的 message list / summary / cards / risk check / index。
- 下游 QA probe，用於重跑並防止本輪修項回退。
- 既有消費 services/stock_api.py fallback OHLCV payload 的報文或資料依據格式化器。

## 輸出契約

### 4. strategy_sample 狀態結構化判定

- _strategy_sample_status() 不得靠 grep 中文渲染文本判定 missing / source-error / insufficient-data / available。
- 優先消費既有結構化來源：daily_signal_snapshot、strategy evidence 查詢結果、既有 structured status 欄位、結構化行數、必要欄位完整度、as_of / data date / freshness。
- 判定輸出應可被 probe 直接驗證，至少包含或可推導：status、source、row_count 或 equivalent evidence count、as_of / data date / freshness、missing_fields 或 completeness 訊號。
- 若 repo 沒有可用結構化來源，Tech 必須將第 4 項標為 blocked 或 deferred，列出缺少來源；不得繼續用中文文案反推冒充完成。

### 5. 資料依據去重與可靠度非硬編碼

- strategy sample 說明全篇只出現一次。
- market/theme 可靠度不得硬寫「中等」或同義固定值。
- market/theme 可靠度應由 evidence_trend 實際指標派生，至少考慮天數 / evidence span、連續支持、新鮮度、available / source status。
- 指標不足時必須保守表達，例如「資料不足」「可靠度不足以判定」「僅供觀察」。

### 6. cross_day source_status 門控

- 消費 cross_day_context / previous_state / dedupe_guard 前必須檢查 source_status。
- insufficient-data、source-error、missing、unresolved-conflict 時，不得使用跨日記憶做確認結論。
- fail closed 輸出必須可辨識為「未用跨日記憶確認」，不得默默產生已確認語氣。
- 不改跨日策略決策，只改是否可用該記憶作確認結論與可見提示。

### 7. LAST_OHLCV fallback stale 標注

- services/stock_api.py fallback 到 LAST_OHLCV 時，payload 必須標注 stale: true、data_date 或 equivalent date field、fallback source。
- 非 fallback 當日 / 即時資料不得被誤標 stale。
- 報文或資料依據可根據 stale payload 提示「非當日資料」。
- 不得靜默把 LAST_OHLCV 當即時或當日日線使用。

### 8. 卡片層重複長句刪除回歸

- 卡片層不得逐卡重複「策略樣本：不可用」「資料：…已確認」或同義長句。
- 資料依據層允許合併說明一次。
- 若資料來源狀態影響單一卡片判斷，只能用短狀態或明確風險標籤。

### 9. 簡報同義 🧭 壓縮

- 多個同義 🧭 行壓縮為 1-2 行。
- 「無有效進場」全篇只保留必要一處。
- 不得犧牲 Summary 決策清楚度。

### 10. 0-count / 空占位隱藏回歸

- 僅追蹤 0、交易執行 0、無新增下單、同義空區塊 / 0-count 標題預設隱藏。
- 本輪 PM 不要求保留任何 0-count / 空占位。
- 若 Tech 發現既有直接消費者必須保留，必須 blocked，列出消費者、理由與替代輸出契約。

### 11. 持倉主行動與排序一致回歸

- 卡片、風控檢查、簡報 / 索引必須復用同一持倉序列。
- 同一持倉同一份報文只能有一個主行動詞：加碼、續抱、觀察、減碼、停損、停利、不動作。
- 不得同一持倉在不同區塊同時出現互斥主行動。
- probe 應比對 symbol sequence 與 main action map。

### 12. 已突破負百分比格式化

- 已突破場景不得顯示 已突破（-21.6%） 或同類負百分比格式。
- 可接受輸出：已突破，位於突破區上方、已突破，低於追價安全區、已突破，過熱不追，或直接隱藏負百分比。
- 不改突破判定與 strategy decision，只改人可讀格式。

## 版本契約

- 若本輪改動影響使用者可見 Telegram / 報文 header、版本字串或常量，Tech 必須同步升版或更新對應 snapshot / fixture。
- 不得把「不要回退版本」解讀成「禁止升版」。
- 若 repo 既有版本契約位置不明，Tech 必須先查明並寫入 CHANGELOG.md；查不到則 blocked。

已存在且不得回退的契約：

- Summary 只回答決策。
- 可買、可準備、僅追蹤、淘汰 / 不可行動必須分開。
- 無可買時不得使用像推薦的文案。
- 空區塊、0-count、無新增下單占位預設不顯示。
- 同一持倉同一份報文只有一個主行動。
- 今日買入後預設只能新倉風控觀察；若轉弱要賣，必須同行說明跌破警戒、停損或策略失效。
- local cache、worktree、runtime dict、agent 對話不得作為跨日記憶 source-of-truth。
- 第 1、2、3 項已完成契約不得回退。

## 驗收條件

Tech 必須先補可重跑 probe 或合併既有 probe，至少覆蓋：

- strategy_sample 狀態不靠中文渲染文案反推。
- strategy sample 資料依據全篇只出現一次。
- market/theme 可靠度不是硬編碼「中等」，資料不足時保守表達。
- cross_day source_status 不足時 fail closed，不用跨日記憶做確認結論。
- LAST_OHLCV fallback payload 帶 stale: true 與資料日期。
- 多個同義 🧭 壓成 1-2 行。
- 「無有效進場」不重複刷屏，只保留必要一處。
- 0-count / 空占位隱藏。
- 持倉卡片、風控檢查、簡報 / 索引排序一致。
- 同一持倉只有一個主行動詞。
- 已突破場景不顯示負百分比格式。
- 第 8、10、11 項回歸不得回退。
- 第 1、2、3 項既有契約不得回退。

QA 必須在 QA_REPORT.md 補 Tech 未覆蓋的手機閱讀反證：

- 以手機閱讀順序檢查 Summary -> 資料依據 -> 卡片 -> 風控 / 索引語意一致。
- 檢查 fixture 中沒有重複長句、0-count 空占位、同義導航刷屏。
- 檢查 stale 行情不會被誤讀成當日資料。
- 檢查 source_status 不足時，不會出現「已確認」或同義確認語氣。
- 檢查同一持倉沒有跨區塊互斥主行動。

QA 結論只能是 通過、阻塞、conditional pass；不得只重跑 Tech 命令後宣告通過。

## 範例或 Fixture

Tech 可用既有 fixture 或新增最小 fixture / probe；不得需要 production DML / backfill。

strategy_sample:
rendered_text: "策略樣本：不可用"
structured_status:
status: "source-error"
row_count: 0
as_of: "2026-06-02"
missing_fields: ["sample_rows"]
expected:
status_source: "structured"
no_text_grep: true

cross_day_context:
source_status: "insufficient-data"
previous_state:
symbol: "2356"
prior_action: "續抱"
expected:
use_for_confirmation: false
visible_phrase_not_contains: ["已確認", "confirmed"]

stock_api_fallback:
realtime_status: "source-error"
daily_status: "source-error"
fallback: "LAST_OHLCV"
last_ohlcv_date: "2026-05-29"
expected_payload:
stale: true
data_date: "2026-05-29"

禁止輸出示例：

策略樣本：不可用
策略樣本：不可用
已突破（-21.6%）
僅追蹤 0
交易執行 0
無新增下單

可接受手機輸出形狀：

資料依據
策略樣本：source-error，未用於確認結論。
行情：使用 LAST_OHLCV 2026-05-29，非當日資料。
市場可靠度：資料不足，保守看待。

突破狀態
已突破，過熱不追。

## 明確禁止事項

- 禁止 Architect / PM 直接改產品代碼或測試。
- 禁止跳過 Tech / QA。
- 禁止改 strategy decision 結果。
- 禁止改 RR 公式。
- 禁止 DB schema / write path / production DML / backfill。
- 禁止 live Telegram delivery。
- 禁止以中文渲染文案 grep / substring 判定 strategy sample source status。
- 禁止假造結構化來源。
- 禁止硬編碼 market/theme 可靠度為「中等」或同義固定值。
- 禁止 source_status 不足時仍使用跨日記憶寫確認結論。
- 禁止 LAST_OHLCV fallback 靜默當即時 / 當日日線。
- 禁止恢復逐卡重複長句、0-count 空占位、同義導航刷屏。
- 禁止同一持倉多個主行動詞。
- 禁止把測試通過升格成 production 已上線或 live delivery 已完成。

## 阻塞條件

以下情況 Tech 必須 blocked 或 deferred，並在 CHANGELOG.md 列 blocked reason 與未吸收 diff：

- repo 沒有可用結構化來源可支撐第 4 項 strategy_sample 狀態判定。
- daily_signal_snapshot / strategy evidence / structured status 缺欄位、缺日期或不足以判斷 freshness。
- 找不到既有版本字串 / header / snapshot 契約，且本輪改動會影響使用者可見報文版本。
- 現有測試環境無法補齊，導致 probes 不可重跑。
- 必須改 DB schema / write path 才能完成任一項。
- 必須 live Telegram 或 production DML 才能驗收。
- 發現第 4、5、6、7、9、12 任一項其實需要 strategy decision 重算才能完成。

## 本輪停止條件

本輪完成口徑：

- 第 4、5、6、7、9、12 已實作或明確 blocked/deferred，且每項都有可重跑 probe 或合併 probe 覆蓋。
- 第 8、10、11 已完成全量回歸，且沒有回退。
- TASK.md、CHANGELOG.md、QA_REPORT.md 標題與內容符合固定格式。
- QA 補手機閱讀反證，結論為 通過，或清楚列出 conditional pass / 阻塞 條件。
- 若有無法完成項，handoff 必須列出 blocked reason、未吸收 diff、未覆蓋驗收條件，不得寫成完成。
- 不要求本輪 commit / push；是否進入 git completion gate 由 Architect 收口依 Owner 流程處理。

旁支停止規則：

- 新發現但不影響本輪 4/5/6/7/8/9/10/11/12 驗收的問題，只記 follow-up，不納入本輪。
- 不新增第 13 項或重開第 1、2、3 項，除非本輪改動造成回退。
- 不擴成策略核心、DB 持久化或 production runner 重構。
