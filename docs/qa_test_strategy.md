# QA Test Strategy

本文件定义 stock-bot 的分层测试架构。目标是让 Codex 和工程师按改动风险选择最低必要测试，避免每次小改动都全仓库扫描、全量测试、全量 build、全量 backtest。

核心原则：

- 小改动只跑小测试。
- 中改动只跑相关模块测试。
- 大改动才跑全局回归。
- 能 mock 就不要打真实服务。
- 能 sample 就不要全市场扫描。
- 能 snapshot 就不要 full render。
- 能局部验证就禁止全局测试。

目标：将日常开发验证的 token 和执行成本降低 70%。

## 测试分级制度

| Level | 适用改动 | 允许测试 | 禁止测试 |
| --- | --- | --- | --- |
| L0 展示与文案 | formatter、Telegram layout、markdown、emoji、文字、字段顺序、message splitting、README/docs、UI mapping | 精准单测、snapshot/mock output、静态阅读目标文件 | full pytest、replay、backfill、historical simulation、全市场扫描、真实 DB/Telegram |
| L1 单模块逻辑 | 单一 strategy helper、scoring、RR、signal validator、condition mapping、单一 parser | 相关 test file 或相关 test case；1-3 个代表性股票样本 | historical backtest、全市场扫描、真实写库、无关模块测试 |
| L2 局部 integration | portfolio logic、market regime、position sizing、snapshot boundary、watchlist alignment、daily snapshot store dry-run 逻辑 | 相关 integration tests；mock Supabase；固定日期小样本；12 档 watchlist 内 sample | 正式 backfill、长区间 replay、全历史模拟、真实写库 |
| L3 full regression | database schema、core engine、execution flow、shared interfaces、跨层资料契约、写库边界、部署入口 | full pytest、dry-run replay validate、必要时短区间 backfill dry-run | 未经 dry-run/validate 的正式写库、无确认的大量 backfill |

默认选择最低等级。只有改动触及更高等级的触发条件，才可升级测试等级。

## 当前项目测试映射

| 变更区域 | 首选验证 |
| --- | --- |
| `core/generator.py` 文案、Telegram 排版、卡片拆分 | `.venv/bin/python -m pytest tests/test_generator_report.py`，必要时只跑单个 test case |
| `services/analysis.py`、RR、持仓策略 | `.venv/bin/python -m pytest tests/test_analysis_engine.py` |
| `core/signal_validator.py` | `.venv/bin/python -m pytest tests/test_signal_validator.py` |
| `core/signal_snapshot.py` 边界或 snapshot schema | `.venv/bin/python -m pytest tests/test_analysis_engine.py tests/test_signal_validator.py` |
| `core/watchlist.py` | `.venv/bin/python -m pytest tests/test_watchlist_alignment.py` |
| `services/stock_api.py` 历史资料解析 | `.venv/bin/python -m pytest tests/test_stock_api_history.py`，优先 mock response |
| `services/daily_snapshot_store.py` | `.venv/bin/python -m pytest tests/test_daily_snapshot_store.py` |
| `scripts/dry_run_replay.py` | `.venv/bin/python -m pytest tests/test_dry_run_replay.py` |
| `scripts/backfill_signals.py` | `.venv/bin/python -m pytest tests/test_backfill_signals.py` |
| `docs/*.sql` schema 或写库契约 | 相关 store/script tests + 短区间 dry-run validate，必要时 full pytest |

精准单测命令格式：

```bash
.venv/bin/python -m pytest tests/test_generator_report.py::GeneratorReportTest::test_holding_add_uses_basis_label
```

## 禁止全局测试的情况

以下改动属于 L0，禁止执行 full regression、historical backtest、全市场扫描或真实外部调用：

- formatter 调整。
- 文案、标题、emoji、标点、markdown 变更。
- Telegram 排版、卡片顺序、message splitting。
- 输出字段顺序、label 改名、显示隐藏规则。
- README、AI_CONTEXT、docs 说明文件。
- mock output 或 snapshot fixture 更新。
- UI mapping 或纯映射文字调整。

L0 改动最多只允许：

- 读相关文件。
- 跑相关 formatter/generator 单测。
- 用 mock payload 产生单一输出。
- 比对 snapshot 或关键字符串。

L0 明确禁止：

- `.venv/bin/python -m pytest` 全量测试。
- `scripts/dry_run_replay.py`。
- `scripts/backfill_signals.py`。
- historical simulation。
- 真实 Telegram 推送。
- 真实 Supabase 写入。
- 超过 watchlist 的全市场扫描。

## Level 1 规则

L1 是单模块逻辑改动，例如 scoring、RR、signal、condition mapping、单一 strategy helper。

执行规则：

- 只读取相关源码和相关 tests。
- 优先跑对应 test file。
- 若只改一个 helper，优先跑单个 test case，再按需要跑该 test file。
- 股票样本限制在 1-3 档。
- 不允许跑 replay/backfill，除非该 helper 直接改变 snapshot 输出契约。

推荐命令：

```bash
.venv/bin/python -m pytest tests/test_analysis_engine.py
.venv/bin/python -m pytest tests/test_signal_validator.py
```

## Level 2 规则

L2 是局部整合改动，例如 portfolio logic、market regime、position sizing、snapshot boundary、daily snapshot store、watchlist alignment。

执行规则：

- 跑相关 integration tests。
- 外部服务必须 mock。
- 日期区间用最短可证明样本。
- 股票范围默认只用 `core/watchlist.py` 的 12 档，能更小就更小。
- 不做正式 backfill。

允许的验证：

