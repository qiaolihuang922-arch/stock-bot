# TASK: 未持仓卡片 gate attribution 试行

## 任務狀態

- task_id: telegram-unheld-gate-attribution-v20.4.40
- 任務類型: normal_patch
- 狀態: ready_for_tech
- 版本建議: 使用者可見 Telegram 報文版本從 v20.4.39 升至 v20.4.40
- QA 分級建議: L2
- 本輪主 bug: 未持仓非可买卡片缺少「距离可买还差哪条 gate」的可读解释，用户无法判断下一步观察重点。

## Owner 問題

Owner 要先试行 Telegram 未持仓卡片的 gate attribution，让用户在手机上看得到一档股票为什么还没有真的变可买，以及目前最关键的 1-3 个阻挡 gate。

当前目标不是改变股票是否可买，而是在既有未持仓卡片 / summary 语义下增强可读性，避免「可准备」「等冷却」「等 RR 修复」「不可追高」「淘汰」等状态被误读成推荐买入。

## 使用者可見結果

Telegram 未持仓卡片中，若股票不是「真正可买」且不是 trend_continuation 小仓 BUY，在卡片内增加一行简短文案，例如：

到達可買差距：RR 0.98/需>=1.5；heat HOT/需降温

或等价短句：

可買差距：距突破 6%/需<=4%；entry quality C/需B以上

手机阅读路径：

- 用户先看 summary，仍只能判断「新仓能不能买」与「哪些只是准备 / 冷却 / 追踪 / 淘汰」。
- 用户再看未持仓卡片，每档非可买股票只看到一行 gate 差距，不新增长段解释。
- 该行不得让「不可买」卡片看起来像推荐；必须和卡片状态、分组标题、summary 语义一致。

## 非目標

- 不改 strategy decision。
- 不改 RR 公式。
- 不改 can_buy / is_valid_entry 语义。
- 不改仓位、买卖建议、加减码、停损停利逻辑。
- 不改 DB schema、RLS、grant、policy、role、write path。
- 不做 live Telegram delivery。
- 不重构全量 formatter、策略状态机或候选排序。
- 不新增大段解释型报文，不把卡片变成诊断报告。

## 影響模組與直接消費者

影響模組：

- Telegram official message formatter。
- 未持仓 card/message-list 生成路径。
- summary 与 card 的可读性一致性检查。
- 与 version/header 常量相关的使用者可见版本位置。

直接消費者：

- Telegram 手机端阅读用户。
- official formatTelegramMessages / message-list replay。
- QA 用于验证最终 Telegram 报文形状的 replay artifact。

## 輸出契約

对未持仓卡片新增单一输出契约：到達可買差距 行。

显示条件：

- 显示：未持仓且当前不是可买的卡片，包括但不限于：
- 等 RR 修复
- 等冷却 / 过热
- 不可追高
- 可准备但尚未触发买入
- 淘汰 / 不可行动
- source-error / insufficient-data / missing-source
- 突破失败 / 需重新转强
- 不显示：
- 已经是真正可买的未持仓 BUY 卡。
- trend_continuation 小仓 BUY 卡。
- 持仓卡片。

内容规则：

- 每张卡最多列 1-3 个最关键 gate。
- 每个 gate 用短格式表达：当前值/所需条件。
- 建议候选 gate 文案：
- RR 0.98/需>=1.5
- heat HOT/需降温
- 距突破 6%/需<=4%
- entry quality C/需B以上
- source-error/需可用
- 突破失败/需重新转强
- gate 排序由既有 payload / formatter 可稳定取得的信息决定；若多个 gate 同时存在，优先呈现最能解释「为什么现在不能买」的 gate。
- 若某卡没有可可靠取得的 gate attribution，不得编造；应显示既有不可行动原因或 fail closed 文案，例如 可買差距：資料不足/需可用。

已存在且不得回退的契约：

- Summary 只回答决策，不把无可买写成推荐。
- 可买、可准备、仅追踪、淘汰 / 不可行动必须分开。
- 无可买时不得使用像推荐的文案。
- 分组标题、卡片状态、漏斗、索引、详情必须一致。
- 同一行動不得在多个区块重复长句。
- 空区块、0-count、无新增下单占位默认不显示。
- 使用者可见版本不得停留在 v20.4.39；本轮应同步为 v20.4.40。

