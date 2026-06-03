# TASK: v20.4.36 trend_continuation 驗證、監控與報文降噪

## 任務狀態

- task_id: trend_continuation_v20_4_36_validation_monitor_report_noise_20260603
- 任務類型: mixed_patch
- 1/2: risk_patch
- 3/4/5: normal_patch
- 狀態: ready_for_tech
- QA 分級建議: L3
- 版本建議: 預設不升版；若使用者可見 header / 報文結構常量要求同步，Tech 必須在 CHANGELOG.md 說明是否維持 v20.4.36 或升版。
- Owner 指令順序: Tech 必須先做第 1 項驗證；若 trend_continuation BUY fixture 不通過，先修階段二實裝，再做 2/3/4/5。

## Owner 問題

Owner 要確認 v20.4.36 的 trend_continuation 不是只出現在文字或 helper，而是正式策略真的能在「回踩延續」條件下觸發小倉 BUY，且同時補上實盤 vs 回測監控、資料依據降噪、QA probe 改讀 manifest、未持倉回測行去重。

本輪不是重設策略，也不是擴大追高授權；核心是驗證與收斂既有 trend_continuation 實裝，並修掉報文與 QA 路由的噪音 / 漂移風險。

## 使用者可見結果

手機報文中：

- 符合回踩延續且 evidence positive 的標的，可顯示：
- 🟢 趨勢延續買入｜小倉
- 倉位仍為小倉，<=15%
- 依據可被 manifest / source_status / evidence_status 追溯
- 一般情境下第三則「資料依據」文字段預設不顯示，避免手機閱讀噪音。
- 隱藏只影響文字段，不影響內部 manifest、source_status、evidence_status、compute_evidence_score、fail-closed、過熱、減碼或其他風控邏輯。
- 未持倉卡片中，同一 setup_key 的回測行不重複刷屏；不同 setup_key 或不同決策含義不得被誤合併。

手機閱讀示例形狀：

台股策略日報 v20.4.36

新倉：趨勢延續小倉 1｜僅追蹤 2｜淘汰 3

3231 緯創
🟢 趨勢延續買入｜小倉
策略：回踩 ma5/ma10 後放量站回
倉位：小倉 <=15%
風控：回踩低點下方停損

預設不再額外露出第三則長段：

資料依據：...

但 report_context / manifest 仍必須保留可供 QA 讀取的來源狀態。

## 非目標

- 不改 RR 公式。
- 不改 DB schema、RLS、grant、policy、role、index、constraint。
- 不做 live Telegram delivery。
- 不新增 production write / backfill。
- 不把 extended spike、無回踩、單純創新高追價改成 BUY。
- 不把其他 decision_type 放開為「證據可開 BUY」。
- 不重寫整體 strategy tree、condition engine 或報文架構。
- 不移除 manifest / source_status / evidence_status。
- 不用 helper-only 測試替代 official generator / report 驗收。
- 不把「資料依據預設隱藏」做成 source fail-closed 豁免。

## 影響模組

- tests/test_trend_continuation.py
- services/analysis.py
- core/condition_engine.py
- scripts/research_trend_continuation.py
- scripts/monitor_trend_continuation.py
- presentation/report.py
- core/generator.py
- report_context / manifest / source_status / evidence_status 相關 fixture 與 QA probe
- official generator / report replay artifact

## 直接消費者

- Owner 手機 Telegram 報文讀者
- official generator / report runner
- strategy decision payload 消費者
- report_context manifest / source_status / evidence_status 消費者
- QA replay / probe
- scripts/monitor_trend_continuation.py 的人工或 runner 只讀監控消費者

## 輸出契約

### 1. trend_continuation 驗證測試契約

新增 tests/test_trend_continuation.py，至少覆蓋：

