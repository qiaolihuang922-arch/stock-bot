# TASK: strategy_soft_gate_patch_v21_1_20260616

## 任務狀態

- task_id: `strategy_soft_gate_patch_v21_1_20260616`
- 任務類型: `risk_patch`
- 狀態: `implemented`
- 版本建議: 報文 header 維持 `v21.1`
- QA 分級: L3

## Owner 問題

Owner 指出 DB replay 後仍有策略不合理：

- 漲停 / 過熱 / 連漲後永遠不能買。
- `等回測`、`等接近`、`買點品質 D`、`RR不足` 可能變成死規則。
- 策略應該能產生真實股市會出現的 `可買` 與 `可準備`，不能只顯示等待。
- 修正必須使用 DB replay 和既有資料，不得用對話記憶或假跨日資料。

## 使用者可見結果

- HOT / EXTENDED / LIMIT_REBOUND 不再一律視為硬性不可行動。
- 漲停鎖死仍不追；漲停後反彈改成隔日確認 / 回測承接邏輯。
- 低 RR 不再全部硬擋：
  - `RR < 1.0` 仍硬擋。
  - `1.0 <= RR < 1.5` 只有在無 setup 且品質低時硬擋。
- 強證據可把軟阻擋股票推到 `可準備`，但不直接變成 `可買`。

## 非目標

- 不做 live Telegram delivery。
- 不寫 DB / 不回寫 / 不去重。
- 不新增 DB schema。
- 不承諾任何單一標的必買。

## 影響模組與直接消費者

- `core/generator.py`
  - strategy gate / funnel decision。
- `presentation/report.py`
  - evidence / score 顯示契約。
- `tests/test_generator_report.py`
  - 使用者可見報文與 funnel regression。
- 直接消費者:
  - official generator message list。
  - dry-run / runner artifact。
  - Telegram mobile reader。

## 輸出契約

- `可買`、`可準備`、`隔日確認`、`等冷卻`、`等回測`、`等接近` 必須語意分開。
- `可準備` 是不可直接下單的準備區，不得升格成買入建議。
- 熱度 / 漲停反彈 / 低 RR 屬軟阻擋時，要能被 evidence 推進到 `可準備`。
- 硬阻擋仍 fail closed。
- 缺資料仍不得產生可買。

## 驗收條件

- Generator report tests 通過。
- Full pytest 通過。
- DB replay artifact 證明：
  - strategy 不再 deadlock。
  - 存在真實 `可買` 路徑。
  - 存在 `可準備` 路徑。
  - snapshot tradeable 不被 funnel 擋掉。
- 不做 DB write / schema change / live TG。

## 失敗標本與驗收路由

- 失敗標本:
  - Owner 貼出的 `06/16` 報文中，多檔連漲後仍被 `淘汰 / 等接近 / 等資料`。
  - Owner 質疑「為什麼連續十幾天沒有可買 / 加碼點」。
- 驗收路由:
  - official generator tests。
  - DB replay artifact:
    - `reports/audit/strategy_buy_path_replay_v21_1_soft_gates_20260616.json`
    - `reports/audit/strategy_rule_outcomes_v21_1_soft_gates_20260616.json`

## 禁止事項與阻塞條件

- 禁止用 helper fixture 宣告 production replay 完成。
- 禁止用 runtime dict / 對話記憶當跨日資料。
- 禁止 live Telegram。
- 禁止手寫 production DML。