## 版本契約

- Telegram 使用者可见报文版本建议升为 v20.4.40。
- 若代码内存在 header/version constant，Tech 必须同步实际输出与常量。
- 若本 repo 当前版本不是 v20.4.39 或版本位置不明，Tech 必须在 CHANGELOG.md 标明实际发现；不能静默跳过版本同步。

## 驗收條件

必须用 official formatTelegramMessages / message-list replay 验证最终用户可见报文，不得只测 helper fixture。

1. 等 RR 修复案例：
- 卡片仍不可买。
- 显示 RR 差距，例如 RR 0.98/需>=1.5。
- Summary 不把该档写成可买推荐。
2. 等冷却 / 过热案例：
- 卡片仍不可买。
- 显示降温差距，例如 heat HOT/需降温。
- Summary 与卡片状态一致，不出现推荐误读。
3. 真正可买案例：
- 卡片仍为可买。
- 不显示 到達可買差距 或等价差距行。
4. trend_continuation 小仓 BUY 案例：
- 卡片仍为小仓 BUY。
- 不显示差距行，避免噪音。
5. 手机阅读误读检查：
- 非可买卡片新增行不得包含「建议买入」「可立即买」等推荐式措辞。
- Summary/card/lists 不出现「summary 说不可买、card 像推荐」的冲突。

## 範例或 Fixture

示例输出形状：

2330 台積電｜等RR修復
...
到達可買差距：RR 0.98/需>=1.5；距突破 6%/需<=4%

NVDA｜等冷卻
...
到達可買差距：heat HOT/需降温

AAPL｜可買
...

可买卡不得出现：

到達可買差距：...

trend_continuation 小仓 BUY 不得出现：

到達可買差距：...

## 失敗標本與驗收路由

失敗標本：

- 当前 official Telegram 未持仓卡片中，非可买股票只显示状态或原因，未显示「到达可买还差哪条 gate」。
- Owner 指定的五类 replay 场景即为本轮验收标本。

驗收路由：

- 必须从 official formatTelegramMessages / message-list replay 产生最终 Telegram 报文文本。
- Tech 自检必须覆盖 formatter / official generator 或 message-list replay 层。
- QA 必须沿相同 official replay 路径反证，并额外检查 summary/card 是否造成推荐误读。
- 若只能测 helper 或局部 formatter，结论只能是 partial，不得宣称用户可见问题完成。

## 明確禁止事項

- 禁止改变策略买卖判断。
- 禁止改变 RR、heat、entry quality、突破距离等计算公式。
- 禁止改变 can_buy / is_valid_entry contract。
- 禁止新增 DB schema/write/live delivery。
- 禁止为了显示差距而伪造 gate。
- 禁止让不可买卡片出现推荐式文案。
- 禁止把本轮扩成全量 Telegram 报文重构或策略解释系统。
- 禁止只用 synthetic helper fixture 宣告通过。

## 阻塞條件

若出现以下情况，Tech/QA 必须 blocked 或 partial，不得硬过：

- official message-list replay 无法运行，且没有等价最终报文 artifact。
- payload 中没有足够信息判断任何 gate，且无法稳定从既有 formatter inputs 取得。
- 当前版本来源不明，无法确认 v20.4.40 是否已同步到用户可见 header。
- 新增差距行会迫使改变 strategy decision、RR 公式或 DB contract。
- replay 无法覆盖 Owner 指定的 5 个场景。

## 本輪停止條件

完成条件：

- official replay 中，非可买未持仓卡片显示 1-3 个关键 gate 差距。
- 可买与 trend_continuation 小仓 BUY 不显示差距。
- Summary/card 在手机阅读路径下不产生推荐误读。
- 版本输出同步到 v20.4.40。
- Tech 提供可重跑命令，QA 使用 official replay 路径完成 L2 反证。

旁支问题不纳入本轮：

- gate 排名算法优化。
- 新增更多策略诊断字段。
- 调整候选排序、仓位、买卖建议。
- production DB 回补。
- live Telegram 发送。
- 全量报文视觉重排。
