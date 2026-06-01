# CHANGELOG:

## 任務尺寸與風險

- 任務尺寸：normal_patch。
- 風險判斷：使用者可見 Telegram 報文 formatter 變更；不改策略 decision、DB write、live delivery。

## 修改內容

- 未持倉卡片若符合「漲停鎖價」且 `volume_ratio < 1.0`，新增提示：`縮量漲停，需開板回測確認，不等同攻擊量`。
- 第三則強勢準備摘要若列出縮量漲停，該標的 action 改為同一風險提示，避免與攻擊量漲停語意等同。
- `volume_ratio >= 1.0` 的漲停鎖價不顯示縮量風險提示。
- 使用者可見版本字串由 `v20.4.22` 升為 `v20.4.23`，並同步版本相關測試期待值。

## 修改檔案

- `core/generator.py`
- `presentation/report.py`
- `tests/test_generator_report.py`
- `tests/test_market_theme_evidence.py`

## 最小改動策略

- 只新增 `low_volume_limit_up_risk_text(data)` 作為窄條件 helper。
- 只在未持倉卡片與強勢準備摘要兩個既有 rendering 點消費 helper。
- 測試只補手機閱讀正反 probe，並同步既有版本字串契約。

## 契約影響

- 使用者可見報文版本：`v20.4.23`。
- 未持倉卡片：新增一行縮量漲停風險提示；原 decision / group / 主狀態不變。
- 第三則強勢準備摘要：縮量漲停標的 action 文案改為風險差異提示；攻擊量漲停維持 `不可追高，待開板回測`。
- 未改 payload shape、DB 寫入、strategy decision、分組規則或 message list 數量。

## 直接消費者同步

- Owner 手機 Telegram 閱讀路徑已同步：低量漲停卡片內可直接看到縮量風險。
- 報文測試 / probe 已同步：
  - `volume_ratio = 0.62` 顯示縮量漲停提示，且仍在 `可準備｜漲停鎖價`。
  - `volume_ratio = 1.71` 不顯示縮量提示，且不被降級。
  - 強勢準備摘要對兩者文案做差異化。

## 未影響模組

- 未改 DB schema / RLS / grant / policy / role。
- 未改 production write / backfill / live Telegram delivery。
- 未改 strategy decision function、RR 計算、持倉加減碼 / 停利 / 停損邏輯。
- 未改可買、可準備、僅追蹤、淘汰分組規則。

## 已跑自檢命令

- `PYTHONPATH=. PYTHONPYCACHEPREFIX=/private/tmp/stock_tech_pycache arch -arm64 .venv/bin/python -m pytest -q tests/test_generator_report.py::GeneratorReportTest::test_low_volume_limit_up_prepare_card_and_summary_show_risk tests/test_generator_report.py::GeneratorReportTest::test_v20_2_4_r3_hot_prepare_overflow_counts_hidden_statuses`：2 passed，13 warnings。
- `PYTHONPATH=. PYTHONPYCACHEPREFIX=/private/tmp/stock_tech_pycache arch -arm64 .venv/bin/python -m py_compile core/generator.py presentation/report.py tests/test_generator_report.py tests/test_market_theme_evidence.py`：passed。
- `PYTHONPATH=. PYTHONPYCACHEPREFIX=/private/tmp/stock_tech_pycache arch -arm64 .venv/bin/python -m pytest -q tests/test_generator_report.py tests/test_market_theme_evidence.py`：134 passed，201 warnings。
- `git diff --check`：passed。

## 殘留風險

- 未跑 full pytest；本輪自檢限於 formatter 與版本 / evidence 相關測試。
- warnings 皆為既有第三方 deprecation / Python 版本警告，非本 patch 新增失敗。

## 旁支待辦

- 全部分組語意清理、漲停策略重設、量能門檻重定義不在本輪。
- 持倉標的行動邏輯、DB 持久化、production runner 流程不在本輪。
