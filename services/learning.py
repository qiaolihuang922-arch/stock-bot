 import json
import os
from datetime import datetime

FILE_PATH = "data/trades.json"


# ===== 建立檔案 =====
def init_storage():
    if not os.path.exists("data"):
        os.makedirs("data")

    if not os.path.exists(FILE_PATH):
        with open(FILE_PATH, "w") as f:
            json.dump([], f)


# ===== 記錄交易 =====
def record_trade(name, decision, price, buy, stop):

    init_storage()

    trade = {
        "time": datetime.now().strftime("%Y-%m-%d %H:%M"),
        "stock": name,
        "decision": decision,
        "price": price,
        "buy": buy,
        "stop": stop,
        "result": None,      # 之後填
        "price_after": None  # 之後填
    }

    with open(FILE_PATH, "r") as f:
        data = json.load(f)

    data.append(trade)

    with open(FILE_PATH, "w") as f:
        json.dump(data, f, indent=2)

    print(f"[記錄] {name} 已寫入")


# ===== 更新結果（未來用）=====
def update_result(stock_name, new_price):

    init_storage()

    with open(FILE_PATH, "r") as f:
        data = json.load(f)

    for trade in reversed(data):
        if trade["stock"] == stock_name and trade["result"] is None:

            trade["price_after"] = new_price

            if new_price > trade["price"]:
                trade["result"] = "win"
            else:
                trade["result"] = "lose"

            break

    with open(FILE_PATH, "w") as f:
        json.dump(data, f, indent=2)