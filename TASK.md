# TASK: evidence chain 候選整包交付修正與指定驗證

## 任務狀態

- task_id：evidence_chain_candidate_changelog_qa_retry_20260530
- 任務類型：normal_patch
- 任務尺寸判斷：normal_patch
- 狀態：ready_for_tech
- 版本建議：本輪不升版，沿用目前 VERSION
- QA 分級建議：L2
- QA 分級理由：本輪不改策略、不改 Telegram、不 live write，但驗證範圍涉及 evidence chain write CLI / dry-run / fake execute / read-after-write / source fail-closed contract，超出單一文件 tiny patch；不升到 L3，因 Owner
明確指定驗證清單且禁止 full scope 擴張。

## Owner 問題

Owner 要繼續現有 evidence chain 候選，不清空 diff。Architect 已在隔離 worktree 放入 untracked dummy config.py 並加入 git exclude，Tech / QA 不得把 config.py 納入 diff。

目前需要 Tech 重新輸出整包 CHANGELOG.md，不能 blocked，不能寫「未編輯 CHANGELOG」或等價自相矛盾句。Tech 必須把 Owner 指定的 arm64 pytest 命令列為自檢之一；只有該命令仍失敗時才可 blocked。

隨後 QA 針對整包候選做指定驗證，確認 evidence chain 候選在 dry-run、fake execute、read-after-write、secret redaction、source fail-closed 與 allowed production row 上符合既有契約。

## 使用者可見結果

- Owner 看到本輪 evidence chain 候選可被完整交付與驗收，不再卡在交付摘要矛盾或測試環境誤判。
- Telegram 報文不變。
- Telegram VERSION 不變。
- 策略 decision 不變。
- 不產生 production DB 寫入。
- 不發送 live Telegram。

## 非目標

- 不清空、重置或重做現有 evidence chain 候選 diff。
- 不把 untracked dummy config.py 納入 diff。
- 不改 DB schema、table、column、RLS、grant、policy、role 或 migration。
- 不做 production live write。
- 不做 formal backfill。
- 不做 live Telegram delivery。
- 不改策略 decision、BUY / SELL / RR / 加減碼 / 停損停利門檻。
- 不改 Telegram formatter、summary、header、message list contract 或 VERSION。
- 不擴成 evidence chain 架構重設、全 repo refactor、全量清理或 full pytest。
- 本輪不處理新發現的旁支問題；旁支只記待辦交回 Architect。

## 影響模組

- 直接交付文件：
- CHANGELOG.md
- QA_REPORT.md
- 直接候選範圍：
- evidence chain approved / forbidden dry-run
- fake execute read-after-write
- read-after-write exception secret redaction
- runtime / unknown / mixed source fail-closed
- allowed production row pass
- 直接測試：
- tests/test_market_theme_evidence.py
- tests/test_market_theme_evidence_handoff.py
- 環境邊界：
- 隔離 worktree 的 untracked dummy config.py 只供測試環境使用，不是交付 diff。

## 直接消費者

- Tech：依本任務卡修正並重新輸出整包 CHANGELOG.md，保留現有候選 diff。
- QA：依本任務卡與 Tech 的 CHANGELOG.md 做整包驗證，輸出完整 QA_REPORT.md。
- Architect：依 TASK.md、CHANGELOG.md、QA_REPORT.md 判斷是否可吸收候選。
- Owner：透過 Architect final summary 看到 evidence chain 候選是否解除阻塞。

## 輸出契約

### Tech 輸出契約

CHANGELOG.md 必須從 # CHANGELOG: 開始，並重新輸出整包內容，至少包含：

