from core.watchlist import STOCKS


# v19.3: live holdings are stored in Supabase positions.
# This file remains only for replay/backfill holding-code boundaries.
HOLDINGS = {}


HOLDING_CODES = {
    STOCKS[name]
    for name in HOLDINGS
    if name in STOCKS
}
