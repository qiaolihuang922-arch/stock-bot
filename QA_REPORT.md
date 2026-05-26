# QA_REPORT.md

本文件由 QA 維護，提交給 Architect。只記錄本輪 v19.5.1 QA 重測結果。

## 任務狀態

- 狀態：QA 驗證完成
- 對應 TASK / CHANGELOG：`TASK.md`、`CHANGELOG.md`
- 提交日期：2026-05-26
- 任務：`v19.5.1-summary-semantic-consistency`
- 版本：v19.5.1
- QA 等級：L1

## 測試範圍

本輪是針對 QA blocker 的重測。依 `DISPATCH.md` 與 `CHANGELOG.md`，重點驗證：

- `未持倉 0 檔僅追蹤` 是否已從今日結論消失。
- `其餘 0 檔僅追蹤` 是否不再出現。
- `未持倉無追蹤` 是否與漏斗 `不可買追蹤 0`、詳情索引 `未持倉追蹤 0` 語意一致。
- 明日執行清單仍保留持倉盈虧百分比與合格可買項。
- 不可買等待標的仍不進明日執行清單。
- Summary-last / reply_markup-last contract 是否未回退。

未執行 full pytest、replay/backfill、live Telegram、live Supabase。

## 執行命令

```bash
.venv/bin/python -m pytest tests/test_generator_report.py tests/test_notifier.py
```

結果：

```text
35 passed, 21 warnings in 2.24s
```

另執行 QA 補充重測 smoke：
- 有持倉 + 合格 BUY + 0 個不可買追蹤候選。
- 無持倉 + 合格 BUY + 0 個不可買追蹤候選。
- 持倉占滿執行清單 + 多個不可買追蹤候選。
- formatter-to-notifier `reply_markup` 契約。

結果：

```text
QA_RETEST_OK 289 242 456
```

## 測試結果

### Blocker 回歸

結果：通過。

上一輪阻塞場景：
- 有 1 檔持倉。
- 有 1 檔合格 `BUY`。
- 沒有不可買等待 / 追蹤候選。

重測確認：
- 今日結論不再出現 `未持倉 0 檔僅追蹤`。
- 今日結論不再出現 `其餘 0 檔僅追蹤`。
- 今日結論改為包含 `未持倉無追蹤`。
- 漏斗仍保留 `可買 1｜不可買追蹤 0`，方便對帳。
- 詳情索引仍保留 `持倉 1｜執行 2｜未持倉追蹤 0｜淘汰 0`。
- 明日執行清單同時列出持倉與可買項。
- 持倉執行項仍有 `+/-xx.xx%` 盈虧百分比。

### 額外分支

無持倉 + 合格 BUY + 0 個不可買追蹤候選：
- 不再出現 `其餘 0 檔僅追蹤`。
- 顯示 `無持倉，可買 1 檔；未持倉無追蹤`。
- 漏斗 / 詳情索引數字一致。

持倉占滿 5 項 + 多個不可買追蹤候選：
- 明日執行清單維持 5 項。
- 不可買追蹤候選不進 numbered 執行項。
- 顯示 `未持倉 4 檔只等觸發，不列入明日執行`。
- 漏斗顯示 `不可買追蹤 4`。
- 詳情索引顯示 `持倉 5｜執行 5｜未持倉追蹤 4`。

Telegram contract：
- 前兩段詳情不帶 `reply_markup`。
- 最後 summary 段帶 `reply_markup`。
- 最後 summary 段仍包含 `🧭 今日結論`。

## 關聯風險掃描

### 直接呼叫方

- `core/generator.formatTelegramMessages()`：仍回傳 list，summary 在 `messages[-1]`。
- `core/generator.generate_report()`：仍回傳 `(messages, reply_markup)`。
- `main.py -> send_many()`：契約未改。
- `services/notifier.send_many()`：未修改，仍將 `reply_markup` 綁到最後一段。

直接消費者契約未見回退。

### 下游與副作用

