# TASK: report_actionability_consistency_v21_1_20260624

## 任務狀態

- task_id: `report_actionability_consistency_v21_1_20260624`
- 任務類型: `normal_patch`
- 狀態: `ready_for_qa_after_followup`
- 版本建議: `v21.1`
- QA 分級: `L2`

## Owner 問題

06/24 盤中報文已出現可買，但整體仍有誤讀風險：

- 低位修復跌破支撐時仍像一般觀察，使用者看不出條件已失效。
- 量能 `0.9x` 文字一邊像不足、一邊又以 `量能不失控` 作觸發，語意衝突。
- 已突破但風險報酬極低時顯示 `0.02 -> 1.5`，閱讀者只看到數字，不知道真正含義是追價不划算。
- 突破失敗距離在百分比接近但絕對價差很大時，顯示 `站回觀察` 容易誤導。
- 可買卡需要像交易指令，不要混入過多模型數據。
- 06/24 後續標本顯示：持倉已跌破警戒仍被寫成 `輕虧不加碼`；低位修復可買卡仍出現 `盤面：弱勢｜弱勢`；絕對價差很大的突破失敗仍可能被寫成站回觀察。

## 使用者可見結果

- 低位修復支撐跌破時，卡片標題與觸發條件明確改成重新築底 / 重新站回支撐。
- 低位修復量能顯示分級為：不足、偏低未失控、剛好、有效、攻擊量。
- 已突破但風險報酬不足時，顯示追價風險過高與回測後修復，不再把極低 RR 數字當主訊息。
- 站回觀察加入絕對價差判斷，避免大價差仍顯示得像快到了。
- 低位修復可買卡改成 `可買：小倉試單`、守線與失效條件。
- 持倉跌破警戒但未到停損時，主決策改成 `警戒觀察，不加碼`。
- 低位修復可買卡的盤面改為 `低位修復成立｜小倉觀察｜量能分級`，避免與弱勢背景衝突。
- 突破失敗站回標籤只要絕對價差大，就顯示 `站回距離偏大`。

## 非目標

- 不改 DB schema。
- 不寫入 / 回寫 / 刪除 production DB。
- 不發 live Telegram。
- 不重新設計全部策略，只修本輪可見誤讀與一致性問題。

## 影響模組與直接消費者

- `core/generator.py`: 低位修復量能門檻與狀態資料。
- `presentation/report.py`: Telegram 未持倉卡片顯示與契約文字。
- `tests/test_generator_report.py`: 報文層回歸測試。
- 直接消費者: Telegram 報文、dry-run report、Owner 手機閱讀。

## 輸出契約

- `距突破` 必須保留。
- 可買卡先顯示交易動作，再顯示守線與失效條件。
- 非可買卡只顯示當前缺口與下一個可驗證觸發，不重複 `進場 / 缺口 / 可買 / 觸發` 同義句。
- 支撐已跌破時不得顯示 `待守` 或 `守住支撐`。
- 低 RR 已突破情境不得以裸數字作主訊息。

## 驗收條件

- Focused report tests pass。
- 相鄰報文分組 / RR 分組測試 pass。
- Official `generate_report(dry_run=True)` 不出現舊誤導字串。
- Official `generate_report(dry_run=True)` 不出現警戒持倉混 `輕虧不加碼`、低位可買卡混弱勢盤面、裸 RR 追價 gap。
- 等價 replay 覆蓋低位修復、突破失敗、RR 追價、可買卡。

## 失敗標本與驗收路由

- Owner 06/24 盤中報文是 failure specimen。
- 驗收路由: formatter helper -> official `formatTelegramMessages`/`formatTelegramUnheldCard` -> dry-run generator smoke。

## 禁止事項與阻塞條件

- 不得只改文字而不改策略門檻。
- 不得用 agent 記憶取代 DB / payload。
- 若 production source 缺資料，必須 fail closed，不得假補。
