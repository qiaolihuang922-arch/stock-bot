STOCKS = {
    "緯創": "3231",
    "建準": "2421",
    "智原": "3035",
    "聯電": "2303",
    "群創": "3481",
    "華邦電": "2344",
    "技嘉": "2376",
    "南亞科": "2408",
    "英業達": "2356",
    "仁寶": "2324",
    "光寶科": "2301",
    "旺宏": "2337"
}


WATCHLIST_CODES = list(STOCKS.values())


def missing_watchlist_codes(results_map, expected_stock_ids=None):
    expected = {
        str(stock_id)
        for stock_id in (expected_stock_ids or WATCHLIST_CODES)
        if stock_id
    }
    actual = {
        str(data.get("stock_code"))
        for data in (results_map or {}).values()
        if data.get("stock_code")
    }

    return sorted(expected - actual)
