# 🔥 AI交易系統（不可破壞架構｜FINAL）

本文件為本專案最高規範  
所有 AI / 人工修改 必須遵守

違反本文件 = 錯誤修改

---

# 🧠 一、核心原則（最高優先）

## 1️⃣ 統一決策（唯一來源）

所有交易決策 **只能來自 `strategy()`**

唯一輸出：
- decision
- buy
- stop
- position

---

### ❌ 嚴禁：
- 第二套 decision
- AI 覆蓋 decision
- score 決定買賣
- generator 自行判斷進出場

---

## 2️⃣ 決策優先級（不可違反）

```
strategy > 風控 > 時間 > score > AI
```

---

說明：

- strategy：唯一交易決策
- 風控：stop / RR
- 時間：市場節奏
- score：排序用途
- AI：輔助解釋

👉 AI 永遠最低優先

---

## 3️⃣ 資料流（不可逆）

```
stock_api → analysis → ai → generator → notifier
```

---

### 🔒 規則：

- 不可逆流
- 不可回寫 decision
- 不可修改上游結果

---

## 4️⃣ AI 角色（嚴格限制）

AI只允許：

- 解釋（WHY）
- 輔助判斷
- 輸出文字

---

### ❌ AI禁止：

- 改 decision
- 改 buy
- 改 stop
- 改 position
- 建立交易邏輯

---

👉 AI = 語言層，不是決策層

---

## 5️⃣ 時間權重（市場節奏）

時間只影響：

- global_decision()
- score_stock()

---

### ❌ 禁止：

- 影響 strategy()
- 影響個股 decision

---

## 6️⃣ 風險優先（強制）

必須存在：

- stop < buy
- 最大風險 ≤ 8%
- RR ≥ 1.2

---

### ❌ 嚴禁：

- 移除停損
- 放寬風控
- 忽略RR

---

# 📦 二、模組職責（不可混用）

---

## 📁 services/analysis.py（🔥唯一決策核心）

負責：

- volume_model()
- trend_model()
- support_resistance()
- strategy()

---

### ⚠️ 規則：

- strategy = 唯一決策來源
- 不可被覆蓋
- 不可拆分決策
- 不可依賴 AI / score / time

---

## 📁 services/ai.py（AI輔助）

負責：

- ai_analysis()
- fallback_ai()

---

### ⚠️ 規則：

- 只輸出：
  - BUY / WAIT / NO
- 不可影響交易結果
- 不可控制倉位
- 不可計算買點

---

## 📁 services/stock_api.py（資料層）

負責：

- 市場數據

---

### ⚠️ 規則：

- 不可分析
- 不可決策

---

## 📁 services/notifier.py（輸出層）

負責：

- 發送訊息

---

### ⚠️ 規則：

- 不可改邏輯
- 不可參與決策

---

## 📁 core/generator.py（🔥整合中樞）

負責：

- 呼叫 strategy
- 呼叫 AI
- 輸出訊息
- 全局判斷

包含：

- global_decision()
- score_stock()
- 預備買點
- 最佳標的

---

### ⚠️ 核心限制：

❌ 不可：
- 做交易決策
- 覆蓋 strategy
- 修改 buy / stop

✅ 只能：
- 整理
- 排序
- 顯示

---

## 📁 core/utils.py

- 工具函數

---

## 📄 main.py

- 程式入口

---

## 📄 app.py

- 部署入口

---

## 📄 config.py

- 設定檔

---

## 📄 render.yaml

- 部署設定

---

## 📄 requirements.txt

- 套件依賴

---

# 🔄 三、系統流程（不可更改）

```
stock_api → analysis(strategy) → ai → generator → notifier
```

---

# 🔥 四、決策模型（strategy 必備）

必須同時包含：

---

## 1️⃣ 趨勢
- MA5 / MA20
- 高低點結構

---

## 2️⃣ 動能
- 漲跌
- 連續性

---

## 3️⃣ 量能
- 放量 / 縮量
- 出貨判斷

---

## 4️⃣ 位置
- 支撐 / 壓力
- 是否高位

---

## 5️⃣ 風控
- 停損
- RR

---

👉 缺一不可

---

# 🔥 五、全局決策（市場層）

輸出：

- 🔴 禁止交易
- 🟡 試單
- 🟢 可進場

---

邏輯：

- 多數一致 → 強
- 單一訊號 → 試單
- 全部觀望 → 禁止

---

# 🔥 六、評分系統（僅排序）

用途：

👉 選「最佳標的」

---

### ❌ 禁止：

- 用 score 決定買不買
- 用 score 覆蓋 decision

---

# 🚫 七、禁止修改清單（紅線）

以下任何一條違反都視為錯誤：

1. 多一個 decision
2. AI 影響交易結果
3. score 取代 strategy
4. generator 做決策
5. 移除停損
6. 移除風控
7. 拆分 strategy
8. 多決策來源

---

# 🧠 八、AI修改前必讀（強制）

AI在修改任何程式碼前，必須確認：

1. 是否改動 strategy？
2. 是否新增決策來源？
3. 是否影響風控？
4. 是否破壞單一決策？

👉 任一為「是」→ 禁止修改

---

# 🔥 九、核心總結（最重要）

```
strategy 決定交易
AI 不得干預
generator 不得決策
風控不可動
```

---

# 🚀 十、最終原則

```
AI只能強化系統
不能改變系統
```