from core.watchlist import STOCKS


def realized_take_profit(ratio, date):
    return {
        "realized_profit_taken_ratio": ratio,
        "realized_profit_taken_date": date
    }


HOLDINGS = {
    "英業達": {
        "shares": 550,
        "avg_price": 52.15,
        **realized_take_profit(0.5, "2026-05-25")
    },
    "智原": {
        "shares": 50,
        "avg_price": 209
    },
    "光寶科": {
        "shares": 50,
        "avg_price": 208.5
    },
    "緯創": {
        "shares": 440,
        "avg_price": 140.92
    }
}


HOLDING_CODES = {
    STOCKS[name]
    for name in HOLDINGS
    if name in STOCKS
}
