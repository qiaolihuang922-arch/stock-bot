import json
import os
from datetime import datetime

# ===== 路徑（100%正確）=====
BASE_DIR = os.path.dirname(os.path.dirname(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")

RAW_FILE = os.path.join(DATA_DIR, "raw_trades.json")
CLEAN_FILE = os.path.join(DATA_DIR, "clean_trades.json")

# ===== 設定 =====
ENABLE_LEARNING = True
MAX_LOSS_STREAK = 3


# ===== 初始化 =====
def init_storage():
    if not os.path.exists(DATA_DIR):
        os.makedirs(DATA_DIR)

    for file in [RAW_FILE, CLEAN_FILE]:
        if not os.path.exists(file):
            with open(file, "w") as f:
                json.dump([], f)


# ===== 基本工具 =====
def load(file):
    with open(file, "r") as f:
        return json.load(f)


def save(file, data):
    with open(file, "w") as f:
        json.dump(data, f, indent=2)


# ===== 防重複 =====
def already_recorded(stock, date):
    data = load(RAW_FILE)
    return any(t["stock"] == stock and t["date"] == date for t in data)


# ===== 驗證 =====
def validate_trade(trade):
    if trade["price"] <= 0:
        return False

    if trade["decision"] not in ["buy", "sell", "hold"]:
        return False

    return True


# ===== 連續虧損 =====
def get_loss_streak():
    data = load(RAW_FILE)

    streak = 0
    for t in reversed(data):
        if t.get("result") == "loss":
            streak += 1
        elif t.get("result") == "win":
            break

    return streak


# ===== 主紀錄（只收集，不學習）=====
def record_trade(name, decision, price, buy=None, stop=None):

    if not ENABLE_LEARNING:
        print("⚠️ Learning 關閉")
        return

    init_storage()

    today = datetime.now().strftime("%Y-%m-%d")

    if already_recorded(name, today):
        print(f"[略過] {name} 今日已記錄")
        return

    trade = {
        "date": today,
        "time": datetime.now().strftime("%H:%M"),
        "stock": name,
        "decision": decision,
        "price": price,
        "buy": buy,
        "stop": stop,
        "result": None,
        "price_after": None
    }

    # 驗證
    if not validate_trade(trade):
        print("❌ 資料錯誤")
        return

    # 風控：停止污染
    loss_streak = get_loss_streak()
    if loss_streak >= MAX_LOSS_STREAK:
        print(f"🚨 連續虧損 {loss_streak} → 停止記錄")
        return

    # 存 RAW
    data = load(RAW_FILE)
    data.append(trade)
    save(RAW_FILE, data)

    print(f"✅ RAW記錄：{name}")


# ===== 更新結果（這才是關鍵）=====
def update_trade_result(name, date, result, price_after):

    init_storage()

    data = load(RAW_FILE)

    target = None

    for t in data:
        if t["stock"] == name and t["date"] == date:
            t["result"] = result
            t["price_after"] = price_after
            target = t
            break

    if not target:
        print("❌ 找不到交易")
        return

    save(RAW_FILE, data)
    print("✅ 已更新結果")

    # ===== 進 CLEAN（唯一入口）=====
    if result in ["win", "loss"]:
        clean = load(CLEAN_FILE)
        clean.append(target)
        save(CLEAN_FILE, clean)

        print("📊 已進入 CLEAN（可訓練）")


# ===== 控制 =====
def set_learning(status: bool):
    global ENABLE_LEARNING
    ENABLE_LEARNING = status
    print(f"🧠 Learning：{ENABLE_LEARNING}")


def reset_learning():
    save(RAW_FILE, [])
    save(CLEAN_FILE, [])
    print("♻️ 清空完成")