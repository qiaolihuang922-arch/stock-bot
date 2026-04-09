import requests
from datetime import datetime, timedelta
import pytz
import time

tz = pytz.timezone("Asia/Taipei")
HEADERS = {"User-Agent": "Mozilla/5.0"}


def get_realtime_price(code):
    try:
        url = f"https://mis.twse.com.tw/stock/api/getStockInfo.jsp?ex_ch=tse_{code}.tw"
        r = requests.get(url, timeout=10).json()

        data = r.get("msgArray")
        if not data:
            return None

        d = data[0]

        z = d.get("z")
        b = d.get("b")
        a = d.get("a")
        y = d.get("y")

        if y in ["-", "", "0"]:
            return None

        prev_close = float(y)
        price = None

        if z not in ["-", "", "0"]:
            price = float(z)
        else:
            try:
                bid = float(b.split("_")[0]) if b else None
                ask = float(a.split("_")[0]) if a else None

                if bid and ask:
                    price = (bid + ask) / 2
                elif bid:
                    price = bid
                elif ask:
                    price = ask
            except:
                return None

        if not price:
            return None

        if price > prev_close * 1.1 or price < prev_close * 0.9:
            return None

        change = (price - prev_close) / prev_close * 100
        return price, change

    except:
        return None


def get_yahoo(code):
    try:
        url = f"https://query1.finance.yahoo.com/v7/finance/quote?symbols={code}.TW"
        r = requests.get(url, headers=HEADERS, timeout=10).json()
        d = r["quoteResponse"]["result"]
        if not d:
            return None
        d = d[0]
        return d["regularMarketPrice"], d["regularMarketChangePercent"]
    except:
        return None


def get_twse(code):
    for _ in range(3):
        try:
            rows = []
            now = datetime.now(tz)

            for i in range(6):
                date = now - timedelta(days=30*i)
                url = f"https://www.twse.com.tw/exchangeReport/STOCK_DAY?response=json&date={date.strftime('%Y%m01')}&stockNo={code}"

                try:
                    r = requests.get(url, headers=HEADERS, timeout=10).json()
                except:
                    continue

                if r.get("stat") != "OK":
                    continue

                for d in r.get("data", []):
                    try:
                        rows.append((
                            d[0],
                            float(d[6].replace(",", "")),
                            float(d[1].replace(",", ""))
                        ))
                    except:
                        continue

            if not rows:
                time.sleep(2)
                continue

            rows.sort(key=lambda x: x[0])

            closes = [x[1] for x in rows]
            volumes = [x[2] for x in rows]

            if len(closes) < 5:
                return None

            price = closes[-1]
            prev = closes[-2]

            change = (price - prev) / prev * 100

            ma5 = sum(closes[-5:]) / 5 if len(closes) >= 5 else price
            ma20 = sum(closes[-20:]) / 20 if len(closes) >= 20 else price

            return price, change, ma5, ma20, closes, volumes

        except:
            time.sleep(2)

    return None