- 回踩延續正向 fixture：
- 趨勢成立
- 回踩 ma5 / ma10
- 回踩後放量站回
- evidence positive
- strategy 輸出 decision_type="trend_continuation"
- action 為 BUY
- 倉位為小倉且 <=15%
- official generator / report 報文出現 趨勢延續 與 小倉
- extended spike 無回踩 fixture：
- 不得 BUY
- 不得輸出 decision_type="trend_continuation" 的 BUY
- 負證據 fixture：
- win_rate < 55% 或 avg_return_5d <= 0 時不得 BUY
- 同源判定 fixture：
- 正式策略形態判定與 scripts/research_trend_continuation.py 共用同一函數或同一抽出 helper
- 同一 OHLCV fixture 的 research_match 與 production_match 必須一致

若第 1 項測試不通過，Tech 必須先修 v20.4.36 階段二實裝，不得只改測試期待值。

### 2. 監控腳本契約

新增 scripts/monitor_trend_continuation.py，只讀、可重跑、不得 live delivery。

輸出至少包含：

{
"status": "ok | alert | insufficient-data | source-error",
"trade_date": "YYYY-MM-DD",
"source": "production-read-only",
"setup_key": "trend_continuation",
"live_hit_count": 0,
"evaluated_trade_count": 0,
"live_win_rate_5d": null,
"backtest_win_rate_5d": 0.5517,
"backtest_avg_return_5d": 0.0226,
"win_rate_diff": null,
"consecutive_below_threshold": 0,
"alert_threshold_win_rate": 0.45,
"alert_after_trades": "N",
"alert": false
}

契約：

- 只讀既有 production source-of-truth。
- 若缺少可驗證的實盤命中 / outcome source，輸出 source-error 或 insufficient-data，不得用 runtime cache 或自造 fixture 當實盤勝率。
- 低於 45% 連續 N 筆才告警；N 必須是明確 CLI 參數或常量，並在 help / output 中可見。
- 監控只產生 stdout / artifact，不發 Telegram，不寫 DB。
- 回測基準需讀既有 trend_continuation artifact 或同源研究輸出，不得硬寫一份會漂移的邏輯。

### 3. 資料依據預設隱藏契約

presentation/report.py 新增或使用：

SHOW_DATA_BASIS = False

契約：

- 預設隱藏第三則「資料依據」文字段。
- 只隱藏文字呈現，不刪 report_context。
- 不改 manifest。
- 不改 source_status。
- 不改 evidence_status。
- 不改 compute_evidence_score。
- 不改 fail-closed。
- 不改過熱、減碼、停損、停利、持倉主行動邏輯。
- 若 SHOW_DATA_BASIS=True，原資料依據段可恢復顯示。

### 4. QA probe 改讀 manifest 契約

原本驗「資料依據」文案的測試 / probe，改讀：

- report_context.manifest
- report_context.source_status
- report_context.evidence_status

驗收重點從「手機文字有沒有資料依據」改為「內部來源狀態是否仍完整、沒有被隱藏文字一起刪掉」。

### 5. 未持倉回測行降噪契約

core/generator.py 對未持倉回測行做同 setup_key 重複降噪。

契約：

- 同一卡片 / 同一未持倉報文區塊內，相同 setup_key 的回測摘要最多顯示一次。
- 不同 setup_key 不得被合併。
- 不得刪除 manifest / evidence payload。
- 不得影響持倉區塊的風控、減碼、停損、停利。
- 不得讓 trend_continuation 小倉依據消失到無法追溯；手機文字可短，manifest 必須完整。

## 版本契約

- 目前已存在使用者可見版本 v20.4.36，不得回退。
- 若本輪只做驗證、只讀監控、預設隱藏文字與降噪，可維持 v20.4.36，但 Tech 必須在 CHANGELOG.md 明確說明。
- 若實際改動新增或改變使用者可見 header / 報文結構常量，需同步升版或更新版本字串。
- QA 必須核對實際 header / 常量與 CHANGELOG.md 說法一致。

