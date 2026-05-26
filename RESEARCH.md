# RESEARCH.md

本文件保存最新研究任務的高信號摘要，不保留完整聊天紀錄。

## Latest Research

- task_id: `agent-role-docs-external-review`
- 日期：2026-05-26
- 狀態：已吸收為 Workflow Rules v3
- 範圍：只研究 PM / Tech / QA 代理文檔與任務交付規則；不改產品代碼。

## Question

Owner 認為目前代理雖然有分工，但實際交付仍容易變笨、含糊、照單驗收或越權。需要參考公開 GitHub / 多代理專案，強化本專案 PM / Tech / QA 代理文檔與拒收規則。

## Evidence

- `agentsmd/agents.md`：AGENTS.md 的核心價值是給 coding agents 一個可預期、專用的專案指令位置；範例包含 dev environment、testing instructions、PR instructions，強調具體命令與測試要求。
- `FoundationAgents/MetaGPT`：用軟體公司模式把 Product Manager、Architect、Project Manager、Engineer 等角色拆開，並以 SOP 協作；重點不是角色名，而是角色輸出與流程標準化。
- `OpenBMB/ChatDev`：多代理軟體開發流程明確分成 design / coding / testing / documenting 等階段，並支援使用者自定義 ChatChain、Phase、Role settings。
- `CrewAI` docs：Agent 需要明確 role / goal / backstory；Task 需要 description、assigned agent、expected output。這點對應本專案的角色卡與任務卡。
- `Microsoft AutoGen`：多代理框架重點是 agent orchestration 與 human-in-the-loop；對本專案的啟示是 agents 不能互相亂串，必須由 Architect runner 控制順序與停止條件。

## Findings

- 目前本專案缺口不是「代理不夠多」，而是「代理交付模板不夠硬」。
- 只寫 PM / Tech / QA 職責不足，還必須定義：
  - 可讀 inputs。
  - 可做 allowed_actions。
  - 禁止 forbidden_actions。
  - 必填 output_schema。
  - 必須 blocked 的 block_conditions。
  - 交付前 self_check。
  - 下游 handoff_contract。
- PM 的價值是把 Owner 需求變成可驗收任務，不是只改寫需求句子。
- Tech 的價值是只在任務契約內實作，並說清契約影響與直接消費者同步。
- QA 的價值是主動反證，而不是重跑 Tech 的測試。
- Architect 的價值是拒收不合格交付，而不是替代理補完它們沒做的工作。

## Architect Conclusion

- 已在 `AGENTS.md` 新增「角色卡與任務卡契約」。
- 已新增 PM / Tech / QA 固定交付欄位。
- 已新增 Architect 拒收條件。
- 已同步 CAO stock agent profiles 與 runner prompt，避免正式文檔和實際代理行為脫節。
- 本輪不需要 PM / Tech / QA 接力，因為這是流程規則補強，屬 Architect 職責。

## Next Action

- 下一次 `run_architect_task.sh auto` 實際任務要觀察：
  - PM 是否輸出完整 `# TASK:`。
  - Tech 是否輸出完整 `# CHANGELOG:`。
  - QA 是否輸出完整 `# QA_REPORT:`。
  - QA 是否真的主動反證，而不是只跑測試。
- 若任一代理不合格，Architect 直接退回，不吸收、不合併、不標記完成。
