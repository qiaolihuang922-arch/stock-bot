# TASK: entry_quality_priority_v21_1_20260616

## 任務狀態

- task_id: `entry_quality_priority_v21_1_20260616`
- 任務類型: `normal_patch`
- 狀態: `QA passed, pending commit/push`
- 版本建議: 報文 header 維持 `v21.1`
- QA 分級: L2

## Owner 問題

06/16 盤前未持倉報文仍把 `個股弱勢 / 買點品質 D` 放成主要阻擋，造成「跌到低點不能買、連漲也不能買、永遠 D」的誤讀。Owner 要求依策略顆粒度顯示，不要只硬改文字。

## 使用者可見結果

- 未持倉卡片主因要依策略路徑排序：
  - 漲停/過熱: 等冷卻或等回測。
  - 急彈: 等回測。
  - 風險報酬不足: 等風險報酬。
  - 距突破很遠: 等接近。
  - 真的沒有買點型態時才顯示等型態 / 品質未過。
- `market_grade D` / `entry_quality D` 不得單獨搶成主阻擋。
- `距突破` 仍保留獨立顯示。
- 不做 live Telegram delivery。
- 不做 DB schema / write / backfill。

## 非目標

- 不重新設計所有交易策略。
- 不修改 Supabase schema、RLS、grant、policy、role、index。
- 不做 production DB DML。
- 不改版本號到 `v21.2` 或 `v22`。

## 影響模組與直接消費者

- `services.analysis`: entry setup state 與 setup blocker 語義。
- `core.trade_state_machine`: 未持倉 guard / transition fallback。
- `core.generator`: blocker 排序、watch state、funnel state。
- `presentation.report`: Telegram 未持倉卡片標題與策略主因顯示。
- 直接消費者: official `generate_report(dry_run=True)` message list、runner/bot Telegram artifact。

## 輸出契約

- 未持倉卡片保留順序：
  - title
  - 距突破
  - 進場
  - 缺口
  - 可買
  - 盤前/盤中/明日觀察
  - 必要補充、歷史、價格
- `買點品質 D` 只能作為缺口補充或等型態主因，不得覆蓋急彈、過熱、RR、距離等更具體 blocker。
- `等型態 + 距突破 > 12%` 的顯示主狀態改為 `等接近｜遠離觸發`。

## 驗收條件

- Owner 樣本等價 dry-run 中，緯創/仁寶/技嘉不再顯示 `等型態｜個股弱勢`。
- 旺宏仍保留 `等回測｜急彈待回測`，不被距突破覆蓋。
- 華邦電仍保留 `等回測｜漲停不追`。
- 聯電仍保留 `等風險報酬`。
- full pytest 通過。

## 失敗標本與驗收路由

- 失敗標本: Owner 貼出的 06/16 盤前未持倉報文。
- 驗收路由:
  - helper/state: `tests/test_analysis_engine.py`, `tests/test_trade_state_machine.py`
  - formatter: `tests/test_unheld_gap_format.py`
  - official generator: `tests/test_generator_report.py`
  - official dry-run: `generate_report(dry_run=True)`

## 禁止事項與阻塞條件

- 禁止 live Telegram delivery。
- 禁止手寫 production DML。
- 若 dry-run 只能局部驗證，不得宣稱 production delivery 已完成。
