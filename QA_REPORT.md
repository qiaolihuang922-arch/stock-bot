# QA_REPORT:

## 測試範圍

依據：`TASK.md`、`CHANGELOG.md`、`git status --short`、`git diff --stat`、必要 diff 與局部 formatter / test code。

可吸收 diff：

- `core/generator.py`
- `tests/test_generator_report.py`
- `tests/test_market_theme_evidence.py`
- `tests/test_notifier.py`
- `CHANGELOG.md`

worktree 殘留：

- `git status --short` 只顯示上述 5 個 tracked 修改，未看到額外殘留或不相關 tracked diff。
- 本 QA 未修改任何 tracked file。

實測命令：

- `arch -arm64 .venv/bin/python -m pytest tests/test_generator_report.py tests/test_market_theme_evidence.py tests/test_notifier.py`
  - 結果：`64 passed, 21 warnings`
- `rg` 檢查舊版 header / 禁止語意 / 舊隔日計畫 / 空明日計畫文案
  - 產品碼未殘留；命中只在測試 `assertNotIn`。
- `rg -n "format_next_day_plan" core tests`
  - 無命中，舊 helper 無直接呼叫方。
- 另跑 inline 手機閱讀 fixture：
  - risk_only：智原 / 緯創只在持倉風控檢查，無明日計畫、無明日計畫 0、無隔日計畫。
  - risk_plus_add：持倉風控檢查早於明日計畫 1，技嘉保留待觸發加碼10，智原 / 緯創未進明日計畫。
  - notifier smoke：最後一則 message 保留 `【05/28 盤後｜v20.1.3】` header。

## 關聯風險掃描

直接消費者：

- Owner 手機 Telegram summary：已用接近 `TASK.md` fixture 的智原 / 緯創 / 技嘉組合反證。
- Telegram message list contract：`formatTelegramMessages()` 仍以 summary 作為最後一則。
- notifier payload 消費者：`send_many()` 最後一則 header smoke 通過。
- formatter regression：新增與既有測試覆蓋 `v20.1.3`、空明日計畫省略、技嘉加碼保留。

契約檢查：

- `VERSION = "v20.1.3"`，未回退 `v20.1.1` / `v20.1.2`。
- 未看到策略、DB、watchlist、live Telegram、Supabase write、replay/backfill 相關檔案變更。
- 本輪不是清理 / 瘦身 / refactor 任務；雖移除舊 helper，但 Tech 有 `rg format_next_day_plan` 證據，QA 也重查無呼叫方。

## 跨區塊語意一致性

手機閱讀順序反證通過：

1. Header：`【05/28 盤後｜v20.1.3】`
2. 今日結論：有非重複明日事項時顯示持倉風控檢查 3 檔；明日計畫 1 項
3. 今日交易紀錄：無新增
4. 持倉風控檢查：智原 / 緯創顯示明日未修復降級
5. 明日計畫：只出現 `技嘉｜待觸發加碼10`
6. 詳情索引：只有風控項時省略 `明日計畫 0`

未發現持倉風控檢查、明日計畫、詳情索引數量或名單互相矛盾。

## 使用者誤讀風險

已反證主要誤讀路徑：

- 智原 / 緯創不會在風控檢查後又被明日計畫重複包裝成第二個降級行動。
- 只有風控事項時，不輸出 `明日計畫 0`、`明日計畫：無新增下單` 或 `隔日計畫`，降低 Owner 誤以為還有隔日下單清單的風險。
- 技嘉 `待觸發加碼10` 仍保留在明日計畫，不會因去重被誤刪。
- 禁止回退文案如 `明日風控｜加碼10`、`若收盤`、`不代表看空產業` 未在產品輸出殘留。

## 質疑與反證

- PM 是否漏需求：`TASK.md` 已列版本、手機閱讀順序、直接消費者、非目標與禁止回退契約；未發現與 `CHANGELOG.md` / diff 矛盾。
- Tech 是否漏同步：版本、summary、詳情索引、formatter tests、notifier test 都有同步；直接呼叫方未漏。
- 測試是否能證明沒有破壞直接消費者：除 Tech 自檢外，QA 補了 inline fixture 與 notifier 最後訊息 smoke。
- 主動質疑：舊 helper 移除是否可能漏 runtime 呼叫方。反證結果：`rg format_next_day_plan core tests` 無命中，且 diff 未改外部 payload / DB / strategy 入口。

## 未測項目

- 未跑 full pytest：`TASK.md` QA 分級為 L1，且 diff 只涉及 formatter / tests / notifier smoke；可接受。
- 未跑 replay/backfill、live Telegram、live Supabase write：`TASK.md` 明確禁止；可接受。
- 未驗證真實 Telegram 手機裝置渲染：以 formatter 連續 summary 文字順序替代，符合本輪 L1 範圍。

## QA 結論

通過
