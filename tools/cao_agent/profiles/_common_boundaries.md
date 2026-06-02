# Common Boundaries

此片段供 `tools/cao_agent/profiles/stock_*.md.template` 引用；角色卡的專屬差異留在各自 `## Boundaries`。

- Secret / credential 禁讀禁輸出：`.env`、`.env.*`、`*.pem`、`*.key`、`~/.aws/credentials`、`~/.ssh/*`、tokens、browser profile、private cookie/session。
- Owner 的「開始 / 繼續 / 修復 / 檢查 / 清理 / 推進 / 直接來」只代表啟動既有流程，不是跳過 PM -> Tech -> QA，也不是 Architect / Tech 直接改產品代碼授權。
- live Telegram delivery、live Supabase / production write、正式 backfill、DB schema / RLS / grant / policy / role / index / constraint 變更，都需要 Owner 對該動作的明確單獨批准。
- `TASK.md` 與 `AGENTS.md`、`DISPATCH.md` 或角色卡衝突時，預設 fail closed，退回 Architect 仲裁；角色不得自行二選一。
- 不把 local cache、runtime dict、worktree 暫存或 agent 對話記憶當跨日 source-of-truth。
