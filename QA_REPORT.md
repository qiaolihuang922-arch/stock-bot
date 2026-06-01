# QA_REPORT:

## 測試範圍

- 任務：`telegram-evidence-entry-dedupe-v20.4.14`
- 任務尺寸 / QA：`tiny_patch / L1`
- 驗證範圍：第三則 Telegram 證據入口去重、版本、fail-closed 與 message order。
- 未做 DB write、live Telegram、replay、backfill、production smoke。

## 風險預算與停止條件

1. `CHANGELOG.md` 還宣稱本任務交付 `v20.4.13`，導致 Architect 誤收版本。
   - 驗證：讀 `CHANGELOG.md` 與 diff；確認使用者可見版本、契約、測試描述均為 `v20.4.14`。
   - 停止條件：任何本任務交付口徑仍寫 `v20.4.13` 即 blocked。
2. 第三則 Telegram 仍同時出現 `📊 策略證據 v20.0` 與 `簡短證據摘要`。
   - 驗證：讀 formatter diff、跑 scoped pytest、補 QA probe 計數第三則入口。
   - 停止條件：第三則入口數不等於 1，或 legacy heading 仍出現即 blocked。
3. 去重時把 `missing-source / insufficient-data` 刪掉或改成可行動。
   - 驗證：scoped tests + QA probe 檢查狀態碼仍在唯一摘要內且含 fail-closed。
   - 停止條件：缺資料語意消失、變成可買 / 推薦 / 通過即 blocked。

## 關聯風險掃描

- 可吸收 diff：`CHANGELOG.md`、`core/generator.py`、`tests/test_generator_report.py`、`tests/test_market_theme_evidence.py`、`TASK.md`、`QA_REPORT.md`。
- `core/generator.py` 版本常量已由 `v20.4.13` 升到 `v20.4.14`。
- `format_telegram_short_report_message()` 會跳過以 `📊 策略證據 v20.0` 開頭的 legacy strategy evidence block。
- `format_evidence_compact_message()` 仍輸出 `v20.4.14 簡短證據摘要`。
- 未看到 DB schema/write path、策略 decision、live Telegram 修改。

## 跨區塊語意一致性

- `TASK.md` 要求：第三則唯一證據入口、版本 `v20.4.14`、missing-source fail-closed、順序持倉 / 未持倉 / short-evidence。
- `CHANGELOG.md` 現在一致描述 `v20.4.14`，不再宣稱本任務交付 `v20.4.13`。
- diff 與測試一致：版本斷言更新到 `v20.4.14`，第三則測試補上 `NotIn("📊 策略證據 v20.0")` 與 `策略樣本（missing-source/insufficient-data）`。

## 使用者誤讀風險

- 手機閱讀順序已驗：messages[0] 持倉、messages[1] 未持倉、messages[2] short/evidence。
- 第三則不再同時提供兩個證據入口；Owner 不會先讀到 legacy `📊 策略證據 v20.0` 再讀 `簡短證據摘要`。
- 缺策略樣本時，第三則仍保留 `missing-source / insufficient-data` 與 fail-closed，不會被誤讀成有策略樣本、可買或推薦。

## 質疑與反證

- QA 補直接消費者 probe：用 `formatTelegramMessages()` 產生三則 Telegram，注入 legacy `📊 策略證據 v20.0 ... 狀態碼：missing-source`，按手機順序檢查。
- Probe 結果：
  - `len == 3`
  - order = 持倉、未持倉、簡短證據摘要
  - 第三則 `簡短證據摘要` count = 1
  - 全 messages `📊 策略證據 v20.0` count = 0
  - 第三則含 `missing-source` 與 `fail-closed`
  - 前三則皆含 `v20.4.14`
- Scoped pytest：4 passed，25 warnings。
- 主倉 scoped tests：119 passed，169 warnings。
- `git diff --check`：passed。

## 未測項目

- 未跑 full pytest，符合 `tiny_patch / L1`。
- 未做 production DB read/write、正式 backfill、live Telegram delivery。
- 未驗 `formatTelegramSummary()` standalone 保留 legacy strategy evidence 的旁支；`CHANGELOG.md` 已列為殘留風險，本輪契約只約束 Telegram 第三則 message。

## QA 結論

通過
