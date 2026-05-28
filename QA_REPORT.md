# QA_REPORT:

## 測試範圍

- 依據：`TASK.md` v20.1.2、`CHANGELOG.md`、git diff。
- 重點復驗 Architect 指定兩個 Tech retry 阻塞點：
  - summary 內 market theme evidence 必須在今日結論 / 主線執行 / 新倉之後。
  - existing `market_theme_evidence` dict 必須重新驗證，report-derived only / malformed dict 不得 confirmed。
- 實測命令：
  - `pytest tests/test_generator_report.py tests/test_market_theme_evidence.py tests/test_notifier.py`
  - 結果：`62 passed, 21 warnings`。
- QA 額外補測：
  - malformed two structured family strings 但缺 required fields，不得 confirmed。
  - stale source family 不得 confirmed。
  - 實際 formatter message list 交給 notifier `send_many()`，最後 summary header / payload 消費不破壞。

## 關聯風險掃描

- 可吸收 diff 僅限：
  - `CHANGELOG.md`
  - `core/generator.py`
  - `core/market_theme_evidence.py`
  - `tests/test_generator_report.py`
  - `tests/test_market_theme_evidence.py`
  - `tests/test_notifier.py`
- worktree 殘留：
  - `git status --short` 只顯示上述 6 個 tracked modified files。
  - `.qa_tmp/pytest_cache` 為本次測試暫存，不屬於 tracked diff。
- 未發現新增 DB schema / migration / cache / external provider / live Telegram / Supabase write / backfill diff。
- formatter direct consumer：
  - `formatTelegramMessages()` 仍回傳 message list，summary 仍為最後一則。
  - `tests/test_notifier.py` 與 QA 補測確認 `send_many()` 可消費 formatter output。
- provider contract：
  - `build_market_theme_evidence_provider()` 會把 existing evidence dict 拆回 source families，再交給 `build_market_theme_evidence()` 檢查 required fields / freshness / family rules。
  - 未直接信任 existing dict 的 `confirmed: true`。

## 跨區塊語意一致性

- Header 已升為 `v20.1.2`。
- summary 手機閱讀順序實測為：
  - Header
  - 市場 / 資料
  - 今日結論
  - 原因
  - 主線
  - 執行
  - 新倉
  - 市場題材 evidence
- QA 補測確認：
  - `🧭 今日結論：` 早於 `🧭 新倉：無有效進場。`
  - `🧭 新倉：無有效進場。` 早於 `市場題材：來源不足，僅追蹤`
- confirmed fixture 仍顯示 guard：
  - `市場題材：AI/電子供應鏈證據偏多，但買點仍看個股條件`
- malformed / report-derived / stale case 不會出現：
  - `今日可追主線買進`
  - `AI / 電子供應鏈 confirmed 偏多`
  - `🧭 主線：AI / 電子供應鏈仍偏多。`

## 使用者誤讀風險

- 上輪阻塞的「市場題材先於今日能不能買」已修掉；evidence 不再壓過新倉結論。
- report-derived only 與 malformed existing dict 均降級為來源不足，僅追蹤，不會讓 Owner 誤讀成可追主線買進。
- v20.1.1 手機降噪契約未見回退：
  - 未恢復 `若收盤`
  - 未恢復 `不代表看空產業`
  - 未恢復 `明日風控｜加碼10`
  - `待觸發加碼10` 測試仍存在。

## 質疑與反證

- 質疑 1：Tech 是否只修測試 helper，未接 production formatter？
  - 反證：`core/generator.py` 的 `market_theme_summary_evidence()` 已呼叫 `build_market_theme_evidence_provider()`，`ai_supply_chain_mainline_supported()` 也改走 normalized evidence。
- 質疑 2：malformed dict 若偽造兩個 structured families 是否仍可能 confirmed？
  - 反證：QA 補測 `source_families=["market_state","structured_strategy_evidence"]` 但缺欄位，結果 `confirmed=False`、`level=weak`。
- 質疑 3：stale source 是否可能被算入 confirmed？
  - 反證：QA 補測 stale `market_state` + fresh `structured_strategy_evidence`，結果 `confirmed=False`，limitations 包含 `freshness=stale`。
- 質疑 4：notifier consumer 是否因 message list/header 變更破壞？
  - 反證：Tech 測試與 QA 補測均確認 `send_many()` 最後送出的 summary 保留 `v20.1.2` header。

## 未測項目

- 未跑 full pytest；本輪為 L2 retry，Architect 指定重點為兩個阻塞點與直接 consumer smoke。
- 未做 live Telegram、live Supabase write、正式 backfill；符合 `TASK.md` 非目標。
- 未驗證未來外部 structured provider，因本輪禁止新增外部 provider。

## QA 結論

通過。兩個 retry 阻塞點已修復；可吸收 diff 限上述 6 個檔案，不建議整包合併 worktree。
