# TASK: telegram_denoise_and_deployment_docs_20260608

## 任務狀態
- task_id: `telegram_denoise_and_deployment_docs_20260608`
- 任務類型: `normal_patch + process_docs`
- 狀態: `qa_passed`
- 版本建議: `v20.4.49`
- QA 分級: `L2`

## Owner 問題
Owner 明確要求：
1. 刪除 `【先看結論】`，因為沒有實際價值。
2. 做真正降噪，不是無腦去重；每檔重複可以接受，但每檔內容要更有決策價值。
3. 清理無效文件。
4. 優化流程與部署文檔，統整部署至今遇到的問題。

## 使用者可見結果
- 第 1 則持倉訊息不再插入 `【先看結論】` preface。
- 盤後持倉卡片保留每檔獨立決策，但移除審計型流水欄位：
  - 保留：倉位、風控、盤面、今日買入短句、決策、原因、下一步、價格。
  - 移除盤後卡片中的 `條件`、`數據`、歷史流水。
- 盤後未持倉淘汰卡片保留每檔 blocker 與再評估路徑，但移除診斷型噪音：
  - 保留：標題、買點、卡關主因、量化差距、解鎖/依據、明日觸發、價格。
  - 移除淘汰卡中的盤面、長原因、數據、歷史流水。
- 部署文檔改成目前 Windows + WSL 實際可用流程。
- 清理 `.cao_agent_context/` runtime output。

## 非目標
- 不改策略、RR、買賣決策、持倉狀態機。
- 不改 DB schema/RLS/grant/policy/role/index/constraint。
- 不做 live Telegram delivery。
- 不修完整歷史報文 suite 的既有 34 個非本輪失敗。

## 影響模組與直接消費者
- `presentation/report.py`: Telegram 卡片 renderer。
- `core/generator.py`: 使用者可見版本與今日買入短句。
- `tests/test_generator_report.py`: focused report regression。
- `tools/cao_agent/DEPLOYMENT.md`, `tools/cao_agent/README.md`: 部署與流程文檔。
- 固定 handoff MD：`TASK.md`, `CHANGELOG.md`, `QA_REPORT.md`, `DISPATCH.md`, `CURRENT_STATE.md`, `RESEARCH.md`, `CLEANUP_PLAN.md`。

## 輸出契約
- `messages[0]` 仍為 `【持倉標的】`。
- `messages[0]` 不包含 `【先看結論】`。
- `messages[2]` 仍為 `🧾 v20.4.49 簡報`。
- message order 不變：持倉 -> 未持倉 -> 簡報 -> 未來30日。
- dry-run only，不觸發 Telegram send。

## 版本契約
使用者可見報文版本升為 `v20.4.49`。

## 驗收條件
- focused pytest 覆蓋：
  - 無 `【先看結論】`。
  - 盤後持倉卡不含 `條件` / `數據`。
  - 盤後未持倉淘汰卡不含盤面 / 長原因 / 數據。
  - message order 與 notifier 契約維持。
- `py_compile` 通過。
- official `generate_report(dry_run=True)` 產生 4 則，且第 1 則不含 preface。

## 失敗標本與驗收路由
- Owner 樣本：2026-06-08 v20.4.48 dry-run 完整報文。
- 驗收路由：official generator `generate_report(dry_run=True)` 最終 message list。

## 明確禁止事項
- 禁止 live Telegram delivery。
- 禁止 production DB write / schema change。
- 禁止用「去重」取代降噪判斷。

## 阻塞條件
- official dry-run 無法產生 message list。
- 降噪後卡片失去每檔主決策或不可買原因。
