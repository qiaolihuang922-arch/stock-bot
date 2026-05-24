# stock-bot

台湾股票策略报文机器人。当前稳定版本：`v19.1.3`。

维护本项目时先读 [AI_CONTEXT.md](/Users/liveroom/stock-bot-main/AI_CONTEXT.md)，里面记录了策略边界、数据库写入边界、回测/回放脚本和不能碰的文件。

## 当前状态

- 报文版本：`v19.1.3`
- 股票清单：只处理 `core/watchlist.py` 内的 12 档配置股票。
- 策略层：`services/analysis.py`
- 显示层：`core/generator.py`
- 条件映射：`core/condition_engine.py`
- 行情来源：`services/stock_api.py`
- 每日信号记录：`services/signal_store.py`
- v19 回测快照：`core/signal_snapshot.py`
- v19 信号验证：`core/signal_validator.py`
- 当前持仓边界：`core/holdings.py`

## Runtime Config

本地复制 `config.example.py` 为 `config.py` 后填入：

- `TOKEN`
- `CHAT_ID`
- `SUPABASE_URL`
- `SUPABASE_KEY`

Render / GitHub Actions 使用平台环境变量或 secrets。不要把真实密钥提交到仓库。

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

正式 backfill 需要同时加上 `--write --confirm-write`。没有这两个参数时，脚本不会写入数据库。

## 数据库

原始信号表：

- `signal_runs`
- `signal_items`
- `signal_outcomes`

v19 回放/回测表：

- `daily_price`
- `daily_signal_snapshot`

建表 SQL 在 [docs/v19_backfill_schema.sql](/Users/liveroom/stock-bot-main/docs/v19_backfill_schema.sql)。

当前原则：

- 盘前、盘中、假日不写入每日稳定样本。
- 收盘/盘后才记录稳定信号。
- 每日路径只在有完整 OHLCV 时写 `daily_price`，不会用单一即时价污染价格表。
- 每日持仓股不会写成新进场 `is_tradeable`。
- replay/backfill 与每日快照共用持仓边界；持仓股不会进入新进场 `is_tradeable / is_best_candidate`。
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
