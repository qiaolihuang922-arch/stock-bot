# TASK: v19.4.1 Telegram 推送順序調整

## 時間性

- 任務日期：2026-05-26
- 來源任務：`DISPATCH.md` Task Brief
- 目標版本：`v19.4.1`
- 任務性質：Telegram 多段訊息推送順序調整
- version_level：`patch`
- qa_level：`L1`
- 狀態：PM 定義需求，等待 Tech 實作
- 邊界：只改 Telegram 多段訊息送出順序，不改策略、不改報文內文、不改 DB

## 需求目標

目前 Telegram 報文是多段訊息連續推送。使用者打開 Telegram 時，最下面的新訊息最容易直接看到。

現在最重要的總覽摘要在第一段，後續持倉詳情與未持倉詳情會把摘要往上推，導致使用者一打開 Telegram 先看到的是詳情，而不是今日決策總覽。

v19.4.1 目標：

- 讓最重要的總覽摘要最後送出。
- 讓使用者打開 Telegram 時，最下面看到的是今日總覽摘要。
- 保留原本三段內容，不刪除持倉詳情與未持倉詳情。
- 不改每段內部排序、策略文案或交易判斷。

## 使用者可見變化

### 1. 預設三段訊息順序

目前使用者收到順序可能是：

```text
1. 總覽摘要
2. 持倉標的詳情
3. 未持倉標的詳情
```

v19.4.1 應改為送出：

```text
1. 持倉標的詳情
2. 未持倉標的詳情
3. 總覽摘要
```

Telegram 畫面最下面應是：

```text
【MM/DD 盤中｜v19.4.1】
📊 市場：...
🎯 今日重點：...
📌 持倉處理優先級
🕒 隔日追蹤
待確認候選
```

### 2. 最重要內容定義

以下內容屬於最重要，必須位於最後一段，也就是總覽摘要段：

- 市場狀態
- 資料來源
- 今日重點
- 不新增原因
- 持倉清單
- 持倉處理優先級
- 隔日追蹤
- 待確認候選
- 未持倉摘要分組

持倉詳情與未持倉詳情仍然保留，但不應壓住總覽摘要。

### 3. include_detail=True 時的順序

若 `include_detail=True`，完整詳情備份不應在總覽摘要後面送出，避免把摘要再次往上推。

建議順序：

```text
1. 完整詳情備份 chunk 1
2. 完整詳情備份 chunk 2
3. 持倉標的詳情
4. 未持倉標的詳情
5. 總覽摘要
```

若完整詳情備份有多個 split chunk，所有完整詳情 chunk 都應在總覽摘要之前送出。

### 4. 無持倉 / 無未持倉情境

即使某段內容為空，也仍遵守「總覽摘要最後」原則。

範例：

```text
1. 持倉標的：無持倉
2. 未持倉標的：...
3. 總覽摘要
```

或：

```text
1. 持倉標的：...
2. 未持倉標的：無
3. 總覽摘要
```

## 報文 / 流程設計

本任務只改「送出順序」，不改每段內部內容。

每段內容仍維持原本職責：

```text
【持倉標的】
完整持倉卡片
```

```text
【未持倉標的】
完整未持倉卡片
```

```text
【MM/DD 盤中｜v19.4.1】
市場摘要
今日重點
持倉處理優先級
隔日追蹤
待確認候選
摘要分組
```

送出後 Telegram 視覺結果應是：

```text
上方：較早送出的詳情
下方：最後送出的總覽摘要
```

## Edge Cases

- 如果只有一段訊息，仍可直接送出該訊息。
- 如果摘要被 split，需確保摘要 split 的最後一個 chunk 仍是最後送出；但應優先避免摘要超長。
- 如果完整詳情備份 include_detail 產生多個 chunk，所有 chunk 都必須在摘要之前。
- 如果未持倉詳情或持倉詳情為 `無`，仍不應跳過摘要最後送出。
- 如果 Telegram API 逐段送出失敗，本任務不改 retry / error handling。
- 不調整每段內部排序。
- 不調整持倉排序。
- 不調整未持倉分組。
- 不調整策略結果。

## 影響模組初判

可能影響：

- Telegram messages list ordering
- formatter messages assembly
- include_detail split chunk ordering
- formatter / snapshot 局部測試

預期主要涉及：

- `core/generator.py`
- `tests/test_generator_report.py`

不應影響：

- `services/analysis.py`
- `services/stock_api.py`
- `services/signal_store.py`
- `services/daily_snapshot_store.py`
- `services/position_store.py`
- `scripts/dry_run_replay.py`
- `scripts/backfill_signals.py`
- DB schema

## 不可變更範圍

本任務不可變更：

- 不改策略層。
- 不改買賣判斷。
- 不改 RR 門檻。
- 不改過熱規則。
- 不改加碼 / 減碼 / 停利 / 停損策略門檻。
- 不改 DB schema。
- 不改 replay / backfill。
- 不改股票池。
- 不改每段報文內部排序。
- 不刪除任何詳情資料。
- 不做全 repo refactor。

## 驗收標準

v19.4.1 需滿足：

1. `version_level` 為 `patch`，不引入新策略意圖。
2. `qa_level` 為 `L1`，驗證範圍以 formatter / 指定回歸為主。
3. 預設訊息列表中，總覽摘要為最後一段。
4. 預設訊息列表順序為：持倉詳情、未持倉詳情、總覽摘要。
5. Telegram 最後送出的訊息包含版本標題與市場摘要。
6. 總覽摘要仍包含市場狀態、今日重點、持倉處理優先級、隔日追蹤、待確認候選。
7. 持倉詳情仍保留完整卡片。
8. 未持倉詳情仍保留完整卡片。
9. `include_detail=True` 時，完整詳情備份 chunk 必須在總覽摘要之前送出。
10. `include_detail=True` 時，總覽摘要仍是最後送出的訊息。
11. 無持倉或無未持倉時，總覽摘要仍最後送出。
12. 不改每段內部排序。
13. 不改策略輸出。
14. 不改 DB / replay / backfill。
