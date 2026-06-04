# TASK: Phase A 盤後未持倉普通 BUY 改為可準備不可買

## 任務狀態

- task_id: phase_a_after_close_unheld_buy_prepare_v20_4_39
- 任務類型: normal_patch
- 狀態: ready_for_tech
- 版本建議: 使用者可見報文版本需由 v20.4.38 升至 v20.4.39
- QA 分級建議: L2
- 主 bug: 盤後未持倉普通 BUY / 明日追蹤候選在 summary、漏斗、卡片被寫成「可買 / 新倉建議 / 新增有效進場 / 40%倉 / 買點成立」，手機閱讀時容易誤讀成已可下單或明日必買。

## Owner 問題

Owner 要先試行 Phase A 條件性放寬 / 分層，不是全域放寬。

2026-06-04 盤後 v20.4.38 報文中，未持倉光寶科仍需「明日開盤後確認」，但多個使用者可見區塊呈現為可執行買進：

- 卡片顯示：🟢 明日追蹤｜40%倉｜買點成立
- 卡片買點顯示：買點：盤後追蹤｜開盤後確認｜不追價
- summary 顯示：新倉建議 1
- summary 顯示：新增有效進場 1 檔需明日開盤前確認
- summary 顯示：光寶科 可買（分批，不追價）｜尚未買入｜建議分批｜明日開盤後確認

問題不是 RR 或策略分數錯，而是「盤後未持倉普通 BUY / 明日追蹤候選」的使用者可見語氣與分組錯誤。

## 使用者可見結果

手機閱讀盤後報文時，未持倉且仍需明日開盤後確認的普通 BUY / 明日追蹤候選，必須被歸為「可準備、不可買」或等價明確不可執行語氣。

光寶科這類卡片仍可保留 RR、技術條件、回測摘要與觀察理由，但不得讓使用者在 summary、漏斗或卡片第一眼讀成已可下單。

示例輸出形狀：

Summary:
新倉：無有效進場
可準備：1 檔需明日開盤後確認，未確認前不可下單
光寶科 可準備（不可買）｜尚未買入｜明日開盤後確認｜不追價

未持倉卡片:
🟡 明日準備｜不可買｜開盤後確認
光寶科
買點：尚未成立｜盤後僅追蹤｜明日開盤後確認｜不追價
RR / 技術 / 回測資訊照常顯示

實際文案可依現有報文風格調整，但語意必須同時滿足：

- 不是新倉建議。
- 不是新增有效進場。
- 不是可買。
- 不顯示 40%倉。
- 不顯示 買點成立。
- 明確指出未經明日開盤後確認前不可下單。

## 非目標

- 不改 RR 公式。
- 不改策略核心買賣判斷。
- 不改 trend_continuation 小倉 BUY 的可買路徑。
- 不改盤中有效 BUY 的可買路徑。
- 不改 DB schema、RLS、grant、policy、role、index、constraint。
- 不新增或修改 production write path。
- 不做 live Telegram delivery。
- 不重設整體推薦分組規則。
- 不做全量報文清理或策略重構。

## 影響模組與直接消費者

影響模組由 Tech 依現有 repo 定位，但範圍限於 official generator / message-list / formatter 中「盤後未持倉普通 BUY / 明日追蹤候選」的使用者可見分類與文案。

直接消費者：

- Telegram 盤後報文手機閱讀者。
- official generator 產出的 message list。
- summary / 漏斗 / 未持倉卡片三個報文區塊。
- 既有測試或 replay artifact 中覆蓋報文生成的 consumer。

## 輸出契約

單一輸出契約：盤後未持倉普通 BUY / 明日追蹤候選，在尚需明日開盤後確認時，必須在 summary、漏斗、卡片三層一致呈現為「可準備不可買」。

必須排除的既有可見詞：

- 新倉建議
- 新增有效進場
- 可買
- 40%倉
- 買點成立

必須保留的資訊類型：

- RR / 風報比資訊。
- 技術條件資訊。
- 回測資訊。
- 明日開盤後確認 / 不追價提醒。

已存在且不得回退的契約：

- 真正 trend_continuation 小倉 BUY 仍可保留既有小倉 BUY / 可買路徑。
- 盤中有效 BUY 仍可保留既有可買路徑。
- 無可買時 summary 不得使用像推薦的文案，應呈現 新倉：無有效進場 或等價不可買表述。
- 同一標的在同一份報文的 summary、漏斗、卡片狀態必須一致。
- 使用者可見報文版本需同步顯示 v20.4.39，不得停留在 v20.4.38。

若 Tech 無法從現有 payload 判斷普通 BUY、trend_continuation BUY、盤中有效 BUY、盤後明日追蹤候選的差異，需 blocked，不得用全域 BUY 降級替代。

## 版本契約

