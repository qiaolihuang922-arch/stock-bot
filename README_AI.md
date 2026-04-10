# 🔥 AI交易系統守則（FINAL v5｜實盤版）

本文件為最高規範  
任何修改必須遵守  

---

# 🧠 一、核心原則（不可動）

## 1️⃣ 唯一決策

所有交易只能來自：

👉 strategy()

輸出：
- decision（BUY / WAIT / NO）
- buy  
- stop  
- position  

---

❌ 禁止：

- 第二 decision  
- generator 判斷  
- score 決策  
- AI 影響 decision  
- learning 影響 decision  

---

## 2️⃣ 決策流程（單向）

市場 → 結構 → 量能 → 事件（突破 / 回踩）→ 風控 → decision  

---

❌ 禁止回頭修正 decision  

---

## 3️⃣ 決策優先級

strategy > 風控 > 市場 > 結構 > AI  

---

## 4️⃣ AI定位（強制隔離）

AI = 解釋  

只能輸出：
- BUY｜原因  
- WAIT｜原因  
- NO｜原因  

---

❌ 禁止：

- 改 decision  
- 改 buy / stop  
- 提供交易建議  
- 提供倉位  

---

## 5️⃣ 資料流（不可逆）

stock_api → analysis → ai → generator → learning  

---

❌ 禁止：

- learning → strategy  
- AI → strategy  
- generator → strategy  

---

## 6️⃣ 風控（內建於 strategy）

必須在 strategy 內完成：

- stop < buy  
- risk ≤ 8%  
- RR ≥ 1.2  

---

❌ 禁止外部補風控  

---

# 📦 二、系統架構（完整不可缺）

---

## 📁 services/analysis.py

👉 唯一決策引擎  

包含：

- volume_signal  
- trend_signal  
- market_signal  
- structure_ok  
- breakout_entry  
- pullback_entry  
- risk_control  
- strategy  

---

❌ 禁止：

- 使用 AI  
- 使用 score  
- 使用 learning  
- 使用外部資料  

---

## 📁 services/ai.py

👉 解釋模組  

包含：

- normalize_ai_output  
- fallback_ai  
- ai_analysis  

---

輸出：

BUY / WAIT / NO（附原因）  

---

❌ 禁止：

- 影響 decision  
- 提供交易建議  

---

## 📁 services/learning.py

👉 記錄模組  

包含：

- record_trade  
- update_trade_result  

---

規則：

- price = buy  
- buy > stop  
- status：pending → closed  

---

❌ 禁止：

- 影響策略  
- 使用未來資料  

---

✅ 必須：

- 回傳 success / fail  
- 有 debug log  

---

## 📁 services/stock_api.py

👉 資料來源  

---

提供：

- get_twse  
- get_yahoo  
- get_realtime_price  

---

❌ 禁止：

- 分析  
- 判斷  

---

## 📁 services/notifier.py

👉 發送訊息  

---

❌ 禁止：

- 參與決策  

---

## 📁 core/generator.py

👉 系統中樞  

---

負責：

- 呼叫 strategy  
- 呼叫 AI  
- 呼叫 learning  
- 整理輸出  

---

❌ 禁止：

- 改 decision  
- 改 buy / stop  
- 做交易判斷  

---

✅ 可做：

- 顯示最佳標的（不改 decision）  

---

## 📁 core/utils.py

👉 工具函數  

---

❌ 禁止：

- 決策  
- 呼叫 API  

---

## 📄 main.py

👉 程式入口  

---

只做：

- 呼叫 generator  
- 輸出結果  

---

❌ 禁止：

- 寫策略  
- 寫邏輯  

---

## 📄 app.py

👉 API / Web入口  

---

只做：

- 接收請求  
- 呼叫 main / generator  

---

❌ 禁止：

- 交易邏輯  

---

## 📄 config.py

👉 設定中心  

---

包含：

- API KEY  
- DB  
- flags（AI開關 / DEBUG）  

---

❌ 禁止寫邏輯  

---

## 📄 render.yaml

👉 部署設定  

---

## 📄 requirements.txt

👉 套件列表  

---

# 📦 三、資料來源

唯一：

👉 Supabase（trades）  

---

❌ 禁止：

- JSON  
- 本地資料  
- 雙資料源  

---

# 📊 四、資料規則

狀態：

- pending  
- closed  
- invalid  

---

## 使用

❌ 禁止：
使用 pending  

✅ 必須：
status = closed  

---

# 🧠 五、資料寫入

## record_trade：

- buy > stop  
- price = buy  
- 不可含未來資料  

---

## update_trade_result：

只能：

- win  
- loss  
- breakeven  

---

❌ 禁止：

- 當日寫結果  
- 未來資料  

---

# 🧠 六、防污染

## 1️⃣ 唯一鍵

(stock, trade_date)  

---

## 2️⃣ extra_data 限制

❌ 禁止：

- result  
- future_price  
- price_after  

---

## 3️⃣ learning隔離

❌ 不得影響 strategy  

---

# 🚫 七、紅線

禁止：

1. 多 decision  
2. AI 決策  
3. score 取代 strategy  
4. generator 做決策  
5. 移除停損  
6. 放寬風控  
7. learning 影響策略  
8. 使用 pending  
9. 多資料源  

---

# 🧠 八、修改前檢查

任何修改必須確認：

- 是否影響 strategy  
- 是否新增 decision  
- 是否影響風控  

👉 有 → 禁止  

---

# 🔥 九、v5 升級重點

- 決策改為「事件驅動」（breakout / pullback）  
- AI 完全對齊 decision_type  
- learning 支援 debug + success 機制  
- 顯示層精簡為交易員模式  

---

# 🚀 十、最終原則

👉 strategy 決定一切  
👉 系統