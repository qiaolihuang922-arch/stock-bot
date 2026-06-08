# QA_REPORT: report_conflict_future_watch_format_20260608

## 測試範圍
- focused pytest:
  - `test_afterhours_cards_are_denoised_without_first_read_preface`
  - `test_v20_4_47_future_30d_watch_optional_fourth_message_official_list`
  - `test_v20_4_12_complete_message_list_orders_holdings_unheld_summary_evidence_details`
  - `tests/test_notifier.py`
- `py_compile` for changed report/future-watch/test modules。
- official `generate_report(dry_run=True)` replay。

## 關聯風險掃描
- Summary 文案只改使用者可見文字，不改交易狀態計數。
- 未持倉 blocker 排序只影響顯示主因，不改漏斗結果。
- 法說會財報拆行只改 formatter，不改 MOPS / fundamentals query/filter。

## 跨區塊語意一致性
- 第 3 則 Summary 現在用 `今日買入紀錄`，與 `新增有效進場：無` 不再互相誤導。
- 第 2 則量能不足卡：title `量能不足`，主因 `量能不足`。
- 第 4 則法說會：財報子行緊跟該檔法說會，未獨立成全市場清單。

## 使用者誤讀風險
- `今日買入紀錄` 明確是已發生交易/ledger，不等於現在可買。
- `財報：` 子行縮排，手機上可讀成上一行法說會的附屬資料。

## 失敗標本反證
- Owner 樣本 v20.4.49：
  - `今日已買` vs `新增有效進場：無` 改為 `今日買入紀錄`。
  - `淘汰｜量能不足` vs `卡關主因：樣本不足` 改為量能主因。
  - 法說會單行財報改為子行。
- official dry-run v20.4.50 confirmed。

## 未測項目
- live Telegram delivery 未測且禁止。
- Production runner delivery artifact 未跑；本輪驗收為 local official dry-run。

## QA 結論
通過