## 已存在且不得回退的契約

- trend_continuation BUY 僅限回踩站回，不包含 extended spike 無回踩。
- trend_continuation 倉位小倉且 <=15%。
- 負證據、缺證據、source-error 不得 BUY。
- 形態判定需與 scripts/research_trend_continuation.py 同源。
- 其他 setup 不得因 evidence 單獨轉 BUY。
- RR 公式不得變。
- DB schema/write path 不得變。
- live Telegram 不得觸發。
- 無可買標的時不得使用像推薦的文案。
- 分組標題、卡片狀態、漏斗、索引、詳情必須一致。
- 同一持倉在同一份報文只能有一個主行動。
- 資料依據文字可隱藏，但 manifest / source_status / evidence_status 不得消失。
- fail-closed、過熱、減碼、同日入場即錯風控不得被資料依據隱藏影響。

## 驗收條件

1. tests/test_trend_continuation.py 存在，且正向回踩延續 fixture 能讓正式 strategy 產生 trend_continuation BUY 小倉。
2. 同一正向 fixture 經 official generator / report 路由後，手機報文出現 趨勢延續 與 小倉。
3. extended spike 無回踩 fixture 不 BUY。
4. 負證據 fixture 不 BUY。
5. 形態判定與 scripts/research_trend_continuation.py 共用函數或同源 helper；測試需能防止研究 / 實盤判定漂移。
6. scripts/monitor_trend_continuation.py 只讀執行，能輸出實盤命中數、勝率、與回測差異、連續低於 45% N 筆告警欄位。
7. monitor 在缺 source-of-truth 時 fail closed 為 source-error / insufficient-data，不得產生假勝率。
8. presentation/report.py 預設不顯示第三則資料依據文字段。
9. SHOW_DATA_BASIS=True 時資料依據文字可恢復。
10. 隱藏資料依據後，manifest / source_status / evidence_status 仍存在且內容不漂移。
11. 原驗資料依據文案的 QA probe 已改讀 report_context manifest / source_status / evidence_status。
12. 未持倉回測行同 setup_key 不重複顯示；不同 setup_key 保留。
13. official generator / report replay 驗證手機報文無資料依據噪音、無回測行重複、仍有 trend_continuation 小倉可讀路徑。
14. QA 必須補至少一個 Tech 未覆蓋的反證：手機報文誤讀、manifest 漂移、source-error fail-closed、或 duplicate setup_key 降噪邊界。
15. QA 結論若拿不到 official generator / report artifact，只能是 conditional pass 或 阻塞，不得用 helper-only fixture 直接通過。

## 範例或 Fixture

### 正向回踩延續 fixture

條件：

- 趨勢成立。
- 回踩 ma5 / ma10 不破。
- 回踩後放量站回。
- evidence:
- sample_n >= 30
- win_rate_5d >= 55%
- avg_return_5d > 0
- polarity = positive

期望：

{
"decision_type": "trend_continuation",
"action": "BUY",
"position_size_max": 0.15,
"card_status_contains": ["趨勢延續", "小倉"]
}

### extended spike 無回踩 fixture

條件：

- 創新高或 extended spike。
- 無 ma5 / ma10 回踩站回。

期望：

{
"action": "WAIT",
"must_not_have_buy_decision_type": "trend_continuation"
}

### 負證據 fixture

條件：

- 形態近似成立。
- win_rate_5d < 55% 或 avg_return_5d <= 0。

期望：

{
"action": "WAIT",
"reason_contains": "證據不足"
}

### 資料依據隱藏 fixture

條件：

- report_context 有 manifest / source_status / evidence_status。
- SHOW_DATA_BASIS=False。

期望：

{
"visible_text_not_contains": "資料依據",
"manifest_exists": true,
"source_status_exists": true,
"evidence_status_exists": true
}

### 回測行降噪 fixture

條件：

