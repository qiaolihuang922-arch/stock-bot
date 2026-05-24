# Stock Bot AI Context

本文件是给 AI 维护本专案用的最小上下文。新对话接手时，先读这个文件，再按需要读取相关源码，避免重复扫描全专案。

## 当前阶段

- 当前稳定线：`v19.1.3`
- 旧版策略升级已完成：策略层、显示层、持仓逻辑、行情显示冲突修复。
- `19.x` 当前目标：可验证、可重跑、可回放、可避免污染的数据库写入流程。
- 不要直接大量 backfill。必须先 dry-run、validate、人工或自动检查无误后，才允许正式写入。

## 禁改与慎改

- `config.py`：包含本地密钥，不要改、不要打印、不要提交。
- 不要把 Supabase、Telegram、GitHub token 写进代码或 Markdown。
- 不要做无关重构；只改用户本轮要求相关文件。
- `services/ai.py`、`services/learning.py` 已不参与当前主流程，除非用户明确要求，否则不要恢复旧逻辑。

## 12 档股票清单

唯一配置来源：`core/watchlist.py`。

当前只处理这 12 档：

- `3231` 緯創
- `2421` 建準
- `3035` 智原
- `2303` 聯電
- `3481` 群創
- `2344` 華邦電
- `2376` 技嘉
- `2408` 南亞科
- `2356` 英業達
- `2324` 仁寶
- `2301` 光寶科
- `2337` 旺宏

`core/generator.py`、`scripts/dry_run_replay.py`、`scripts/backfill_signals.py` 都应从 `core.watchlist` 读取默认清单。不要在脚本里另写一份股票清单。

当前持仓清单由 `core/holdings.py` 统一提供；generator、replay、backfill 不应各自维护持仓副本。

## 文件职责

- `services/analysis.py`：唯一策略来源。负责 `BUY / WAIT / NO_TRADE / FAIL`、品质分、持仓策略、最强候选过滤。
- `core/condition_engine.py`：条件映射层。只整理 `market / trend / volume / event / edge / rr` 等条件，不反推策略。
- `core/generator.py`：报文显示、排序摘要、Telegram 输出内容。不得自行推翻 `analysis.py` 的交易结论。
- `services/stock_api.py`：行情来源、实时价修正、涨跌停价格保护、TWSE OHLCV 历史资料。
- `services/signal_store.py`：原始 3 表写入层，负责 `signal_runs / signal_items / signal_outcomes`。
- `services/daily_snapshot_store.py`：v19 每日快照写入层，负责每日 `daily_signal_snapshot`；只有拿到完整 OHLCV 时才写 `daily_price`，写入前必须验证。
- `core/signal_snapshot.py`：把策略结果或 OHLCV 转成统一可回测 snapshot。
- `core/signal_validator.py`：检查 snapshot 逻辑冲突，防止错误资料入库。
- `core/holdings.py`：当前持仓清单与持仓股票代码集合，供 generator / replay / backfill 共用持仓边界。
- `scripts/dry_run_replay.py`：dry-run replay，不写数据库。
- `scripts/backfill_signals.py`：受保护 backfill，默认不写数据库。
- `docs/v19_backfill_schema.sql`：v19 两张新表建表 SQL。

## 数据库边界

原始 3 表：

- `signal_runs`
- `signal_items`
- `signal_outcomes`

v19 回测/回放 2 表：

- `daily_price`
- `daily_signal_snapshot`

写入原则：

- 盘前、盘中、假日不写入每日稳定样本。
- 收盘/盘后才允许记录稳定信号。
- 每日报文路径不得用 realtime/yahoo/twse 单价补写 `daily_price`；`daily_price` 只接受完整 OHLCV。
- 每日正式 snapshot 中，持仓股只代表持仓管理，必须排除新进场 `is_tradeable / is_best_candidate` 统计。
- replay/backfill snapshot 也必须套用相同持仓边界；持仓股不得成为新进场可交易或最强候选。
- backfill 必须使用 upsert，可重复执行，不得产生重复资料。
- replay/backfill 某一天时，只能使用当天及之前资料，禁止未来数据污染。
- `dry_run_replay.py` 与 `backfill_signals.py` warmup 都应维持 90 天，避免同区间样本数量不一致。
- `dry_run_replay.py` 与 `backfill_signals.py` 必须验证每日完整覆盖预期股票清单；缺任一档或整日无样本时不得通过 validate。
- 默认只处理 `core/watchlist.py` 的 12 档股票。
- 当前已经测试过 2024 少量写入和重复 upsert，随后已删除测试资料。不要误以为正式 backfill 已完成。

## v19 表结构

`daily_price`：

- `stock_id`
- `trade_date`
- `open`
- `high`
- `low`
- `close`
- `volume`
- `source`
- `created_at`
- `updated_at`

唯一键：`stock_id + trade_date`

`daily_signal_snapshot`：

- `stock_id`
- `trade_date`
- `version`
- `close`
- `volume_ratio`
- `pattern`
- `market_state`
- `structure_state`
- `position_state`
- `rr`
- `score`
- `heat_level`
- `action`
- `reasons`
- `is_tradeable`
- `is_best_candidate`
- `created_at`
- `updated_at`

唯一键：`stock_id + trade_date + version`

`reasons` 使用 JSON/JSONB。

## 策略层硬规则

- 持仓逻辑和未持仓新进场逻辑必须分离。
- 持仓股可以：`续抱 / 洗盘观察 / 停利 / 停损 / 减码 / 加码`。
- 非持仓股只能：`观察 / 等量 / 不交易 / 等确认 / 不追高`。
- 持仓非加码时，不显示新进场 RR / Edge 缺口。
- `overheat` 只能作为风险标签，不应覆盖原本型态。
- 涨停锁价不追高；已持仓可停利一部分并保留核心仓。
- 最强股只能从有效新进场候选挑选，不能从持仓、过热、低量、小仓观察中选。
- 强势但 RR 不足，不应被选为最佳进场标的。
- `LOCK_LIMIT / LIMIT_REBOUND / WEAK_REBOUND` 这类被限制交易的 WAIT snapshot 必须写出阻断原因，不得空 reasons。

