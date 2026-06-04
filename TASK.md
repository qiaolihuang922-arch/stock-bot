# TASK: future_30d_watch_live_readonly_sources_v20_4_46

## 任務狀態

- task_id: future_30d_watch_live_readonly_sources_v20_4_46
- 任務類型: normal_patch
- 狀態: ready_for_tech
- 版本建議: v20.4.46
- QA 分級建議: L2
- 流程: PM -> Tech -> QA；本 TASK 不授權 Architect / PM 直接改產品代碼。

## Owner 問題

Owner 要把 v20.4.45 Telegram 第 4 則 `【未來30日關注】` 改成 live readonly source 試行版：

- 不走 DB。
- 不寫庫。
- 不 live Telegram。
- 每次 `generate_report()` 產生報文時即時查資料。
- 資料不足或來源不穩定時 fail closed，不假造市場類比、法說會或官方事件。

本輪聚焦三個 source：

1. 台股今日盤勢 / 歷史類比：使用 TWSE OpenAPI / 官方 TAIEX 歷史或 Yahoo readonly 備援，資料不足 fail closed。
2. 法說會：使用 MOPS 官方 live；若 MOPS SPA/AJAX 無穩定表格或被安全頁擋住，顯示 source-error，不假造。
3. 全球事件：使用官方央行 / 統計 / 政府日程 live 或可解析 source；解析失敗可保留固定 seed fallback，但必須標明 source / fallback。

## 使用者可見結果

手機閱讀時，Telegram message-list 應維持 4 則：

1. 持倉相關報文。
2. 未持倉相關報文。
3. 決策簡報。
4. `【未來30日關注】`。

第 4 則固定三段：

```text
【06/04 未來30日關注｜v20.4.46】
【未來30日關注】

歷史類比
歷史類比：無高相似崩盤樣本｜依據不足/相似度低｜source=TWSE

法說會提醒
法說會提醒：source-error（MOPS），本次不列事件

全球事件
06/05 美國就業報告｜影響面：通膨/利率｜source=BLS
06/10 美國 CPI｜影響面：通膨/利率｜source=BLS
...
```

手機閱讀要求：

- 第 4 則只能是「關注 / 提醒 / source 狀態」，不得寫成買賣建議。
- 第 4 則不得污染前三則 summary、漏斗、索引、持倉卡、未持倉卡。
- 若某段資料不足，該段單獨 fail closed，不應讓整份前三則報文失真。

## 非目標

- 不改交易策略、RR、買賣 / 加減碼 / 停損停利判斷。
- 不改 DB schema、RLS、grant、policy、role、index / constraint。
- 不讀 production DB、不寫 DB、不做 production backfill。
- 不發 live Telegram。
- 不新增跨日記憶或 local cache 當 source-of-truth。
- 不把全球事件 seed fallback 擴成交易判斷。
- 不把 MOPS 解析失敗時的公司法說會自行補字或假造。
- 不做全量 repo 清理或第 4 則以外的報文重設計。

## 影響模組與直接消費者

影響模組：

- `core/future_watch.py`
- `core/generator.py`
- `presentation/report.py` 若第 4 則 contract 需要同步。
- `tests/test_generator_report.py` 或新增 focused tests。

直接消費者：

- Telegram 第 4 則 message。
- `generate_report(dry_run=True)` official message-list。
- Owner 手機閱讀。
- QA replay / runner artifact parser。

## 輸出契約

### Source 契約

每個 live source adapter 必須 read-only、timeout bounded、fail closed：

- 成功：回傳 `status="available"` 與 items / line。
- 無資料：回傳 `status="available"` 與 empty items，只有在確定官方 source 成功解析且查無資料時才可視為 empty。
- source 失敗、被擋、HTML 結構不符、日期解析失敗：回傳 `status="source-error"` 或 `insufficient-data`。

`source-error` 不得被當成「無事件」。

### 歷史類比契約

主源：

- TWSE OpenAPI `https://openapi.twse.com.tw/v1/exchangeReport/MI_INDEX`
- TWSE OpenAPI `https://openapi.twse.com.tw/v1/exchangeReport/MI_5MINS_HIST`
- TWSE RWD 備援 `https://www.twse.com.tw/rwd/zh/TAIEX/MI_5MINS_HIST?response=json&date=YYYYMMDD`

Yahoo chart 只能作 readonly 備援，不能當完成口徑主源。

本輪最小試行：

- 若只取得今日 TAIEX / 近月資料，且不足以量化歷史崩盤 similarity，顯示 no high similarity / insufficient-data。
- 不得主觀硬套崩盤樣本。
- 不得出現「即將崩盤」「重演」。

### 法說會契約

主源：

- MOPS `https://mops.twse.com.tw/mops/web/t100sb02_1`
- MOPS AJAX 若可穩定解析才使用。

本輪最小試行：

