# TASK: v20.2.4 R3 強勢偏熱時 Evidence Absent 與未持倉準備層文案修正

## 任務狀態

- task_id：v20.2.4_r3_hot_market_evidence_absent_prepare_layer
- 任務類型：normal_patch
- 任務尺寸判斷：normal_patch。主 bug 是 Telegram 報文在外部盤面強勢、R3 進攻偏熱、未持倉多檔漲停 / 過熱 / 接近突破但不可追時，把 market/theme evidence absent 寫得像「市場沒有證據」，且 summary 缺少「不可追高但列入準
備」層。此任務改使用者可見報文與 message list contract，不改策略門檻、DB、live 或 backfill，因此不是 risk_patch / major。
- 狀態：ready_for_tech
- 版本契約：升版至 v20.2.4，Telegram header / formatter 版本字串 / 測試期望必須同步。
- QA 分級建議：L2

## Owner 問題

外部盤面明顯強勢、漲停與過熱股很多時，現有報文寫 市場/題材證據 absent、無有效進場、未持倉僅追蹤，Owner 手機閱讀時容易誤讀為系統否定市場強勢，或完全不提供後續準備方向。

真正要修的是報文語意與手機閱讀層次：

- evidence absent 只能表示內部結構化市場 / 題材 evidence 未啟用、不足或未 confirmed。
- R3 進攻偏熱且未持倉有強勢但不可追標的時，summary 要補「不可追高，但列入開板 / 回測 / 降溫觸發準備」。
- 不得把漲停、過熱、接近突破股票改成可買。

## 使用者可見結果

Owner 手機打開 Telegram 後應先看到：

- 系統沒有否定外部市場強勢；只是說明內部結構化題材證據不足或未啟用。
- 新倉仍是 無有效進場 或無 BUY 時，不會被誤讀成完全沒有準備標的。
- R3 進攻偏熱情境下，未持倉 summary 會新增「強勢準備 / 回測觀察」層，清楚標示不可買、不可追高、待觸發。
- 最多列 1-3 檔，並按狀態分組，例如漲停鎖價、過熱降溫、突破回測。
- 漏斗計數仍能對上：可買 / 可準備 / 僅追蹤 / 淘汰；不可買的準備層必須標示 不可買 或 待觸發。

## 非目標

- 不放寬 BUY / 可買門檻。
- 不把漲停鎖價、過熱強勢、接近突破或已突破但不可追的股票改成買入。
- 不改 RR、過熱、冷卻、回測、量能、突破等策略 threshold。
- 不新增外部新聞 / 題材 provider。
- 不改 market/theme evidence confirmed 判斷。
- 不改 DB schema。
- 不做 live Supabase write。
- 不做 live Telegram delivery。
- 不做正式 backfill 或 replay 寫入。
- 不重排整份報文、不做全量文案清理、不改持倉停利 / 停損邏輯。

## 影響模組

- Telegram 報文 formatter / summary 組裝。
- 市場 / 題材 evidence 顯示文案。
- 未持倉 summary 的可買 / 可準備 / 僅追蹤分層。
- 未持倉漏斗與詳情分類的顯示一致性。
- 直接相關 formatter / snapshot / notifier consumer tests。

## 直接消費者

- Owner 手機 Telegram 報文。
- Telegram message list / formatter output。
- Summary 決策區。
- 未持倉漏斗。
- 未持倉詳情卡片。
- Telegram notifier / snapshot tests。
- core/generator.py 或等價版本 header 消費者。

## 已存在且不得回退的契約

- 最新使用者可見 Telegram 版本目前為 v20.2.3，本輪必須升為 v20.2.4。
- 未持倉漏斗母集合固定為：可買 / 可準備 / 僅追蹤 / 淘汰。
- 僅追蹤 再拆：等冷卻 / 等回測 / 等RR修復 / 等量能。
- 市場 / 題材 evidence 不得放寬個股買點；confirmed theme 也不能自動產生 BUY。
- 無可買時不得使用像推薦買入的文案；只能清楚標示 不可買、待觸發、僅追蹤 或 追蹤最強。
- 可買、準備、僅追蹤、不可行動 必須分開，不得混在同一行造成誤讀。
- Summary 手機優先，短句、短行、少長名單。
- 未持倉長名單最多列 1-3 檔，超過用同狀態的「另 N 檔見詳情」，不得把不同狀態混成一個 另 N 檔。
- 空區塊、0-count、無行動占位不得輸出。

