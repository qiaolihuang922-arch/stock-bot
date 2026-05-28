# TASK: Telegram Breakout Distance Always Visible

## 任務狀態

- task_id: telegram-breakout-distance-always-visible-v20.2.1
- 任務類型: tiny_patch
- 狀態: ready_for_tech
- 主 bug: Telegram / 報文卡片的盤面行在部分突破狀態下未保留「突破距離」資訊，Owner 手機閱讀時無法快速判斷距離突破點遠近。
- 版本建議: patch v20.2.1
- QA 分級建議: L1
- 停止條件: 完成持倉與未持倉卡片「盤面行」突破距離顯示契約，並通過直接 formatter / snapshot / notifier consumer smoke；不延伸到策略、資料來源、DB、watchlist、backfill 或全量報文重設。

## Owner 問題

Owner 要解決的是：目前 Telegram / 報文中，突破距離資訊可能只在部分狀態顯示，導致手機上看到「已突破 / 臨界突破 / 接近突破 / 遠離突破」時，無法一致判斷距離突破點多少。

本輪只修顯示契約：不管距離突破點多少，只要有突破距離資料，持倉與未持倉卡片的盤面行都要保留括號距離資訊。

## 使用者可見結果

Owner 在 Telegram 手機報文中查看持倉或未持倉卡片時，盤面行會一致看到突破距離，例如：

- 已突破也顯示距離。
- 臨界突破也顯示距離。
- 接近突破也顯示距離。
- 遠離突破也顯示距離。
- 只有資料缺失時，才可省略距離或顯示明確缺資料文案。

## 非目標

- 不改策略 decision。
- 不改買 / 賣 / 加碼 / 減碼 / 停損 / 停利判斷。
- 不改突破分類邏輯或門檻。
- 不改 DB schema。
- 不改 watchlist。
- 不做 live Supabase write。
- 不做 live Telegram delivery。
- 不做 replay / backfill。
- 不重構整份報文、summary、漏斗、持倉主行動或市場 / 題材 evidence。

## 影響模組

- 直接模組:
- Telegram / 報文 formatter：core/generator.py 或等價卡片盤面行 formatter。
- 相關 formatter / snapshot tests。
- notifier direct-consumer smoke tests。
- 不應影響模組:
- services/analysis.py
- core/watchlist.py
- DB store / schema / migration
- replay / backfill scripts
- live Telegram sender behavior

## 直接消費者

- Owner 手機 Telegram 報文。
- Telegram message list formatter output。
- Telegram notifier payload consumer。
- 既有 formatter / snapshot tests。

## 輸出契約

### 單一輸出契約

持倉與未持倉卡片的「盤面行」若有突破距離資料，必須一律顯示括號距離，不得因狀態是已突破、臨界突破、接近突破或遠離突破而省略。

### 顯示規則

- 有距離資料:
- 盤面行必須包含突破狀態 + 括號距離。
- 括號距離格式沿用既有報文風格，不新增新的長句。
- 無距離資料:
- 可省略距離。
- 或顯示明確缺資料，例如 距離缺資料。
- 不得用 0%、空括號或看似有效的假距離代替缺資料。
- 持倉與未持倉卡片需一致套用。
- 不改卡片排序、分組、主行動、summary 結論或漏斗計數。

### 版本契約

- 本輪是使用者可見 Telegram 報文顯示修正，建議 header / VERSION 升為 v20.2.1。
- 已存在且不得回退的契約:
- Telegram 報文手機優先。
- 使用者可見報文變更需同步 core/generator.py 的 VERSION 或等價 header 常量。
- 不得低於已推送的 v20.2.0 使用者可見契約；若程式目前 header 與摘要文件版本不一致，Tech 必須 blocked 要求 Architect 釐清，不得自行降版。
- 市場 / 題材 evidence 不得放寬個股買點。
- 同一檔持倉同一份報文只能有一個主行動。
- 空區塊、0 計數、無行動占位不得新增。

## 驗收條件

1. Formatter 產出的持倉卡片盤面行，在已突破、臨界突破、接近突破、遠離突破任一狀態且有距離資料時，都保留括號距離。
2. Formatter 產出的未持倉卡片盤面行，在已突破、臨界突破、接近突破、遠離突破任一狀態且有距離資料時，都保留括號距離。
3. 距離資料缺失時，不輸出假距離；可省略或顯示明確缺資料。
4. Telegram header / version 顯示 v20.2.1，且測試期望同步。
5. Notifier direct-consumer smoke 確認 message list / payload shape 未破壞。
6. 驗證到 formatter / snapshot / notifier direct consumer 即可停止；若發現策略分類、突破門檻、資料來源缺漏或其他報文噪音問題，只記待辦，不納入本輪。

## 範例或 fixture

手機閱讀路徑：Owner 打開 Telegram，先掃 summary，再往下看持倉與未持倉卡片；在每張卡片的盤面行應直接看到突破狀態與距離，不需要進詳情或自行推算。

期望輸出形狀：

持倉｜2330 台積電
盤面：已突破（距突破點 +1.8%）
行動：續抱

未持倉｜2454 聯發科
盤面：遠離突破（距突破點 -6.4%）
狀態：僅追蹤

缺資料可接受形狀：

未持倉｜XXXX 範例股
盤面：接近突破（距離缺資料）
狀態：僅追蹤

或沿用既有風格省略距離，但不得輸出假距離。

## 明確禁止事項

- 禁止修改策略 decision、突破門檻、買賣 / 加減碼判斷。
- 禁止修改 DB schema、migration、Supabase write path。
- 禁止修改 watchlist。
- 禁止 live Supabase write。
- 禁止 live Telegram delivery。
- 禁止正式 replay / backfill。
- 禁止把本 tiny patch 擴成報文重排、summary 改寫、market evidence 改寫或 L3 驗證。
- 禁止新增空區塊、0-count 文案、無行動占位。
- 禁止回退既有 v20.2.0 Telegram / evidence / 手機閱讀契約。

## 阻塞條件

- 若 formatter 卡片資料模型完全沒有突破距離欄位，且無法從既有 formatter input 取得距離，Tech 必須 blocked，要求 Architect 補充資料來源邊界；不得新增策略計算或改資料來源。
- 若目前程式 header / VERSION 不是已推送的 v20.2.0 或更高，且摘要文件互相矛盾，Tech 必須 blocked 要求 Architect 釐清版本基準；不得自行降版或沿用舊版。
- 若完成本顯示契約需要改策略分類、DB schema、watchlist、live delivery 或 backfill，必須 blocked，另開任務。
- 若 QA 發現同一距離資訊在持倉與未持倉卡片顯示規則不一致，或 notifier payload shape 被破壞，本輪不得通過。
