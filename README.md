# stock-bot

台湾股票策略报文机器人。

维护本项目时先读 `AI_CONTEXT.md`。当前 `19.0` 已启用线上 Supabase 记录，只保存每日收盘/盘后稳定信号。

## Runtime Config

本地复制 `config.example.py` 为 `config.py` 后填入：

- `TOKEN`
- `CHAT_ID`
- `SUPABASE_URL`
- `SUPABASE_KEY`

Render 的 `GITHUB_TOKEN` 使用环境变量配置，不写入 `config.py`。
