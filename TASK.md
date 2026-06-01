# TASK: Telegram 第三則改為單一「簡報＋資料依據」結構 v20.4.15

## 任務狀態

- task_id: telegram-brief-data-evidence-v20.4.15
- 任務類型: normal_patch
- 狀態: QA 通過，待 git 收口
- 版本建議: 使用者可見 Telegram 報文版本升至 v20.4.15
- QA 分級建議: L2
- 主 bug: 第三則 short/evidence 雖已去重，但閱讀上仍像多個 evidence/status 片段拼接，Owner 在手機上難以理解它是「簡報＋資料」。

## Owner 問題

Owner 指出 v20.4.14 第三則雖已去掉重複 evidence entry，但 market/theme、strategy sample、持倉/候選 source、漏斗/風險仍各自分散呈現，整體不像一份可快速閱讀的決策簡報，也不像集中資料依據。

本輪要把 Telegram 第三則 short/evidence 收斂成單一「簡報＋資料依據」結構：先給統一決策簡報，再給一段集中資料依據，說清楚 market/theme production、strategy sample、持倉/候選 source-of-truth 的資料庫/持久來源狀態與限制。

## 使用者可見結果

完整 Telegram 仍是三則主訊息：

- 第一則: 持倉卡片，不改。
- 第二則: 未持倉/候選卡片，不改。
- 第三則: 改為單一「簡報＋資料依據」訊息。

第三則手機閱讀路徑：

- 使用者打開第三則時，先看到一個統一決策簡報區塊。
- 接著只看到一個資料依據區塊。
- 不再看到分裂入口，例如「簡短證據摘要」「策略證據」「來源狀態」「漏斗證據」「風險證據」各自成段。
- market/theme confirmed 只可作背景脈絡，不得被包裝成買點或可買理由。
- 策略樣本缺 source 時仍必須 fail-closed，不得寫成樣本不足但可參考、可準備或推薦。

## 非目標

- 不改第一則、第二則卡片內容、排序、分類、行動文案。
- 不改策略 decision、BUY/SELL/加減碼/續抱/觀察/停利/停損判斷。
- 不改 DB schema、RLS、grant、policy、role、index、constraint。
- 不新增 write path、不做 backfill、不做 production DML。
- 不做 live Telegram delivery。
- 不處理 Telegram reply markup 附著最後一則 message 的旁支風險。
- 不稽核 2356 英業達 production ledger/source-of-truth 是否正確。
- 不全量重構報文產生器或 evidence 模型。

## 影響模組

Tech 需自行定位實際檔案；預期範圍只限 Telegram 報文第三則組裝、版本字串與對應測試。

可能影響：

- Telegram report/message list formatter。
- short/evidence message builder。
- version/header 常量。
- 既有 generator/notifier 測試或 snapshot 測試。

不得影響：

- 策略計算核心。
- 持倉狀態機。
- DB schema/write path。
- live delivery path。
- 第一、第二則卡片 decision payload。

## 直接消費者

- Owner 在手機 Telegram 上閱讀三則報文。
- Telegram notifier/message list consumer。
- 產生完整 Telegram sample 的 dry-run/測試工具。
- QA 用完整三則 Telegram sample 驗證第三則手機閱讀路徑。

## 已存在且不得回退的契約

- 報文主順序維持: messages[0] 持倉、messages[1] 未持倉/候選、messages[2] short/evidence；include_detail=True 時 Details Backup 仍追加在最後。
- v20.4.14 已移除 legacy 📊 策略證據 v20.0 與簡短摘要重複出現的問題，不得回退。
- 第三則不得同時出現多個 evidence entry 或多個可被理解為 evidence/status 入口的段落。
- 策略樣本 missing-source / insufficient-data 必須 fail closed。
- market/theme production evidence、strategy sample evidence、stock decision 三層語意不得混淆；market/theme confirmed 不得升格成 BUY 或進場依據。
- 不改持倉/未持倉主卡片的使用者可見決策。

## 輸出契約

第三則 message 必須是單一訊息、兩個主要區塊，順序固定：

1. 決策簡報

- 以手機可讀的短段或短 bullet 呈現。
- 只整合既有第一、第二則決策結果與第三則資料限制，不新增策略判斷。
- 必須明確區分：持倉先處理什麼、新倉是否有有效進場、哪些資訊只是背景或追蹤。
- 若無可買標的，使用「新倉：無有效進場」或等價不可買表述，不得使用像推薦的語氣。

2. 資料依據

- 只能是一個連續資料依據區塊，不拆成多個 evidence/status 入口。
- 必須集中說明 market/theme production 來源狀態、strategy sample 來源狀態、持倉/候選 source-of-truth 的資料庫/持久來源狀態與限制。
- market/theme 若有日期/範圍可用，應摘要顯示，但用途限市場/題材背景。
- strategy sample 若缺 source，明確顯示 missing-source 或 insufficient-data 並 fail-closed。
- 持倉/候選來源不足時，只能顯示 fail-closed 或 source limitation，不得推導新行動。
- 不得把 source limitation 分散到第三則其他位置。
- 不得新增 DB 欄位或要求 live 查寫。

