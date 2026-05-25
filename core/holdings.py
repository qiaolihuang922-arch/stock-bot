from core.watchlist import STOCKS


HOLDINGS = {
    "英業達": {
        "shares": 825,
        "avg_price": 50.22
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
