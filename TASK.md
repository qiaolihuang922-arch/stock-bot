# TASK: v20.4.42 未持倉非可買卡片 attribution 兩層可讀化

## 任務狀態

- task_id: pm-20260604-v20.4.42-unheld-attribution-readable-gap
- 任務類型: normal_patch
- 狀態: ready_for_tech
- 版本建議: 使用者可見報文版本升至 v20.4.42
- QA 分級: L2
- 失敗標本: 2026-06-04 盤後 v20.4.41 未持倉報文中，非可買卡片只顯示單行「到達可買差距」，Owner 無法知道卡在哪裡、差多少。

## Owner 問題

06/04 盤後 v20.4.41 未持倉報文中，非可買未持倉卡片的 attribution 單行「到達可買差距」太抽象。Owner 在手機上看不出是 RR 不足、距突破太遠、過熱、盤後待確認、突破失敗，或其他 source / 策略限制，也不知道量化上差多少。

## 使用者可見結果

- 非可買未持倉卡片的 attribution 改為兩層可讀輸出：
  - 卡關主因：...
  - 量化差距：...
- 真正可買卡片與 trend_continuation 小倉 BUY 卡片不顯示這兩行。
- 手機閱讀時，Owner 能直接看到「不能買的主要原因」與「離可買條件差多少 / 下一步要等什麼」。

## 非目標

- 不改策略決策。
- 不改 RR 公式。
- 不改 can_buy / is_valid_entry 判定。
- 不改持倉建議、持倉狀態機、買賣 / 加減碼 / 停損停利邏輯。
- 不改 DB schema、DB read/write、production source-of-truth。
- 不做 live Telegram delivery。
- 不新增人工 DML 或繞過既有介面。
- 不把 raw enum 直接搬到報文中。

## 影響模組與直接消費者

影響模組：

- 未持倉報文 formatter / card attribution formatter。
- official Telegram message generator 路徑。
- formatTelegramMessages / message-list replay 相關測試或 fixture。
- 報文版本字串 / header 常量。

直接消費者：

- Owner 手機閱讀 Telegram 盤後報文。
- official formatTelegramMessages 產出的 message list。
- QA replay artifact / message-list snapshot。

## 輸出契約

對「非可買未持倉卡片」輸出兩行 attribution，順序固定：

1. 卡關主因：{human_readable_primary_blocker}
2. 量化差距：{human_readable_gap_or_next_confirmation}

對真正可買卡片與 trend_continuation 小倉 BUY：

- 不輸出 卡關主因：
- 不輸出 量化差距：

RR不足：

- 卡關主因：RR不足
- 量化差距：RR {current_rr}｜需>=1.5｜差{delta}
- 範例：量化差距：RR 0.98｜需>=1.5｜差0.52

距突破太遠：

- 量化差距：距突破 {distance_pct}%｜需<=4%｜差{delta_pct}%
- 範例：量化差距：距突破 6%｜需<=4%｜差2%
- 若距離 <=4%，不得列為「距突破太遠」差距。

過熱：

- 卡關主因：熱度 Lv.3 或 卡關主因：過熱觀察
- 量化差距：需降至 Lv.1/觀察以下 或 量化差距：需降溫至可評估
- 不列 RR / entry quality 次因。

post-market ordinary prepare：

- 卡關主因：盤後待確認
- 量化差距：明日開盤站穩才算成立 或 量化差距：需開盤後重新確認
- 不得寫成資料不足。

FAILED_BREAKOUT：

- 卡關主因：突破失敗
- 量化差距：需重新站回突破區
- 不得顯示 RR 0 或 RR需>=1.5。

source missing / strategy sample / limit lock / weak rebound：

- 必須人話化，不得顯示 raw enum。
- 建議映射：
  - source missing: 卡關主因：資料來源缺失；量化差距：需補齊有效行情 / 策略來源
  - strategy sample: 卡關主因：樣本不足；量化差距：需更多有效策略樣本確認
  - limit lock: 卡關主因：漲跌停鎖定；量化差距：需解除鎖定後重新評估
  - weak rebound: 卡關主因：反彈力道不足；量化差距：需放量轉強後重新評估