## 輸出契約

- Evidence absent 文案：
- 不得再寫成「市場沒有證據」、「題材不存在」、「市場/題材證據 absent」這類會否定外部盤面的語意。
- 應改為類似：內部題材證據未啟用，仍依量價/風控判斷。
- 若內部 evidence 是 absent / unavailable / missing，文案只能描述內部結構化資料狀態，不得推論外部市場不強。
- R3 強勢準備層：
- 當 R3 進攻偏熱，且未持倉中存在漲停鎖價、過熱強勢、接近突破、已突破但不可追高股票時，summary 必須新增強勢準備 / 回測觀察層。
- 文字必須同時表達：不可追高、不可買 或 待觸發、列入開板 / 回測 / 降溫觸發準備。
- 最多列 1-3 檔。
- 必須按狀態分組，不得混成可買清單。
- 漏斗與詳情一致：
- 可買 仍只包含符合 BUY / 有效進場門檻的標的。
- 可準備 可包含待開板、待回測、待降溫、待觸發的強勢標的，但必須標示不可買 / 待觸發。
- 僅追蹤 仍保留冷卻、回測、RR、量能等不可行動追蹤原因。
- Summary、漏斗、詳情卡的分類名稱與數量必須一致。
- 手機閱讀順序：
- Summary 先回答今天能不能買。
- 接著說明強勢但不可追的準備層。
- 再列未持倉追蹤 / 淘汰，不得讓不可買標的看起來像推薦。

## 手機閱讀路徑

1. Header 顯示 v20.2.4。
2. Summary 先看到：新倉：無有效進場 或可買狀態，但不把強勢股包裝成買入。
3. Evidence 說明看到：內部題材證據未啟用，仍依量價/風控判斷，不會誤讀為市場不強。
4. 強勢準備層看到：漲停 / 過熱 / 突破附近股票被列為 不可追高、待開板 / 待回測 / 待降溫。
5. 漏斗看到：可買 / 可準備 / 僅追蹤 / 淘汰 數量與 summary、詳情一致。
6. 詳情卡看到：每檔股票狀態與 summary 分組一致，不出現 summary 說準備、詳情卻歸到可買或相反情況。

## 驗收條件

- Evidence absent 不誤導：
- 在 market/theme evidence 為 absent / unavailable / missing 的 fixture 中，Telegram 不得出現會被解讀為外部市場沒有證據或題材不存在的文案。
- 必須出現類似 內部題材證據未啟用，仍依量價/風控判斷 的限定語。
- R3 強勢準備層出現：
- 在 05/29 類似盤面 fixture 中，R3 進攻偏熱且未持倉有漲停鎖價、過熱強勢、接近 / 已突破但不可追標的時，summary 必須出現強勢準備 / 回測觀察層。
- 不可追高仍不可買：
- 漲停鎖價、過熱強勢、接近 / 已突破但不可追標的不得被放入 可買 或輸出買入建議。
- 文案必須包含 不可追高、不可買 或 待觸發。
- 計數一致：
- Summary、漏斗、詳情卡的 可買 / 可準備 / 僅追蹤 / 淘汰 計數一致。
- 準備層股票不得同時被 summary 當準備、漏斗當僅追蹤、詳情當可買。
- 手機閱讀：
- Owner 連續閱讀 Telegram 報文時，能清楚分辨「今天不可買」與「後續開板 / 回測 / 降溫可準備」。
- 版本檢查：
- 實際 formatter output header 必須顯示 v20.2.4。
- 策略不變性：
- 無策略 threshold diff。
- 無 DB schema diff。
- 無 live write / live Telegram / backfill diff。
- 無 watchlist、持倉停利、停損、execution dedupe 回退。

## 範例或 fixture

### Fixture：05/29 類似 R3 強勢偏熱盤面

條件形狀：

