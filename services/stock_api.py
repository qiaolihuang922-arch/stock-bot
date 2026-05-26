from datetime import datetime, timedelta
import time

try:
    import requests
except ImportError:
    requests = None

try:
    import pytz
except ImportError:
    pytz = None

# ================================
# 🔥 stock_api.py（v19.1.3｜行情資料層）
# ================================

tz = pytz.timezone("Asia/Taipei") if pytz else None
HEADERS = {"User-Agent": "Mozilla/5.0"}
LAST_ERRORS = {}
LAST_OHLCV = {}


def compact_error(error):
    text = str(error)

    if "nodename nor servname" in text or "NameResolutionError" in text:
        return "DNS failed"

    if "Read timed out" in text or "Timeout" in text:
        return "timeout"

    if len(text) > 120:
        return text[:117] + "..."

    return text


def record_error(code, source, error):
    LAST_ERRORS[str(code)] = f"{source}: {compact_error(error)}"


def clear_error(code):
    LAST_ERRORS.pop(str(code), None)


def get_last_error(code):
    return LAST_ERRORS.get(str(code))


def get_last_errors():
    return dict(LAST_ERRORS)


def get_last_ohlcv(code):
    return LAST_OHLCV.get(str(code))


def parse_twse_date(value):
    try:
        parts = str(value).split("/")
        if len(parts) != 3:
            return None

        year = int(parts[0])
        if year < 1911:
            year += 1911

        return datetime(
            year,
            int(parts[1]),
            int(parts[2])
        ).date()
    except:
        return None


def parse_twse_number(value):
    try:
        text = str(value).replace(",", "").strip()
        if text in ["", "--", "-"]:
            return None
        return float(text)
    except:
        return None


def parse_yahoo_timestamp(value):
    try:
        timezone = tz or datetime.now().astimezone().tzinfo
        return datetime.fromtimestamp(int(value), timezone).date()
    except:
        return None


def parse_quote_level(raw):
    if not raw:
        return None

    for item in str(raw).split("_"):
        try:
            price = float(item)
        except:
            continue

        if price > 0:
            return price

    return None


def get_realtime_price(code):
    try:
        if requests is None:
            return None

        r = None

        # 中文註釋：v19.1.3 先查上市 tse，再查上櫃 otc，保留未來股票池擴充彈性。
        for market in ["tse", "otc"]:
            url = f"https://mis.twse.com.tw/stock/api/getStockInfo.jsp?ex_ch={market}_{code}.tw"
            r = requests.get(url, timeout=10).json()

            if r.get("msgArray"):
                break

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
                # 中文註釋：v19.1.3 漲停 / 跌停時第一檔可能是 "-" 或 0，逐檔找有效價格避免退回昨收。
                bid = parse_quote_level(b)
                ask = parse_quote_level(a)

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

        # 中文註釋：v19.1.3 漲跌停價有 tick rounding，放寬到 10.5% 避免合法漲停價被誤判異常。
        if price > prev_close * 1.105 or price < prev_close * 0.895:
            return None

        change = (price - prev_close) / prev_close * 100
        return price, change

    except:
        return None


def get_yahoo(code):
    try:
        if requests is None:
            return None

        url = f"https://query1.finance.yahoo.com/v7/finance/quote?symbols={code}.TW"
        r = requests.get(url, headers=HEADERS, timeout=10).json()
        d = r["quoteResponse"]["result"]
        if not d:
            return None
        d = d[0]
        return d["regularMarketPrice"], d["regularMarketChangePercent"]
    except:
        return None


def get_yahoo_history(code, months=4, min_rows=45):
    if requests is None:
        record_error(code, "yahoo_daily", "requests unavailable")
        return None

    last_error = None

    for suffix in ["TW", "TWO"]:
        try:
            symbol = f"{code}.{suffix}"
            url = (
                f"https://query1.finance.yahoo.com/v8/finance/chart/{symbol}"
                f"?range={max(1, months)}mo&interval=1d"
            )
            payload = requests.get(url, headers=HEADERS, timeout=10).json()
            result = (payload.get("chart") or {}).get("result") or []

            if not result:
                error = (payload.get("chart") or {}).get("error")
                last_error = error or f"{symbol}: no result"
                continue

            item = result[0]
            timestamps = item.get("timestamp") or []
            quote = ((item.get("indicators") or {}).get("quote") or [{}])[0]
            opens = quote.get("open") or []
            highs = quote.get("high") or []
            lows = quote.get("low") or []
            closes_raw = quote.get("close") or []
            volumes_raw = quote.get("volume") or []

            rows = []

            for index, timestamp in enumerate(timestamps):
                try:
                    close = closes_raw[index]
                    volume = volumes_raw[index]

                    if close is None or volume is None:
                        continue

                    trade_date = parse_yahoo_timestamp(timestamp)
                    if not trade_date:
                        continue

                    open_price = opens[index] if index < len(opens) else None
                    high = highs[index] if index < len(highs) else None
                    low = lows[index] if index < len(lows) else None

                    rows.append((trade_date, float(close), float(volume)))

                    if all(value is not None for value in [open_price, high, low]):
                        cached = LAST_OHLCV.get(str(code)) or {}
                        cached_date = cached.get("trade_date")
                        if cached_date and trade_date <= cached_date:
                            continue
                        LAST_OHLCV[str(code)] = {
                            "stock_id": str(code),
                            "trade_date": trade_date,
                            "open": float(open_price),
                            "high": float(high),
                            "low": float(low),
                            "close": float(close),
                            "volume": float(volume),
                            "source": "yahoo"
                        }
                except Exception as exc:
                    last_error = f"parse: {exc}"
                    continue

            rows.sort(key=lambda item: item[0])

            if len(rows) < min_rows:
                last_error = f"{symbol}: insufficient rows={len(rows)}"
                continue

            closes = [item[1] for item in rows]
            volumes = [item[2] for item in rows]
            price = closes[-1]
            prev = closes[-2]
            change = (price - prev) / prev * 100
            ma5 = sum(closes[-5:]) / 5 if len(closes) >= 5 else price
            ma20 = sum(closes[-20:]) / 20 if len(closes) >= 20 else price

            clear_error(code)
            return price, change, ma5, ma20, closes, volumes

        except Exception as exc:
            last_error = f"{type(exc).__name__}: {exc}"
            continue

    record_error(code, "yahoo_daily", last_error or "empty data")
    return None


