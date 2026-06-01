# QA_REPORT:

## 測試範圍

- 任務：`telegram_card_source_humanize_v20_4_16`
- 任務尺寸 / QA：`normal_patch / L2`
- 驗證範圍：Telegram 三則 sample 結構、第一則持倉卡資料行、第二則未持倉卡資料行、持倉新倉 RR 顯示、版本字串與缺資料 fail-closed。
- 未做 full pytest、replay、backfill、production read/write 或 live Telegram。

## 風險預算與停止條件

1. `TASK.md / CHANGELOG.md / diff` 再次不一致。
   - 驗證：逐項比對版本、修改範圍、禁止事項、測試聲明。
   - 停止條件：任一文件聲稱與 diff 不符即 blocked。
2. 手機閱讀仍看到 raw Source/status dump 或持倉 RR 數字。
   - 驗證：完整三則 Telegram sample，按 messages[0] 持倉、messages[1] 未持倉、messages[2] summary/evidence 順序檢查。
   - 停止條件：第一則 / 第二則出現 raw `Source：... available/derived` 或持倉非加碼顯示 `RR 2.33` 類數字即 blocked。
3. 缺資料但仍給可買 / 推薦 / 準備進場語氣。
   - 驗證：Tech 覆蓋缺 OHLCV；QA 另補缺 price 且 decision=BUY 的反證 probe。
   - 停止條件：缺 price/OHLCV 任一仍出現可買、推薦、準備進場、建議倉位即 blocked。

## 關聯風險掃描

- `TASK.md / CHANGELOG.md / diff` 一致：本輪只改 Telegram formatter、人話資料行、持倉 RR 顯示、版本 `v20.4.16` 與測試。
- `core/generator.py` diff 未觸及 strategy decision、RR/score/volume 公式、DB schema/write、backfill、live Telegram delivery。
- `git diff --check`：passed。
- `py_compile core/generator.py services/notifier.py`：passed。
- Scoped L2 tests：
  - `tests/test_generator_report.py tests/test_market_theme_evidence.py`：117 passed，169 warnings。
  - `tests/test_notifier.py`：3 passed。

## 跨區塊語意一致性

- 完整三則 Telegram QA sample 驗證通過：message count = 3，三則皆顯示 `【06/01 盤中｜v20.4.16】`。
- 第一則持倉卡：
  - 有 `資料：持倉與現價已確認；風控由持倉成本/停損推算`
  - 有 `數據：新倉 RR：持倉不適用｜...`
  - 無 raw `Source：position available｜price available｜risk derived｜RR derived`
  - 無 `RR 2.33 / 數據：RR 2.33`
- 第二則未持倉卡：
  - 有 `資料：現價與 OHLCV 已確認；RR/分數/量能為模型推算`
  - 無 raw `Source：price available｜OHLCV available｜RR derived｜score derived｜volume derived`
- Summary / evidence 維持第三則，未回退到舊版本字串。

## 使用者誤讀風險

- 持倉卡不再把新倉 RR 數字放在持倉判斷旁，手機閱讀不會把 `RR 2.33` 誤讀成持倉續抱依據。
- 未持倉資料完整時，人話資料行明確分出「現價與 OHLCV 已確認」與「RR/分數/量能為模型推算」。
- 缺 price 反證中，即使輸入策略結果是 BUY，輸出仍為 `資料：缺現價，停止新倉判斷`，summary 為 `新倉：無有效進場`，未出現可買 / 建議倉位 / 推薦 / 準備進場語氣。
- 缺 OHLCV 已由新增測試覆蓋，輸出 `資料：缺OHLCV，停止新倉判斷` 並不可行動。

## 質疑與反證

- 主動質疑：若 formatter 只換完整資料路徑，缺 price 但 strategy result 仍為 BUY 時可能沿用可買文案。
  - 反證：QA inline probe 通過；缺 price 情境完整三則 sample 仍 fail-closed，沒有可買或推薦語氣。
- 主動質疑：CHANGELOG 先前 mismatch 是否仍存在。
  - 反證：目前 `CHANGELOG.md` 已改為 `v20.4.16` 與第一/第二則卡片修正，和 TASK / diff 對齊。

## 未測項目

- 未跑 full pytest，符合 `normal_patch / L2` scoped 驗證。
- 未做 production DB read/write、replay、backfill。
- 未做 live Telegram delivery。
- 第三則 evidence 仍保留部分 source/status 語彙；TASK 明確限定本輪修第一則持倉卡與第二則未持倉卡，列後續風險不阻塞本輪。

## QA 結論

通過
