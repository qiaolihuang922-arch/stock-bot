# QA_REPORT:

## 測試範圍

- 任務：`telegram-evidence-human-readable-v20-4-20`，normal_patch，QA L2。
- 聚焦 Telegram 三則 message 手機閱讀順序、第三則 evidence 人話化、raw evidence slot 隱藏、內部 maturity artifact/gate 不回退、持倉非加碼 RR、strategy sample unavailable 卡片。
- 未擴張到 full repo pytest、replay、backfill、production DB write 或 live Telegram。

## 關聯風險掃描

- 可吸收 diff：`core/generator.py`、`tests/test_generator_report.py`、`tests/test_market_theme_evidence.py`、`tools/cao_agent/check_evidence_handoff_gate.sh`、`TASK.md`、`CHANGELOG.md`。
- 未見 DB schema/write、backfill、live Telegram sender 相關 diff。
- `git diff --check`：passed。
- `tools/cao_agent/check_evidence_handoff_gate.sh . .qa_tmp/evidence_maturity_report_v20_4_20_qa.json`：passed。

## 跨區塊語意一致性

- message 順序一致：messages[0] 持倉、messages[1] 未持倉、messages[2] 簡報＋資料依據。
- 第三則不再顯示 `source:`、`status:`、`use:`、`limit:`、`conflict:` 或 raw status；內部 `evidence_manifest` 仍保留 machine-readable 欄位。
- Re-QA blocker 已修：當第三則說「新倉：無有效進場」且候選只有追蹤/不可行動時，不再出現推薦感的 `最強：<symbol>`、`排序★`、`評級★`。
- conflict case 仍有人話提醒「紀錄仍有待釐清的差異」，沒有用可讀性改善掩蓋衝突。

## 使用者誤讀風險

- 持倉非加碼情境顯示 `新倉 RR：不適用（既有持倉）`，不再顯示新倉 RR 數字。
- strategy sample unavailable 時，卡片不顯示樣本數、勝率、相對報酬等回測數字。
- 手機第三則只保留決策簡報與資料依據；資料依據用人話說明用途與限制。

## 質疑與反證

- QA 補兩個非有效進場候選反證：一個 WAIT、一個 BUY 但 HOT blocker，且傳入 best/score；messages[2] 仍輸出「最強：無有效進場標的」。
- QA 補 artifact 反證：ledger conflict 的 Telegram 第三則隱藏 raw 欄位，但 structural artifact 仍保留 `source/status/use/limit/conflict`，maturity_score=100，安全旗標 false。
- QA 初判 `conditional pass`，條件是同步 CHANGELOG 測試數字；Architect 已同步為 88 / 36 / 124 passed。

## 未測項目

- 未跑 full repo pytest。
- 未做 production DB write、backfill、live Telegram。
- 未做實際手機 Telegram delivery。

## QA 結論

通過
