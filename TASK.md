# TASK: v20.4.44 Telegram card evidence wording clarity

## 任務狀態

- task_id: telegram_card_evidence_wording_v20_4_44
- 任務類型: normal_patch
- 狀態: ready_for_tech
- 任務尺寸判斷: normal_patch。這是 Telegram 使用者可見顯示語意修正，會改 official message list wording / card lines，但不得改策略 decision、RR 公式、DB、持倉狀態機或 live delivery。
- 版本建議: 使用者可見報文升版到 v20.4.44；若實際 VERSION 不是 v20.4.43，Tech 必須 blocked 回報。
- QA 分級建議: L2

## Owner 問題

Owner 接受 v20.4.43 evidence-chain 方向，但 Telegram 卡片的「決策證據」語意太內部、重複且不夠具體。

v20.4.43 post-market failure specimen 中可見問題包括：

- 顯示「決策證據：來源可追溯」這類 source availability，像交易證據但實際不是交易理由。
- 外露或半外露內部詞：hard stop / 持倉風控、持倉硬風控、既有買點與倉位規則通過。
- 卡片同時寫明日準備不可買，又用像已通過買點的文字，造成語意衝突。
- 解鎖 / 量化差距可顯示數字時仍使用籠統詞，讀者看不出差多少、要等什麼。

## 使用者可見結果

手機 Telegram 卡片要把 evidence-chain 改成人能直接理解的交易語意：

- 不顯示「來源可追溯」作為交易依據。
- 不顯示 raw/internal hard gate 名稱。
- 未持倉卡片能看出：現在結論、主因、目前差距、如何解鎖、輔助依據。
- 有可信數字時優先顯示數字差距，例如 RR、距突破、熱度、停損 / 警戒距離、確認門檻。
- 沒有可信數字時，明確說明 blocker 是事件型，例如「盤後待開盤確認」。
- 明日準備卡仍清楚不可下單，且解鎖條件是開盤後確認，不是買點已通過。
- 持倉卡不再刷 generic evidence；只有停損 / 減碼等硬風險需要人話原因時才顯示。

## 非目標

- 不改 strategy decision、can_buy、is_valid_entry、RR 計算、heat 判定、breakout 判定或持倉主行動。
- 不改 DB schema / RLS / grant / policy / role / index / constraint。
- 不做 DB write、backfill、manual DML 或 live Telegram delivery。
- 不重新設計 Telegram 卡片版型。
- 不新增 evidence-chain 架構。
- 不全量清理報文文案。
- 不把本輪擴成策略準備層、持倉風控或資料治理工程。

## 影響模組與直接消費者

影響模組：

- Telegram card wording / reason builder。
- evidence-chain decision wording formatter。
- official formatTelegramMessages 或等價 full message-list generation path。
- 版本字串所在報文 header / VERSION 常量。
- focused regression tests / replay fixtures。

直接消費者：

- Owner 手機 Telegram 閱讀路徑。
- official report generator / runner artifact consumer。
- QA official message-list replay。
- Summary / funnel / card 一致性檢查者。

## 輸出契約

未持倉卡片契約：

- 買點 = 結論 + primary reason。不得塞 source availability。
- 卡關 或 卡關主因 = 最大 blocker，只顯示一個主 blocker，避免次因搶焦點。
- 量化差距 = 有可信數字時顯示 current -> threshold / diff。
- 解鎖 = 要變成可行動必須發生什麼；有數字就顯示數字，沒有數字就說事件型原因。
- 依據 = 輔助 evidence；不得重複已在買點 / 卡關 / 量化差距 / 解鎖出現的 RR、突破、熱度主 gate。

數字格式示例：

- RR 0.98 -> 需 >=1.5 / 差 0.52
- 距突破 6% -> 需 <=4% / 差 2%
- 熱度 Lv.3 -> 需降至 Lv.1/觀察以下
- 突破失敗 -> 需重新站回突破區；若有距離，補距離。
- 停損 / 警戒距離存在且對持倉風險有用時，顯示具體距離，不寫 raw hard stop label。

Prepare 卡契約：

- 光寶科類明日準備卡不得顯示 既有買點與倉位規則通過。
- 應表達：盤後訊號達準備層，但 開盤確認未完成 / 不可下單。
- 解鎖 應表達：明日開盤後仍守突破區 / 不追價。
- RR / volume / backtest 只能作為 依據，且不得重複 gate lines。

持倉卡契約：

- 建準類持倉觀察卡不得顯示 generic 決策證據：來源可追溯。
- 一般續抱 / 觀察卡可不顯示決策證據行。
- 停損 / 減碼 / 硬風險卡若要顯示 evidence，必須是人話原因，例如跌破警戒、距停損多少、結構轉弱；不得顯示 raw hard stop、持倉硬風控。

## 版本契約

已存在且不得回退：