## lifecycle 优先级

型态优先级：

1. 涨停锁价
2. 突破确认
3. 接近突破
4. 弱势反弹
5. 弱势

`overheat` 是风险标签，不是 lifecycle 主状态。

## RR 与交易限制

- RR 不可除以 0。
- RR 不可因 `None` 报错。
- RR `< 1` 时必须标记 `RR不足`。
- 已持仓股票没有新进场 RR 时，不应误判成可加码。
- `RR不足 / 过热 Lv3 / 漲停鎖價 / 不追高 / 無量 / 市場弱` 都必须限制交易。

## 最强股规则

候选必须满足：

- `decision == BUY`
- `action > 0`
- 未持仓
- `entry_quality` 为 `A` 或 `A+`
- 非 `HOT / EXTREME`
- 非 `WEAK_REBOUND / LIMIT_REBOUND / LIMIT_LOCK`
- 非低量且非攻击结构
- `rr >= 1`
- `is_tradeable == true`

否则底部应显示 `无有效进场标的`，或由其他合格候选胜出。

## 禁止出现的报文冲突

- `V < 0.8x` 但显示 `A+ / C95`。
- `过热观察` 同时显示 `成立：完整`。
- `不交易 / 禁追 / 观察` 被底部列为 `最强`。
- 持仓续抱显示成 `缺口：持仓续抱`。
- 持仓警戒显示成 `缺口：持仓警戒`。
- 假日显示 `价格(realtime)`。
- 涨停锁价建议追高。
- RR 隐藏后，评级原因还写 `高RR`。
- `FAIL` 同时显示禁追、过热、可交易等互斥状态。
- `action = 不交易`，但 reasons 显示可进场。
- `action = 停利`，但没有过热、涨停、急涨或风控原因。
- `action = 续抱`，同时出现停损讯号。

## 持仓策略边界

- 持仓处理优先看结构、量能、市场、价格行为，不只看盈亏百分比。
- `续抱`：没有破坏结构，或弱势但尚未触发风控。
- `洗盘观察`：缩量回测、未见出货、趋势未破，避免被假卖点洗掉。
- `警戒`：轻亏、市场弱、量能弱、趋势未转强。
- `减码`：出货风险、突破失败、弱势中亏扩大。
- `停损 100%`：硬停损或明显破位。
- `停利 25% / 50%`：获利明显且过热，保留核心仓，避免假卖掉真主升。
- `加码`：只允许在持仓盈利、结构转强、市场强、量能不弱、RR 足够、品质达标时出现。

## 常用验证命令

运行全部测试：

```bash
.venv/bin/python -m pytest
```

dry-run replay，不写入数据库：

```bash
.venv/bin/python scripts/dry_run_replay.py \
  --dry-run \
  --validate \
  --source twse \
  --version v19.1.3 \
  --start-date 2026-05-11 \
  --end-date 2026-05-22
```

backfill dry-run，不写入数据库：

```bash
.venv/bin/python scripts/backfill_signals.py \
  --dry-run \
  --source twse \
  --version v19.1.3 \
  --start-date 2026-05-11 \
  --end-date 2026-05-22
```

正式 backfill 必须显式加：

```bash
--write --confirm-write
```

没有这两个参数时，`scripts/backfill_signals.py` 不得写入数据库。

## 已验证事项

- 测试套件已覆盖策略层、dry-run replay、TWSE OHLCV 解析、signal validator、backfill guard、daily snapshot store、watchlist 对齐。
- 最近一次完整测试为 `36 tests OK`。
- 2026 TWSE 历史资料可查；之前出现 0 rows 是因为执行环境网络受限，不是 TWSE 没资料。
- 已确认 `3231` 在 `2026-05-22` 可取到 OHLCV：open `142.5`、high `146.0`、low `139.5`、close `144.5`、volume `70277790`。
- 已用真实 TWSE 跑过 `2026-05-18` 到 `2026-05-21` dry-run replay，生成 48 条 snapshot，`VALIDATION OK`，未写入数据库。当前 replay/backfill validate 会阻止缺档、整日缺样本、持仓股误入 `is_tradeable / is_best_candidate`，并要求 `LOCK_LIMIT` 有阻断原因。
- 已做过 2024 少量 DB 写入、重复 upsert、删除测试资料；两张 v19 表已清空测试样本。

## 每次升级流程

1. 先读 `AI_CONTEXT.md`。
2. 根据用户报文定位冲突。
3. 只读取相关源码，不全仓库扫大段无关文件。
4. 修改策略层时同时检查显示层是否对齐。
5. 修改处保留必要中文注释。
6. 不碰 `config.py`，真实密钥只留在本地或平台环境变量。
7. 跑测试或最小验证。
8. 若涉及 DB 写入，先 dry-run + validate。
9. 最后回复改动文件、修复点、验证结果。

## 部署与触发

- Render 入口：[app.py](/Users/liveroom/stock-bot-main/app.py)
- GitHub Actions workflow：[.github/workflows/stock-bot.yml](/Users/liveroom/stock-bot-main/.github/workflows/stock-bot.yml)
- 正式 URL：`https://stock-bot-ia2o.onrender.com`
- 测试 URL：`https://stock-bot-ia2o.onrender.com/?test=1`

UptimeRobot 免费版可能只能用 `HEAD`，`app.py` 需要兼容 `HEAD` 唤醒。