- R3 進攻偏熱。
- market/theme structured evidence：absent 或 unavailable。
- 未持倉：
- A：漲停鎖價，量價強，但不可追。
- B：過熱強勢，已突破但需降溫。
- C：接近突破，需回測或觸發。
- D/E：僅追蹤或淘汰。
- 無符合 BUY / 有效進場股票。

期望輸出形狀：

v20.2.4

新倉：無有效進場

市場/題材：
內部題材證據未啟用，仍依量價/風控判斷。

強勢準備：
- 漲停鎖價：A 不可追高，待開板回測
- 過熱降溫：B 不可買，待降溫後重評
- 突破回測：C 待觸發，不追高

未持倉漏斗：
可買 0｜可準備 3｜僅追蹤 1｜淘汰 1

詳情卡期望形狀：

A
狀態：可準備 / 漲停鎖價
行動：不可追高，待開板回測

B
狀態：可準備 / 過熱強勢
行動：不可買，待降溫後重評

C
狀態：可準備 / 接近突破
行動：待觸發，不追高

禁止輸出形狀：

市場/題材證據 absent，所以無有效進場

強勢股：A、B、C 可買

新倉：無有效進場
未持倉僅追蹤：A、B、C

## 明確禁止事項

- 不得把 evidence absent 寫成外部市場沒有證據、題材不存在或系統否定強勢。
- 不得放寬 BUY / 可買門檻。
- 不得把漲停鎖價、過熱強勢、接近突破、已突破但不可追的股票轉為買入。
- 不得把不可買準備層混入可買清單。
- 不得讓 summary、漏斗、詳情分類名稱或數量互相矛盾。
- 不得輸出空區塊、0-count、無行動占位。
- 不得改策略 threshold、RR、過熱、漲停不追、watchlist。
- 不得改 DB schema、live write、Telegram live、backfill。
- 不得回退 v20.2.1 突破距離顯示契約。
- 不得回退 v20.2.2 / v20.2.3 持倉停利 execution 去重契約。
- 不得回退市場 / 題材 evidence 不放寬買點的契約。

## 本輪停止條件

- 完成 05/29 類似 fixture 驗證：
- evidence absent 文案不誤導。
- R3 強勢準備層出現。
- 不可追高標的仍不可買。
- summary / 漏斗 / 詳情計數一致。
- header 為 v20.2.4。
- 完成 formatter / snapshot / notifier 直接 consumer smoke。
- 完成策略不變性檢查，確認無 threshold、DB、live、backfill、watchlist diff。
- 若發現需要真實外部新聞、題材 provider、DB evidence schema、正式 backfill 或策略閾值調整，停止本輪並記待辦，不納入 v20.2.4。
- 若發現其他非 R3 / 非 evidence absent 的報文噪音，除非阻塞上述驗收，只記待辦，不擴大本輪。

## 旁支問題處理

- 若 QA 發現強勢準備層文字仍偏長，可在本輪內只收斂 summary 的 1-3 檔手機閱讀文案。
- 若發現未持倉分類底層資料本身沒有 可準備 狀態，只允許在 formatter 層把既有不可買原因映射為可準備顯示，不得改策略 decision。
- 若需要新增正式 market/theme evidence provider、DB schema 或外部資料接入，另開研究 / major 任務。
- 若需要重新設計整份未持倉漏斗，另開 normal_patch 或 minor 任務。

## 阻塞條件

- 若現有資料無法判斷 R3 進攻偏熱，且無法建立可驗收 fixture，Tech 必須 blocked，要求 Architect 補充可用欄位或 fixture。
- 若現有未持倉結果無法區分漲停鎖價、過熱強勢、接近 / 已突破但不可追，且不能在 formatter 層以既有欄位映射，Tech 必須 blocked。
- 若 可準備 是否可容納「不可買但待觸發」與既有契約矛盾，Tech / QA 必須 blocked，要求 Architect/Owner 補充。
- 若修正必須改策略 threshold、DB schema、正式 backfill 或 live provider，停止本輪並回報超出 v20.2.4 normal_patch 範圍。
- 若 formatter header 版本來源不明，必須 blocked，要求 Architect 指定版本常量位置。
