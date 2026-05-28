# TASK: market_theme_evidence_dry_run_contract_v20_1_0 版本契約 QA blocker patch

## 任務狀態

- task_id: market_theme_evidence_dry_run_contract_v20_1_0_version_contract_patch
- 任務類型: tiny_patch
- 狀態: ready_for_tech
- 版本建議: patch
- 版本契約: 將使用者可見 Telegram header / VERSION / 相關測試期望 / CHANGELOG.md 版本同步由 v20.0.12 升到 v20.0.13
- QA 分級建議: L1
- QA 停止條件: 只驗版本字串同步、相關 formatter tests、notifier 直接消費者、以及 evidence blocker 修復未回退；不得擴大到 v20.1.0 新能力驗收

## Owner 問題

上一輪 market_theme_evidence_dry_run_contract_v20_1_0_qa_blocker 的 evidence blocker 修復已獲 QA conditional pass，只剩版本契約衝突：使用者可見版本仍卡在 v20.0.12，但 Owner 要求修 bug 後應正常進 patch。

本輪只修正版本契約，明確標示這是 QA blocker patch 修復，不是 v20.1.0 新能力發布。

## 使用者可見結果

Owner 在 Telegram 手機報文第一眼 header 應看到版本升為 v20.0.13。

手機閱讀路徑：

1. Owner 打開 Telegram。
2. 第一行 header 看到類似 【05/28 盤中｜v20.0.13】 或 【05/28 盤後｜v20.0.13】。
3. Summary 仍保留已通過的 evidence blocker 語意：缺 explicit source 時，不得把 AI / 電子供應鏈寫成 confirmed bullish。
4. Owner 不應看到任何 v20.1.0 新能力發布語意。

## 非目標

- 不重開 PM 需求範圍。
- 不改 evidence 判斷邏輯。
- 不改策略 decision。
- 不改 DB schema / DB payload。
- 不改 watchlist。
- 不做 live Telegram delivery。
- 不做 live Supabase write。
- 不改 scheduler / cron。
- 不新增 v20.1.0 能力。
- 不新增外部資料來源。
- 不修改 market theme confirmed / weak / absent contract，除非是防止本輪版本同步造成回退的測試期望更新。

## 影響模組

- 直接模組:
- Telegram formatter header 版本常量所在模組。
- VERSION 或等價使用者可見版本常量。
- formatter 版本 header 測試。
- notifier 直接消費者測試。
- CHANGELOG.md 版本描述。
- 不應影響模組:
- market theme evidence 判斷邏輯。
- strategy decision core。
- DB write path。
- watchlist generation。
- live Telegram sender 的實際發送行為。
- Supabase write path。
- scheduler / cron entrypoint。

## 直接消費者

Tech 必須確認並同步以下直接消費者：

- Telegram 報文 header formatter。
- notifier 組裝 / 傳送前讀取 formatter output 的直接路徑。
- 相關 formatter tests 中的 header 版本期望。
- 相關 notifier tests 中的版本字串期望。
- CHANGELOG.md 中本輪版本說明。

## 輸出契約

### Version Contract

- 使用者可見 Telegram header 必須顯示 v20.0.13。
- 程式版本常量 VERSION 或等價來源必須為 v20.0.13。
- formatter tests / notifier tests 不得仍期待 v20.0.12。
- CHANGELOG.md 必須說明：
- 本輪是 v20.0.13 QA blocker patch 修復。
- 本輪不是 v20.1.0 新能力發布。
- 保留已通過的 evidence blocker 修復。

### Evidence Regression Contract

必須保留上一輪已通過修復：

- 舊 market_summary 不能自我證明。
- 缺 explicit source 不得 confirmed。
- market_summary='AI / 電子供應鏈仍偏多' 加 market_mode='進攻偏熱' 不得湊成 confirmed。
- 缺 source 時 summary 不得輸出 AI / 電子供應鏈 confirmed bullish 語意。

## 驗收條件

1. Telegram header 實際輸出版本為 v20.0.13。
2. VERSION 或等價版本常量為 v20.0.13。
3. 相關 formatter tests 的版本期望已同步為 v20.0.13。
4. 相關 notifier tests 的版本期望已同步為 v20.0.13。
5. CHANGELOG.md 明確寫本輪是 v20.0.13 QA blocker patch，不是 v20.1.0 新能力發布。
6. 負面 evidence fixture 仍通過：舊 market_summary + market_mode='進攻偏熱' + 無 explicit source 時不得 confirmed。
7. 同一負面 fixture 的 Telegram summary 不得出現 AI 題材偏多、電子供應鏈偏多或等價 confirmed bullish 文案。
8. 不得改策略、DB、watchlist、live delivery、scheduler。
9. QA 只復驗版本字串、相關 formatter tests、notifier 直接消費者，以及 evidence 邏輯未回退。
10. QA 結論只能是 通過 或 conditional pass，且 QA_REPORT.md 格式必須符合 runner。

## 範例或 fixture

### Telegram header 期望形狀

【05/28 盤中｜v20.0.13】

或：

【05/28 盤後｜v20.0.13】

### Evidence 負面 fixture

input_fixture = {
"market_mode": "進攻偏熱",
"market_summary": "AI / 電子供應鏈仍偏多",
"internal_report_input": {
"summary": "AI / 電子供應鏈仍偏多",
},
"market_theme_evidence_sources": [],
}

### 負面 fixture 期望 summary 形狀

今日新倉：無有效進場
AI 題材：可追蹤，證據不足
電子供應鏈：可追蹤，證據不足
買點未成立，不可買

### 禁止輸出形狀

【05/28 盤中｜v20.0.12】
AI 題材偏多
電子供應鏈偏多

【05/28 盤中｜v20.1.0】

## 明確禁止事項

- 禁止重開 PM 需求範圍。
- 禁止改 evidence 判斷邏輯，除非 Tech 發現版本同步造成測試回退且必須阻塞說明。
- 禁止改策略 decision。
- 禁止改 DB schema / DB payload。
- 禁止 live Supabase write。
- 禁止 live Telegram delivery。
- 禁止改 watchlist。
- 禁止改 scheduler / cron。
- 禁止新增 v20.1.0 新能力。
- 禁止把本輪描述成 v20.1.0 發布。
- 禁止讓舊 market_summary 字串支撐 confirmed。
- 禁止讓缺 explicit source 的 AI / 電子供應鏈寫成 bullish confirmed 語意。
- 禁止刪除固定 8 份 Markdown。
- 禁止 Tech 修改 TASK.md。
- 禁止 QA 擴大為 full pytest、replay、backfill 或 live path 驗證，除非發現版本同步直接破壞契約。

## 阻塞條件

若出現以下任一情況，Tech 必須標記 blocked：

- 無法定位使用者可見 Telegram header 的唯一版本來源。
- 程式中存在多個互相衝突的使用者可見版本來源，且無法在 tiny patch 範圍內安全同步。
- 版本同步會迫使改動 evidence 邏輯、策略、DB、watchlist、live delivery 或 scheduler。
- formatter / notifier 測試無法在 runner 準備的環境中執行。
- 上游文件同時要求 v20.0.13 與 v20.1.0 作為同一 Telegram header 版本。