- 報文 header / 版本常量 / 使用者可見版本需升至 v20.4.39。
- 不得只改測試期待值而漏改實際報文版本。
- 不得把 v20.4.39 套用成策略核心版本變更；本輪只代表報文分類與語氣修正。

## 驗收條件

1. 使用 2026-06-04 盤後 v20.4.38 光寶科 failure specimen，透過 official generator/message-list 或等價 replay artifact 驗證：
- summary 不再出現 新倉建議 1 指向光寶科。
- summary 不再出現 新增有效進場 1 檔需明日開盤前確認 指向光寶科。
- summary 不再出現 光寶科 可買（分批，不追價）。
- 光寶科卡片不再出現 40%倉、買點成立。
- 光寶科被呈現為可準備 / 明日追蹤 / 不可買 / 開盤後確認的等價語氣。
- RR、技術、回測資訊仍保留。
2. 補一個保護案例驗證不得全域放寬：
- 真正 trend_continuation 小倉 BUY 或盤中有效 BUY 仍可進入既有可買路徑。
- 不得因本輪修正被降成「可準備不可買」。
3. 手機閱讀路徑驗收：
- 只看 summary 第一屏，不會讀到光寶科是今日可買或明日必買。
- 只看卡片標題與買點行，不會讀到 40%倉、買點成立 或可立即下單。
- summary、漏斗、卡片對光寶科的狀態一致。

## 範例或 Fixture

Failure specimen 來源：2026-06-04 盤後 v20.4.38 報文，未持倉光寶科。

需保留的關鍵摘錄：

🟢 明日追蹤｜40%倉｜買點成立
買點：盤後追蹤｜開盤後確認｜不追價
新倉建議 1
新增有效進場 1 檔需明日開盤前確認
光寶科 可買（分批，不追價）｜尚未買入｜建議分批｜明日開盤後確認

期望等價輸出形狀：

新倉：無有效進場
可準備：1 檔需明日開盤後確認，未確認前不可下單
光寶科 可準備（不可買）｜尚未買入｜明日開盤後確認｜不追價

🟡 明日準備｜不可買｜開盤後確認
買點：尚未成立｜盤後僅追蹤｜明日開盤後確認｜不追價

## 失敗標本與驗收路由

失敗層級：使用者可見 official report/message-list，不是單一 helper fixture。

驗收路由優先順序：

1. official generator 以 2026-06-04 盤後等價 payload/replay artifact 產出 message list。
2. 若不能取得完整 official replay，Tech 必須產出等價 replay artifact，包含足以重現 summary、漏斗、未持倉光寶科卡片的 payload 欄位。
3. 若只能測 helper 或局部 formatter，CHANGELOG 必須標記 partial，QA 結論不得直接通過。

## 明確禁止事項

- 禁止全域放寬 BUY 或把所有 BUY 都降成可準備。
- 禁止改 RR 公式。
- 禁止改策略核心買賣判斷。
- 禁止改 DB schema/write path。
- 禁止 live Telegram。
- 禁止用 synthetic helper fixture 取代 Owner failure specimen 後宣稱完成。
- 禁止只改卡片但 summary / 漏斗仍顯示可買。
- 禁止只改 summary 但卡片仍顯示 40%倉 或 買點成立。
- 禁止回退 trend_continuation 小倉 BUY 與盤中有效 BUY 的既有可買路徑。
- 禁止把本輪擴成策略重設、全量清理或 L3 大驗證。

## 阻塞條件

- 找不到或無法重建 2026-06-04 盤後 v20.4.38 光寶科等價 replay artifact。
- 現有 payload 無法區分盤後普通 BUY / 明日追蹤候選與真正 trend_continuation 小倉 BUY、盤中有效 BUY。
- official generator/message-list 路徑無法執行，且沒有可接受的等價 replay artifact。
- 報文版本來源不明，無法確認 v20.4.39 實際會顯示在使用者可見報文。
- 需要 DB schema/write 或 live Telegram 才能完成時，本輪 blocked。

## 本輪停止條件

完成條件：

- 2026-06-04 盤後光寶科 failure specimen 在 official generator/message-list 或等價 replay 中，summary、漏斗、卡片一致改為可準備不可買。
- 新倉建議 / 新增有效進場 / 可買 / 40%倉 / 買點成立 不再套用到該盤後未持倉普通 BUY 候選。
- RR、技術、回測資訊保留。
- trend_continuation 小倉 BUY 或盤中有效 BUY 保護案例未回退。
- 使用者可見版本為 v20.4.39。

旁支問題只記待辦，不納入本輪：

- 其他標的的策略門檻重新設計。
- RR / 回測模型調整。
- DB 持久化或跨日狀態補強。
- Telegram 全報文版面整理。
- Phase B / Phase C 條件放寬策略。
