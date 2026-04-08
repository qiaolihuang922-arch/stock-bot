import requests
from datetime import datetime

TOKEN = "8714533132:AAGEAYs-Q-oZJDwwBwwuB0MPb27mqnDtzxs"
CHAT_ID = "7119676798"

stocks = {
    "緯創": "3231.TW",
    "建準": "2421.TW",
    "智原": "3035.TW"
}

def get_stock_price(symbol):
    try:
        url = f"https://query1.finance.yahoo.com/v7/finance/quote?symbols={symbol}"
        data = requests.get(url, timeout=10).json()
        result = data["quoteResponse"]["result"]

        if not result:
            return None, None, None

        r = result[0]

        price = r.get("regularMarketPrice")
        change = r.get("regularMarketChangePercent")
        prev_close = r.get("regularMarketPreviousClose")

        # fallback：沒價格就用昨收
        if price is None:
            price = prev_close

        return price, change, prev_close

    except:
        return None, None, None


def analyze_stock(change):
    if change is None:
        return "資料不足", "觀望"

    if change > 3:
        return "強勢噴出", "可關注"
    elif change > 1:
        return "偏多走勢", "可觀察"
    elif change > -1:
        return "盤整", "觀望"
    elif change > -3:
        return "轉弱", "保守"
    else:
        return "明顯走弱", "暫不進場"


def generate_report():
    today = datetime.now().strftime("%m/%d")
    msg = f"【{today} AI股票穩定分析】\n\n"

    best = None
    best_score = -999

    for name, code in stocks.items():
        price, change, prev = get_stock_price(code)
        trend, suggestion = analyze_stock(change)

        if change is not None and change > best_score:
            best_score = change
            best = name

        price_text = price if price else "無資料"
        change_text = f"{round(change,2)}%" if change is not None else "無資料"
        prev_text = prev if prev else "無資料"

        msg += f"📌 {name}\n"
        msg += f"→ 現價：{price_text}\n"
        msg += f"→ 昨收：{prev_text}\n"
        msg += f"→ 漲跌：{change_text}\n"
        msg += f"→ 趨勢：{trend}\n"
        msg += f"→ 建議：{suggestion}\n\n"

    msg += f"👉 今日策略：{best if best else '全面觀望'}"

    return msg


def send_telegram(msg):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    requests.post(url, data={
        "chat_id": CHAT_ID,
        "text": msg
    })


if __name__ == "__main__":
    report = generate_report()
    send_telegram(report)