- 本輪 diff 未修改 `services/analysis.py`、DB、replay/backfill、notifier、watchlist。
- 本輪只修 summary 結論文案分支。
- 漏斗與詳情索引保留 0 數字是合理的對帳資訊；主結論使用 `未持倉無追蹤` 做降噪，語意不衝突。

## 跨區塊語意一致性

已檢查：
- `今日結論`
- `明日執行清單`
- `未持倉漏斗（非執行）`
- `詳情索引`
- `reply_markup` 最後摘要段契約

結論：
- `今日結論` 用 `未持倉無追蹤` 表達沒有等待候選。
- `未持倉漏斗` 用 `不可買追蹤 0` 保留數字對帳。
- `詳情索引` 用 `未持倉追蹤 0` 保留數字對帳。
- 三者語意一致：主結論降噪，漏斗 / 索引保留統計。
- 明日執行清單的 numbered items 與 `執行 N` 可對上。

## 使用者誤讀風險

已解除上一輪主要誤讀風險：
- 不再讓使用者看到不存在的 `0 檔僅追蹤`。
- `未持倉無追蹤` 可清楚表達沒有等待候選。
- `可買 1` 與 `不可買追蹤 0` 分離，使用者不會把 0 追蹤誤解成行動項。
- 不可買等待候選仍標示為只等觸發、不列入明日執行。

殘留風險：
- 真實 Telegram UI 未測，但本輪本地 formatter 與 notifier contract 已通過。

## 質疑與反證

### PM 是否漏需求

PM 沒漏；`TASK.md` 已明確要求避免 `追 0 檔` 噪音。本輪 Tech 已補齊該分支。

### Tech 是否漏同步

未見漏同步。`CHANGELOG.md` 明確說明修復 `holding_count and buy_count and tracking_count == 0`，並同步處理 `無持倉 + 可買 + tracking_count == 0`。

### 測試是否能證明沒有破壞直接消費者

可以。QA 已用 formatter 產生 messages，餵入 `send_many()` mock，確認 `reply_markup` 仍綁最後 summary 段。

### QA 是否主動找到指定清單之外的風險

有。除上一輪 blocker 精確回歸外，本輪也補測了無持倉 + 可買 + 0 追蹤，以及持倉占滿清單 + 不可買追蹤候選，未發現新阻塞。

## 驗收項結果

- `version_level=patch`：通過。
- `qa_level=L1`：通過。
- 今日結論不再輸出 `未持倉 0 檔僅追蹤`：通過。
- 今日結論不再輸出 `其餘 0 檔僅追蹤`：通過。
- `未持倉無追蹤` 與漏斗 / 詳情索引一致：通過。
- 明日執行清單全是持倉時顯示持倉優先：通過既有測試。
- 不可買等待標的不列入明日執行：通過。
- 漏斗標明非執行 / 不可買追蹤：通過。
- 詳情索引區分執行 / 未持倉追蹤 / 淘汰：通過。
- 持倉執行清單保留盈虧百分比：通過。
- Summary-last / reply_markup-last contract：通過。
- 不改 strategy / DB / replay / backfill：未見 diff。

## 未測項目

本輪未執行：
- full pytest。
- replay / backfill dry-run。
- live Telegram delivery。
- live Supabase write。
- Telegram 客戶端實機截圖。

原因：
- `DISPATCH.md` 指定 `qa_level=L1`。
- `TASK.md` / `CHANGELOG.md` 限定本輪只改 formatter / summary view model。

## 殘留風險

- 真實 Telegram 到達順序與 UI 呈現未測。
- 若未來產品要求完全不顯示任何 0 統計，需另開 PM 任務；本輪保留漏斗 / 索引中的 0 是為了數字可追溯。

## QA 結論

QA 結論：通過。

v19.5.1 QA blocker 已解除。`未持倉 0 檔僅追蹤` 已消失，`未持倉無追蹤` 與漏斗 / 詳情索引一致，summary-last / reply_markup-last contract 未回退。可交回 Architect 更新狀態。
