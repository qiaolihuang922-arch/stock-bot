# TASK: 05/31 假日报文 execution memory 与 evidence 日期显示修正

## 任務狀態

- task_id: risk_patch_20260531_holiday_report_execution_memory_evidence_dates
- 任務尺寸: risk_patch
- 狀態: ready_for_tech
- 版本建議: 使用者可見假日报文文案 / 语义会变化，需同步报文 header / version 常量；不得回退既有版本字串。
- QA 分級建議: L2；若 Tech 触及 DB write path、持仓状态机核心或策略 decision 核心，升 L3。
- 流程要求: 必须 PM -> Tech -> QA；Owner 的“继续”只代表启动流程，不授权跳过 Tech / QA 或直接改代码。

## Owner 問題

继续执行现有任务，不重新定义目标。当前 2026-05-31 假日报文存在四个同一报文链路问题：

1. 英业达 2356 已在 production DB 于 2026-05-29 执行部分停利，但 05/31 假日报文仍重复输出「第二段停利 本次建议 56 股」，并进入明日计划。
2. 假日 evidence 日期显示 same_trade_date，容易让用户误读为证据来自 05/31 假日当天，或 evidence 日期无效。
3. market/theme trend lookback 被默认 row limit 压缩，导致五月 production history 存在时仍像只有近 2 个证据日。
4. 策略證據 v20.0「样本 0」与 market/theme production evidence 混在一起，容易误读为 market/theme evidence 无效。

## 使用者可見結果

Owner 在手机阅读 2026-05-31 假日报文时应看到：

- 2356 已识别 production latest trading day execution memory，不再重复建议第二段停利 56 股。
- Summary、持仓卡片、今日交易、持仓风控、明日计划、索引对 2356 的主行动一致。
- market/theme evidence 显示实际可解释日期，例如 latest_trade_date=2026-05-29、previous_trade_date=...、lookback_range=...，不得只显示 same_trade_date。
- 五月 trend 若有 production history，应显示足够 lookback 或明确资料范围；不得把 row limit 结果包装成完整趋势。
- v20.0「样本 0」只描述 strategy sample 层，不否定 market/theme production confirmed evidence。

## 非目標

- 不放宽买点、不新增买入机会、不调整策略阈值。
- 不重设停利 / 停损策略、不重写整体持仓状态机。
- 不新增 / 修改 DB schema、RLS、grant、policy、role、index、constraint。
- 不做 live Telegram delivery。
- 不使用假数据伪造 production confirmed。
- 不做全量历史回补、资料清理或整体报文改版。
- 不处理其他股票潜在重复建议问题，除非同一修复路径自然覆盖且不扩大契约。

## 影響模組

Tech 自行定位实际文件，但范围限于：

- 假日报文生成流程。
- 持仓 / 今日交易 / 明日计划 / 索引 message list 或 payload 组装。
- production DB execution memory 读取与 latest trading day fallback。
- market/theme evidence 日期显示。
- market/theme trend lookback 查询或展示逻辑。
- v20.0 strategy evidence 文案分层。

不得扩大到策略核心阈值、DB 写入流程或 live delivery。

## 直接消費者

- Owner 手机 Telegram 假日报文读者。
- Telegram report renderer / message list consumer。
- Summary / 索引区块。
- 持仓卡片区块。
- 今日交易区块。
- 持仓风控区块。
- 明日计划区块。
- evidence chain / production confirmed 展示区块。

## 已存在且不得回退的契約

若 Tech 无法确认以下契约，必须 blocked，不得自行假设：

- production DB 是跨日 execution memory 的 source-of-truth；local cache、runtime dict、agent 对话不得作为跨日记忆。
- 缺 production source、读取失败、字段不足或可信度不足时必须 fail closed，显示 missing-source / source-error / insufficient-data，不得静默输出重复卖出数量。
- 同一持仓在同一份报文只能有一个主行动。
- 假日报文原有分组结构应保留，实际名称以现有报文为准。
- 无可买时不得使用类似推荐文案，应显示「新仓：无有效进场」或等价不可买表述。
- 使用者可见报文变更需同步版本字串 / header 常量。
- market/theme production confirmed 状态不得被 v20.0 strategy sample 0 覆盖。