- 僅查持倉 + watchlist / 未持倉候選股票。
- 若 MOPS 回安全頁、SPA shell、無 table、欄位無法辨識，顯示 `source-error（MOPS），本次不列事件`。
- 不 fallback 到非官方公司 IR 頁或新聞。

### 全球事件契約

優先官方 live / public schedule：

- Fed FOMC calendar
- BLS CPI / Employment release schedule
- BOJ calendar / release schedule
- BEA news schedule
- ECB calendar / monetary policy decision page

本輪最小試行：

- 只取 `today <= event_date <= today + 30 days`。
- 最多 5 筆。
- 日期升冪排序。
- 若 live parse 成功，顯示 `source=<official>`。
- 若部分 live source 失敗，可使用固定 seed fallback，但必須在資料結構或文案中保留 source / fallback 可追溯，不得假稱 live。

## 版本契約

- 使用者可見版本升 `v20.4.46`。
- 前三則版本同步為 `v20.4.46`，不得殘留 `v20.4.45`。
- 第 4 則 header 使用同版本。

## 驗收條件

- `generate_report(dry_run=True)` message-count 仍為 4，第 4 則在最後。
- 前三則不得包含 `【未來30日關注】`、`法說會提醒`、`全球事件`。
- Mock TWSE success / partial history 時，歷史類比有 source 狀態；相似度不足時不得顯示崩盤樣本。
- Mock TWSE source-error 時，歷史類比 fail closed。
- Mock MOPS blocked / security page / malformed HTML 時，法說會區塊 fail closed，不列假事件。
- Mock MOPS parsed rows 時，只列未來 30 日內、持倉 / 候選相關股票，最多 5 筆。
- Mock global official schedules 時，只列 30 日內官方事件，最多 5 筆，按日期排序。
- Mock global live source failure 時，seed fallback 可顯示，但不得污染前三則。
- 第 4 則不得含 `可買`、`可準備`、`今日下單`、`新倉建議`、`停損`、`停利`、`即將崩盤`、`重演`。
- 不得新增 DB read/write path。

## 範例或 Fixture

### TWSE insufficient fixture

```python
twse_source = {"status": "available", "today": {"index": "發行量加權股價指數", "change_pct": -1.68}, "history_rows": 4}
```

期望：

```text
歷史類比：無高相似崩盤樣本｜依據不足/相似度低｜source=TWSE
```

### MOPS blocked fixture

```python
mops_html = "<script>location.href = location.origin + '/mops';</script>"
```

期望：

```text
法說會提醒：source-error（MOPS），本次不列事件
```

### Global live fixture

```python
events = [
    {"date": "2026/06/05", "event": "美國就業報告", "impact": "通膨/利率", "source": "BLS"},
    {"date": "2026/06/10", "event": "美國 CPI", "impact": "通膨/利率", "source": "BLS"},
    {"date": "2026/06/16-17", "event": "Fed FOMC SEP", "impact": "利率/匯率", "source": "Fed"},
]
```

## 失敗標本與驗收路由

- Owner 看到的是最終 Telegram 報文；驗收路由必須打到 official `generate_report()` 或 `formatTelegramMessages()` message-list，不只測 helper。
- MOPS 失敗標本：官方頁回安全限制 / SPA shell / AJAX 無法解析時，第 4 則只可顯示 source-error，不可列公司事件。
- TWSE 失敗標本：OpenAPI 空資料、日期非交易日、欄位缺失時顯示 insufficient-data。
- 全球事件失敗標本：官方頁改版、日期解析失敗、非 30 日內事件，不得列入 live items。

## 明確禁止事項

- 禁止 DB read/write/backfill。
- 禁止用 local cache 當跨 run source-of-truth。
- 禁止手寫 production DML。
- 禁止從新聞媒體摘要推導全球大事件。
- 禁止 MOPS 不穩時 fallback 到非官方公司 IR 頁並當官方法說會。
- 禁止把歷史類比寫成預測或交易訊號。
- 禁止 live Telegram delivery。

## 阻塞條件

- 若 Tech 無法在不寫 DB、不用 token、不用登入、不依賴瀏覽器 session 的前提下取得 live source，該 source 必須 fail closed。
- 若 source adapter 需要新增 secret / credential，blocked。
- 若改動觸及策略 decision、DB schema/write path、交易狀態機，blocked 並退回 Architect。
- 若不能覆蓋 official message-list 驗收路由，QA 只能 conditional pass 或阻塞。

## 本輪停止條件

- 完成 v20.4.46 live readonly 試行 adapter 與 focused tests。
- QA 至少反證 official message-list、MOPS blocked、global fallback、前三則不污染。
- 不要求 full pytest、production runner artifact、live Telegram。
- 若 MOPS live 無法穩定解析，保留 fail-closed 即可，不在本輪硬解 SPA / token。
