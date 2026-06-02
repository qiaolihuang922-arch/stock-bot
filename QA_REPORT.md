# QA_REPORT: fix_market_theme_evidence_gate_v20_4_31

## 測試範圍

- 任務尺寸 / QA：normal_patch / L2。
- 驗證範圍：8 日 confirmed_trend 不再被 15 日 gate 阻擋；per-stock 缺 market_theme 時 fallback report-level evidence；英業達卡片證據不再顯示不適用；strategy evidence version filter 未回歸；VERSION 不 bump。
- 未執行：full pytest、production read-only smoke、live Telegram、DB write、backfill。

## 關聯風險掃描

- `core/generator.py` 新增 `_market_theme_confirmed_trend_eligible()`，使用 confirmed + source_status available + `evidence_trend.status == confirmed_trend`，未再使用 `observed_days >= 15` gate。
- `_manifest_status("ready")` 正規化為 available，測試 fixture 的 `source_status: ready` 可被消費。
- per-stock market_theme 缺失時 fallback `report_context["market_theme_evidence"]`；source-error / missing-source 仍 fail closed。
- `services/strategy_evidence.py::load_strategy_evidence_summary()` 無 current VERSION filter；未見 `daily_signal_snapshot.eq("version", "v20.4.31")`。
- `core/generator.py` 仍為 `VERSION = "v20.4.31"`，未見 `v20.4.32`。

## 跨區塊語意一致性

- 8 日 confirmed_trend 可 decision eligible：通過。
- per-stock 缺 market_theme fallback report-level：通過。
- 英業達卡片顯示 +X evidence，不是 `不適用`：通過。
- strategy version filter remains removed：通過。
- VERSION remains v20.4.31：通過。

## 使用者誤讀風險

- QA 補直接消費者 card probe：英業達持倉、per-stock 缺 market_theme、report-level 8 日 confirmed evidence。
- 產出卡片包含：`數據：新倉 RR：不適用（既有持倉）｜綜合 53｜技術 49｜證據 +8%（supporting）｜V 1x`。
- 卡片不包含 `證據：不適用`。

## 質疑與反證

- Targeted L2 tests：4 passed，13 warnings。
- `git diff --check`：passed。
- Direct card probe：passed。
- Strategy summary mock calls 不含 `("daily_signal_snapshot", "eq", ("version", "v20.4.31"), {})`，且 v20.4.5 fixture 可進入 summary。
- VERSION scan：未 bump。

## 未測項目

- 未跑 full pytest。
- 未做 production read-only smoke、live Telegram、DB write、backfill。
- 未驗全量 market/theme cleanup、逐股 mapping 品質、D2/B5 rendered message；不在本 TASK/diff 範圍。

## QA 結論

通過