## 輸出契約

### 1. 2356 execution memory 去重

对 2026-05-31 假日报文，若 production DB 可证明：

- latest trading day: 2026-05-29
- symbol: 2356
- position_events: -112、-75
- positions.remaining_quantity = 225
- positions.realized_profit_taken_ratio = 0.5

则报文必须：

- 不输出「第二段停利 本次建议 56 股」。
- 不在明日计划列出 2356 待执行第二段停利。
- 可显示「已完成部分停利 / 第二段已执行至 50% / 剩余持仓进入风控观察」等同义语义。
- 若 execution memory 缺失或矛盾，必须 fail closed，不得输出明确重复卖出数量。

### 2. 跨区块一致性

同一份报文中，2356 在 Summary、卡片、今日交易、持仓风控、明日计划、索引不得同时出现「已停利」与「明日再卖第二段」的冲突语义。

### 3. evidence 日期显示

market/theme evidence 若为 production confirmed，用户可见字段必须包含实际日期来源，例如：

- latest_trade_date
- previous_trade_date
- evidence_trade_date
- lookback_range

不得只显示 same_trade_date。若 report date 是假日，文案需说明使用最近交易日证据。

### 4. trend lookback

market/theme trend 不得被默认 row limit 压成近 2 个证据日而无说明。

- 若 production 五月历史存在，应用足够 lookback 呈现可用趋势。
- 若只取得部分日期，应显示可用范围或资料不足原因。
- 不得把「只查到 2 笔」写成完整五月趋势。

### 5. v20.0 样本 0 分层

v20.0「样本 0」只代表 strategy evidence / strategy sample 层无样本或无命中；不得让用户误解为 market/theme production evidence 无效。

## 手機閱讀路徑與示例輸出形狀

手机阅读路径：

1. Summary：确认新仓、持仓优先处理项、不可行动项。
2. 持仓卡片：确认 2356 当前主行动。
3. 今日交易：确认 2026-05-29 已卖出 -112、-75 被识别。
4. 持仓风控：确认剩余 225 股进入风控观察或续抱逻辑。
5. 明日计划：确认没有 2356 第二段停利 56 股。
6. 索引：确认索引不重复列出 2356 待卖。

示例形状，非强制逐字：

持仓｜2356 英业达
主行动：已完成部分停利，剩余 225 股进入风控观察
执行记忆：production latest_trade_date=2026-05-29，已卖出 -112、-75，realized_profit_taken_ratio=0.5
明日计划：不新增第二段停利单；仅观察剩余持仓风控线

市场 / 题材证据
状态：production confirmed
证据日期：latest_trade_date=2026-05-29；previous_trade_date=YYYY-MM-DD
趋势范围：2026-05 可用交易日 N 日
策略证据 v20.0：策略样本 0；不影响市场 / 题材证据有效性

## 驗收條件

### 必測案例 1: 2356 假日 latest trading day execution memory

Fixture / production-like 条件：

- report date: 2026-05-31
- latest trading day: 2026-05-29
- symbol: 2356
- position events: -112、-75
- remaining quantity: 225
- realized profit taken ratio: 0.5

期望：

- 报文不出现「第二段停利 本次建议 56 股」。
- 明日计划不出现 2356 待卖第二段停利# TASK: 05/31 假日报文 production execution memory 与 evidence 日期显示修正

## 任務狀態

- task_id: risk_patch_20260531_holiday_report_execution_memory_evidence_dates
- 任務尺寸判斷: risk_patch
- 狀態: ready_for_tech
- 版本建議: 使用者可見假日报文有文案 / 语义变化，需升版或同步现有报文 header / version 常量；不得回退既有版本字串。
- QA 分級建議: L2；若 Tech 触及 DB write path、持仓状态机核心、策略 decision 核心或 production 写入路径，则升 L3。
- 本輪原則: 继续执行现有 TASK 目标，不重新定义目标，不扩大为策略重设、全量清理或报文大改版。