- v20.4.42 的 卡關主因 / 量化差距 可讀性不得退回單行或 vague 文案。
- v20.4.43 evidence-chain hard-gate fail-closed 行為不得移除。
- 可買、可準備、僅追蹤、淘汰 / 不可行動分組語意不得混淆。
- 無可買時不得使用推薦語氣。
- 盤後 ordinary prepare 不得寫成可買或可下單。
- trend_continuation 小倉 BUY 契約不得變成一般 BUY。
- source-error / missing-source / conflicting evidence 必須 fail closed。
- official Telegram path 優先於 helper-only fixture。

## 驗收條件

- official formatTelegramMessages 或等價 full message-list replay 顯示 header/version 為 v20.4.44。
- Owner v20.4.43 post-market failure specimen 等價 replay 中，不再出現：
- 決策證據：來源可追溯
- hard stop
- 持倉硬風控
- 既有買點與倉位規則通過
- 把明日準備寫成可下單的語意
- 光寶科 prepare：顯示盤後準備但不可下單；解鎖為開盤後守突破區 / 不追價；RR / volume / backtest 不重複搶主 gate。
- 華邦電 / 群創等 overheat 或 failed breakout 卡：只顯示與 卡關主因 一致的 primary blocker；有可信 RR、距突破、熱度差距時顯示數字 gap。
- 建準 holding observation：不顯示 generic evidence wording。
- hard stop / reduce holding cards：顯示人話風險原因；有 stop/warning distance 時顯示距離。
- QA 必須補一個 Tech 未覆蓋的手機閱讀反證路徑，不得只重跑 Tech 命令。

## 範例或 Fixture

手機閱讀輸出形狀示例，實際股票與數字以 replay fixture 為準：

未持倉 RR 不足：

買點：不可買｜RR 未達門檻
卡關主因：RR 不足
量化差距：RR 0.98 -> 需 >=1.5 / 差 0.52
解鎖：風險報酬比修復到 >=1.5
依據：量能達標；回測僅輔助

盤後 prepare：

買點：明日準備｜不可下單
卡關主因：開盤確認未完成
量化差距：盤後待開盤確認
解鎖：明日開盤後仍守突破區 / 不追價
依據：RR 達標；量能達標；回測僅輔助

突破失敗：

買點：不可買｜突破失敗
卡關主因：未站回突破區
量化差距：距突破區 6% -> 需 <=4% / 差 2%
解鎖：重新站回突破區後再評估
依據：不重複 RR / 突破主 gate

持倉風險：

行動：減碼｜跌破警戒
原因：距停損線 1.8%，結構轉弱

失敗標本與驗收路由：

- failure specimen: Owner v20.4.43 post-market report。
- 若原文 artifact 不在 worktree，Tech 必須建立等價 official replay fixture，至少覆蓋光寶科 prepare、華邦電 / 群創 blocker priority、建準 holding observation、hard stop / reduce holding。
- 驗收路由：production-like payload -> official formatTelegramMessages -> message list / mobile-readable text -> QA 反證。

## 明確禁止事項

- 禁止改策略 decision 或 hard gate 判斷。
- 禁止改 DB schema/write/backfill/manual DML。
- 禁止 live Telegram delivery。
- 禁止把 source availability 顯示成交易 evidence。
- 禁止 raw internal label 外露。
- 禁止只驗 helper 就宣稱手機報文完成。
- 禁止為了文案簡化而移除 v20.4.42 卡關主因 / 量化差距 數字可讀性。
- 禁止 overheat / failed breakout 卡列多個次要 blocker 造成主因失焦。

## 阻塞條件

- 找不到 Owner v20.4.43 specimen，且無法產生等價 official replay fixture。
- 現有 payload 沒有可信數字來源，卻需求要求顯示數字；此時只能顯示事件型 blocker，不能捏造數字。
- 實際 VERSION/header 不是 v20.4.43 基準。
- 需要 DB write、schema change、live delivery 或策略變更才可驗收。
- Tech 發現 卡關主因 / 量化差距 既有契約與本任務輸出契約衝突。

## 本輪停止條件

驗到 official Telegram message-list replay 層即停止。完成定義：

- v20.4.44 header/version 正確。
- failure specimen 等價 replay 中的 vague/internal wording 全部消失。
- 光寶科 prepare、華邦電 / 群創 blocker priority、建準 holding observation、hard stop / reduce holding 四條手機閱讀路徑通過。
- 可用數字 gap 已顯示；不可用數字時有明確事件型 blocker。
- QA 結論為 通過，或若 artifact / 權限不足則只能 conditional pass / 阻塞 並列出缺口。

旁支只記待辦，不納入本輪：

- 新策略閾值。
- 全量文案 redesign。
- production DB source artifact。
- live Telegram。
- 全市場資料品質治理。
- unrelated card ordering cleanup。
