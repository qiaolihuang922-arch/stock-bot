# CURRENT_STATE.md

本文件由 Architect 維護，作為專案短上下文。新會話應先讀本文件，再依任務讀必要摘要文件或局部源碼。

## 專案狀態

- 專案：台股策略報文機器人。
- 目前穩定線：`v19.3.4` 報文解釋力修正已通過指定 QA。
- 最近已出現 `v19.3.1` formatter / daily write guard / Yahoo daily fallback 修正紀錄。
- `v19.4` 曾有策略診斷方向，屬待 PM 確認的下一階段，不代表已實作。
- 預設只處理 `core/watchlist.py` 的 12 檔股票。

## 已完成功能

- 策略層、顯示層、持倉邏輯、行情顯示衝突修復已完成。
- 第一版回測已完成：每日 snapshot、replay/backfill、相對表現驗證、持倉/新進場顯示邊界已接入。
- 線上持倉來源改為 Supabase `positions`，`shares=0` 視為未持倉，`shares>0` 視為持倉。
- Telegram 報文採總覽摘要、持倉卡片、觀察卡片的多訊息格式；完整字段仍保留於 formatter。
- daily snapshot 寫入已有 12 檔完整覆蓋保護，缺檔時不得寫入每日穩定樣本。
- TWSE daily K-line 不可用時，已有 Yahoo daily fallback 設計紀錄。
- v19.3.2 盤中報文驗收補充已通過指定 QA：
  - 智原持倉小虧洗盤語意顯示為 `洗盤警戒`。
  - RR raw 為 0 或接近 0 且未被隱藏時顯示 `RR 0.00（不足）`。
  - 價格行保留完整全形右括號。
  - 報文版本維持 `v19.3.2`，未持倉四分類未退回全 `不買`。
- v19.3.3 formatter 一致性修正已通過指定 QA：
  - 合格未持倉 `BUY` 摘要顯示 `【可買 N】`，不進入 `可觀察但不可買`。
  - `ADD_10 / ADD_20 / ADD_30` 在持倉摘要、詳情標題、決策行顯示加碼語意。
  - `TAKE_PROFIT_*` 顯示停利，`REDUCE_*` 顯示減碼，`STOP_100` 顯示停損且不壓成減碼。
  - 停利 / 減碼 / 停損詳情決策行直接呈現策略 action。
  - 阻擋原因在摘要 / 詳情保持一致。
- v19.3.4 報文解釋力修正已通過指定 QA：
  - 回測行顯示樣本數、參考度、3 日勝率、相對報酬、判讀結果。
  - R3 且不新增時，摘要顯示 `🧭 原因`。
  - 今日新倉浮虧顯示 `新倉風控觀察` 或 `洗盤警戒`，不回退普通 `續抱觀察`。
  - 持倉詳情卡片包含 `下一步`。
  - 停利 / 減碼 / 停損詳情包含 `原因` 與 `下一步`，且不改變交易 action。

## 現有模組

- `main.py`：主要執行入口。
- `app.py`：Render 入口，觸發 GitHub Actions workflow。
- `core/watchlist.py`：12 檔股票唯一配置來源。
- `services/analysis.py`：策略決策來源。
- `core/generator.py`：報文產生、排序、Telegram 輸出。
- `core/condition_engine.py`：條件映射層。
- `services/stock_api.py`：行情與歷史資料來源。
- `services/signal_store.py`：`signal_runs / signal_items / signal_outcomes` 寫入。
- `services/daily_snapshot_store.py`：`daily_price / daily_signal_snapshot` 寫入。
- `core/signal_snapshot.py`：snapshot 組裝。
- `core/signal_validator.py`：snapshot 邏輯驗證。
- `services/position_store.py`：Supabase `positions` 持倉讀取。
- `core/holdings.py`：舊 replay/backfill 邊界兼容，不是線上持倉來源。
- `scripts/dry_run_replay.py`：dry-run replay。
- `scripts/backfill_signals.py`：受保護 backfill，預設不寫庫。
- `supabase/functions/telegram-execution/index.ts`：Telegram 持倉文字命令處理。
- `tests/`：目前以策略、formatter、snapshot、backfill/replay、行情來源等局部測試為主。

## 已知問題與風險

- `v19.4` 診斷指出未持倉股票的 `不買` 顯示過度壓縮，容易讓報文感覺過度保守。
- `shakeout_protected` 持倉保護條件偏寬，可能讓弱勢且離觸發遠的持倉仍顯示為 `洗盤觀察`。
- 高獲利、HOT/EXTENDED、量縮回落的持倉尚未有更清楚的 `核心續抱` 或 `風控觀察` 分支。
- intraday 報文可能混用 realtime price/change 與 Yahoo daily K-line 結構/量能，來源拆分需要更清楚顯示。
- RR 隱藏規則可解釋，但使用者視角可能覺得不一致。
- 正式 backfill 尚未完成；目前僅可依規定先 dry-run 與 validate。

