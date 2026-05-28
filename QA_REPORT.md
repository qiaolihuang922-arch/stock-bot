# QA_REPORT:

## 測試範圍

依據 `TASK.md`、`CHANGELOG.md`、git diff 驗證本輪 `v20.1.1` Telegram 手機閱讀降噪任務。

實測範圍：

- `core/generator.py` 版本、summary、明日計畫、持倉風控、未持倉卡、淘汰卡文案。
- 直接測試：`tests/test_generator_report.py`、`tests/test_market_theme_evidence.py`、`tests/test_notifier.py`。
- git diff 僅包含：
  - 可吸收 diff：`core/generator.py`、三個相關測試、`CHANGELOG.md`。
  - worktree 殘留：未見本輪範圍外檔案；但目前仍是 uncommitted worktree，不應整包合併為主 repo，需由 Architect 只吸收上述 diff。

已執行：

- `arch -arm64 .venv/bin/python -m pytest tests/test_generator_report.py tests/test_market_theme_evidence.py tests/test_notifier.py`
- 結果：`60 passed, 21 warnings`
- 警告為既有相依套件 / Python deprecation，未造成測試失敗。

另補 QA fixture：

- 盤後持倉加碼 + 未持倉追蹤 fixture。
- 驗證 summary 為最後一則、header 為 `v20.1.1`、無 `v20.1.0`、無 `若收盤`、無 `不代表看空產業`、無 `技嘉｜明日風控｜加碼10`。

## 關聯風險掃描

`TASK.md`、`CHANGELOG.md`、diff 一致：本輪只改 Telegram formatter 呈現與測試，未見策略 decision、DB schema、watchlist、live delivery、replay/backfill 變更。

直接消費者：

- `formatTelegramMessages()` 仍回傳 message list，順序維持詳情在前、summary 最後。
- `tests/test_notifier.py` 驗證 `send_many()` 仍消費最後 summary，版本 header 已同步 `v20.1.1`。
- `core/generator.py` message list contract 未改型別或 payload shape。

主要契約點：

- `VERSION = "v20.1.1"` 已在 `core/generator.py`。
- 盤後加碼計畫輸出 `待觸發加碼10/20/30`。
- 持倉風控收斂為 `風控：守警戒線，不追價`。
- 未持倉買點改為手機短句。
- 淘汰 guard 改為 `產業：未判斷產業多空`。

清理 / 瘦身 / refactor 證據表要求：本輪不是清理任務，不適用 `path / claim / evidence / risk / action` 表。

## 跨區塊語意一致性

以 Owner 手機閱讀順序檢查：

1. 最後一則 summary 第一行顯示 `【05/28 盤後｜v20.1.1】`。
2. Summary 先列今日結論、新倉、持倉、明日計畫與風控，不再把加碼列成風控。
3. 明日計畫顯示 `技嘉｜待觸發加碼10`。
4. 持倉風控顯示 `技嘉｜風控：守警戒線，不追價`，未重複完整加碼下一步。
5. 未持倉卡顯示 `買點：不買，等RR達標` 或 `買點：不可買，等...` 類短句，未見舊式長 pipe chain。
6. 淘汰卡不再出現 `不代表看空產業`，改為短 guard。

未發現 summary、明日計畫、持倉風控、詳情卡之間把同一行動互相改寫成相反含義。

## 使用者誤讀風險

已反證主要誤讀路徑：

- 加碼不再被放入 `明日風控｜加碼10`，降低 Owner 把加碼與風控混讀的風險。
- 盤後輸出未見 `若收盤`，避免盤後報文像盤中未定案。
- 未持倉追蹤在 summary 中仍標示僅追蹤、不列入明日計畫，不會被包裝成可買。
- 淘汰股 guard 改成 `未判斷產業多空`，沒有把策略淘汰誤讀成產業看空。

殘留但可接受：

- Summary 仍保留較多舊版漏斗 / 索引資訊；`CHANGELOG.md` 已列為殘留風險。本輪目標是降噪與禁止語意修正，不是完整 message list 重排。

## 質疑與反證

- PM 是否漏需求：直接消費者、版本契約、手機閱讀路徑、禁止文案都有列出；未見 `TASK.md` / `CHANGELOG.md` / diff 矛盾。
- Tech 是否漏同步：版本同步到 formatter 與三個直接測試；notifier consumer 有測。
- 測試是否只覆蓋欄位：QA 額外用盤後混合 fixture 檢查實際 Telegram message list、summary 最後一則、手機閱讀順序與 forbidden 文案。
- 指定清單外風險：檢查了 worktree diff 範圍，未見策略、DB、watchlist、live delivery 變更；未見需要阻塞的範圍外殘留。

## 未測項目

- 未跑 full pytest：本輪 QA 分級為 L2，且 diff 限於 formatter 與直接 consumer tests。
- 未做 live Telegram delivery、live Supabase write、正式 backfill：`TASK.md` 明確禁止。
- 未驗證真實 Owner 長報文全量資料源：本輪以既有與補充 fixture 驗證 formatter contract，未接 live data。

## QA 結論

通過
