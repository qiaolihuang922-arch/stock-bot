# stock-bot

台湾股票策略报文机器人。当前稳定版本：`v19.2.1`。

维护本项目时先读 [AI_CONTEXT.md](/Users/liveroom/stock-bot-main/AI_CONTEXT.md)，里面记录了策略边界、数据库写入边界、回测/回放脚本和不能碰的文件。

## 当前状态

- 报文版本：`v19.2.1`
- 股票清单：只处理 `core/watchlist.py` 内的 12 档配置股票。
- 策略层：`services/analysis.py`
- 显示层：`core/generator.py`
- 条件映射：`core/condition_engine.py`
- 行情来源：`services/stock_api.py`
- 每日信号记录：`services/signal_store.py`
- v19.2.1 回测快照：`core/signal_snapshot.py`
- v19.2.1 信号验证：`core/signal_validator.py`
- 当前持仓边界：Supabase `positions` 表，经由 `services/position_store.py` 读取
- Telegram 持仓输入：报文只显示输入格式提示，实际用文字命令写入 `position_events` 并同步 `positions`
- Telegram 输出：采用总览摘要、持仓卡片、观察卡片的多讯息格式；完整字段仍在 formatter 组装时保留给写库与测试，不默认推送完整长报文。

第一版回测已经完成：当前报文已接入 snapshot 样本、同型态/量能/位置验证、相对表现评估，以及持仓/新进场分离显示。v19.2.1 起持仓不再靠代码文件手动维护，`shares=0` 走未持仓逻辑，`shares>0` 走持仓逻辑。

## Runtime Config

本地复制 `config.example.py` 为 `config.py` 后填入：

- `TOKEN`
- `CHAT_ID`
- `SUPABASE_URL`
- `SUPABASE_KEY`
- `SUPABASE_SERVICE_ROLE_KEY`

Render / GitHub Actions 使用平台环境变量或 secrets。不要把真实密钥提交到仓库。
v19.2.1 持仓读取必须配置 `SUPABASE_SERVICE_ROLE_KEY`；只用 publishable/anon key 时，RLS 可能让 `positions` 查询回传 0 行，报文会明确提示持仓状态不可信。

## 常用命令

运行当前报文：

```bash
.venv/bin/python - <<'PY'
from core.generator import generate
print(generate())
PY
```

运行测试：

```bash
.venv/bin/python -m pytest
```

dry-run replay，不写入数据库：

```bash
.venv/bin/python scripts/dry_run_replay.py \
  --dry-run \
  --validate \
  --source twse \
  --version v19.2.1 \
  --start-date 2026-05-11 \
  --end-date 2026-05-22
```

backfill dry-run，不写入数据库：

```bash
.venv/bin/python scripts/backfill_signals.py \
  --dry-run \
  --source twse \
  --version v19.2.1 \
  --start-date 2026-05-11 \
  --end-date 2026-05-22
```

正式 backfill 需要同时加上 `--write --confirm-write`。没有这两个参数时，脚本不会写入数据库。

## 数据库

原始信号表：

- `signal_runs`
- `signal_items`
- `signal_outcomes`

v19.2.1 回放/回测表：

- `daily_price`
- `daily_signal_snapshot`
- `positions`
- `position_events`

建表 SQL 在 [docs/v19_backfill_schema.sql](/Users/liveroom/stock-bot-main/docs/v19_backfill_schema.sql)。
持仓执行表 SQL 在 [docs/v19_position_execution_schema.sql](/Users/liveroom/stock-bot-main/docs/v19_position_execution_schema.sql)。
若 `positions` 已经先建立，升级 v19.2.1 需再执行 [docs/v19_2_position_zero_migration.sql](/Users/liveroom/stock-bot-main/docs/v19_2_position_zero_migration.sql)，补齐 12 档股票与 0 股持仓。

当前原则：

- 盘前、盘中、假日不写入每日稳定样本。
- 收盘/盘后才记录稳定信号。
- 每日路径只在有完整 OHLCV 时写 `daily_price`，不会用单一即时价污染价格表。
- 每日持仓股不会写成新进场 `is_tradeable`。
- 线上报文持仓由 `positions.shares` 决定；`0` 股就是未持仓，非 `0` 股才是持仓。
- 买入会用库内当前均价加权重算，卖出不改变均价；手动 `設定` 会覆盖股数与均价，后续买入继续以设定后的均价为基准。
- replay/backfill 仍需遵守持仓边界；历史样本应以当日已知持仓为准，不得用未来持仓污染过去。
- replay/backfill validate 会检查每日是否完整覆盖预期股票清单，缺档或整日无样本不会通过。
- backfill 必须先 dry-run 和 validate。
- 回放某一天时，只能使用当天及之前的数据，禁止未来数据污染。
- replay/backfill 默认使用 90 天 warmup。
- 默认只处理 `core/watchlist.py` 的 12 档股票，不做全市场写入。

## 部署

Render 服务由 UptimeRobot 定时访问唤醒。Render 入口在 [app.py](/Users/liveroom/stock-bot-main/app.py)，实际触发 GitHub Actions workflow。

workflow 文件：

- [.github/workflows/stock-bot.yml](/Users/liveroom/stock-bot-main/.github/workflows/stock-bot.yml)

测试入口：

- 正式：`https://stock-bot-ia2o.onrender.com`
- 测试：`https://stock-bot-ia2o.onrender.com/?test=1`

`?test=1` 用来绕过假日/时间判断做手动测试。