## Owner 問題

Owner 要修复 2026-05-31 假日报文中 4 个已指定问题：

1. 英业达 2356 已在 production DB 于 2026-05-29 执行部分停利，但 05/31 假日报文仍重复输出「第二段停利 本次建议 56 股」并进入明日计划。
2. 假日 evidence 日期显示 same_trade_date，手机读者会误解为假日当天证据或 evidence 日期无效。
3. market / theme trend lookback 被默认 row limit 压缩，导致五月历史存在时仍像只有近 2 个 evidence 日。
4. 策略证据 v20.0「样本 0」与 market/theme production evidence 混在一起，造成用户误解为 market/theme evidence 无效。

## 使用者可見結果

手机阅读 2026-05-31 假日报文时，用户应看到：

- 2356 英业达已根据 production DB / latest trading day execution memory 识别为已执行部分停利，不再重复建议第二段停利 56 股。
- Summary、持仓卡片、今日交易、持仓风控、明日计划、索引对 2356 的主行动一致。
- market / theme evidence 显示实际可解释日期，例如 latest_trade_date=2026-05-29、previous_trade_date=...、evidence_trade_date=... 或 lookback_range=...，不得只显示 same_trade_date。
- trend 若有 production 五月历史，应呈现足够 lookback 或明确显示可用趋势范围；不得因 row limit 让用户误读为只有 2 天趋势。
- v20.0「样本 0」只说明 strategy sample 层，不覆盖 market/theme production confirmed evidence。

## 非目標

- 不放宽买点、不新增买入机会、不调整策略进出场阈值。
- 不重设停利 / 停损策略，不重写整体持仓状态机。
- 不新增或修改 DB schema、RLS、grant、policy、role、index / constraint。
- 不做 live Telegram delivery。
- 不使用假数据伪造 production confirmed。
- 不处理其他股票或未来日期的类似问题，除非同一路径自然覆盖且不扩大契约。
- 不做全量历史回补、全量 evidence audit 或报文信息架构重设计。

## 影響模組

Tech 自行定位实际文件，但范围限制在：

- 假日报文生成流程。
- 持仓 / 今日交易 / 明日计划 / 索引的 message list 或 report payload 组装。
- production DB execution memory 读取与 latest trading day fallback。
- market / theme evidence 日期来源显示。
- market / theme trend lookback 查询或展示逻辑。
- v20.0 strategy evidence 文案层或分层说明。

不得扩大到策略核心阈值、DB schema、production write path 或 live delivery。

## 直接消費者

- Owner 手机 Telegram 假日报文读者。
- Telegram report renderer / message list consumer。
- Summary / 索引区块。
- 持仓卡片区块。
- 今日交易区块。
- 持仓风控区块。
- 明日计划区块。
- evidence chain / production confirmed 展示区块。

## 已存在且不得回退的契約

若 Tech 无法确认以下契约，必须 blocked，不得自行假设：

- production DB 是跨日 execution memory 的 source-of-truth；local cache、runtime dict、agent 对话不得作为跨日记忆。
- 缺 production source、读取失败、字段不足或可信度不足时必须 fail closed，显示 missing-source / source-error / insufficient-data，不得静默继续输出明确卖出数量。
- 已买入 / 已卖出 / 已减码 / 已停利等跨日状态必须来自 production DB 或 Owner 指定持久来源。
- 假日报文保留既有分组结构，实际名称以现有报文为准。
- 同一持仓在同一份报文只能有一个主行动。
- 无可买时不得使用类似推荐的文案，应显示「新仓：无有效进场」或等价不可买表述。
- 使用者可见报文变化需同步版本字串或 header 常量，不得回退既有版本。

## 輸出契約

### 1. 2356 execution memory 去重

当 report date 为 2026-05-31 且 latest trading day 为 2026-05-29：

