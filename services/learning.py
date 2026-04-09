import json
import os
from datetime import datetime

FILE_PATH = "data/trades.json"


def init_storage():
    if not os.path.exists("data"):
        os.makedirs("data")

    if not os.path.exists(FILE_PATH):
        with open(FILE_PATH, "w") as f:
            json.dump([], f)


def already_recorded(stock, date):
    with open(FILE_PATH, "r") as f:
        data = json.load(f)

    for t in data:
        if t["stock"] == stock and t["date"] == date:
            return True

    return False


def record_trade(name, decision, price, buy, stop):

    init_storage()

    today = datetime.now().strftime("%Y-%m-%d")

    # 🔥 防重複（跨程式）
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

    with open(FILE_PATH, "r") as f:
        data = json.load(f)

    data.append(trade)

    with open(FILE_PATH, "w") as f:
        json.dump(data, f, indent=2)

    print(f"[記錄] {name} 成功")