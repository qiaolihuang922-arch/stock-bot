# CHANGELOG

## 2026-05-26 - v19.4.1 Telegram 推送順序與按鈕綁定修正

### 修改內容
- 依 `TASK.md` 與 Architect 收口補充處理 v19.4.1 patch。
- 保留既有 `formatTelegramMessages()` 多段順序：
  - 預設順序：`【持倉標的】` -> `【未持倉標的】` -> 總覽摘要。
  - `include_detail=True`：完整詳情備份 chunk -> `【持倉標的】` -> `【未持倉標的】` -> 總覽摘要。
- 補修 Telegram 發送層 `reply_markup` 綁定位置：
  - 多段訊息 list 發送時，inline keyboard / `reply_markup` 改為綁定最後一段訊息。
  - v19.4.1 最後一段是總覽摘要，因此按鈕會跟隨最下面的總覽摘要。
  - 單段字串訊息仍維持原行為，`reply_markup` 直接附在該訊息。
- 新增 notifier 層單元測試，覆蓋：
  - 三段訊息時只有最後一段收到 `reply_markup`。
  - 單段字串訊息仍可收到 `reply_markup`。

### 修改檔案
- `core/generator.py`
- `services/notifier.py`
- `tests/test_generator_report.py`
- `tests/test_notifier.py`
- `CHANGELOG.md`

### 未影響模組
- `services/analysis.py`
- RR 門檻
- 過熱 / 漲停不追規則
- 加碼 / 減碼 / 停利 / 停損策略門檻
- scoring
- strongest candidate 硬規則
- snapshot 組裝與驗證
- DB schema
- DB 寫入邏輯
- replay / backfill
- 股票池
- Supabase Edge Function
- TWSE/Yahoo provider 底層請求邏輯
- 每段報文內部排序與文案

### 風險點
- 本次只改 Telegram 多段發送時 `reply_markup` 附著位置，不改策略輸出。
- 若外部流程仍假設按鈕一定在第一段訊息，需要改以最後一段摘要為準。
- `include_detail=True` 時，完整詳情 chunk 會先送出，按鈕仍會附在最後送出的總覽摘要。
- 本次未跑 full regression、live Telegram、DB、replay/backfill。

### 建議 QA 驗證範圍
- 預設 `formatTelegramMessages()`：
  - `messages[0]` 是 `【持倉標的】`。
  - `messages[1]` 是 `【未持倉標的】`。
  - `messages[-1]` 是總覽摘要，且包含版本標題與市場摘要。
- `include_detail=True`：
  - 完整詳情備份 chunk 在最前面。
  - 總覽摘要仍是最後一段。
- `send_many(messages, reply_markup=...)`：
  - 多段訊息時，前面詳情段不帶 `reply_markup`。
  - 最後的總覽摘要段帶 `reply_markup`。
  - 單段字串訊息仍帶 `reply_markup`。
- 無持倉 / 無未持倉：
  - 空段仍保留。
  - 總覽摘要仍最後送出。
- 確認不改每段內部排序、策略判斷、DB / replay / backfill。
- 已執行最低必要驗證：
  - `.venv/bin/python -m pytest tests/test_notifier.py tests/test_generator_report.py`
  - 結果：`34 passed`