- 若 production DB 显示 2356 已卖出 -112 与 -75，remaining_quantity=225，realized_profit_taken_ratio=0.5：
- 不得输出「第二段停利 本次建议 56 股」。
- 不得在明日计划列 2356 待执行第二段停利。
- 可显示「已完成部分停利 / 第二段已执行至 50% / 剩余持仓进入风控观察」等同义语义。
- 若 execution memory 缺失或矛盾，必须 fail closed，不得输出重复卖出数量。

### 2. 跨区块一致性

2356 在同一份 2026-05-31 假日报文中的主行动必须一致，至少覆盖：

- Summary / 索引。
- 持仓卡片。
- 今日交易。
- 持仓风控。
- 明日计划。

不得同时出现「已停利」与「明日再卖第二段」的冲突语义。

### 3. evidence 日期显示

market / theme evidence 若为 production confirmed：

- 用户可见来源不得只显示 same_trade_date。
- 必须显示 actual / latest / previous trade date 或 lookback range。
- 若 evidence 日期与 report date 不同，文案需让手机读者理解「假日报文使用最近交易日证据」。

### 4. trend lookback

market / theme trend 不得被默认 row limit 压成近 2 个证据日并暗示完整五月趋势：

- 若 production 五月历史存在，应使用足够 lookback 呈现可用趋势。
- 若只返回部分日期，必须显示可用趋势范围或资料不足原因。
- 不得把「只查到 2 笔」包装成完整五月趋势。

### 5. v20.0 样本 0 分层

- 「样本 0」仅代表 strategy evidence / strategy sample 层当前无样本或无命中。
- 不得让用户误解为 market/theme production evidence 无效。
- market/theme production confirmed 状态需保留并独立说明。

## 手機閱讀路徑與示例輸出形狀

手机阅读路径：

1. Summary：确认新仓、持仓优先处理项、不可行动项。
2. 持仓卡片：确认 2356 当前主行动。
3. 今日交易：确认 2026-05-29 已卖出 -112 与 -75 被识别。
4. 持仓风控：确认剩余 225 股只进入风控观察或续抱逻辑。
5. 明日计划：确认没有 2356 第二段停利 56 股。
6. 索引：确认不重复列出 2356 待卖。

示例形状，非强制逐字：

持仓｜2356 英业达
主行动：已完成部分停利，剩余 225 股进入风控观察
执行记忆：production latest_trade_date=2026-05-29，已卖出 -112、-75，realized_profit_taken_ratio=0.5
明日计划：不新增第二段停利单；仅观察剩余持仓风控线

市场 / 题材证据
状态：production confirmed
证据日期：latest_trade_date=2026-05-29；previous_trade_date=YYYY-MM-DD
趋势范围：2026-05 可用交易日 N 日
策略证据 v20.0：策略样本 0；不影响市场 / 题材证据有效性

## 驗收條件

### 必測 1: 2356 假日 latest trading day execution memory

Fixture / production-like 条件：

- report date: 2026-05-31
- latest trading day: 2026-05-29
- symbol: 2356
- position_events: 2026-05-29 quantity -112、2026-05-29 quantity -75
- positions.remaining_quantity: 225
- positions.realized_profit_taken_ratio: 0.5

期望：

- 报文不出现「第二段停利 本次建议 56 股」。
- 明日计划不出现 2356 待卖第二段停利。
- 今日交易或 execution memory 区块能说明 latest trading day 已执行卖出。
- Summary、卡片、今日交易、持仓风控、明日计划、索引对 2356 主行动一致。

### 必測 2: 假日当天无 events，但前一交易日有 execution memory

期望：

- 系统使用 2026-05-29 execution memory。
- 不因 2026-05-31 当天无 events 而重新建议卖出。
- 若 latest trading day source 读取失败，报文 fail closed，不输出重复卖出数量。

### 必測 3: market/theme evidence 日期

期望：