- 未持倉候選含兩筆相同 setup_key="trend_continuation" 回測摘要。
- 另有一筆不同 setup_key。

期望：

{
"trend_continuation_backtest_line_count": 1,
"different_setup_key_line_preserved": true
}

## 失敗標本與驗收路由

失敗標本：

- trend_continuation 實裝後，正向回踩延續 fixture 仍無法 BUY。
- 報文只出現文字，但 strategy payload 沒有 decision_type="trend_continuation"。
- extended spike 無回踩被 BUY。
- 負證據仍 BUY。
- 研究腳本與正式策略各自判定，導致同一 fixture 結果不同。
- 隱藏「資料依據」時，把 manifest / source_status / evidence_status 一起刪掉。
- QA probe 仍依賴可見文案，導致資料依據隱藏後誤判。
- 同一 setup_key 回測行在未持倉卡片重複刷屏。
- 降噪誤刪不同 setup_key 或誤刪 trend_continuation 可追溯依據。

官方驗收路由：

1. research/shared pattern function fixture
2. strategy / condition engine payload
3. tests/test_trend_continuation.py
4. scripts/monitor_trend_continuation.py read-only CLI output
5. core/generator.py message list
6. presentation/report.py report_context
7. official generator / report replay artifact
8. 手機閱讀路徑反證
9. manifest / source_status / evidence_status 不漂移反證

## 明確禁止事項

- 禁止改 RR 公式。
- 禁止改 DB schema / RLS / grant / policy / role / index / constraint。
- 禁止 live Telegram delivery。
- 禁止新增 production write。
- 禁止把 extended spike 無回踩改成 BUY。
- 禁止把負證據或 source-error 改成 BUY。
- 禁止只改測試期待值來通過 trend_continuation 正向 fixture。
- 禁止另寫一套與研究腳本不同的 trend_continuation 形態判定。
- 禁止刪 manifest / source_status / evidence_status 來達成資料依據隱藏。
- 禁止讓 QA probe 只看手機文字。
- 禁止用 synthetic helper fixture 取代 official generator / report 驗收。
- 禁止把同 setup_key 降噪擴成全量刪除不同 setup 或不同卡片資訊。

## 阻塞條件

- 找不到 v20.4.36 trend_continuation 正式決策路徑，且無法在本輪修到 strategy payload 層。
- 找不到可共用的研究形態判定函數，且抽出同源 helper 會超出本輪範圍。
- monitor 缺可驗證的實盤命中 / outcome source-of-truth；此時監控部分應輸出 source-error / insufficient-data，不得偽造勝率。
- official generator / report replay 無法產生，且任務仍宣稱手機報文完成。
- 隱藏資料依據會破壞 manifest / source_status / evidence_status。
- 需要 DB schema、production write 或 live Telegram 才能完成；本輪不得越權，需 blocked 回 Architect / Owner。

## 本輪停止條件

完成到以下範圍即停止：

- tests/test_trend_continuation.py 覆蓋正向 BUY、extended spike 不 BUY、負證據不 BUY、研究 / 實盤同源判定。
- 若第 1 項不通過，已先修到正式 strategy + official generator / report 路由可重跑通過。
- scripts/monitor_trend_continuation.py 只讀輸出命中數、勝率、回測差異與 45% 連續 N 筆告警欄位；缺 source 時 fail closed。
- SHOW_DATA_BASIS=False 預設隱藏第三則資料依據文字，且 manifest/source_status/evidence_status 不漂移。
- QA probe 改讀 manifest/source_status/evidence_status。
- 未持倉同 setup_key 回測行已降噪。
- QA 完成手機報文與 manifest 不漂移反證。

旁支問題不納入本輪，只能記待辦：

- 重新設計 trend_continuation 門檻。
- 擴大到其他 setup 的 evidence BUY。
- 新增 DB outcome ledger 或 schema。
- production backfill / write。
- live Telegram 發送。
- 全報文重排或策略樹重構。
