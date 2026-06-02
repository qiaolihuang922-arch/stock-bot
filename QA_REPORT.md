# QA_REPORT: per-stock evidence 決策分數與 B5 漏斗一致性收口

## 測試範圍

- 任務尺寸 / QA：risk_patch / L3。
- 驗證範圍：M1-M7 的 evidence modifier、per-stock setup sample、弱勢/失敗/過熱封頂、資料不足 fail closed、rendered Telegram card、B5 漏斗一致、VERSION 不變。
- 未執行：full pytest、production read-only smoke、live Telegram、DB write/backfill、production replay。

## 關聯風險掃描

- 可吸收 diff：`CHANGELOG.md`、`core/generator.py`、`services/strategy_evidence.py`、`tests/test_generator_report.py`、`tests/test_strategy_evidence.py`。
- `load_strategy_evidence_summary()` 缺來源 / insufficient 分支仍為文字 fail-closed；rows 足夠時回傳 structured dict，含 `rendered_text`、`structured_status`、`setup_strategy_samples`。
- `VERSION` 保持 `v20.4.31`。
- 未見 DB schema/write、approved write CLI、live Telegram、RR 公式改動。

## 跨區塊語意一致性

- 旺宏 / 聯電不同 explicit setup modifier：通過。
- 缺 explicit setup 不用 report layer 推導補 boost：通過。
- weak / failed / EXTREME / technical=0 不吃正向 boost：通過。
- B5 official rendered path：Summary、漏斗、card 在同一 market_mode 下三方一致。
- strategy 跨版本 outcome history：通過。

## 使用者誤讀風險

- 不可用 evidence 顯示 `證據：不適用`，不顯示 `證據 +%`。
- Summary 明確寫 `新倉：無有效進場 / 目前沒有可行動候選`。
- B5 漏斗沒有把 `隔日確認` 併入 `等冷卻`，split sum 與僅追蹤 count 一致。

## 質疑與反證

- Targeted tests：4 passed。
- QA 負面 probe：WEAK、EXTREME、technical=0 即使有正向 setup sample，也不顯示 boost。
- QA 手機閱讀 probe：Telegram Summary / 未持倉漏斗 / card 的 B5 計數一致。
- 初次 pytest 使用預設架構命中 `.venv` arm64/x86_64 不相容；已按 runner 口徑用 `arch -arm64 .venv/bin/python` 重跑通過。

## 未測項目

- 未跑 full pytest。
- 未跑 production read-only smoke、live Telegram、DB write/backfill。
- 未驗長期 production setup 欄位覆蓋率與樣本分布。

## QA 結論

通過
