# TASK: research_trend_continuation_phase1

## 任務狀態

- task_id: research_trend_continuation_phase1
- 任務類型: research
- 狀態: ready_for_tech
- 任務尺寸判斷: research
- QA 分級建議: L2
- 版本建議: 不升版；本輪不改 Telegram / UI / strategy version
- 本輪目標: 继续执行已写入 TASK.md 的阶段一趋势延续研究任务，新增只读 DB 脚本并输出可重跑研究报告与 RESEARCH.md 高信号结论

## Owner 問題

Owner 要用 production DB 既有資料，只讀驗證「上升趨勢中，縮量回踩 ma5/ma10 不破後，放量站回」是否具備可討論的正 edge。

本輪只回答研究問題：

- pullback continuation 組是否勝率顯著高於 50%
- pullback continuation 組平均收益是否為正
- 相比 extended spike 追高組，是否更值得進入下一階段策略設計

## 使用者可見結果

- 新增只讀 DB 腳本：scripts/research_trend_continuation.py
- 產出可重跑研究報告：stdout 或 repo 既有 research artifact 位置，必須可由 QA 重跑驗證
- 更新 RESEARCH.md 高信號結論：包含資料來源、重跑命令、樣本數、核心 metrics、結論或 blocked reason
- 若 DB 不可讀、必要資料不足或欄位不可可靠映射，結果必須是 blocked / insufficient-data，不得造資料

## 非目標

- 不改產品策略規則
- 不改 services/analysis.py
- 不改 core/condition_engine.py
- 不改 core/generator.py
- 不改 DB schema / RLS / grant / policy / role / index / constraint
- 不做 DB write、backfill、insert、update、delete
- 不 live Telegram
- 不把研究結論接入正式買入建議
- 不做參數最佳化、全市場策略重設或報文改版

## 影響模組

允許影響：

- scripts/research_trend_continuation.py
- RESEARCH.md
- 必要時可新增只讀研究報告 artifact，但須在 CHANGELOG.md 寫明路徑

不得影響：

- services/analysis.py
- core/condition_engine.py
- core/generator.py
- DB schema / migration / write path
- Telegram live delivery path

## 直接消費者

- Owner：閱讀研究結論，決定是否進入下一階段策略任務
- Architect：判斷研究證據是否足以開產品 / 策略設計任務
- Tech：按本 TASK 實作只讀研究腳本與報告
- QA：重跑腳本，驗證只讀約束、輸出契約、fail closed 行為

## 已存在且不得回退的契約

- production DB 或 Owner 指定持久 source-of-truth 才能作為跨日研究資料來源
- local cache、runtime dict、agent 對話、synthetic fixture 不得作為正式研究結論來源
- 缺 DB 憑證、缺表、缺欄位、讀取錯誤或可信度不足時必須 fail closed
- 本輪不得改正式 Telegram 報文、策略輸出、版本常量或 live runner
- 若既有表名 / 欄位名與任務描述不同，Tech 不得猜語意；必須 blocked 或在 CHANGELOG.md 寫明可靠映射證據

## 輸出契約

腳本：

- 路徑：scripts/research_trend_continuation.py
- 行為：只讀 production DB 或 Owner 指定既有持久來源
- 禁止：任何 write SQL / DML / schema mutation / Telegram send
- DB 不可讀時：exit non-zero 或明確 status: blocked

候選定義：

- 趨勢成立：
- close > ma20
- ma5 > ma20
- 近 10 交易日淨漲 > 0
- 回踩：
- 近 1-3 日縮量回踩到 ma5 或 ma10 不破
- low 觸及 ma5 或 ma10 的 ±1%
- volume < 5日均量
- 站回：
- 進場日 close 重新站上 ma5
- vol_ratio >= 1
- extended spike 對照組：
- price / ma20 >= 1.08
- price / ma20 >= 1.15
- price / ma20 >= 1.22

輸出分組：

- pullback_continuation
- extended_spike_1.08
- extended_spike_1.15
- extended_spike_1.22

每組輸出欄位：

- group
- extended_level
- sample_count
- horizon: 1d / 3d / 5d / 10d
- win_rate
- avg_return
- MFE
- MAE
- conclusion: positive / negative / insufficient-data / blocked

完成輸出形狀：

research_trend_continuation
source: production-db-readonly
status: completed

