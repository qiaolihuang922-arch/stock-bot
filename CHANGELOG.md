# CHANGELOG: telegram_denoise_and_deployment_docs_20260608

## 修改內容與修改檔案
- `presentation/report.py`
  - 移除 `_mobile_first_read_preface(...)` 與第 1 則 preface 插入。
  - 盤後持倉卡片移除 `條件`、`數據`、歷史流水，保留每檔決策與風控原因。
  - 盤後未持倉淘汰卡片移除盤面、長原因、數據、歷史流水，保留 blocker / gap / trigger / price。
- `core/generator.py`
  - 版本升至 `v20.4.49`。
  - 今日買入盤後說明短句化。
- `tests/test_generator_report.py`
  - 將 preface 測試改成盤後降噪回歸。
  - 同步版本字串。
- `tools/cao_agent/DEPLOYMENT.md`
  - 重寫為 Windows + WSL 實際部署流程。
  - 補齊已遇到的 `fcntl`、CRLF、macOS npm、Codex auth/trust、TUI automation gap。
- `tools/cao_agent/README.md`
  - 壓縮成 runner 入口、標準 WSL env、日常命令、安全邊界。
- `.cao_agent_context/`
  - 已移除本地 runtime output。

## 契約影響
- message list 順序不變。
- 使用者可見報文版本變為 `v20.4.49`。
- 卡片內容更短，但每檔仍保留主決策與不可買/風控原因。
- 無 DB write、無 live Telegram delivery。

## 自檢命令與結果
- `python -m py_compile core/generator.py presentation/report.py tests/test_generator_report.py tests/test_trend_continuation.py tests/test_notifier.py` -> passed。
- `python -m pytest tests/test_generator_report.py::GeneratorReportTest::test_afterhours_cards_are_denoised_without_first_read_preface tests/test_generator_report.py::GeneratorReportTest::test_v20_4_12_complete_message_list_orders_holdings_unheld_summary_evidence_details tests/test_notifier.py -q` -> 5 passed。
- `generate_report(dry_run=True)` -> 4 messages, header `v20.4.49`, no live Telegram delivery。

## 覆蓋層級
- formatter: focused `formatTelegramMessages` regression covers holding/unheld/summary message route。
- official generator: `generate_report(dry_run=True)` dry-run artifact covers Owner sample route。
- process docs: deployment docs manually checked against current WSL path。

## 殘留風險
- CAO/Codex TUI automation prompt/send gap 尚未修。
- 完整歷史 report suite 不是乾淨基線，另列 cleanup / baseline follow-up。
