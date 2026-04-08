import requests
from datetime import datetime

TOKEN = "8714533132:AAGEAYs-Q-oZJDwwBwwuB0MPb27mqnDtzxs"
CHAT_ID = "7119676798"

# 股票代碼（台股）
stocks = {
    "緯創": "3231.TW",
    "建準": "2421.TW",
    "智原": "3035.TW"
}

def get_stock_price(symbol):
    url = f"https://query1.finance.yahoo.com/v7/finance/quote?symbols={symbol}"
    data = requests.get(url).json()
    
    try:
        result = data["quoteResponse"]["result"][0]
        price = result["regularMarketPrice"]
        change = result["regularMarketChangePercent"]
        return price, change
    except:
        return None, None

def analyze_stock(change):
    if change is None:
        return "資料錯誤", "觀望"

    if change > 2:
        return "強勢上漲", "可關注"
    elif change > 0:
        return "小幅上漲", "觀察"
    elif change > -2:
        return "震盪整理", "觀望"
    else:
        return "偏弱下跌", "暫不進場"

def generate_report():
    today = datetime.now().strftime("%m/%d")
    msg = f"【{today} AI股票自動分析】\n\n"

    best = None
    best_score = -999

    for name, code in stocks.items():
        price, change = get_stock_price(code)
        trend, suggestion = analyze_stock(change)

        if change is not None and change > best_score:
            best_score = change
            best = name

        msg += f"📌 {name}\n"
        msg += f"→ 價格：{price}\n"
        msg += f"→ 漲跌：{round(change,2)}%\n"
        msg += f"→ 趨勢：{trend}\n"
        msg += f"→ 建議：{suggestion}\n\n"

    msg += f"👉 今日結論：優先關注 {best}"

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