## 目前進行中項目

- 建立 AI Team Workflow 的 Architect 控制文件。
- 常駐 Architect 規則文件為 `DISPATCH.md`、`RESEARCH.md`、`CURRENT_STATE.md`、`AGENTS.md`、`CLEANUP_PLAN.md`。
- 部門交付文件 `TASK.md`、`CHANGELOG.md`、`QA_REPORT.md` 保留為工作流入口，不視為無用文件。
- 固定 8 份 Markdown 工作流文件不得刪除，只允許更新內容。
- Architect 狀態輸出固定為 `DISPATCH.md`、`RESEARCH.md`、`CURRENT_STATE.md`、`AGENTS.md`、`CLEANUP_PLAN.md`。
- PM 已提交 `TASK.md`：v19.3.3 formatter 一致性修正需求。
- Tech 已提交 `CHANGELOG.md`：v19.3.3 formatter 映射修正與影響範圍。
- QA 已提交 `QA_REPORT.md`：指定局部 formatter / snapshot / strategy-output-to-card 驗證通過，`27 passed`。
- 本輪 v19.3.3 可視為指定顯示層一致性驗收通過；未覆蓋 full pytest、live Telegram、DB、replay/backfill。
- 研究任務已完成：策略層與顯示層一致性、買入 / 賣出 / 加碼提示缺失原因已整理到 `RESEARCH.md`。
- Architect 結論：`v19.3.3 formatter 一致性修正` 已完成指定驗收；後續若要處理策略門檻、live Telegram 或 full regression，需另開任務。
- v19.3.4 報文解釋力修正已完成指定 QA。
- v19.3.4 驗證：`.venv/bin/python -m pytest tests/test_generator_report.py`，`29 passed`。
- v19.3.4 未覆蓋：full pytest、live Telegram、DB、replay/backfill、策略門檻 regression。

## 影響模組判斷規則

- 報文分類、顯示文字、Telegram 卡片：主要影響 `core/generator.py` 與 formatter tests。
- 持倉策略、買賣/續抱/停利/風控邏輯：主要影響 `services/analysis.py` 與策略 tests。
- 行情來源、TWSE/Yahoo fallback、source 標示：主要影響 `services/stock_api.py`、`core/generator.py` 與行情 tests。
- snapshot / DB 寫入保護：主要影響 `services/daily_snapshot_store.py`、`services/signal_store.py`、`core/signal_validator.py`。
- replay/backfill：主要影響 `scripts/dry_run_replay.py`、`scripts/backfill_signals.py` 與相關 tests。
- Telegram 持倉命令：主要影響 `supabase/functions/telegram-execution/index.ts` 與 Supabase schema docs。

## 當前交付檢查

- `DISPATCH.md`：已更新為 v19.3.4 報文解釋力修正。
- `TASK.md`：PM 已改寫為 v19.3.4 報文解釋力修正需求。
- `CHANGELOG.md`：Tech 已更新 v19.3.4 報文解釋力修正摘要。
- `QA_REPORT.md`：QA 已更新，指定測試通過。
- Architect 結論：本輪摘要鏈路已同步，可作為 v19.3.4 報文解釋力修正驗收狀態。

## 對話窗啟動規則

- 各部門對話窗不會自動收到通知。
- Owner 只需在對應對話窗發送 `DISPATCH.md` 內的固定啟動句。
- 各角色自行讀 `DISPATCH.md` 判斷是否該工作。
- 若狀態未輪到該角色，該角色只回報等待或阻塞，不做越權工作。

## 當前研究任務

- task_id: `v19.3.2-strategy-display-alignment-research`
- 研究文件：`RESEARCH.md`
- 目前狀態：PM / Tech / QA 研究摘要已完成，Architect 已吸收結論。
- 研究限制：先不改代碼，不升 v19.4，不跑全局測試，不正式寫庫。
- 核心結論：
  - 未持倉買入少主要由 RR、過熱、漲停不追、量能、距離等 blocker 造成。
  - 持倉賣出 / 加碼少部分來自策略保護持倉與加碼條件偏嚴。
  - 顯示層確有一致性風險：合格 BUY 摘要、ADD 顯示、STOP 顯示、TAKE_PROFIT / REDUCE / STOP 詳情決策行需補強。
- 後續狀態：
  - v19.3.3 formatter 一致性修正已完成。
  - Tech 已只修 formatter 映射與必要測試，未改策略門檻。
  - QA 已做局部 formatter / snapshot / strategy-output-to-card 一致性驗證。