禁止出現在第三則的分裂入口示例：

- v20.4.14 簡短證據摘要
- 📊 策略證據 v20.0
- 單獨的「策略證據」段
- 單獨的「來源狀態」段
- 單獨的「漏斗」或「風險」evidence 段
- 多個 evidence entry heading

版本契約：

- 使用者可見版本升為 v20.4.15。
- 若有 header、常量、測試 snapshot 或 sample fixture 顯示版本，必須同步。
- 不得保留 v20.4.14 作為新第三則標題。

## 範例或 fixture

### Fixture A: strategy sample 缺 source

完整三則 Telegram sample 中，第三則形狀必須類似：

🧾 v20.4.15 簡報＋資料依據

決策簡報
持倉：依第一則既有卡片處理，不新增第二個主行動。
新倉：無有效進場。
背景：市場/題材資料已確認只能說明環境，不構成買點；策略樣本來源不足，本輪 fail-closed。

資料依據
market/theme：production DB 已有可用 confirmed evidence（顯示實際日期/範圍，如可取得），用途限背景。
strategy sample：missing-source / insufficient-data，無可驗證樣本來源，fail-closed，不產生進場理由。
持倉/候選：依 production DB 或 Owner 指定持久 source-of-truth；若來源不足，僅顯示限制，不推導新行動。

驗收重點不是逐字相同，而是只有「決策簡報」與「資料依據」兩個主要入口，且 missing-source 仍 fail-closed。

### Fixture B: market/theme confirmed 但無新倉

完整三則 Telegram sample 中：

- 第三則可提到 market/theme confirmed 或 production coverage。
- 第三則不得因此寫「可買」「推薦」「進場」「買點成立」。
- 第一、第二則原有不可買/追蹤分類不因第三則資料背景而改變。

## 驗收條件

1. 完整三則 Telegram sample 驗收

- messages[0]、messages[1] 卡片內容與排序不因本輪改動發生契約性變更。
- messages[2] 是 v20.4.15 第三則。
- 手機閱讀第三則時，只能看到一個「決策簡報」塊與一個「資料依據」塊。
- 第三則不得出現分裂的策略證據/簡短證據/來源狀態多入口。

2. fail-closed 驗收

- 注入或使用 strategy sample missing-source / insufficient-data case。
- 第三則資料依據中必須集中呈現缺 source 與 fail-closed。
- 不得在任何區塊把該樣本描述成可買、可準備、推薦或買點。

3. market/theme 背景驗收

- market/theme confirmed 可出現在資料依據。
- 不得改變第一、第二則策略 decision。
- 不得把 market/theme confirmed 寫成進場條件已成立。

4. 版本驗收

- 使用者可見版本為 v20.4.15。
- 測試、sample 或 snapshot 不得仍以 v20.4.14 簡短證據摘要作為第三則新結構標題。

## 明確禁止事項

- 禁止改第一、第二則主卡片、分類、行動、排序。
- 禁止改策略 decision 或任何交易建議邏輯。
- 禁止改 DB schema/write path。
- 禁止 live Telegram。
- 禁止新增多個 evidence entry 來解釋資料。
- 禁止把 market/theme confirmed 當成買點。
- 禁止策略樣本缺 source 時用模糊文案弱化 fail-closed。
- 禁止用 local cache、runtime dict、worktree 或 agent 對話當跨日 source-of-truth。
- 禁止把本輪擴成全報文重構、策略重設、ledger 稽核或 reply markup 任務。

## 阻塞條件

Tech 應 blocked 並回報 Architect，而不是自行擴權，如果出現以下任一情況：

- 無法在既有 message list 中穩定定位第三則 short/evidence message。
- 需要改 DB schema/write path 才能取得必要 source 狀態。
- 既有資料無法判定 strategy sample source 狀態，且無法以 missing-source / insufficient-data fail-closed 呈現。
- 修改第三則必然改動第一、第二則 decision 或卡片契約。
- 找不到使用者可見版本常量或 sample 驗證入口，無法證明升版到 v20.4.15。

## 本輪停止條件

做到以下即完成本輪，不再擴 scope：

- 第三則已改成單一「決策簡報」＋單一「資料依據」結構。
- 完整三則 Telegram sample 證明手機閱讀第三則沒有多 evidence/status 入口。
- strategy sample 缺 source 仍 fail-closed。
- market/theme confirmed 仍只作背景。
- 版本升到 v20.4.15。
- Tech 自檢與 QA L2 覆蓋上述驗收。

以下旁支只記待辦，不納入本輪：

- 2356 ledger/source-of-truth 稽核。
- reply markup 附著最後一則 message 的 delivery consumer 風險。
- 全報文文案盤點。
- strategy evidence 模型重構。
- production data backfill 或 DB schema 設計。