```bash
.venv/bin/python -m pytest tests/test_daily_snapshot_store.py
.venv/bin/python -m pytest tests/test_dry_run_replay.py
.venv/bin/python -m pytest tests/test_backfill_signals.py
```

只有当 replay/backfill 脚本本身被修改，或 daily snapshot 写入契约改变，才运行短区间 dry-run validate。

## Level 3 规则

L3 才允许 full regression。触发条件必须明确：

- database schema 改动。
- core engine 或 execution flow 改动。
- shared interfaces 或跨模块资料契约改动。
- `daily_signal_snapshot`、`daily_price`、`positions`、`position_events` 写入语义改变。
- watchlist 覆盖完整性规则改变。
- replay/backfill 的防污染、validate、upsert、安全 guard 改动。
- 部署入口、定时触发、外部服务调用路径改变。

L3 推荐顺序：

1. 相关单测。
2. full pytest。
3. 必要时短区间 dry-run replay validate。
4. 必要时 backfill dry-run。
5. 只有用户明确要求并确认，才允许正式写库。

全量测试命令：

```bash
.venv/bin/python -m pytest
```

dry-run replay 示例：

```bash
.venv/bin/python scripts/dry_run_replay.py \
  --dry-run \
  --validate \
  --source twse \
  --version v19.3 \
  --start-date 2026-05-11 \
  --end-date 2026-05-22
```

## Token 控制规则

Codex 必须控制读取范围和输出范围：

- 先读 `AI_CONTEXT.md` 和本文件，再定位相关文件。
- 禁止一开始全 repo 大段读取。
- 搜索用 `rg`，只搜关键函数、错误文字、目标 test 名称。
- 每次最多打开与任务直接相关的 3-5 个源码文件。
- 测试失败时只读失败 stack trace 对应文件。
- 不贴整份测试输出，只总结失败 test、错误原因、修复点。
- 不运行会产生大量日志的 replay/backfill，除非达到 L3 条件。
- 不把完整历史数据、全市场输出、Telegram 长报文塞进对话。
- 对 L0/L1 改动，最终回复只列改动文件和最低必要验证。

## Codex 开发规则

Codex 在每次修改前必须先判断测试等级：

1. 说明本次改动属于 L0/L1/L2/L3。
2. 说明为什么不需要更高等级测试。
3. 只读取相关上下文。
4. 只改用户要求相关文件。
5. 先跑最低等级测试。
6. 只有最低等级测试无法覆盖风险时，才升级测试。
7. 若要升级到 full pytest、replay 或 backfill，必须在回复中写明触发条件。

Codex 不得因为“保险起见”直接跑全量测试。全量测试必须由 L3 触发条件支持。

## 工程师执行规范

工程师提交或审查改动时，应在 PR/最终回复中写明：

- 改动等级：L0/L1/L2/L3。
- 影响区域：formatter、strategy、snapshot、store、script、schema 等。
- 执行测试：具体命令。
- 未执行的测试：说明为什么禁止或不必要。
- 是否触及真实外部服务：Telegram、Supabase、TWSE。
- 是否存在 DB 写入风险。

推荐格式：

```text
Test Level: L0
Scope: Telegram formatter layout only
Ran: .venv/bin/python -m pytest tests/test_generator_report.py::GeneratorReportTest::...
Skipped: full pytest, replay, backfill because formatter-only changes do not affect strategy or persistence
External services: none, mocked only
```

## 给技术对话窗的规则

把以下规则贴到技术 Codex 对话开头：

```text
你维护 stock-bot 时必须遵守最低必要测试原则。

每次改动前先判断测试等级：

L0 formatter / text / Telegram layout / markdown / emoji / message splitting / docs:
- 只允许相关 snapshot、mock output、关键字符串测试。
- 禁止 full pytest。
- 禁止 dry_run_replay。
- 禁止 backfill。
- 禁止 historical simulation。
- 禁止全市场扫描。
- 禁止真实 Telegram / Supabase 调用。

L1 单一 strategy module / scoring / RR / signal / validator:
- 只跑对应 module test 或单个 test case。
- 股票样本限制 1-3 档。
- 不跑 replay/backfill，除非 snapshot 契约被改变。

L2 portfolio logic / market regime / position sizing / snapshot boundary / store dry-run:
- 跑相关 integration tests。
- 外部服务必须 mock。
- 日期区间和股票范围使用最小样本。
- 不做正式写库。

L3 database schema / core engine / execution flow / shared interfaces / persistence contract:
- 先跑相关单测，再允许 full pytest。
- 只有需要验证历史路径时，才跑短区间 dry-run replay validate。
- backfill 必须 dry-run + validate；正式写库必须由用户明确确认。

默认规则：
- 能局部测试，就禁止全局测试。
- 能 mock，就不要跑真实资料。
- 能 sample，就不要全市场扫描。
- 能 snapshot，就不要 full render。
- 只有 core engine / schema / shared interfaces / persistence contract 才允许 full regression。

每次最终回复必须写：
- Test Level
- Ran
- Skipped and why
```

## 最低必要测试原则

最低必要测试不是少测，而是只验证本次改动真正可能破坏的行为。

- Formatter 改动，只验证 formatter 输出。
- Telegram layout 改动，只验证 mock output 和 message splitting。
- 文案和 emoji 改动，只验证关键字符串或 snapshot。
- 单一股票逻辑，只测单档或少量代表样本。
- Strategy scoring 改动，只测 scoring module。
- Signal validator 改动，只测 validator。
- Store guard 改动，只测 store/script guard。
- Schema、core engine、shared interface 改动，才做 full regression。

升级测试必须有理由；没有理由时，保持最低等级。
