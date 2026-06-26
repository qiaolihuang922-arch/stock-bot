# QA_REPORT: future_watch_institutional_mobile_compact_20260626

## 測試範圍

- Future-watch institutional trading display line。
- 手機短格式 regression。
- 既有 institutional source / future-watch focused regression。

## 關聯風險掃描

- 風險: 移除日期後可能看不出時間口徑。
  - 反證: 前綴保留 `昨日`，符合 Owner 要求。
- 風險: 四捨五入造成資訊略少。
  - 反證: 單位是張，手機決策只需方向與量級；完整 source 不變。
- 風險: 短標籤不清楚。
  - 反證: 同一行固定順序 `外/投/自/合`，並位於 `三大法人` 欄位下。

## 跨區塊語意一致性

- 股票卡片仍不顯示三大法人行。
- Future-watch 財報區保留法人資訊，但更短。
- 缺資料仍 fail closed，不輸出 0。

## 使用者誤讀風險

- 已降低：日期不再每檔重複。
- 已降低：每個分項不再重複 `張`。
- 已降低：小數不再干擾掃讀。

## 失敗標本反證

- Owner specimen 的長句已改為：
  - `昨日三大法人：外+2,736｜投-102｜自-480｜合+2,153張`
- Regression 反證不含：
  - `昨日三大法人買賣超 20260625`
  - `2,735.61張`

## 質疑與反證

- 質疑: 是否改到 source 數值？
  - 反證: 本輪只改 formatter；source regression 仍通過。
- 質疑: 是否破壞資料源修復？
  - 反證: focused suite `9 passed, 229 deselected`。

## 未測項目

- 未發 live Telegram。
- 未寫 production DB。
- 未跑 full suite；已知 full `tests/test_generator_report.py` 仍有舊文案預期清理項。

## QA 結論

通過。