- 修改內容：描述本輪實際完成的 evidence chain 候選與交付修正。
- 修改檔案：逐一列出實際 diff 檔案；不得列入 untracked dummy config.py。
- 契約影響：說明 dry-run、fake execute、read-after-write、source status、telegram_confirmed、strategy_consumer、secret redaction、allowed production row 的 contract。
- 版本同步：明確寫本輪不改 Telegram VERSION，且未改 Telegram header。
- 直接消費者同步：CLI / tests / QA 驗證路徑已同步。
- 未影響模組：DB schema、production live write、formal backfill、live Telegram、策略 decision、Telegram formatter / summary / header 均未改。
- 自檢命令：必須包含以下命令之一：
- arch -arm64 .venv/bin/python -m pytest tests/test_market_theme_evidence.py tests/test_market_theme_evidence_handoff.py -q
- 殘留風險：只列本輪真實殘留風險，不得用「QA 會驗」代替自檢。

Tech 禁止在 CHANGELOG.md 寫：

- 未編輯 CHANGELOG.md
- 本回覆提供完整 CHANGELOG 供 runner 寫入
- 任何暗示 CHANGELOG.md 沒被本輪更新、但實際又已 modified 的矛盾文字。
- 在 arm64 指定測試未失敗前，不得寫 blocked。

### QA 輸出契約

QA_REPORT.md 必須從 # QA_REPORT: 開始，並整包驗證以下項目：

- approved dry-run pass。
- forbidden dry-run fail closed / pass negative expectation。
- fake execute read-after-write pass。
- read-after-write exception secret redaction。
- runtime source：status=insufficient-data、telegram_confirmed=false、strategy_consumer=fail-closed。
- unknown source：status=insufficient-data、telegram_confirmed=false、strategy_consumer=fail-closed。
- mixed source：status=insufficient-data、telegram_confirmed=false、strategy_consumer=fail-closed。
- allowed production row pass。
- git diff --check 通過。
- 確認 dummy config.py 未納入 diff。
- 確認未改 DB schema、未 live write、未 live Telegram、未改策略 decision、未改 Telegram VERSION。

QA 必須使用或覆蓋以下命令：

arch -arm64 .venv/bin/python -m pytest tests/test_market_theme_evidence.py tests/test_market_theme_evidence_handoff.py -q
git diff --check

## 已存在且不得回退的契約

- evidence chain 候選 diff 必須保留，不得清空。
- config.py 是隔離 worktree 的 untracked dummy config，不得納入 diff。
- write credential resolution 既有契約不得回退：env 優先，env 缺失時可 fallback repo config；service key alias 兼容 SERVICE_ROLE_KEY 與 SUPABASE_SERVICE_ROLE_KEY。
- execute JSON / validation output 不得輸出 URL、read key、service-role key、截斷值或 hash。
- approved dry-run 可產生合法 dry-run 結果。
- forbidden dry-run 必須 fail closed，不得產生可執行寫入。
- fake execute 只可用於測試 read-after-write contract，不代表 production live write。
- read-after-write exception 必須 secret redaction。
- runtime / unknown / mixed source 不得 confirmed，必須：
- status=insufficient-data
- telegram_confirmed=false
- strategy_consumer=fail-closed
- allowed production row 必須 pass。
- 本輪不得改 DB schema。
- 本輪不得 live write。
- 本輪不得 live Telegram。
- 本輪不得改策略 decision。
- 本輪不得改 Telegram VERSION。

## 驗收條件

1. Tech 重新輸出整包 CHANGELOG.md，且不包含「未編輯 CHANGELOG.md」或等價自相矛盾句。
2. Tech CHANGELOG.md 明確列出實際修改檔案，且不包含 dummy config.py。
3. Tech 自檢至少包含並通過：

arch -arm64 .venv/bin/python -m pytest tests/test_market_theme_evidence.py tests/test_market_theme_evidence_handoff.py -q

