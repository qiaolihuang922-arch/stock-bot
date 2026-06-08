# QA_REPORT: telegram_denoise_and_deployment_docs_20260608

## 測試範圍
- focused pytest:
  - `test_afterhours_cards_are_denoised_without_first_read_preface`
  - `test_v20_4_12_complete_message_list_orders_holdings_unheld_summary_evidence_details`
  - `tests/test_notifier.py`
- official dry-run: `generate_report(dry_run=True)`。
- 部署文檔人工核對：Windows + WSL path、已遇到的 runner 問題、安全邊界。

## 關聯風險掃描
- message order 未重排，降低 notifier reply markup 風險。
- 盤後降噪限定在顯示層，不改策略/決策資料。
- 部署文檔更新不改 live delivery / DB policy。

## 跨區塊語意一致性
- 第 1 則不再出現 `【先看結論】`。
- 第 1 則持倉仍保留每檔主行動、風控線、決策、原因、下一步、價格。
- 第 2 則未持倉淘汰仍明確是 `不可買` / `淘汰`，不會被讀成買入清單。
- 第 3 則 Summary 仍保留完整決策簡報。

## 使用者誤讀風險
- 降噪不能刪掉每檔主行動。
- 不把「每檔重複」本身視為錯；只刪審計型流水與低價值診斷欄位。

## 失敗標本反證
- Owner 樣本：v20.4.48 報文中 `【先看結論】` 無效，持倉/未持倉卡片過長。
- official dry-run replay:
  - 產生 4 則 `v20.4.49` 報文。
  - 第 1 則持倉無 `【先看結論】`、無 `條件` / `數據`。
  - 第 2 則未持倉淘汰無 `盤面` / 長 `原因` / `數據`。

## 未測項目
- live Telegram delivery 未測且禁止。
- CAO runner e2e 未測，因 TUI automation gap。

## QA 結論
通過