group                    level   n    h1_win h1_avg h3_win h3_avg h5_win h5_avg h10_win h10_avg mfe   mae
pullback_continuation    none    ...  ...    ...    ...    ...    ...    ...    ...     ...     ...   ...
extended_spike           1.08    ...  ...    ...    ...    ...    ...    ...    ...     ...     ...   ...
extended_spike           1.15    ...  ...    ...    ...    ...    ...    ...    ...     ...     ...   ...
extended_spike           1.22    ...  ...    ...    ...    ...    ...    ...    ...     ...     ...   ...

conclusion:
pullback_continuation_edge: positive | negative | insufficient-data
reason: win_rate_5d=..., avg_return_5d=..., sample_count=...

blocked 輸出形狀：

research_trend_continuation
status: blocked
reason: missing-production-db-credentials | source-error | missing-table | missing-column | insufficient-data
no_synthetic_data: true

## 版本契約

- 不升 Telegram / UI / strategy version
- 不改正式報文 header 或 core/generator.py 的版本常量
- RESEARCH.md 可新增本輪日期 2026-06-03 與 task_id
- 若新增研究 artifact，檔名需可追溯 task_id 或日期

## 驗收條件

1. scripts/research_trend_continuation.py 存在，且可用 repo 既有環境重跑。
2. 腳本只讀 DB；QA 必須掃描並反證沒有 write SQL、DML、schema migration、approved write service、Telegram live send。
3. 腳本實作趨勢、回踩、站回、extended spike 對照組定義；若欄位不足無法可靠實作，必須 blocked。
4. 輸出每組 sample_count、1/3/5/10 日 win_rate、avg_return、MFE、MAE。
5. RESEARCH.md 包含資料來源、重跑命令、完成或 blocked 狀態、核心結論。
6. DB 不可讀、表不可讀、欄位不足或樣本不足時，腳本與 RESEARCH.md 都必須 fail closed，不得產生 fabricated metrics。
7. QA 至少補一個負面案例：缺 DB env 或缺必要欄位時，輸出 blocked，而不是 fallback 到 mock / empty positive result。
8. Tech CHANGELOG.md 必須標明覆蓋層級：production source、script output、fixture/helper coverage、未覆蓋項目。

## 範例或 Fixture

正式研究結論不可使用 synthetic fixture。

允許 fixture 僅用於：

- 驗證分類邏輯
- 驗證輸出格式
- 驗證 fail closed 行為

最小 fixture 欄位形狀：

date,symbol,close,low,ma5,ma10,ma20,volume,vol_ma5,vol_ratio,future_return_1d,future_return_3d,future_return_5d,future_return_10d

fixture 結果不得寫成 Owner 研究結論；CHANGELOG.md / QA_REPORT.md 必須清楚區分 fixture coverage 與 production DB coverage。

## 明確禁止事項

- 禁止改 services/analysis.py
- 禁止改 core/condition_engine.py
- 禁止改 core/generator.py
- 禁止 DB write / DML / schema change
- 禁止 live Telegram
- 禁止用 local cache、runtime dict、聊天記錄或 synthetic fixture 當正式研究資料源
- 禁止 DB 不可讀時造資料、補假 metrics 或宣告 positive edge
- 禁止把研究結論直接接入正式買入建議
- 禁止擴大成策略重設、參數最佳化、全市場策略工程或報文改版

## 阻塞條件

- production DB 憑證不可用
- 必要表不可讀
- 必要欄位無法可靠映射
- 既有 outcomes 不存在，且 repo 無可用只讀 outcomes 計算路徑
- 樣本不足以判斷 edge，且無法明確標示 insufficient-data
- 完成任務需要 DB schema 或 write path
- 需要 Owner 確認新資料來源、策略語意或正式產品行為

## QA 分級建議

- QA 分級：L2
- 理由：本輪不改策略 / 報文 / DB schema，但會讀 production source 並產出研究結論；需驗證只讀約束、輸出契約與 fail closed，不可只跑 happy path。

## 本輪停止條件

驗到以下即算本輪完成：

- 腳本可重跑且只讀
- 產出 pullback continuation 與 extended spike 對照 metrics
- RESEARCH.md 有資料來源、重跑命令、樣本數、核心結論或 blocked reason
- QA 反證只讀約束、輸出契約與 fail closed 行為

以下旁支只記待辦，不納入本輪：

- 是否把 positive edge 接入正式策略
- 是否新增 Telegram 報文區塊
- 是否改買入評分、持倉狀態機、停損停利
- 是否補 DB schema、outcomes 表或 production backfill
- 是否做更多參數搜尋、regime 分層或策略最佳化