- 禁止輸出 raw enum，例如 FAILED_BREAKOUT、source_missing、strategy_sample、limit_lock、weak_rebound。

## 版本契約

- 使用者可見報文版本必須由 v20.4.41 升至 v20.4.42。
- QA 必須核對 official message header / version constant / replay output 實際顯示 v20.4.42。
- 不得回退既有 v20.4.x 報文結構中與本任務無關的欄位、分組、排序。

## 驗收條件

- 使用 official formatTelegramMessages / message-list replay 驗收，不可只測 helper。
- replay 中至少覆蓋以下未持倉卡片：
  - RR 不足。
  - 距突破太遠，且距離 >4%。
  - 距突破 <=4% 的負面案例，確認不得列為距突破差距。
  - 過熱。
  - post-market ordinary prepare。
  - FAILED_BREAKOUT。
  - source missing。
  - strategy sample。
  - limit lock。
  - weak rebound。
  - 真正可買。
  - trend_continuation 小倉 BUY。
- 非可買未持倉卡片必須出現兩行：
  - 卡關主因：...
  - 量化差距：...
- 真正可買與 trend_continuation 小倉 BUY 不得出現這兩行。
- RR 不足案例必須顯示 RR 現值、門檻 需>=1.5、差值。
- FAILED_BREAKOUT 案例不得出現 RR 0、RR需>=1.5 或等價誤導。
- 過熱案例不得列 RR / entry quality 作次因。
- post-market ordinary prepare 不得被寫成資料不足。
- replay output 不得出現 raw enum。
- 手機閱讀路徑需確認：兩行 attribution 不應造成卡片主結論與分組標題矛盾。

## 範例或 Fixture

RR不足：

- 卡關主因：RR不足
- 量化差距：RR 0.98｜需>=1.5｜差0.52

距突破太遠：

- 卡關主因：距突破太遠
- 量化差距：距突破 6%｜需<=4%｜差2%

過熱：

- 卡關主因：熱度 Lv.3
- 量化差距：需降至 Lv.1/觀察以下

盤後待確認：

- 卡關主因：盤後待確認
- 量化差距：明日開盤站穩才算成立

突破失敗：

- 卡關主因：突破失敗
- 量化差距：需重新站回突破區

## 失敗標本與驗收路由

失敗標本：

- 2026-06-04 盤後 v20.4.41 未持倉報文，非可買卡片單行「到達可買差距」導致 Owner 不知道差多少。

驗收路由：

- 必須建立或使用等價 replay payload，經 official formatTelegramMessages 產出 message list。
- QA 直接檢查 official message-list output 的文字、版本、卡片分組與手機閱讀風險。
- helper-level 測試只能作補充，不得作為本任務唯一驗收證據。

## 明確禁止事項

- 不改策略結果，只改使用者可見 attribution 文案與差距呈現。
- 不改 RR 計算、entry quality 計算、突破距離計算、過熱判定。
- 不改 can-buy gate、valid-entry gate。
- 不碰持倉、DB、runner live delivery、Telegram live send。
- 不輸出 raw enum。
- 不用 synthetic helper fixture 直接宣告完成。
- 不把 post-market ordinary prepare 寫成資料不足。
- 不讓 FAILED_BREAKOUT 顯示 RR 0 或 RR 門檻差距。
- 不讓真正可買與 trend_continuation 小倉 BUY 顯示兩層卡關 attribution。

## 阻塞條件

- 找不到 official formatTelegramMessages / message-list replay 路徑。
- 無法取得或建立等價 06/04 盤後未持倉 replay payload。
- 現有資料沒有足夠欄位顯示 RR 現值、突破距離、熱度等量化差距，且不能在不改策略 / DB 的前提下取得。
- 版本字串來源不明，無法保證 official output 顯示 v20.4.42。
- QA 只能測 helper，無法驗 official message-list output。

## 本輪停止條件

- Tech 完成 scoped formatter / version / replay test 修改並輸出 CHANGELOG.md。
- QA 以 official message-list replay 反證通過、conditional pass 或阻塞並輸出 QA_REPORT.md。
- 若 QA 通過，Architect 後續仍需依 git completion gate 收口；未 commit / push 前不得宣告 repo 落地完成。
