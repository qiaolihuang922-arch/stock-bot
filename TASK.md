# TASK: afterhours_summary_trade_plan_v21_1_20260616

## 任務狀態

- task_id: `afterhours_summary_trade_plan_v21_1_20260616`
- 任務類型: `normal_patch`
- 狀態: `implemented + full pytest passed`
- 版本建議: 報文 header 維持 `v21.1`
- QA 分級: L2

## Owner 問題

Owner 指出盤後 `決策簡報` 除了 `持倉風控檢查` 外，多數內容沒有交易決策價值：

- 市場 / 今日買入 / 未持倉統計像流水帳。
- `今日買入紀錄後風控` 與持倉檢查重複。
- `未持倉狀態` 漏斗在沒有可買 / 可準備時只增加噪音。

Owner 追問是否真的對照網路交易計畫規範。

## 使用者可見結果

- 盤後 summary 改為交易計畫式：
  - `結論`
  - `明日計畫`
  - `持倉風控檢查`
- 刪除盤後 summary 的市場統計流水、今日買入流水、空的新倉占位與無操作漏斗。
- `未持倉狀態` 只在有新倉候選或可準備時顯示。
- 今日買入仍會反映在 `明日計畫`，但不再另開重複行。

## 非目標

- 不修改買賣 / 加減碼 / 停損策略判斷。
- 不修改 DB schema/write/backfill/prune。
- 不做 live Telegram delivery。
- 不修改盤中 summary 或持倉 / 未持倉卡片策略欄位。

## 影響模組與直接消費者

- `presentation/report.py`
  - `_afterhours_brief_lines`
- `tests/test_generator_report.py`
  - 更新盤後 summary 契約 regression。
- 直接消費者:
  - Telegram summary 第 3 則 / official generator message list。

## 輸出契約

- 盤後 summary 不再顯示：
  - `市場：...｜執行動作...｜今日買入...｜未持倉...`
  - `今日買入紀錄後風控：...`
  - `新增有效進場：無`
  - 無新倉候選 / 可準備時的 `未持倉狀態` 漏斗。
- 盤後 summary 必須顯示：
  - `結論：...`
  - `明日計畫：...`
  - 持倉存在時顯示 `持倉風控檢查`。

## 對標依據

- Schwab trade plan: trading plan should decide what to trade, when to enter, position sizing and risk management.
- IG trading checklist: checklist should focus on market conditions, entry/exit signals and risk management rules.
- ForTraders checklist: entry / exit checklist should use entry rules, support/resistance, volume, stops and risk/reward.

## 驗收條件

- Owner 樣本的盤後 summary 只保留可行動資訊，不再顯示統計流水與無用漏斗。
- `generate_report(dry_run=True)` 的 summary 顯示：
  - `結論：新倉無有效進場；今日買入紀錄已轉風控。`
  - `明日計畫：英業達、建準減碼/停損優先；未持倉：...`
  - `持倉風控檢查`
- Targeted regression 與 full pytest 通過。

## 失敗標本與驗收路由

- 失敗標本:
  - Owner 貼出的 `【06/16 盤後｜v21.1】 🧾 v21.1 簡報`。
- 驗收路由:
  - `generate_report(dry_run=True)`
  - `formatTelegramMessages`
  - official summary message。

## 禁止事項與阻塞條件

- 禁止只刪字而丟失明日可執行計畫。
- 禁止把無新倉寫成推薦語氣。
- 禁止 live Telegram delivery。
- 禁止 DB write / schema 變更。