4. 若上述 arm64 pytest 仍失敗，Tech 才可 blocked，且必須列出失敗測試與錯誤摘要。
5. QA 重新輸出完整 QA_REPORT.md，不得只重跑 Tech 命令；必須逐項覆蓋 Owner 指定驗證清單。
6. QA 驗證 approved dry-run、forbidden dry-run、fake execute read-after-write、read-after-write exception secret redaction、runtime / unknown / mixed source fail-closed、allowed production row。
7. QA 驗證 git diff --check 通過。
8. QA 確認未清空現有 evidence chain 候選 diff，且 dummy config.py 未納入 diff。
9. QA 確認未改 DB schema、未 live write、未 live Telegram、未改策略 decision、未改 Telegram VERSION。
10. QA 結論只有在以上條件全部滿足時才可寫 通過；若指定契約任一失敗，必須 阻塞 或 conditional pass 並列出可驗證條件。

## 範例或 fixture

### Tech 自檢命令形狀

arch -arm64 .venv/bin/python -m pytest tests/test_market_theme_evidence.py tests/test_market_theme_evidence_handoff.py -q

### QA 驗證命令形狀

arch -arm64 .venv/bin/python -m pytest tests/test_market_theme_evidence.py tests/test_market_theme_evidence_handoff.py -q
git diff --check

### source fail-closed 期望形狀

runtime source:
status=insufficient-data
telegram_confirmed=false
strategy_consumer=fail-closed

unknown source:
status=insufficient-data
telegram_confirmed=false
strategy_consumer=fail-closed

mixed source:
status=insufficient-data
telegram_confirmed=false
strategy_consumer=fail-closed

### allowed production row 期望形狀

source_family=production_db
support_level=confirmed 或 supporting
evidence_status=confirmed
freshness=fresh
result=pass

### 手機閱讀路徑

本輪不改 Telegram 報文、summary、header 或 VERSION，因此沒有新的手機報文輸出形狀。QA 只需確認 Telegram 使用者可見輸出未被本輪 diff 改動；不得要求新增手機報文 snapshot。

## 明確禁止事項

- 禁止清空、重置或丟棄現有 evidence chain 候選 diff。
- 禁止把 dummy config.py 納入 diff。
- 禁止使用 destructive git 操作處理候選 diff。
- 禁止修改 DB schema、table、column、RLS、grant、policy、role 或 migration。
- 禁止 production live write。
- 禁止 formal backfill。
- 禁止 live Telegram delivery。
- 禁止修改策略 decision。
- 禁止修改 Telegram VERSION。
- 禁止修改 Telegram formatter、summary、header 或 message list contract。
- 禁止把 runtime / local / unknown / mixed source 描述成 production source-of-truth。
- 禁止在指定 arm64 pytest 尚未失敗前寫 blocked。
- 禁止把本輪擴成 full pytest、全 repo refactor、evidence chain 架構重設或策略重設。

## 阻塞條件

- arch -arm64 .venv/bin/python -m pytest tests/test_market_theme_evidence.py tests/test_market_theme_evidence_handoff.py -q 仍失敗，且失敗不是可由本輪交付摘要修正解決。
- Tech 無法確認 CHANGELOG.md 實際 diff 或無法移除自相矛盾文字。
- dummy config.py 已被納入 diff，且無法在不破壞候選 diff 的前提下移除。
- QA 發現現有 evidence chain 候選 diff 被清空、重置或混入本輪禁止變更。
- QA 發現 DB schema、live write、live Telegram、策略 decision 或 Telegram VERSION 被修改。
- QA 發現 runtime / unknown / mixed source 任一未 fail closed。
- QA 發現 read-after-write exception 會外洩 secret。
- QA 發現 allowed production row 無法 pass。

## 本輪停止條件

完成以下範圍即停止：

1. Tech 重新輸出合格整包 CHANGELOG.md。
2. Tech 用指定 arm64 pytest 作為自檢之一。
3. QA 依 Owner 指定清單完成整包驗證。
4. QA 通過 git diff --check。
5. Architect 可依 CHANGELOG.md 與 QA_REPORT.md 判斷是否吸收候選。

以下旁支不納入本輪：新增 DB schema、production backfill、真實 live write、live Telegram、策略門檻調整、Telegram 文案優化、runner 長期環境治理、full pytest 或 evidence chain 下一階段產品設計。若驗證中發現相關問題，只記
待辦交回 Architect。
