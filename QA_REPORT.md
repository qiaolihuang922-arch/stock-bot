# QA_REPORT.md

本文件由 QA 維護，提交給 Architect。只記錄本輪 v19.4.1 QA 結果。

## 任務狀態

- 狀態：QA 驗證完成
- 對應 TASK / CHANGELOG：`TASK.md`、`CHANGELOG.md`
- 提交日期：2026-05-26
- 任務：`v19.4.1-telegram-order`
- 版本：v19.4.1
- QA 等級：L1

## 測試範圍

依 `DISPATCH.md` 指定 `qa_level=L1`，本輪做局部 formatter / notifier contract / 指定回歸驗證。

覆蓋範圍：
- `formatTelegramMessages()` 預設多段訊息順序。
- `include_detail=True` 時完整詳情備份 chunk 與摘要順序。
- 無持倉 / 無未持倉情境下摘要仍最後送出。
- 總覽摘要內容仍包含版本、市場摘要、持倉處理優先級、隔日追蹤、待確認候選。
- `send_many(messages, reply_markup=...)` 多段訊息時，`reply_markup` 綁定最後一段摘要。
- `send_many("single message", reply_markup=...)` 單段字串保留原行為。
- `main.py` 直接呼叫契約為 `generate_report() -> send_many(messages, reply_markup=reply_markup)`，本輪確認 notifier 層已按 messages list 最後一段附加按鈕。

未執行全局測試、full pytest、replay/backfill dry-run、live Telegram、live Supabase write。

## 執行命令

```bash
.venv/bin/python -m pytest tests/test_notifier.py tests/test_generator_report.py
```

```bash
.venv/bin/python - <<'PY'
from datetime import datetime
from unittest.mock import patch
from core import generator
from services import notifier
from tests.test_generator_report import render_payload

base = [100,101,102,103,104,105,106,107,108,109,110,111,112,113,114,115,116,117,118,119]
holding = render_payload(base, {"shares": 50, "avg_price": 118}, price=119, change=1.4)
unheld = render_payload(base, None, price=119, change=1.4)
unheld["stock_code"] = "2421"
messages = generator.formatTelegramMessages(
    {"智原": holding, "建準": unheld},
    "FULL DETAIL",
    None,
    None,
    "⏳ 觀望",
    datetime(2026, 5, 25),
)
reply_markup = generator.execution_reply_markup({"智原": holding, "建準": unheld})

assert len(messages) == 3
assert "【持倉標的】" in messages[0]
assert "【未持倉標的】" in messages[1]
assert "｜v19.4.1】" in messages[-1]
assert "📊 市場：" in messages[-1]

with patch.object(notifier, "send", return_value=True) as mock_send, patch.object(notifier.time, "sleep"):
    ok = notifier.send_many(messages, reply_markup=reply_markup)

assert ok is True
assert mock_send.call_args_list[0].kwargs["reply_markup"] is None
assert mock_send.call_args_list[1].kwargs["reply_markup"] is None
assert mock_send.call_args_list[-1].kwargs["reply_markup"] == reply_markup
assert "📊 市場：" in mock_send.call_args_list[-1].args[0]
print("CONTRACT OK", len(messages), mock_send.call_count)
PY
```

## 測試結果

### Formatter / Notifier 指定回歸

結果：通過。

```text
34 passed, 21 warnings in 1.66s
```

警告來自既有第三方套件 / Python 版本 deprecation，未見 v19.4.1 測試失敗。

### Formatter -> Notifier Contract Smoke

結果：通過。

```text
CONTRACT OK 3 3
```

結論：
- 真實 formatter 輸出 3 段訊息。
- 第 1 段為 `【持倉標的】`。
- 第 2 段為 `【未持倉標的】`。
- 最後一段為 `v19.4.1` 總覽摘要，且包含 `📊 市場：`。
- `send_many()` 對前兩段傳入 `reply_markup=None`。
- `send_many()` 對最後一段總覽摘要傳入 `reply_markup`。

## 驗收項結果

- `version_level` 為 patch，不引入新策略意圖：通過。
- `qa_level` 為 L1，本輪只做 formatter / notifier contract / 指定回歸：通過。
- 預設訊息列表中，總覽摘要為最後一段：通過。
- 預設訊息列表順序為持倉詳情、未持倉詳情、總覽摘要：通過。
- Telegram 最後送出的訊息包含版本標題與市場摘要：通過。
- 總覽摘要仍包含市場狀態、今日重點、持倉處理優先級、隔日追蹤、待確認候選：通過。
- 持倉詳情仍保留完整卡片：通過。
- 未持倉詳情仍保留完整卡片：通過。
- `include_detail=True` 時，完整詳情備份 chunk 在總覽摘要之前：通過。
- `include_detail=True` 時，總覽摘要仍是最後送出的訊息：通過。
- 無持倉或無未持倉時，總覽摘要仍最後送出：通過。
- 多段訊息時，`reply_markup` 綁定最後一段總覽摘要：通過。
- 單段字串訊息時，`reply_markup` 仍綁定該訊息：通過。
- 不改每段內部排序：通過。
- 不改策略輸出：未發現變更，且本輪未測策略 regression。
- 不改 DB / replay / backfill：未發現變更，本輪未執行相關測試。

## 未測項目

本輪未執行：
- full pytest。
- replay / backfill dry-run。
- live Telegram delivery。
- live Supabase write。
- formal backfill write。
- Telegram 客戶端實機渲染截圖。
- 真實 Telegram API 對多段訊息的實際到達順序。

原因：
- `DISPATCH.md` 指定 `qa_level=L1`。
- `TASK.md` 與 `CHANGELOG.md` 明確本輪只改 Telegram messages list ordering 與 notifier `reply_markup` 附著位置。
- `CHANGELOG.md` 明確未修改策略、DB、replay/backfill、股票池與 Supabase Edge Function。

## 殘留風險

- 本輪使用 mock 驗證 `send_many()` 參數綁定，未實際呼叫 Telegram API；若 Telegram 平台端發生送達順序延遲或 UI 特殊呈現，仍需 live Telegram 驗證。
- 若其他外部流程繞過 `send_many()` 直接發送 messages list，本輪未覆蓋該路徑；目前本地直接呼叫方確認為 `main.py`。
- 若未來摘要內容超長被 split，目前測試重點仍是完整詳情 split 與多段發送，摘要 split 的產品呈現需另開任務補測。

## QA 結論

QA 結論：通過。

v19.4.1 Telegram 推送順序與按鈕綁定修正已通過 L1 驗證。可交回 Architect 更新狀態。
