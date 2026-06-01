# TASK: v20.4.14 第三則 Telegram 證據入口去重

## 任務狀態

- task_id：telegram-evidence-entry-dedupe-v20.4.14
- 任務類型：tiny_patch
- 狀態：QA 通過，待 git 收口
- 版本建議：v20.4.14
- QA 分級建議：L1
- 本輪主 bug：第三則 Telegram 同時出現兩個證據說明入口，造成手機閱讀重複與割裂。

## Owner 問題

Owner 指出 v20.4.13 第三則 Telegram 仍同時顯示：

- 📊 策略證據 v20.0 / 策略樣本不可用 / missing-source
- v20.4.13 簡短證據摘要

兩段語意重複，手機閱讀像拆成兩個片段。第三則只能保留一個證據說明入口；missing-source 必須仍 fail-closed，但不能再額外輸出完整策略證據長段。

## 使用者可見結果

第三則 Telegram 手機閱讀時，只看到一個證據入口：

- 保留或升版後顯示 v20.4.14 簡短證據摘要 作為唯一證據入口。
- 策略樣本不可用 / missing-source 若存在，需合併在簡短證據摘要內，或壓成一行短句。
- 不再另外出現完整長段 📊 策略證據 v20.0。

## 非目標

- 不改策略 decision。
- 不改買賣、加減碼、停損停利判斷。
- 不改 DB schema、RLS、grant、policy、role、index、constraint。
- 不改 DB write path。
- 不做 live Telegram delivery。
- 不重構整份 Telegram 報文。
- 不清理全量證據模組。
- 不調整第一則、第二則 Telegram 的產品語意，除非它們共享同一版本字串常量且必須同步升版。

## 影響模組

Tech 需在 repo 內定位實際第三則 Telegram 報文組裝位置與版本字串來源；PM 不指定檔名。

預期影響範圍限於：

- 第三則 Telegram 報文的證據區塊組裝 / formatter。
- 使用者可見版本字串：v20.4.13 -> v20.4.14。
- 對應的最小測試或 fixture。

## 直接消費者

- Owner 在手機 Telegram 讀第三則報文。
- Telegram 報文產生 runner / dry-run 輸出。
- 既有測試 fixture 或 snapshot 消費者，如 repo 已存在。

## 已存在且不得回退的契約

- 第三則仍需提供證據說明，不可完全刪除 evidence 訊息。
- missing-source 必須 fail-closed，不可改寫成有資料、可交易、可買、通過或推測性證據。
- 無策略樣本時，不得偽造策略樣本、勝率、回測或可信來源。
- 使用者可見版本不得停留在 v20.4.13；本輪應升為 v20.4.14。
- 報文仍需維持手機可讀：短句、單一入口、避免重複長段。
- live delivery 需 Owner 另行批准，本輪不得發送正式 Telegram。

## 輸出契約

單一輸出契約：第三則 Telegram 的證據入口只允許一個。

當策略樣本缺失時，第三則報文應符合：

- 不包含獨立長段標題：📊 策略證據 v20.0
- 包含一個簡短證據入口，例如：v20.4.14 簡短證據摘要
- missing-source 出現在該簡短摘要內，或被壓成一句短提示。
- 語意保持 fail-closed：明確表示策略樣本不可用或來源缺失，不得導向可行動建議。

禁止同時存在兩個入口：

- 📊 策略證據 v20.0
- 簡短證據摘要

## 手機閱讀路徑

Owner 從 Telegram 手機端打開第三則報文，應能在一次滑動內看到：

1. 第三則的主要決策 / 分組內容。
2. 單一證據入口。
3. 若策略樣本缺失，只看到一行或摘要內提示 missing-source，不再看到另一個完整策略證據長段。

## 範例或 fixture

### 修正前，不合格形狀

📊 策略證據 v20.0
策略樣本不可用
missing-source

v20.4.13 簡短證據摘要
...

### 修正後，合格形狀

v20.4.14 簡短證據摘要
策略樣本：missing-source，樣本不可用，維持 fail-closed。
...

或等價短句：

v20.4.14 簡短證據摘要
策略樣本不可用（missing-source）；不產生策略證據推論。
...

## 驗收條件

1. 在能重現 v20.4.13 問題的第三則 Telegram dry-run / fixture / test output 中，修正後不得同時包含 📊 策略證據 v20.0 與 簡短證據摘要 兩個證據入口。
2. 策略樣本缺失案例中，missing-source 仍保留 fail-closed 語意，不得被改成可用資料、推薦、可買、通過或推測性證據。
3. 使用者可見版本顯示為 v20.4.14，且不得回退 v20.4.13。
4. 本輪只驗第三則證據入口去重與 missing-source 語意；其他報文排序、策略內容、DB 行為若發現旁支問題，記入待辦，不納入本輪修正。

## 明確禁止事項

- 禁止改策略 decision。
- 禁止改 DB schema / write path。
- 禁止 live Telegram delivery。
- 禁止為了通過測試刪掉 missing-source。
- 禁止偽造策略樣本、回測數據或資料來源。
- 禁止把任務擴成全量報文重構、策略重設或清理工程。
- 禁止跳過 Tech / QA；PM 只定義任務卡。

## 阻塞條件

若 Tech 無法定位第三則 Telegram 的產生路徑、無法產出 dry-run / fixture、或無法確認哪個版本字串是使用者可見版本，需 blocked 並回報缺口，不得用猜測修改。

若修正需要碰 DB schema/write、策略 decision、live Telegram，需 blocked 並回 Architect / Owner 確認，不得在本輪擴權。

## 本輪停止條件

完成條件只限於：

- 第三則 Telegram 證據入口去重。
- missing-source 合併進簡短證據摘要或壓成一句。
- 版本升 v20.4.14。
- 最小可重跑驗收證明第三則不再雙入口，且 missing-source 仍 fail-closed。

以下旁支不納入本輪：

- 其他 Telegram 則數的版面優化。
- 全量 evidence formatter 清理。
- 策略樣本來源修復。
- DB 持久化或 production data backfill。
- live 發送驗證。
