# QA_REPORT:

## 測試範圍

- 依據：`TASK.md`、`CHANGELOG.md`、git status、git diff、`core/generator.py`、`core/market_theme_evidence.py`、`tests/test_market_theme_evidence.py`、`tests/test_generator_report.py`、`tests/test_notifier.py`。
- 實測命令：
  - `TMPDIR=.qa_tmp PYTHONPATH=.qa_tmp:. PYTHONDONTWRITEBYTECODE=1 arch -arm64 .venv/bin/python -m pytest -p no:cacheprovider tests/test_market_theme_evidence.py tests/test_generator_report.py tests/test_notifier.py`
  - 結果：`59 passed, 21 warnings`
- QA 補充反證：
  - 用 dict 型 `market_summary`，內含 `strategy_evidence_summary: market_theme_evidence:confirmed｜AI 主線偏多` 與未成立買點，直接走 `formatTelegramMessages()`。
  - 結果：summary 第一屏顯示 `v20.1.0`、`weak｜來源不足｜只追蹤`、不可買，且未出現 `confirmed`、`AI/電子供應鏈偏多`、今日可買。

## 關聯風險掃描

- 直接消費者已檢查：
  - `formatTelegramSummary()`：會在市場狀態後插入 market theme lines。
  - `formatTelegramMessages()`：summary 仍是最後一則 message，符合 Owner 手機先看最後 summary 的路徑。
  - `services/notifier.py::send_many()`：payload shape 未改，測試確認最後一則 summary 原樣送出。
  - DB / migration：本輪未新增 `.sql` 或 migration 檔。
  - strategy / watchlist / scheduler：本輪 diff 未觸及 `services/analysis.py`、watchlist、scheduler。
- 可吸收候選必須包含：
  - tracked 修改：`core/generator.py`、`tests/test_generator_report.py`、`tests/test_notifier.py`、`CHANGELOG.md`。
  - 新檔：`core/market_theme_evidence.py`、`tests/test_market_theme_evidence.py`。
- 若只吸收 tracked diff，`core/generator.py` 會 import 不存在的 module；Architect 已將兩個新檔納入同一變更集。

## 跨區塊語意一致性

- Owner 手機閱讀順序檢查：
  - Header 為 `【05/28 盤中｜v20.1.0】`，符合版本契約。
  - 市場主題區在 source summary 與今日結論前出現。
  - report-derived only 顯示：
    - `市場主題：AI/電子供應鏈`
    - `狀態：weak｜來源不足｜只追蹤`
    - `行動：不可買，等 structured evidence 補強`
  - 後續今日結論、主線、執行、新倉仍維持 `無有效進場 / 不追高 / 僅追蹤` 語意。
  - confirmed 主題但個股買點未成立的測試覆蓋顯示 market theme confirmed，但未把個股列成今日可買。

## 使用者誤讀風險

- 已反證上一輪阻塞風險：legacy 字串或 report-derived input 不能讓 Owner 誤讀為 confirmed bullish。
- 殘留風險：
  - 這一輪完成的是 dry-run contract 與 formatter 呈現，production `generate_report()` 尚未接 structured provider。
  - 真實預設路徑目前通常只會 absent / weak，不會自動 confirmed。
  - 若後續要 production confirmed，需要接 structured market_state / strategy evidence provider；若要持久化歷史，會進入建表決策點。

## 質疑與反證

- PM 是否漏需求：TASK 已列 source family contract、Telegram summary contract、版本契約、直接消費者與負面 fixtures，足以驗收。
- Tech 是否漏同步：formatter、notifier 測試與 header 已同步；新檔已被列為必須吸收範圍。
- 測試是否能證明沒有破壞直接消費者：helper / formatter / notifier 測試通過；QA 另補 dict 型 `market_summary` 反證，避免 legacy confirmed 字串藏在 dict 中造成誤判。
- QA 主動找到指定清單之外風險：git diff --stat 遺漏 untracked 新檔，已要求 Architect 吸收時納入。

## 未測項目

- 未跑 full pytest：本輪 QA 分級為 L2，且 TASK 限定 helper / formatter / notifier 相關驗證。
- 未跑 replay/backfill dry-run、live Telegram、live Supabase write：TASK 明確禁止或非目標。
- 未驗證真正 structured provider 接線：`CHANGELOG.md` 已聲明 production 尚未接線，本輪只驗 helper contract 與 formatter 呈現。

## QA 結論

conditional pass

功能與使用者可見語意驗證通過；條件是 Architect 必須把 `core/market_theme_evidence.py` 與 `tests/test_market_theme_evidence.py` 兩個新檔納入候選 diff。Architect 已按此條件吸收。
