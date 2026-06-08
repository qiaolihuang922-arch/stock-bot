# QA_REPORT: telegram_mobile_first_preface_20260608

## 測試範圍
- 手機首屏 preface 是否出現在第 1 則 `【持倉標的】` 的第一張卡片前。
- 原 Telegram message order 是否維持：持倉 -> 未持倉 -> 簡報 -> 未來30日。
- notifier reply markup 是否仍依既有契約處理。
- official `generate_report(dry_run=True)` 是否能產出最終報文 artifact。

## 關聯風險掃描
- 未重排 message list，避免破壞 `send_many` 最後訊息附 inline keyboard 的契約。
- preface 使用既有 renderer 資料，不新增 DB/source 依賴。
- 無策略 decision / RR / DB write path 變更。

## 跨區塊語意一致性
- 第 1 則首屏：`新倉：無有效進場`。
- 第 3 則簡報：`新增有效進場：無`。
- 第 1 則首屏：`今日買入：5 檔已全部轉入風控`。
- 第 3 則簡報：`今日已買 5（已風控 5）` 與 `今日買入後風控：5 檔`。
- 未持倉在首屏明確標成第 2 則僅追蹤/淘汰，不當作買入清單。

## 使用者誤讀風險
- 原風險：手機先看到長持倉卡，可能晚一步才知道新倉無有效進場。
- 修正後：第 1 則開頭先回答新倉、今日買入、持倉風控與未持倉閱讀方式。
- 殘留：完整細節仍在多則訊息內，未做大幅重排；若 Owner 要「簡報第一則」，需另開任務評估 notifier/reply markup 契約。

## 失敗標本反證
- Owner 等價標本: 2026-06-08 official dry-run message list。
- 反證結果:
  - `MESSAGES 4`
  - message 1 begins `【06/08 盤後｜v20.4.48】` / `【持倉標的】` / `【先看結論】`
  - message 1 contains `新倉：無有效進場` and `今日買入：5 檔已全部轉入風控`
  - message 3 remains `🧾 v20.4.48 簡報`

## 質疑與反證
- 質疑: 加 preface 會不會把未持倉淘汰誤導成推薦？
  - 反證: preface 寫 `未持倉：僅追蹤/淘汰見第 2 則，不當作買入清單`。
- 質疑: message order 是否被改壞？
  - 反證: focused order test passed；dry-run 仍為 4 messages，前 3 則順序不變。
- 質疑: live TG 是否被觸發？
  - 反證: 只跑 `dry_run=True`、pytest、py_compile；無 live delivery。

## 未測項目
- 未做 live Telegram delivery。
- 未把完整歷史 `tests/test_generator_report.py` 修到全綠；本次重跑結果仍有 34 個非本輪範圍的既有策略/漏斗期望失敗。
- 未修 CAO TUI runner prompt automation gap。

## QA 結論
conditional pass

本輪手機首屏報文優化在 focused tests 與 official dry-run artifact 下通過；由於完整歷史報文 suite 仍非乾淨基線，結論不得升格為全量報文系統通過。

## 測試範圍

- 任務：`cao_wsl_deployment_repair_20260608`。
- 範圍：本地 WSL CAO runner deployment readiness。
- 未跑 live Telegram。

## 關聯風險掃描

- Windows 原生 CAO 不可用，因 CAO Python package 使用 Unix-only `fcntl`。
- WSL 原先卡住是首次 distro 註冊與舊 Windows path worktree；已重建 WSL worktree。
- repo scripts 原本 CRLF 與 macOS-only npm command 會讓 WSL 部署失敗。

## 跨區塊語意一致性

- `DEPLOYMENT.md` 的 bootstrap / ensure services 路徑現在可在 WSL 中落地。
- `README.md` 的 CAO API/UI URL 已實際可連。
- `AGENTS.md` 要求的 Architect runner 入口下輪可改由 WSL 執行。

## 使用者誤讀風險

- CAO 服務可用不等於 Telegram 已發送。
- 本輪沒有 live delivery，也沒有重跑 PM/Tech/QA 修產品。

## 失敗標本反證

- `fcntl` failure：改走 WSL Linux CAO。
- CRLF shell failure：新增 `.gitattributes` 並正規化 CAO shell scripts。
- macOS `arch -arm64 npm` failure：`ensure_cao_services.sh` 改為 `NPM_BIN` / `npm`。
- WindowsApps `codex` permission failure：Linux ELF binary 已複製到 `/root/.local/bin/codex-real`，wrapper 可執行。

## 質疑與反證

- WSL bootstrap 全 `[ok]`。
- WSL ensure services 成功。
- Windows HTTP probe：API docs 200，UI 200。
- WSL Codex wrapper version probe passed。

## 未測項目

- 未跑完整 `run_architect_task.sh auto`。
- 未測 CAO agent 實際完成 PM / Tech / QA 的 end-to-end handoff。
- 未做 live Telegram。

## QA 結論

通過。

本輪已補齊 deployment readiness；下一輪可從 WSL 以正式 Architect entry 啟動，但仍需對具體任務另行 PM -> Tech -> QA 驗收。
