# TASK: v20.4.13 Telegram 第三則 short/evidence 報文降噪與自然語言化

## 任務狀態

- task_id：tg-evidence-short-ux-v20.4.13
- 任務類型：tiny_patch
- 狀態：QA 通過，待 git 收口
- 版本建議：v20.4.13
- QA 分級建議：L1；需補一個完整三則 Telegram sample 驗收

## Owner 問題

Owner 已提供 v20.4.12 Telegram output，拒收第三則 report short/evidence 訊息品質。

核心問題是：第三則 evidence/short 報文太像 debug 輸出，包含文件名、表名、raw 日期欄位、0-count/source debug 文案與互相衝突的敘述，手機上難以閱讀，也削弱證據鏈可信度。

本輪只修第三則 short/evidence 訊息的 UX 與證據表達，不改策略、不改資料來源、不改 DB。

## 使用者可見結果

Telegram 仍輸出三則訊息，順序不得變：

1. 持倉處理
2. 未持倉候選
3. 簡短報告 / 證據說明

第三則訊息改為手機可讀的自然語言摘要：

- 先說本次判斷依據來自哪類可信來源，例如「持久化交易紀錄」「今日策略樣本」「候選清單狀態」。
- 再說哪些資料不足、因此哪些結論 fail-closed。
- 不顯示 debug 欄位、table/file 名、raw per-stock date lines。
- 不捏造證據；資料沒有就明確說「缺少可驗證紀錄」或「本輪不輸出可行動結論」。

## 非目標

- 不調整買賣、加減碼、停損、停利或任何策略 decision。
- 不新增 DB schema、RLS、grant、policy、role、index、constraint。
- 不做 production DB write、backfill 或 live Telegram delivery。
- 不重構整個報文系統。
- 不改第一則持倉訊息與第二則未持倉訊息的主結構、排序或策略語意。
- 不把缺資料包裝成看似完整的證據鏈。
- 不新增大型 evidence dashboard、CLI 模式或全量清理工程。

## 影響模組

預期最小影響範圍：

- Telegram 第三則 short/evidence 報文 formatter。
- Evidence Compact / summary evidence 文字生成邏輯。
- 版本字串或 Telegram header 常量：v20.4.12 -> v20.4.13。
- 對應 formatter / Telegram output tests。

若 Tech 發現必須改 public payload shape、DB read path、策略 decision 或 message list 結構，必須 blocked 回報，不得自行擴大。

## 直接消費者

- Owner 在手機 Telegram 閱讀每日報文。
- QA 使用 sample Telegram output 驗證三則訊息順序與第三則可讀性。
- 既有 Telegram runner 仍消費同一份 message list。

## 已存在且不得回退的契約

- Telegram message order：持倉 first、未持倉 second、short/evidence last。
- 無有效新倉時，不得把追蹤或不可行動候選寫成推薦。
- 缺持久 source-of-truth、缺紀錄、缺策略樣本或資料不足時，必須 fail closed。
- source truth 必須保留，但只能用自然語言描述，不得偽造 evidence。
- 使用者可見版本需同步升到 v20.4.13，不得仍顯示 v20.4.12。
- 不做 live Telegram delivery。

## 輸出契約

第三則 Telegram 訊息必須符合以下形狀：

[版本/標題：v20.4.13 對應既有格式]

本次證據摘要：
- 持倉判斷依據：用一句自然語言說明是否找到可驗證的持久化交易紀錄。
- 未持倉判斷依據：用一句自然語言說明候選策略樣本是否足夠支持可行動結論。
- 資料不足處理：若缺資料，用 fail-closed 語句說明，不輸出行動建議。

結論：
用 1-2 句說明本輪是否有可行動新倉、持倉是否需要優先處理；不得和前兩則訊息衝突。

禁止出現在第三則使用者可見文案中的 debug terms：

- position_events
- db_table
- source_of_truth
- latest_trade_date
- lookback_range
- raw table/file name
- raw per-stock position event line
- contradictory 0-count / source debug text
- 若替換 Evidence Compact raw heading，則不得再顯示 raw heading：Evidence Compact

允許保留自然語言等價資訊，例如：

持倉紀錄：本輪沒有找到可驗證的持久化買入紀錄，因此不把任何持倉狀態升格成已確認倉位。

## 手機閱讀路徑

Owner 打開 Telegram 後應能在第三則訊息內快速讀到：

1. 本輪證據從哪裡來。
2. 哪些資料不足。
3. 因為不足，所以哪些行動被關閉。
4. 最終結論是否和前兩則一致。

第三則不得要求 Owner 從表名、欄位名、文件名或日期流水自行推理。

## 驗收條件

1. 使用 2026-06-01 類似 sample 產生完整三則 Telegram output：
- 第一則仍是持倉。
- 第二則仍是未持倉。
- 第三則仍在最後，且為自然語言 short/evidence。
- 第三則不包含禁止 debug terms。
- 第三則不包含 raw per-stock position_events / 日期流水。
- 第三則不出現和前兩則相衝突的 0-count/source debug 敘述。
2. 使用「策略樣本全部 unavailable / insufficient」fixture：
- 第三則仍說明資料不足。
- 結論 fail-closed。
- 不產生假 evidence。
- 不把 unavailable 樣本寫成可買、可準備或推薦。

本輪停止條件：以上兩個驗收案例通過，且版本顯示 v20.4.13，即可收口。其他報文冗長、第一二則文案優化、策略準確度、資料補齊與 DB source 改造，只記待辦，不納入本輪。

## 範例或 fixture

### Fixture A：06/01 類似三則報文

輸入條件：

- 有完整 Telegram output pipeline。
- 第三則 currently 會輸出 evidence/debug 類內容。
- 部分持倉或候選資料來源不足。

期望第三則示例形狀：

v20.4.13 簡短證據摘要

本次判斷以持久化交易紀錄與今日策略樣本為準。持倉側目前缺少可驗證的買入紀錄，因此不把任何項目升格成已確認倉位；未持倉側只保留策略樣本足夠的候選，其餘維持追蹤或不可行動。

結論：本輪沒有新的有效進場訊號；資料不足的項目已關閉行動建議，避免把缺證據誤讀成推薦。

### Fixture B：全部策略樣本 unavailable

期望第三則示例形狀：

v20.4.13 簡短證據摘要

今日候選缺少可驗證的策略樣本，無法支持進場、加碼或轉強判斷。本輪採 fail-closed：資料不足的標的只保留為不可行動狀態，不輸出買入建議。

結論：新倉無有效進場；需等待可驗證樣本恢復後再重新評估。

## 明確禁止事項

- 禁止改策略 decision 或 action mapping。
- 禁止新增或修改 DB schema / RLS / grant / policy / role。
- 禁止 production write、backfill、live Telegram delivery。
- 禁止在使用者可見文案中輸出 raw table name、file name、欄位名、debug key、raw date line。
- 禁止用自然語言包裝不存在的 evidence。
- 禁止改三則 Telegram message order。
- 禁止把本輪擴成全報文重設或 evidence 系統重構。
- 禁止只更新版本不修文案。
- 禁止只刪 debug term 但留下語意衝突。

## 阻塞條件

Tech 必須 blocked 的情況：

- 找不到第三則 short/evidence formatter 或 Evidence Compact 生成入口。
- 現有測試 / runner 無法產生完整三則 Telegram sample。
- 修第三則必須改 public payload shape、策略 decision、DB read/write path 或 message list 結構。
- source truth 欄位本身無法判斷缺資料與可驗證資料的差異。
- 版本字串來源不明，無法可靠同步 v20.4.13。
