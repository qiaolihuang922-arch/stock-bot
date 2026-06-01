# TASK: v20.4.21 報文剩餘手機閱讀修正

## 任務狀態

- task_id: report_v20_4_21_mobile_readability_remaining_fixes
- 任務類型: normal_patch
- 狀態: qa_passed_pending_git_close
- 版本建議: 不回退，維持 `v20.4.21`
- QA 分級建議: L2

## Owner 問題

目前 v20.4.21 報文仍有手機閱讀誤讀與跨區塊衝突：

1. 近 3 個交易證據日容易被理解成策略證據或策略勝率，實際只能稱為短期背景 / 短期市場溫度。
2. 非加碼持倉 RR 顯示不一致；建準這類非加碼持倉不得顯示 RR 2.73。
3. 盤後下一步仍像盤中文案，應改為明日語境。
4. 未持倉卡片重複長資料來源句，手機閱讀噪音過高。
5. 第三則資料依據需要人話化：持倉與價格可支持風控；未持倉只支持分類觀察，不支持直接進場。

## 使用者可見結果

- 三日資料只被描述為短期背景或短期市場溫度，不出現策略證據 / 策略勝率 / 勝率證據等暗示。
- 非加碼持倉卡片顯示新倉 RR 不適用，不顯示具體新倉 RR 數字。
- 盤後下一步使用明日語境，例如明日觀察是否守住警戒。
- 未持倉卡片不再每張重複長資料來源句；資料來源說明集中放到第三則。
- 第三則用白話說明資料能支持什麼、不能支持什麼。

## 非目標

- 不改策略邏輯、選股規則、RR 計算公式或進出場決策。
- 不變更 DB schema、RLS、grant、policy、role、index、constraint。
- 不做 DB write、backfill、production DML 或 live Telegram delivery。
- 不修復本輪五項以外的文案偏好、排序、策略分數或資料完整性問題。
- 不把三日短期背景升格為策略驗證、勝率統計或回測結論。

## 影響模組

- `presentation/report.py`
- `tests/test_generator_report.py`
- `tests/test_market_theme_evidence.py`
- 固定 handoff Markdown

不得改動策略核心、DB 寫入路徑、交易狀態機或 live delivery runner。

## 直接消費者

- Owner 手機閱讀 Telegram 報文。
- Telegram message list / report renderer。
- v20.4.x 報文 fixture / probe。
- QA 驗收流程。

## 輸出契約

### 三日短期背景命名

使用者可見文案中，近 3 個交易日相關段落只能使用短期背景語意。

允許：

- 近 3 個交易日短期背景
- 短期市場溫度
- 短期背景資料

禁止：

- 策略證據
- 策略勝率
- 勝率證據
- 任何讓使用者以為三日資料可證明策略有效或可直接進場的文字。

### 非加碼持倉 RR

- 非加碼持倉不得顯示具體新倉 RR 數字。
- 非加碼持倉 RR 欄位顯示為新倉 RR 不適用或等價短句。
- 加碼候選可沿用既有加碼 RR 顯示契約。

### 盤後下一步

盤後報文的下一步文案需改為明日語境，例如：

- 明日觀察是否守住警戒
- 明日確認是否修復

### 卡片資料來源降噪

- 未持倉卡片不得每張重複長資料來源句。
- 資料來源說明集中到第三則資料依據。

### 第三則資料依據人話化

第三則需同時表達：

- 持倉與價格可支持風控。
- 未持倉只支持分類觀察。
- 未持倉不支持直接進場。

## 驗收條件

- 可重跑手機閱讀 probe 覆蓋三日短期背景命名、非加碼 RR、盤後下一步、卡片資料說明降噪與第三則人話化。
- `tests/test_generator_report.py` 通過。
- `tests/test_market_theme_evidence.py` 通過。
- QA 補一個 source-error 或等價負面路徑，確認策略樣本狀態不混用且手機順序無誤讀。
- 不做 DB write、live Telegram、DB schema。

## 明確禁止事項

- 禁止 DB write。
- 禁止 live Telegram delivery。
- 禁止 DB schema / RLS / grant / policy / role / index / constraint 變更。
- 禁止改策略核心買賣判斷。
- 禁止只改文件不補可重跑 probe。

## 本輪停止條件

完成以上五項使用者可見修正與可重跑驗證後停止；其他文案偏好、reply markup、2356 ledger 稽核另開任務。
