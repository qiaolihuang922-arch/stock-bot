# TASK: 建立策略層 / 顯示層 / 服務層 import gate

## 任務狀態

- task_id: import-boundary-gate-20260601
- 任務類型: process
- 狀態: qa_passed
- 版本建議: 不升 VERSION
- QA 分級建議: L2
- 本輪主問題: 只建立可重跑的靜態 import 邊界檢查與高信號模組地圖摘要，不做架構重設或全量清理。

## Owner 問題

Owner 認為文件與模組邊界已失控，本輪要防止繼續亂新增檔案與反向依賴：

- presentation / 顯示層不得反向 import strategy writer / DB write 相關服務。
- strategy / core / services 不得 import presentation。
- 既有 main / notifier runner 可照舊。
- core/generator 作為過渡 bridge 可 import presentation.report，但必須在模組地圖標成 transitional bridge。

## 使用者可見結果

本輪沒有 Telegram / UI / 報文可見變更。

使用者可見結果是 repo 內新增可重跑 gate：

- 測試失敗時能指出 offending file 與 offending import。
- 固定文件中有簡短分層地圖摘要，讓後續任務知道哪些 import 是禁止、哪些是暫時允許。
- 不新增新的業務模組，不新增新的架構文檔。

## 非目標

- 不改 Telegram 報文內容、排序、標題、emoji、文案或手機閱讀形狀。
- 不升 VERSION，除非現有測試機制強制要求；若需要升版需先 blocked 交回 Architect。
- 不做 DB schema / RLS / grant / policy / role / index / constraint 變更。
- 不新增 production write、backfill、live Telegram delivery。
- 不重構 strategy / presentation / services 實作。
- 不新增新的架構文檔。
- 不新增新的業務模組。
- 不做全 repo 清理或刪檔分類；旁支清理問題只記入既有固定文件待辦。

## 影響模組

優先影響：

- tests/test_generator_report.py
- 或 tests/test_workflow_runtime_config.py

文件摘要可影響：

- CURRENT_STATE.md
- CLEANUP_PLAN.md
- DISPATCH.md

被 gate 掃描但不應被功能性改寫的模組：

- presentation / report 相關 Python files
- services 相關 Python files
- core / strategy 相關 Python files
- main / notifier runner 相關 Python files

## 直接消費者

- Tech: 依本卡在既有 test file 中加 AST / import graph gate。
- QA: 用靜態 fixture 或臨時偽造違規 import 反證 gate 會失敗。
- Architect: 用測試結果與 git 狀態收口，不依賴聊天紀錄。
- 後續開發者: 在 PR / runner 測試中立即看到 import 邊界違規。

## 已存在且不得回退的契約

- main / notifier runner 既有 import path 與 runtime 行為不得因 gate 被禁止。
- core/generator 可過渡 import presentation.report，但文件摘要必須明確標為 transitional bridge。
- Telegram / report 使用者可見輸出不得變更。
- DB write / Supabase client 既有 production 行為不得被本輪觸碰。
- 既有固定文件 8 份不得刪除；本輪只允許在既有固定文件加入高信號摘要。
- 若 Tech 發現上述契約與實際 repo 衝突，必須 blocked，不得自行擴大規則或重構。

## 輸出契約

### Import gate 掃描範圍

- 掃描 repo 內 relevant Python files。
- 可排除 .venv、cache、build artifact、generated artifact。
- 測試必須使用 AST 或明確 import graph parser，不得只用脆弱全文 grep 作最終判斷。

### 禁止規則

1. presentation 層不得 import：
- services.signal_store
- services.strategy_evidence.get_supabase_client
- services.strategy_evidence.record_daily_signals
- services.strategy_evidence.record_strategy_evidence
- services.strategy_evidence.record_daily_snapshots
2. services 與 core 策略模組不得 import presentation：
- 禁止 import presentation...
- 禁止 from presentation... import ...
3. 允許例外：
- main / notifier runner 可照舊。
- core/generator 可 import presentation.report，但此例外必須集中列在 gate allowlist，並在模組地圖摘要標成 transitional bridge。

### 失敗輸出契約

測試失敗時至少包含：

- offending file path
- offending import module 或 imported symbol
- violated boundary rule name

示例形狀：

Import boundary violation: presentation_db_write_import
file=presentation/report.py
import=services.strategy_evidence.record_strategy_evidence

