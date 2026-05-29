# RESEARCH.md

本文件保存最新研究任務的高信號摘要，不保留完整聊天紀錄。

## Latest Research

- task_id: `20260529_145601_6802_online_research_pair`
- 日期：2026-05-29
- 狀態：已吸收並轉為 `v20.3.1` data-authenticity fail-closed 任務。
- 來源輸出：`.cao_agent_context/outputs/20260529_145601_6802_online_research_pair.md`

## Question

Owner 要求檢查目前策略 / 報文 / 證據鏈 / 行情 / 持倉 / 回測 / DB 相關 runtime 是否仍在拿假資料。DB 已有資料後，production runtime 必須拒絕 fake/mock/dummy/sample/synthetic/default/hardcoded fallback；缺真實來源時 fail closed。

## Findings

- Online research agent 無法讀完整 repo，因此不能獨立完成逐 path / function / rg / import-chain 證據表。
- 需求成立，必須進 PM -> Tech -> QA，而不是用口頭結論宣告乾淨。
- 高風險候選：
  - `services/position_store.py` 持倉來源 fallback。
  - `services/position_store.py` 今日 `position_events` 來源錯誤被當成 0 event。
  - `core/market_theme_evidence.py` runtime watchlist breadth fallback 被誤讀為市場 / 題材證據。
  - dry-run / backfill synthetic fixture 必須留在 dry-run gate，不可進 production runtime。
- 允許保留：
  - tests fixture。
  - 明確 dry-run 且禁止 live write 的 synthetic replay。
  - 真實來源重試，例如 TWSE / Yahoo real-source retry，不算 fake data。

## Outcome

- 已開發並驗證 `v20.3.1`：
  - positions 缺來源不再回 0 股 fallback。
  - position_events source-error / missing-source 不再回全 0 event summary。
  - runtime watchlist breadth fallback 降為非交易診斷，不稱市場證據、不 weak/runtime、不 confirmed。
  - 缺來源時 Telegram / CLI report 先 fail closed，不產生可買 / 持倉 / 今日交易 / evidence confirmed 結論。
- 驗證：
  - `tests/test_market_theme_evidence.py tests/test_generator_report.py tests/test_position_store.py tests/test_notifier.py`：`88 passed, 13 warnings`。
  - full pytest：`162 passed, 13 warnings`。
  - `git diff --check` 通過。

## Next

- 若要進一步 production 化證據鏈，需要 Owner 先確認是否建 DB table / cache、接 market_index / sector_index、接 external provider 或持久化 evidence。
- 若要禁止 dry-run synthetic replay 本身，也需另開任務；目前只禁止它進 production runtime 或 live write。