def get_twse(code, months=2, retries=1, min_rows=45, max_months=4):
    if requests is None:
        record_error(code, "twse", "requests unavailable")
        return None

    clear_error(code)
    last_error = None

    for _ in range(max(1, retries)):
        try:
            rows = []
            now = datetime.now(tz) if tz else datetime.now()

            month_count = max(1, months)

            for i in range(max(1, max_months)):
                date = now - timedelta(days=30*i)
                url = f"https://www.twse.com.tw/exchangeReport/STOCK_DAY?response=json&date={date.strftime('%Y%m01')}&stockNo={code}"

                try:
                    response = requests.get(url, headers=HEADERS, timeout=10)
                    r = response.json()
                except Exception as exc:
                    last_error = f"{type(exc).__name__}: {exc}"
                    if "nodename nor servname" in str(exc) or "NameResolutionError" in str(exc):
                        record_error(code, "twse", last_error)
                        return None
                    continue

                if r.get("stat") != "OK":
                    last_error = f"stat={r.get('stat')}"
                    continue

                for d in r.get("data", []):
                    try:
                        trade_date = parse_twse_date(d[0])
                        close = float(d[6].replace(",", ""))
                        volume = float(d[1].replace(",", ""))
                        rows.append((
                            d[0],
                            close,
                            volume
                        ))
                        open_price = parse_twse_number(d[3])
                        high = parse_twse_number(d[4])
                        low = parse_twse_number(d[5])
                        if trade_date and all(value is not None for value in [open_price, high, low, close, volume]):
                            cached = LAST_OHLCV.get(str(code)) or {}
                            cached_date = cached.get("trade_date")
                            if cached_date and trade_date <= cached_date:
                                continue
                            LAST_OHLCV[str(code)] = {
                                "stock_id": str(code),
                                "trade_date": trade_date,
                                "open": open_price,
                                "high": high,
                                "low": low,
                                "close": close,
                                "volume": volume,
                                "source": "twse"
                            }
                    except Exception as exc:
                        last_error = f"parse: {exc}"
                        continue

                if i + 1 >= month_count and len(rows) >= min_rows:
                    break

                if i + 1 >= month_count and len(rows) < min_rows:
                    month_count = min(month_count + 1, max(1, max_months))

            if not rows:
                record_error(code, "twse", last_error or "empty data")
                continue

            rows.sort(key=lambda x: x[0])

            closes = [x[1] for x in rows]
            volumes = [x[2] for x in rows]

            if len(closes) < 5:
                record_error(code, "twse", f"insufficient rows={len(closes)}")
                return None

            price = closes[-1]
            prev = closes[-2]

            change = (price - prev) / prev * 100

            ma5 = sum(closes[-5:]) / 5 if len(closes) >= 5 else price
            ma20 = sum(closes[-20:]) / 20 if len(closes) >= 20 else price

            return price, change, ma5, ma20, closes, volumes

        except Exception as exc:
            record_error(code, "twse", f"{type(exc).__name__}: {exc}")
            time.sleep(2)

    if last_error:
        record_error(code, "twse", last_error)

    return None


def get_twse_ohlcv_history(code, start_date, end_date):
    if requests is None:
        raise RuntimeError("requests is required for --source twse")

    rows = {}
    cursor = datetime(end_date.year, end_date.month, 1).date()
    first_month = datetime(start_date.year, start_date.month, 1).date()

    while cursor >= first_month:
        url = (
            "https://www.twse.com.tw/exchangeReport/STOCK_DAY"
            f"?response=json&date={cursor.strftime('%Y%m01')}&stockNo={code}"
        )

        try:
            payload = requests.get(url, headers=HEADERS, timeout=10).json()
        except:
            payload = {}

        if payload.get("stat") == "OK":
            for item in payload.get("data", []):
                trade_date = parse_twse_date(item[0])

                if not trade_date or trade_date < start_date or trade_date > end_date:
                    continue

                open_price = parse_twse_number(item[3])
                high = parse_twse_number(item[4])
                low = parse_twse_number(item[5])
                close = parse_twse_number(item[6])
                volume = parse_twse_number(item[1])

                if close is None or volume is None:
                    continue

                rows[trade_date] = {
                    "stock_id": str(code),
                    "trade_date": trade_date,
                    "open": open_price,
                    "high": high,
                    "low": low,
                    "close": close,
                    "volume": volume,
                    "source": "twse"
                }

        # 中文註釋：v19.1.3 歷史 OHLCV 逐月往回抓，供 dry-run replay 使用；不在此函式寫入資料庫。
        if cursor.month == 1:
            cursor = datetime(cursor.year - 1, 12, 1).date()
        else:
            cursor = datetime(cursor.year, cursor.month - 1, 1).date()

        time.sleep(0.2)

    return [
        rows[trade_date]
        for trade_date in sorted(rows)
    ]