### 文件摘要契約

只在既有固定文件寫高信號摘要，不新增架構文檔：

- strategy/core/services -> 不得 import presentation
- presentation -> 不得 import DB writer / signal_store / strategy_evidence writer
- main/notifier runner -> allowed integration edge
- core/generator -> transitional bridge to presentation.report

## 驗收條件

1. Tech 開工前記錄 git clean baseline：
- git status --short
- 若 baseline dirty 且與本任務無關，需在交付中標明，不得覆蓋或回退。
2. Gate 可重跑：
- 使用既有 test file 增加測試，優先 tests/test_generator_report.py 或 tests/test_workflow_runtime_config.py。
- 不新增新的 test file，除非既有兩個檔案技術上不可用；若不可用需 blocked 說明。
3. Gate 覆蓋禁止 import：
- presentation import services.signal_store 會 fail。
- presentation import listed services.strategy_evidence writer/client symbols 會 fail。
- services/core strategy import presentation 會 fail。
- main/notifier runner 不被誤殺。
- core/generator -> presentation.report 只作 allowlisted transitional bridge。
4. 失敗訊息可定位：
- QA 或開發者可從 failure output 看到 offending file/import/rule。
5. 文件摘要完成：
- 只更新 CURRENT_STATE.md / CLEANUP_PLAN.md / DISPATCH.md 中必要高信號摘要。
- 不新增新的架構文檔。
6. 無產品可見變更：
- Telegram / UI / report message snapshot 不應因本輪變更改變。
- VERSION 不變。
7. QA 需補反證：
- 使用靜態 fixture、tmp module、monkeypatch 掃描集合，或等價方式偽造至少一個違規 import。
- 證明 gate 能抓到違規並輸出 offending file/import。
- QA 不得做 production write 或 live Telegram。

## 範例或 fixture

可接受 QA / test fixture 形狀：

# fake file path: presentation/fake_report.py
from services.strategy_evidence import record_strategy_evidence

預期：

Import boundary violation: presentation_db_write_import
file=presentation/fake_report.py
import=services.strategy_evidence.record_strategy_evidence

另一個 fixture：

# fake file path: services/fake_service.py
from presentation import report

預期：

Import boundary violation: strategy_or_service_imports_presentation
file=services/fake_service.py
import=presentation.report

允許例外 fixture：

# real or fake bridge path: core/generator.py
from presentation import report

預期：

allowed transitional bridge: core/generator -> presentation.report

## 明確禁止事項

- 禁止新增新的業務模組。
- 禁止新增新的架構文檔。
- 禁止把本輪擴成全量依賴重構。
- 禁止改 Telegram 可見報文。
- 禁止升 VERSION，除非 blocked 回報後另行確認。
- 禁止 production DB write / backfill / schema 變更。
- 禁止 live Telegram delivery。
- 禁止用 local cache、聊天紀錄或 runtime dict 當跨日 source-of-truth。
- 禁止為了讓 gate 通過而移除既有 main / notifier runner 合法路徑。
- 禁止把 core/generator bridge 靜默視為永久合法；必須標 transitional bridge。

## 阻塞條件

- 找不到可穩定辨識 presentation / services / core strategy Python files 的 repo 結構。
- 既有 test file 無法承載 gate，且新增 test file 又違反 Owner 限制。
- 現有合法 import 已違反本卡禁止規則，且無法判斷應 allowlist 還是重構。
- 需要改 DB schema、production write path、Telegram live delivery 才能驗收。
- 需要新增架構文檔或業務模組才可完成。
- 測試環境缺 pytest / dependency 且無法補足。

## 本輪停止條件

完成以下即停止：

- 既有 test file 中有可重跑 import boundary gate。
- Gate 對指定禁止 import 能 fail，對 main/notifier 與 core/generator transitional bridge 不誤殺。
- 失敗輸出含 offending file/import/rule。
- 固定文件中有簡短模組地圖摘要。
- QA 用偽造違規 import 或靜態 fixture 反證 gate 有效。
- 無 Telegram / VERSION / production write 變更。

不納入本輪、只記待辦：

- 清理所有歷史亂檔。
- 移除 core/generator -> presentation.report bridge。
- 重畫完整架構圖。
- 拆分 strategy / services / presentation 模組。
- 修復 gate 掃描外發現的其他架構味道。
