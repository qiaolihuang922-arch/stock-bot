# QA_REPORT: telegram_mobile_readability_consolidation_20260626

## 測試範圍

- Future-watch final message。
- Institutional trading display。
- Afterhours summary。
- 今日買入說明。
- 盤後持倉風控 checklist。

## 關聯風險掃描

- 風險: 隱藏 MOPS source-error 會漏掉資料來源問題。
  - 反證: source-error 對手機決策沒有幫助；文件保留 runner/source 風險，報文不顯示未確認事件。
- 風險: 財報壓成兩行會少資訊。
  - 反證: EPS、營收、法人判讀都保留，只移除多餘換行。
- 風險: 持倉 summary 股數計算錯。
  - 反證: STOP_100 用持股數；REDUCE_50/25 有 fallback regression。

## 跨區塊語意一致性

- Summary 的 `明日優先` 與持倉風控檢查同口徑。
- Future-watch 不再顯示已移除的 history/global sections。
- 未持倉沒有可買時仍是等觸發，不升格成推薦。

## 使用者誤讀風險

- 已降低：MOPS 錯誤不再佔第一眼。
- 已降低：財報區滑動量減少。
- 已降低：法人數字有偏買/偏賣判讀。
- 已降低：盤後 summary 直接列明日賣多少股。

## 失敗標本反證

- Owner afterhours specimen 的可見問題已反證：
  - MOPS source-error hidden。
  - 財報每檔兩行。
  - 法人行有偏買/偏賣。
  - Summary 新增明日優先。
  - 今日買入長句縮短。

## 質疑與反證

- 質疑: 是否只改 helper？
  - 反證: focused tests hit `formatTelegramMessages`、`formatTelegramPositionCard`、`format_future_watch_message`。
- 質疑: 是否改策略？
  - 反證: 本輪只改 formatter / fallback display shares；無 DB/write/source/strategy changes。

## 未測項目

- 未發 live Telegram。
- 未寫 production DB。
- 未跑 full suite；已知 full `tests/test_generator_report.py` 仍有舊文案預期清理項。

## QA 結論

通過。