- 用户可见报文不只显示 same_trade_date。
- 报文显示 latest / previous / actual evidence trade date 或 lookback range。
- 手机阅读不会误解为假日当天证据或 evidence 无效。

### 必測 4: trend lookback

Fixture / production-like 条件：

- production 五月历史存在多于 2 个 evidence trade dates。
- 默认 row limit 曾只返回近 2 日。

期望：

- 报文趋势使用足够 lookback 或显示可用趋势范围。
- 不得只呈现近 2 日却暗示完整五月趋势。
- 若资料不足，必须显示不足原因。

### 必測 5: v20.0 样本 0 分层

期望：

- 报文清楚区分 strategy sample 与 market/theme evidence。
- 不得出现会让用户理解为「市场 / 题材证据无效」的文案。
- production confirmed 状态不被样本 0 覆盖。

## QA 反證要求

QA 不得只重跑 Tech 命令，至少补一个 Tech 未覆盖的反证：

- 负面案例：假日当天无 events，但 latest trading day 有 events，确认不会重复卖。
- 使用者误读路径：按手机阅读顺序检查 Summary、卡片、今日交易、持仓风控、明日计划、索引是否仍暗示再次卖 2356。
- 契约风险：确认 evidence source 日期不再以 same_trade_date 作为唯一用户可见来源。
- 趋势风险：确认 row limit 不会让五月趋势只剩 2 天且无说明。
- 版本风险：确认报文 header / version 常量与使用者可见变化一致。

QA 结论只能是 通過、阻塞、conditional pass。

## 明確禁止事項

- 禁止 live Telegram delivery。
- 禁止用假数据或硬编码单一报文结果冒充 production confirmed。
- 禁止绕过既有 DB interface 直接手写 production DML。
- 禁止新增 / 修改 DB schema、RLS、grant、policy、role、index / constraint。
- 禁止放宽买点或改变策略阈值。
- 禁止把 local cache、runtime dict、agent 对话当作跨日 execution memory。
- 禁止在 source-error / insufficient-data 时继续输出明确卖出数量。
- 禁止只修 2356 文案但不修 underlying execution memory 消费路径，除非 Tech 证明现有架构只能由该路径消费且不会影响其他持仓。
- 禁止把「样本 0」写成 market/theme evidence 无效。
- 禁止扩大为全量策略重构、报文大改版或清理工程。

## 阻塞條件

Tech 应 blocked 并回报 Architect，而不是自行假设：

- 无法读取 production DB 或 approved production-like fixture。
- 无法确认 latest trading day 来源。
- 无法确认 positions.realized_profit_taken_ratio、remaining quantity 或 position_events 字段语义。
- 无法定位假日报文 message list / renderer 的直接消费者。
- 现有版本字串 / header 常量位置不明，且报文变化需要同步版本。
- 修复需要 DB schema / RLS / grant / policy / role / index / constraint 变更。
- 修复必须 live Telegram 才能验证。
- production data 与 Owner 给出的 2356 状态矛盾。

## 本輪停止條件

本轮完成定义为：

- Tech 交付修复，并在 CHANGELOG.md 说明修改文件、契约影响、版本同步、直接消费者、自检命令与结果、残留风险。
- QA 读取 TASK.md 与 CHANGELOG.md 后完成 L2 反证，并在 QA_REPORT.md 给出 通過、阻塞 或 conditional pass。
- 2026-05-31 假日报文在 production-like 或 approved fixture 下满足：
- 2356 不再重复建议第二段停利 56 股。
- 跨区块不再暗示再次卖 2356。
- evidence 日期显示可解释 actual/latest/previous trade date。
- 五月 trend 不被默认 row limit 误导。
- v20.0 样本 0 与 market/theme evidence 分层清楚。

旁支问题只记录为后续待办，不纳入本轮：

- 其他股票是否也存在历史 execution memory 异常。
- 更完整的 execution ledger audit。
- 报文整体信息架构重设计。
- 策略 v20.0 样本生成逻辑优化。
- production 五月历史缺口补数。
