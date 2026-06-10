"""Future 30-day Telegram watch payload helpers."""

import re
from concurrent.futures import ThreadPoolExecutor, as_completed
from html import unescape
from datetime import date, datetime, timedelta
from time import monotonic

try:
    import requests
except ImportError:
    requests = None


CRASH_ANALOGY_FALLBACK = "歷史類比：無高相似台股急跌樣本｜依據不足/相似度低"
TAIWAN_MARKET_EVENT_SOURCE_ERROR = "未來30日台股影響事件：官方來源暫時不可用，本次不列未確認事件"
TAIWAN_MARKET_EVENT_EMPTY = "未來30日台股影響事件：未查到未來30日官方事件"
MOPS_SOURCE_ERROR = "未來30日法說會：MOPS 官方來源暫時不可解析，本次不列未確認事件"
MOPS_ENDPOINT = "https://mopsov.twse.com.tw/mops/web/ajax_t100sb02_1"
MOPS_METHOD = "POST"
MOPS_TYPEKS = ("sii", "otc", "rotc", "pub")
MOPS_DEFAULT_MAX_TARGETS = 12
MOPS_DEFAULT_MAX_QUERIES = 32
MOPS_DEFAULT_MAX_SECONDS = 8
MOPS_DEFAULT_MAX_ITEMS = 10
MOPS_TYPEK_PRIORITY = {
    "sii": ("sii", "otc", "rotc", "pub"),
    "otc": ("otc", "sii", "rotc", "pub"),
    "rotc": ("rotc", "otc", "sii", "pub"),
    "pub": ("pub", "sii", "otc", "rotc"),
}
TWSE_MI_INDEX_ENDPOINT = "https://openapi.twse.com.tw/v1/exchangeReport/MI_INDEX"
TWSE_TAIEX_HISTORY_ENDPOINT = "https://openapi.twse.com.tw/v1/exchangeReport/MI_5MINS_HIST"
TWSE_TAIEX_HISTORY_RWD_ENDPOINT = "https://www.twse.com.tw/rwd/zh/TAIEX/MI_5MINS_HIST"
TWSE_MONTHLY_REVENUE_ENDPOINT = "https://openapi.twse.com.tw/v1/opendata/t187ap05_L"
TPEX_MONTHLY_REVENUE_ENDPOINT = "https://www.tpex.org.tw/openapi/v1/t187ap05_R"
MOPS_MONTHLY_REVENUE_ENDPOINT = "https://mopsov.twse.com.tw/mops/web/ajax_t05st10_ifrs"
TWSE_EPS_ENDPOINT = "https://openapi.twse.com.tw/v1/opendata/t187ap14_L"
TPEX_EPS_ENDPOINT = "https://www.tpex.org.tw/openapi/v1/mopsfin_t187ap14_O"
HTTP_HEADERS = {"User-Agent": "Mozilla/5.0"}

_EVENT_PRIORITY = {
    "利率": 0,
    "通膨": 1,
    "匯率": 2,
    "能源": 3,
    "政治風險": 4,
}

_DEFAULT_GLOBAL_EVENT_SEED = (
    {
        "date": "2026/06/10-11",
        "event": "ECB 利率決策/記者會",
        "impact": "利率/匯率",
        "source": "ECB",
    },
    {
        "date": "2026/06/10",
        "event": "美國 CPI（May 2026）",
        "impact": "通膨/利率",
        "source": "BLS",
    },
    {
        "date": "2026/06/15-16",
        "event": "日本央行 BOJ 利率會議",
        "impact": "利率/匯率",
        "source": "BOJ",
    },
    {
        "date": "2026/06/15-17",
        "event": "G7 領袖峰會",
        "impact": "政治風險",
        "source": "G7",
    },
    {
        "date": "2026/06/16-17",
        "event": "Fed FOMC 利率決策/SEP",
        "impact": "利率/匯率",
        "source": "Fed",
    },
    {
        "date": "2026/06/18",
        "event": "英國央行 BoE 利率決策",
        "impact": "利率/匯率",
        "source": "BoE",
    },
    {
        "date": "2026/06/25",
        "event": "美國 BEA GDP/PCE",
        "impact": "通膨/利率",
        "source": "BEA",
    },
)

TAIWAN_CRASH_TEMPLATE_LIBRARY = (
    {
        "event": "1987 全球黑色星期一外溢",
        "pattern": "全球股災外溢",
        "change_band": (-8.0, -3.5),
        "pullback_band": (-18.0, -5.0),
        "base_similarity": 0.31,
        "difference": "全球同步恐慌型，需美股與亞股連鎖下跌才接近",
        "watch": "觀察美股隔夜續跌、外資賣超與隔日開盤承接",
    },
    {
        "event": "1990 台股萬點泡沫崩跌",
        "pattern": "泡沫長空",
        "change_band": (-6.0, -2.5),
        "pullback_band": (-20.0, -6.0),
        "base_similarity": 0.24,
        "difference": "泡沫破裂型長空，需連續跌破月線/季線才接近",
        "watch": "觀察融資退潮、月線失守與量能失控",
    },
    {
        "event": "1995 台海飛彈危機急跌",
        "pattern": "地緣政治急跌",
        "change_band": (-4.5, -1.8),
        "pullback_band": (-9.0, -3.0),
        "base_similarity": 0.26,
        "difference": "地緣政治壓力型，需事件風險升溫才接近",
        "watch": "留意台海/政治風險與外資連續賣超",
    },
    {
        "event": "1997 亞洲金融風暴",
        "pattern": "區域金融壓力",
        "change_band": (-5.5, -2.0),
        "pullback_band": (-12.0, -4.0),
        "base_similarity": 0.28,
        "difference": "區域金融壓力型，需匯率與金融股同步轉弱",
        "watch": "留意台幣、金融股與外資賣超擴大",
    },
    {
        "event": "1998 俄債/LTCM 新興市場風暴",
        "pattern": "國際信用緊縮",
        "change_band": (-5.0, -2.0),
        "pullback_band": (-12.0, -4.0),
        "base_similarity": 0.28,
        "difference": "信用收縮外溢型，需新興市場/金融壓力同步才接近",
        "watch": "留意美元流動性、新興市場跌勢與金融股壓力",
    },
    {
        "event": "2000 網路泡沫/政權輪替壓力",
        "pattern": "科技估值修正",
        "change_band": (-5.0, -2.0),
        "pullback_band": (-12.0, -4.0),
        "base_similarity": 0.27,
        "difference": "科技泡沫估值修正型，需電子權值股同步轉弱",
        "watch": "觀察電子權值與高估值題材是否續弱",
    },
    {
        "event": "2001 911 恐攻全球風險事件",
        "pattern": "全球事件風險",
        "change_band": (-7.0, -2.5),
        "pullback_band": (-13.0, -4.0),
        "base_similarity": 0.30,
        "difference": "突發事件風險型，需事件衝擊與避險同步升溫才接近",
        "watch": "留意事件釐清、美元/避險資產與隔日流動性",
    },
    {
        "event": "2003 SARS 台股急跌",
        "pattern": "疫情需求衝擊",
        "change_band": (-4.5, -1.8),
        "pullback_band": (-10.0, -3.0),
        "base_similarity": 0.28,
        "difference": "疫情/需求衝擊型，需基本面預期同步下修才接近",
        "watch": "留意消費、運輸與景氣預期是否惡化",
    },
    {
        "event": "2004 319選舉事件急跌",
        "pattern": "事件型急殺",
        "change_band": (-7.0, -3.0),
        "pullback_band": (-8.0, -2.0),
        "base_similarity": 0.30,
        "difference": "單一政治事件急殺型，需隔日是否止跌確認",
        "watch": "留意事件釐清、政策訊號與隔日開盤承接",
    },
    {
        "event": "2006 全球升息/雙卡風暴壓力",
        "pattern": "內需信用與升息壓力",
        "change_band": (-4.0, -1.5),
        "pullback_band": (-10.0, -3.0),
        "base_similarity": 0.25,
        "difference": "內需信用與全球升息壓力型，需金融/消費同步轉弱才接近",
        "watch": "留意金融股、內需股與外資風險偏好",
    },
    {
        "event": "2007 次貸風暴前段",
        "pattern": "信用風險前段",
        "change_band": (-5.0, -1.8),
        "pullback_band": (-11.0, -3.5),
        "base_similarity": 0.29,
        "difference": "信用風險前段，需金融壓力擴散才升級",
        "watch": "留意金融股、信用利差與外資連續賣超",
    },
    {
        "event": "2008 金融海嘯",
        "pattern": "系統性信用風險",
        "change_band": (-6.5, -2.8),
        "pullback_band": (-18.0, -6.0),
        "base_similarity": 0.31,
        "difference": "系統性信用風險型，需金融/出口鏈同步惡化才接近",
        "watch": "留意金融壓力、信用風險與出口權值股",
    },
    {
        "event": "2011 歐債/美國信評急跌",
        "pattern": "主權債風險收縮",
        "change_band": (-5.5, -2.2),
        "pullback_band": (-12.0, -4.0),
        "base_similarity": 0.29,
        "difference": "主權債與風險偏好收縮型，需美元與外資同步確認",
        "watch": "留意美元、外資與電子權值修正幅度",
    },
    {
        "event": "2015 台股急跌/中國股災外溢",
        "pattern": "高檔壓力前段",
        "change_band": (-3.0, -1.2),
        "pullback_band": (-6.0, -1.2),
        "base_similarity": 0.30,
        "difference": "屬壓力前段，不是崩盤等級",
        "watch": "未來3-5日是否跌破本月低點",
    },
    {
        "event": "2018 美股波動/貿易戰急跌",
        "pattern": "外部風險偏好收縮",
        "change_band": (-6.5, -2.5),
        "pullback_band": (-10.0, -3.0),
        "base_similarity": 0.29,
        "difference": "外部風險偏好收縮型，需美股與外資賣壓同步確認",
        "watch": "留意美股科技股、美元/台幣與外資賣超",
    },
    {
        "event": "2020 台股疫情急跌",
        "pattern": "疫情急跌",
        "change_band": (-5.0, -3.0),
        "pullback_band": (-14.0, -5.0),
        "base_similarity": 0.32,
        "difference": "急跌情境，但仍需連續性確認",
        "watch": "留意是否連續跌破前低與量能放大",
    },
    {
        "event": "2021 本土疫情/航運電子高檔回檔",
        "pattern": "本土疫情與題材退潮",
        "change_band": (-5.0, -1.8),
        "pullback_band": (-10.0, -3.0),
        "base_similarity": 0.27,
        "difference": "本土疫情與高檔題材退潮型，需類股輪動同步轉弱才接近",
        "watch": "留意疫情政策、航運/電子權值與融資變化",
    },
    {
        "event": "2022 升息通膨修正",
        "pattern": "利率估值修正",
        "change_band": (-4.5, -1.8),
        "pullback_band": (-14.0, -4.0),
        "base_similarity": 0.28,
        "difference": "利率估值修正型，需殖利率/美元與科技股同步壓力",
        "watch": "留意Fed路徑、美元與電子權值估值修正",
    },
    {
        "event": "2024/08/05 台股日圓套利平倉急殺",
        "pattern": "槓桿平倉急殺",
        "change_band": (-10.0, -5.5),
        "pullback_band": (-12.0, -5.0),
        "base_similarity": 0.36,
        "difference": "急殺等級，需看隔日是否止跌",
        "watch": "留意外資/匯率與隔日開盤承接",
    },
)

_FULL_DATE_RE = re.compile(r"(?P<year>\d{4})[/-](?P<month>\d{1,2})[/-](?P<day>\d{1,2})")
_ROC_DATE_RE = re.compile(r"(?P<year>\d{2,3})[/-](?P<month>\d{1,2})[/-](?P<day>\d{1,2})")
_MONTHS = {
    "january": 1,
    "february": 2,
    "march": 3,
    "april": 4,
    "may": 5,
    "june": 6,
    "july": 7,
    "august": 8,
    "september": 9,
    "october": 10,
    "november": 11,
    "december": 12,
}


def _safe_date(year, month, day):
    try:
        return date(int(year), int(month), int(day))
    except (TypeError, ValueError):
        return None


def _parse_date_range(value):
    if isinstance(value, datetime):
        parsed = value.date()
        return parsed, parsed
    if isinstance(value, date):
        return value, value
    if not isinstance(value, str):
        return None, None

    text = value.strip()
    if not text:
        return None, None

    matches = list(_FULL_DATE_RE.finditer(text))
    if not matches:
        return None, None

    first = matches[0]
    start = _safe_date(first.group("year"), first.group("month"), first.group("day"))
    if start is None:
        return None, None

    if len(matches) >= 2:
        second = matches[1]
        end = _safe_date(second.group("year"), second.group("month"), second.group("day"))
        return start, end if end and end >= start else start

    remainder = text[first.end():]
    short = re.match(r"\s*[-~–—]\s*(?:(?P<month>\d{1,2})[/-])?(?P<day>\d{1,2})(?!\d)", remainder)
    if short:
        end_month = int(short.group("month") or start.month)
        end = _safe_date(start.year, end_month, short.group("day"))
        if end and end >= start:
            return start, end
    return start, start


def _as_date(value):
    start, _end = _parse_date_range(value)
    return start


def _date_label(value):
    start, end = _parse_date_range(value)
    if not start:
        return str(value or "").strip()
    if not end or end == start:
        return start.strftime("%m/%d")
    if start.year == end.year and start.month == end.month:
        return f"{start.strftime('%m/%d')}-{end.strftime('%d')}"
    if start.year == end.year:
        return f"{start.strftime('%m/%d')}-{end.strftime('%m/%d')}"
    return f"{start.strftime('%Y/%m/%d')}-{end.strftime('%Y/%m/%d')}"


def _roc_year(value):
    return value.year - 1911


def _parse_number(value):
    try:
        text = str(value).replace(",", "").replace("%", "").strip()
        if text in {"", "-", "--", "N/A"}:
            return None
        return float(text)
    except (TypeError, ValueError):
        return None


def _fmt_pct(value):
    try:
        return f"{float(value):+.2f}%"
    except (TypeError, ValueError):
        return "-"


def _fmt_compact_pct(value):
    try:
        return f"{float(value):+.1f}%"
    except (TypeError, ValueError):
        return "-"


def _fmt_compact_number(value):
    try:
        number = float(str(value).replace(",", "").strip())
    except (TypeError, ValueError):
        return "-"
    return f"{number:.2f}".rstrip("0").rstrip(".")


def _financial_period_label(year, quarter=None, month=None):
    try:
        ad_year = int(year)
        if ad_year < 1911:
            ad_year += 1911
    except (TypeError, ValueError):
        ad_year = None
    if quarter not in (None, "") and ad_year:
        return f"{ad_year}Q{quarter}"
    if month:
        text = str(month)
        if len(text) >= 5:
            roc_year = text[:-2]
            try:
                ad_year = int(roc_year) + 1911
            except (TypeError, ValueError):
                ad_year = None
            return f"{ad_year}/{text[-2:]}" if ad_year else text
        return text
    return str(year or "")


def _parse_official_date(value, default_year=None):
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value
    text = str(value or "").strip()
    if not text:
        return None
    compact_roc = re.fullmatch(r"(?P<year>\d{3})(?P<month>\d{2})(?P<day>\d{2})", text)
    if compact_roc:
        return _safe_date(
            int(compact_roc.group("year")) + 1911,
            compact_roc.group("month"),
            compact_roc.group("day"),
        )
    start = _as_date(text)
    if start:
        return start
    match = _ROC_DATE_RE.search(text)
    if match:
        year = int(match.group("year"))
        if year < 1911:
            year += 1911
        return _safe_date(year, match.group("month"), match.group("day"))
    short = re.search(r"(?P<month>\d{1,2})[/-](?P<day>\d{1,2})", text)
    if short and default_year:
        return _safe_date(default_year, short.group("month"), short.group("day"))
    month_name = re.search(
        r"(?P<month>January|February|March|April|May|June|July|August|September|October|November|December)"
        r"\s+(?P<day>\d{1,2})(?:\s*,\s*(?P<year>\d{4}))?",
        text,
        flags=re.I,
    )
    if month_name:
        year = int(month_name.group("year") or default_year or datetime.now().year)
        month = _MONTHS[month_name.group("month").lower()]
        return _safe_date(year, month, month_name.group("day"))
    return None


def _extract_text_number(row, keys):
    for key in keys:
        value = _parse_number(row.get(key))
        if value is not None:
            return value
    return None


def _normalize_official_event_date(raw_date, default_year):
    text = str(raw_date or "").strip()
    month_range = re.search(
        r"(?P<month>January|February|March|April|May|June|July|August|September|October|November|December)"
        r"\s+(?P<start>\d{1,2})\s*[-–]\s*(?P<end>\d{1,2})(?:\s*,\s*(?P<year>\d{4}))?",
        text,
        flags=re.I,
    )
    if month_range:
        year = int(month_range.group("year") or default_year)
        month = _MONTHS[month_range.group("month").lower()]
        return f"{year:04d}/{month:02d}/{int(month_range.group('start')):02d}-{int(month_range.group('end')):02d}"
    numeric_range = re.search(
        r"(?P<month>\d{1,2})[/-](?P<start>\d{1,2})\s*[-–]\s*(?P<end>\d{1,2})(?:[/-](?P<year>\d{4}))?",
        text,
    )
    if numeric_range:
        year = int(numeric_range.group("year") or default_year)
        return f"{year:04d}/{int(numeric_range.group('month')):02d}/{int(numeric_range.group('start')):02d}-{int(numeric_range.group('end')):02d}"
    parsed = _parse_official_date(text, default_year=default_year)
    return parsed.isoformat() if parsed else None


def _request_get_json(url, requester=None, timeout=6):
    if requester is None:
        if requests is None:
            raise RuntimeError("requests unavailable")
        requester = requests.get
    response = requester(url, headers=HTTP_HEADERS, timeout=timeout)
    if hasattr(response, "raise_for_status"):
        response.raise_for_status()
    return response.json()


def _request_get_text(url, requester=None, timeout=6):
    if requester is None:
        if requests is None:
            raise RuntimeError("requests unavailable")
        requester = requests.get
    response = requester(url, headers=HTTP_HEADERS, timeout=timeout)
    if hasattr(response, "raise_for_status"):
        response.raise_for_status()
    return response.text


def _request_post_text(url, data, requester=None, timeout=6):
    if requester is None:
        if requests is None:
            raise RuntimeError("requests unavailable")
        requester = requests.post
    response = requester(
        url,
        data=data,
        headers={
            **HTTP_HEADERS,
            "Content-Type": "application/x-www-form-urlencoded",
            "Referer": "https://mops.twse.com.tw/mops/web/t100sb02_1",
        },
        timeout=timeout,
    )
    if hasattr(response, "raise_for_status"):
        response.raise_for_status()
    return response.text


def _month_keys(start, end):
    keys = []
    current = date(start.year, start.month, 1)
    while current <= end:
        keys.append((_roc_year(current), f"{current.month:02d}"))
        if current.month == 12:
            current = date(current.year + 1, 1, 1)
        else:
            current = date(current.year, current.month + 1, 1)
    return keys


def _pick_first_value(data, keys):
    for key in keys:
        if not isinstance(data, dict):
            continue
        value = data.get(key)
        if value not in (None, ""):
            return value
    return None


def _normalize_mops_typek(value):
    text = str(value or "").strip().lower()
    if not text:
        return None
    if text in MOPS_TYPEKS:
        return text
    if any(token in text for token in ("上市", "twse", "tse", "sii")):
        return "sii"
    if any(token in text for token in ("上櫃", "tpex", "otc")):
        return "otc"
    if any(token in text for token in ("興櫃", "emerging", "rotc")):
        return "rotc"
    if any(token in text for token in ("公開發行", "public", "pub")):
        return "pub"
    return None


def _target_exchange_typek(data):
    result = data.get("result") if isinstance(data, dict) and isinstance(data.get("result"), dict) else {}
    value = _pick_first_value(
        data,
        ("mops_typek", "TYPEK", "typek", "exchange", "market", "listed_market", "市場別"),
    )
    if value is None:
        value = _pick_first_value(
            result,
            ("mops_typek", "TYPEK", "typek", "exchange", "market", "listed_market", "市場別"),
        )
    return _normalize_mops_typek(value)


def _target_priority(data):
    if not isinstance(data, dict):
        return 90
    result = data.get("result") if isinstance(data.get("result"), dict) else {}
    state = str(
        data.get("decision")
        or data.get("action")
        or data.get("status")
        or result.get("trade_state")
        or result.get("decision")
        or ""
    ).lower()
    if data.get("holding"):
        return 0
    if any(token in state for token in ("buy", "可買", "準備", "prepare", "watch")):
        return 20
    if any(token in state for token in ("淘汰", "eliminated", "不可", "blocked")):
        return 80
    return 50


def _mops_typek_order(target):
    preferred = target.get("typek")
    if preferred in MOPS_TYPEK_PRIORITY:
        return MOPS_TYPEK_PRIORITY[preferred]
    return MOPS_TYPEKS


def _mops_query_key(params):
    return (
        params.get("TYPEK"),
        params.get("year"),
        params.get("month"),
        params.get("co_id"),
    )


def _target_stocks(results_map, max_targets=None):
    targets = []
    seen = set()
    for name, data in (results_map or {}).items():
        code = str((data or {}).get("stock_code") or "").strip()
        if not code or code in seen:
            continue
        seen.add(code)
        reason = "持倉" if (data or {}).get("holding") else "候選"
        targets.append({
            "code": code,
            "name": name,
            "reason": reason,
            "typek": _target_exchange_typek(data or {}),
            "priority": _target_priority(data or {}),
        })
    targets.sort(key=lambda item: (item["priority"], item["code"], item["name"]))
    if max_targets is not None:
        return targets[:max_targets]
    return targets


def _in_window(event_date, start, end):
    range_start, range_end = _parse_date_range(event_date)
    return range_start is not None and range_start <= end and (range_end or range_start) >= start


def _similarity_percent(value):
    try:
        return round(float(value) * 100)
    except (TypeError, ValueError):
        return None


def build_historical_analogy(today_features=None, historical_source=None, threshold=0.78):
    source = historical_source or {}
    if source.get("line"):
        return {"status": source.get("status") or "available", "line": source["line"]}
    if source.get("status") in {"source-error", "missing-source", "insufficient-data"}:
        return {"status": "insufficient-data", "line": CRASH_ANALOGY_FALLBACK}

    samples = source.get("samples") or source.get("events") or []
    best = None
    for sample in samples:
        similarity = sample.get("similarity")
        if similarity is None:
            features = sample.get("matched_features") or sample.get("features") or []
            base = today_features or source.get("today_features") or {}
            if isinstance(features, dict) and base:
                matched = sum(1 for key, value in features.items() if base.get(key) == value)
                similarity = matched / max(len(features), 1)
            else:
                similarity = 0
        try:
            score = float(similarity)
        except (TypeError, ValueError):
            score = 0
        if best is None or score > best[0]:
            best = (score, sample)

    if not best or best[0] < threshold:
        return {"status": "low-similarity", "line": CRASH_ANALOGY_FALLBACK}

    sample = best[1]
    percent = _similarity_percent(best[0])
    features = sample.get("matched_features") or sample.get("features") or []
    if isinstance(features, dict):
        features = list(features.keys())
    feature_text = "、".join(str(item) for item in features[:3] if item)
    event = sample.get("event") or sample.get("name") or "歷史樣本"
    event_date = sample.get("date") or sample.get("trade_date")
    prefix = f"歷史類比：{_date_label(event_date)} {event}" if event_date else f"歷史類比：{event}"
    parts = [prefix, f"相似度 {percent}%" if percent is not None else None]
    if feature_text:
        parts.append(f"相似：{feature_text}")
    parts.append("類比不是預測")
    line = "｜".join(item for item in parts if item)
    detail_lines = [line]
    if feature_text:
        detail_lines.append(f"相似點：{feature_text}")
    if sample.get("difference"):
        detail_lines.append(f"不相似/限制：{sample.get('difference')}")
    else:
        detail_lines.append("不相似/限制：事件背景未必相同，類比只作壓力參考")
    if sample.get("watch"):
        detail_lines.append(f"下一步觀察：{sample.get('watch')}")
    return {"status": "available", "line": "\n".join(detail_lines)}


def _value_or_zero(value):
    try:
        return float(value)
    except (TypeError, ValueError):
        return 0.0


def _band_similarity(value, band):
    low, high = band
    if low <= value <= high:
        return 1.0
    width = max(abs(high - low), 0.1)
    distance = min(abs(value - low), abs(value - high))
    return max(0.0, 1.0 - (distance / width))


def _score_taiwan_crash_template(template, features):
    change = _value_or_zero(features.get("change_pct"))
    pullback = _value_or_zero(features.get("pullback_from_high_pct"))
    intraday = _value_or_zero(features.get("intraday_range_pct"))
    volume_ratio = _value_or_zero(features.get("turnover_ratio"))
    high_position = _value_or_zero(features.get("close_position_5d_pct"))
    change_score = _band_similarity(change, template["change_band"])
    pullback_score = _band_similarity(pullback, template["pullback_band"])
    intraday_score = min(abs(intraday) / 5.0, 1.0) if intraday else 0.0
    volume_score = min(abs(volume_ratio - 1.0) / 1.0, 1.0) if volume_ratio else 0.0
    position_score = 1.0 - min(abs(high_position - 50.0) / 50.0, 1.0) if high_position else 0.0
    score = (
        template["base_similarity"]
        + (0.24 * change_score)
        + (0.12 * pullback_score)
        + (0.04 * intraday_score)
        + (0.04 * volume_score)
        + (0.03 * position_score)
    )
    return min(max(score, 0.0), 0.92)


def _historical_module_scores(template, features):
    change = _value_or_zero(features.get("change_pct"))
    pullback = _value_or_zero(features.get("pullback_from_high_pct"))
    intraday = _value_or_zero(features.get("intraday_range_pct"))
    volume_ratio = _value_or_zero(features.get("turnover_ratio"))
    high_position = _value_or_zero(features.get("close_position_5d_pct"))
    price_score = round(
        (
            0.65 * _band_similarity(change, template["change_band"])
            + 0.35 * min(abs(intraday) / 5.0, 1.0)
        ) * 100
    )
    position_score = round(
        (
            0.70 * _band_similarity(pullback, template["pullback_band"])
            + 0.30 * (1.0 - min(abs(high_position - 50.0) / 50.0, 1.0) if high_position else 0.0)
        ) * 100
    )
    liquidity_score = round((min(abs(volume_ratio - 1.0) / 1.0, 1.0) if volume_ratio else 0.0) * 100)
    context_score = round(float(template.get("base_similarity") or 0) * 100)
    return {
        "price": price_score,
        "position": position_score,
        "liquidity": liquidity_score,
        "context": context_score,
    }


def _historical_pressure_template(features):
    if not features:
        return {
            "event": "一般高檔震盪回測",
            "pattern": "一般震盪",
            "similarity": 0.35,
            "difference": "TWSE特徵不足，僅能低信心觀察",
            "watch": "觀察是否重新站回短線高點",
            "library_size": len(TAIWAN_CRASH_TEMPLATE_LIBRARY),
        }
    best = None
    for template in TAIWAN_CRASH_TEMPLATE_LIBRARY:
        score = _score_taiwan_crash_template(template, features)
        if best is None or score > best[0]:
            best = (score, template)
    if not best or best[0] < 0.48:
        return {
            "event": "一般高檔震盪回測",
            "pattern": "一般震盪",
            "similarity": 0.45,
            "difference": "未達台股急跌樣本相似門檻",
            "watch": "觀察是否重新站回短線高點",
            "library_size": len(TAIWAN_CRASH_TEMPLATE_LIBRARY),
        }
    template = best[1]
    return {
        "event": template["event"],
        "pattern": template.get("pattern"),
        "similarity": best[0],
        "module_scores": _historical_module_scores(template, features),
        "difference": template["difference"],
        "watch": template["watch"],
        "library_size": len(TAIWAN_CRASH_TEMPLATE_LIBRARY),
    }


def _fmt_ratio(value):
    try:
        return f"{float(value):.2f}x"
    except (TypeError, ValueError):
        return "-"


def _fmt_position_pct(value):
    try:
        return f"{float(value):.0f}%"
    except (TypeError, ValueError):
        return "-"


def _historical_strength_label(features):
    change = _value_or_zero(features.get("change_pct"))
    pullback = _value_or_zero(features.get("pullback_from_high_pct"))
    volume_ratio = _value_or_zero(features.get("turnover_ratio"))
    if change <= -3.0 or pullback <= -6.0:
        return "急跌"
    if change <= -1.2 and volume_ratio >= 1.2:
        return "帶量轉弱"
    if change <= -1.2:
        return "壓力前段"
    return "一般回測"


def _historical_module_score_line(template):
    scores = template.get("module_scores") or {}
    if not scores:
        return ""
    return (
        f"模組分數：價格 {scores.get('price', 0)}｜"
        f"位置 {scores.get('position', 0)}｜"
        f"量能 {scores.get('liquidity', 0)}｜"
        f"情境 {scores.get('context', 0)}"
    )


def _historical_followup_line(template, features):
    checks = []
    if _value_or_zero(features.get("change_pct")) <= -1.2:
        checks.append("隔日是否續破當日低點")
    if _value_or_zero(features.get("turnover_ratio")) >= 1.2:
        checks.append("量能是否再放大")
    if _value_or_zero(features.get("close_position_5d_pct")) <= 35:
        checks.append("是否跌破5日區間下緣")
    if _value_or_zero(features.get("pullback_from_high_pct")) <= -4:
        checks.append("高檔回落是否擴大")
    if not checks:
        checks.append("是否重新站回短線高點")
    checks.append(template["watch"])
    return "；".join(dict.fromkeys(checks[:4]))


def _build_twse_pressure_line(features):
    template = _historical_pressure_template(features)
    matched = [
        f"跌幅 {_fmt_pct(features.get('change_pct'))}",
        f"高檔回落 {_fmt_pct(features.get('pullback_from_high_pct'))}",
        f"盤中震盪 {_fmt_pct(features.get('intraday_range_pct'))}",
        f"量能 {_fmt_ratio(features.get('turnover_ratio'))}",
        f"5日位置 {_fmt_position_pct(features.get('close_position_5d_pct'))}",
    ]
    matched = [item for item in matched if not item.endswith(" -") and not item.endswith(" -x")]
    context = [
        f"型態 {template.get('pattern') or '-'}",
        f"壓力級別 {_historical_strength_label(features)}",
        f"樣本 {features.get('history_rows') or 0}日",
        f"樣本庫 {template['library_size']}件",
    ]
    gaps = [
        template["difference"],
    ]
    if _value_or_zero(features.get("pullback_from_high_pct")) > -4:
        gaps.append("高檔回落尚未到深度修正")
    if features.get("turnover_ratio") is None:
        gaps.append("量能資料不足，未納入主要判斷")
    elif _value_or_zero(features.get("turnover_ratio")) < 1.2:
        gaps.append("量能未明顯失控")
    if features.get("intraday_range_pct") is not None:
        if _value_or_zero(features.get("intraday_range_pct")) < 2:
            gaps.append("盤中震盪仍有限")
    percent = round(template["similarity"] * 100)
    return "\n".join([
        f"歷史類比：{template['event']}｜相似度 {percent}%｜{context[0]}｜{context[1]}｜source=TWSE",
        f"相似點：{'｜'.join(matched[:5])}",
        _historical_module_score_line(template),
        f"不相似/限制：{'；'.join(dict.fromkeys(gaps[:3]))}",
        f"下一步觀察：{_historical_followup_line(template, features)}",
        f"資料：TWSE近{features.get('history_rows') or 0}日｜樣本庫台股急跌 {template['library_size']}件",
    ])


def build_live_twse_historical_source(now=None, get_json=None):
    try:
        today_rows = _request_get_json(TWSE_MI_INDEX_ENDPOINT, requester=get_json)
        taiex = None
        for row in today_rows or []:
            if row.get("指數") == "發行量加權股價指數":
                taiex = row
                break
        if not taiex:
            return {
                "status": "insufficient-data",
                "line": f"{CRASH_ANALOGY_FALLBACK}｜source=TWSE",
                "source_url": TWSE_MI_INDEX_ENDPOINT,
            }

        history_rows = _request_get_json(TWSE_TAIEX_HISTORY_ENDPOINT, requester=get_json)
        parsed_history = []
        for row in history_rows or []:
            trade_date = _parse_official_date(row.get("Date"))
            close = _extract_text_number(row, ("ClosingIndex", "收盤指數"))
            if trade_date and close is not None:
                parsed_history.append({
                    "date": trade_date,
                    "open": _extract_text_number(row, ("OpeningIndex", "開盤指數")),
                    "high": _extract_text_number(row, ("HighestIndex", "最高指數")),
                    "low": _extract_text_number(row, ("LowestIndex", "最低指數")),
                    "close": close,
                    "turnover": _extract_text_number(row, ("TradingValue", "TradeValue", "成交金額", "成交值")),
                })
        parsed_history.sort(key=lambda item: item["date"])

        change_pct = _parse_number(taiex.get("漲跌百分比"))
        close = _parse_number(taiex.get("收盤指數"))
        if close is None and parsed_history:
            close = parsed_history[-1]["close"]
        current_row = parsed_history[-1] if parsed_history else {}
        if change_pct is None and len(parsed_history) >= 2 and parsed_history[-2].get("close"):
            change_pct = (parsed_history[-1]["close"] / parsed_history[-2]["close"] - 1) * 100
        recent_high = max(
            [row.get("high") or row.get("close") for row in parsed_history if row.get("high") or row.get("close")],
            default=None,
        )
        recent_low = min(
            [row.get("low") or row.get("close") for row in parsed_history if row.get("low") or row.get("close")],
            default=None,
        )
        recent_turnovers = [
            row.get("turnover")
            for row in parsed_history[-6:-1]
            if row.get("turnover") not in (None, 0)
        ]
        pullback = (close / recent_high - 1) * 100 if close and recent_high else None
        intraday_range = None
        if current_row.get("high") and current_row.get("low") and close:
            intraday_range = (current_row["high"] - current_row["low"]) / close * 100
        current_turnover = _extract_text_number(taiex, ("成交金額", "TradeValue", "成交值"))
        if current_turnover is None:
            current_turnover = current_row.get("turnover")
        avg_turnover = sum(recent_turnovers) / len(recent_turnovers) if recent_turnovers else None
        turnover_ratio = current_turnover / avg_turnover if current_turnover and avg_turnover else None
        close_position_5d = None
        if close and recent_high and recent_low and recent_high != recent_low:
            close_position_5d = ((close - recent_low) / (recent_high - recent_low)) * 100
        features = {
            "index": "發行量加權股價指數",
            "close": close,
            "change_pct": change_pct,
            "pullback_from_high_pct": pullback,
            "intraday_range_pct": intraday_range,
            "turnover_ratio": turnover_ratio,
            "close_position_5d_pct": close_position_5d,
            "recent_low": recent_low,
            "history_rows": len(parsed_history),
        }
        line = _build_twse_pressure_line(features)
        return {
            "status": "available",
            "line": line,
            "source_url": TWSE_MI_INDEX_ENDPOINT,
            "today_features": features,
        }
    except Exception as exc:
        return {
            "status": "source-error",
            "line": f"{CRASH_ANALOGY_FALLBACK}｜source=TWSE source-error",
            "error": str(exc)[:120],
            "source_url": TWSE_MI_INDEX_ENDPOINT,
        }


def _extract_html_table_rows(html):
    if not html or "location.href" in html or "<table" not in html.lower():
        return []
    rows = []
    for row_html in re.findall(r"<tr[^>]*>(.*?)</tr>", html, flags=re.I | re.S):
        cells = []
        for cell_html in re.findall(r"<t[dh][^>]*>(.*?)</t[dh]>", row_html, flags=re.I | re.S):
            text = re.sub(r"<[^>]+>", " ", cell_html)
            text = re.sub(r"\s+", " ", unescape(text)).strip()
            if text:
                cells.append(text)
        if cells:
            rows.append(cells)
    return rows


def _parse_mops_rows(html, fallback_code=None, fallback_name=None):
    rows = _extract_html_table_rows(html)
    has_official_header = any(
        "召開法人說明會日期" in " ".join(cells) or "法人說明會" in " ".join(cells)
        for cells in rows
    )
    parsed = []
    for cells in rows:
        joined = " ".join(cells)
        event_date = None
        for cell in cells:
            event_date = _parse_official_date(cell)
            if event_date:
                break
        if not event_date:
            continue
        code = str(fallback_code or "")
        for cell in cells:
            match = re.search(r"\b\d{4}\b", cell)
            if match:
                code = match.group(0)
                break
        if fallback_code and code != str(fallback_code):
            continue
        if not has_official_header and "法" not in joined and "說明會" not in joined and "法人" not in joined:
            continue
        parsed.append({
            "date": event_date,
            "co_id": code or fallback_code,
            "name": fallback_name or (cells[1] if len(cells) > 1 and re.fullmatch(r"\d{4}", str(cells[0])) else ""),
            "event": "法人說明會",
            "summary": cells[5] if len(cells) > 5 else "",
        })
    return parsed, has_official_header


def live_mops_adapter(params, post_text=None):
    try:
        request_params = {
            **(params or {}),
            "encodeURIComponent": str((params or {}).get("encodeURIComponent") or "1"),
            "step": str((params or {}).get("step") or "1"),
            "firstin": str((params or {}).get("firstin") or "1"),
            "off": str((params or {}).get("off") or "1"),
        }
        body = _request_post_text(MOPS_ENDPOINT, request_params, requester=post_text)
        rows, has_official_header = _parse_mops_rows(body, fallback_code=request_params.get("co_id"))
        if not rows:
            if has_official_header:
                return {"status": "available", "rows": []}
            return {"status": "source-error", "source": "MOPS", "reason": "unparseable"}
        return {"rows": rows}
    except Exception as exc:
        return {"status": "source-error", "source": "MOPS", "reason": str(exc)[:120]}


def _stock_code_from_financial_row(row):
    return str(
        row.get("公司代號")
        or row.get("SecuritiesCompanyCode")
        or row.get("stock_code")
        or ""
    ).strip()


def _merge_monthly_revenue_rows(target, rows):
    for row in rows or []:
        code = _stock_code_from_financial_row(row)
        if not code:
            continue
        target.setdefault(code, {})
        if row.get("revenue_month") or row.get("revenue_yoy"):
            revenue_yoy = row.get("revenue_yoy") or _fallback_revenue_yoy(row)
            target[code].update({
                "revenue_month": row.get("revenue_month"),
                "revenue_yoy": revenue_yoy,
                "revenue_cumulative_yoy": row.get("revenue_cumulative_yoy"),
                "revenue_source_date": row.get("revenue_source_date"),
            })
            continue
        target[code].update({
            "revenue_month": row.get("資料年月"),
            "revenue_yoy": row.get("營業收入-去年同月增減(%)"),
            "revenue_cumulative_yoy": row.get("累計營業收入-前期比較增減(%)"),
            "revenue_source_date": row.get("出表日期"),
        })


def _fallback_revenue_yoy(row):
    stock_code = str((row or {}).get("stock_code") or "")
    revenue_month = str((row or {}).get("revenue_month") or "")
    numeric_values = []
    for key, value in (row or {}).items():
        if key in {"source", "stock_code", "code", "revenue_month", "revenue_cumulative_yoy", "revenue_source_date"}:
            continue
        text = str(value or "").replace(",", "").strip()
        if not text or text in {stock_code, revenue_month}:
            continue
        if re.fullmatch(r"[+-]?\d+(?:\.\d+)?", text):
            if "." in text or text.startswith(("+", "-")):
                return text
            numeric_values.append(text)
    for text in numeric_values:
        try:
            if abs(float(text)) <= 10000:
                return text
        except Exception:
            continue
    return None


def _roc_year_month_from_date(value):
    return _roc_year_month_candidates(value, lookback=1)[0]


def _roc_year_month_candidates(value, lookback=4):
    current = value or date.today()
    if isinstance(current, datetime):
        current = current.date()
    year = current.year
    month = current.month - 1
    if month == 0:
        year -= 1
        month = 12
    candidates = []
    for _ in range(max(1, lookback)):
        candidates.append(f"{year - 1911}{month:02d}")
        month -= 1
        if month == 0:
            year -= 1
            month = 12
    return candidates


def _clean_mops_number(value):
    text = unescape(str(value or ""))
    text = re.sub(r"<[^>]+>", "", text)
    text = text.replace("&nbsp;", " ").replace(",", "").strip()
    return text


def _mops_value_after_label(html, label):
    pattern = (
        rf"<TH[^>]*>\s*{re.escape(label)}\s*</TH>\s*"
        r"<TD[^>]*>\s*(?P<value>.*?)\s*</TD>"
    )
    match = re.search(pattern, html or "", flags=re.I | re.S)
    return _clean_mops_number(match.group("value")) if match else ""


def _mops_values_after_label(html, label):
    pattern = (
        rf"<TH[^>]*>\s*{re.escape(label)}\s*</TH>\s*"
        r"<TD[^>]*>\s*(?P<value>.*?)\s*</TD>"
    )
    return [
        _clean_mops_number(match.group("value"))
        for match in re.finditer(pattern, html or "", flags=re.I | re.S)
    ]


def _parse_mops_monthly_revenue_row(code, html):
    if not html or str(code) not in html:
        return None
    period = re.search(r"民國\s*(?P<year>\d+)\s*年\s*(?P<month>\d+)\s*月", html)
    if not period:
        return None
    revenue = _mops_value_after_label(html, "本月")
    yoy_values = _mops_values_after_label(html, "增減百分比")
    if not revenue or not yoy_values:
        return None
    return {
        "公司代號": str(code),
        "資料年月": f"{int(period.group('year'))}{int(period.group('month')):02d}",
        "營業收入-當月營收": revenue,
        "營業收入-去年同月增減(%)": yoy_values[0],
        "累計營業收入-前期比較增減(%)": yoy_values[1] if len(yoy_values) > 1 else "",
        "出表日期": "",
        "source": "MOPS",
    }


def fetch_mops_monthly_revenue_row(code, revenue_month, requester=None, timeout=3, attempts=1):
    if not requests and requester is None:
        raise RuntimeError("requests unavailable")
    year = str(revenue_month)[:-2]
    month = str(revenue_month)[-2:]
    payload = {
        "encodeURIComponent": "1",
        "step": "1",
        "firstin": "1",
        "off": "1",
        "TYPEK": "all",
        "year": year,
        "month": month,
        "co_id": str(code),
        "queryName": "co_id",
        "inpuType": "co_id",
    }
    headers = dict(HTTP_HEADERS)
    headers["Referer"] = "https://mopsov.twse.com.tw/mops/web/t05st10_ifrs"
    last_error = None
    for _attempt in range(max(1, attempts)):
        try:
            if requester:
                html = requester(MOPS_MONTHLY_REVENUE_ENDPOINT, payload, headers)
            else:
                response = requests.post(
                    MOPS_MONTHLY_REVENUE_ENDPOINT,
                    data=payload,
                    headers=headers,
                    timeout=timeout,
                )
                response.raise_for_status()
                html = response.text
            row = _parse_mops_monthly_revenue_row(code, html)
            if row:
                row.setdefault("stock_code", str(code))
                row.setdefault("revenue_month", str(revenue_month))
            return row
        except Exception as exc:
            last_error = exc
    if last_error:
        raise last_error
    return None


def _fetch_mops_revenue_from_candidates(fetch, code, revenue_months):
    for revenue_month in revenue_months:
        try:
            row = fetch(code, revenue_month)
        except Exception:
            continue
        if row:
            row.setdefault("stock_code", str(code))
            row.setdefault("revenue_month", str(revenue_month))
            return row
    return None


def _can_refresh_revenue_month(target, code, row):
    new_month = str((row or {}).get("revenue_month") or "")
    old_month = str(((target or {}).get(str(code)) or {}).get("revenue_month") or "")
    return bool(new_month) and (not old_month or new_month > old_month)


def _refresh_monthly_revenue_from_mops(target, codes, revenue_month, fetcher=None, max_workers=3, retry_limit=6):
    unique_codes = [str(code) for code in dict.fromkeys(codes or []) if code]
    if not unique_codes:
        return []
    revenue_months = list(revenue_month) if isinstance(revenue_month, (list, tuple)) else [revenue_month]
    refreshed = []
    fetch = fetcher or fetch_mops_monthly_revenue_row
    if max_workers <= 1 or len(unique_codes) == 1:
        for code in unique_codes:
            row = _fetch_mops_revenue_from_candidates(fetch, code, revenue_months)
            if not row:
                continue
            if not _can_refresh_revenue_month(target, code, row):
                continue
            _merge_monthly_revenue_rows(target, [row])
            refreshed.append(code)
        return refreshed
    with ThreadPoolExecutor(max_workers=max(1, min(max_workers, len(unique_codes)))) as executor:
        futures = {
            executor.submit(_fetch_mops_revenue_from_candidates, fetch, code, revenue_months): code
            for code in unique_codes
        }
        for future in as_completed(futures):
            code = futures[future]
            try:
                row = future.result()
            except Exception:
                continue
            if not row:
                continue
            if not _can_refresh_revenue_month(target, code, row):
                continue
            _merge_monthly_revenue_rows(target, [row])
            refreshed.append(code)
    missing_codes = [code for code in unique_codes if code not in set(refreshed)]
    for code in missing_codes[:retry_limit]:
        retry_fetch = fetch if fetcher else (
            lambda stock_code, month: fetch_mops_monthly_revenue_row(stock_code, month, timeout=2, attempts=1)
        )
        row = _fetch_mops_revenue_from_candidates(retry_fetch, code, revenue_months)
        if not row:
            continue
        if not _can_refresh_revenue_month(target, code, row):
            continue
        _merge_monthly_revenue_rows(target, [row])
        refreshed.append(code)
    return refreshed


def _merge_eps_rows(target, rows):
    for row in rows or []:
        code = _stock_code_from_financial_row(row)
        if not code:
            continue
        target.setdefault(code, {})
        target[code].update({
            "eps": row.get("基本每股盈餘(元)") or row.get("基本每股盈餘") or row.get("EPS"),
            "eps_year": row.get("年度") or row.get("Year"),
            "eps_quarter": row.get("季別") or row.get("Season"),
            "eps_source_date": row.get("出表日期") or row.get("Date"),
        })


def build_live_stock_fundamentals_source(now=None, get_json=None):
    endpoints = (
        ("tpex_revenue", TPEX_MONTHLY_REVENUE_ENDPOINT, _merge_monthly_revenue_rows),
        ("twse_eps", TWSE_EPS_ENDPOINT, _merge_eps_rows),
        ("tpex_eps", TPEX_EPS_ENDPOINT, _merge_eps_rows),
    )
    rows_by_code = {}
    errors = []
    fetched = {}
    with ThreadPoolExecutor(max_workers=len(endpoints)) as executor:
        futures = {
            executor.submit(_request_get_json, url, requester=get_json): label
            for label, url, _merger in endpoints
        }
        for future in as_completed(futures):
            label = futures[future]
            try:
                fetched[label] = future.result()
            except Exception as exc:
                errors.append(f"{label}:{str(exc)[:60]}")
    for label, _url, merger in endpoints:
        try:
            merger(rows_by_code, fetched.get(label) or [])
        except Exception as exc:
            errors.append(f"{label}:{str(exc)[:60]}")
    if not rows_by_code:
        return {"status": "source-error", "items_by_code": {}, "errors": errors}
    return {
        "status": "available",
        "items_by_code": rows_by_code,
        "errors": errors,
        "source": "TWSE/TPEX OpenAPI",
    }


def _fundamentals_for_code(fundamentals_source, code):
    if not isinstance(fundamentals_source, dict):
        return {}
    items = fundamentals_source.get("items_by_code") or fundamentals_source.get("items") or {}
    return items.get(str(code)) or {}


def _fundamentals_label(fundamentals):
    if not fundamentals:
        return ""
    parts = []
    eps = fundamentals.get("eps")
    if eps not in (None, ""):
        eps_period = _financial_period_label(fundamentals.get("eps_year"), quarter=fundamentals.get("eps_quarter"))
        eps_label = f"EPS {eps_period} {_fmt_compact_number(eps)}" if eps_period else f"EPS {_fmt_compact_number(eps)}"
        parts.append(eps_label)
    revenue_yoy = fundamentals.get("revenue_yoy")
    if revenue_yoy not in (None, ""):
        revenue_period = _financial_period_label(None, month=fundamentals.get("revenue_month"))
        revenue_label = (
            f"營收 {revenue_period} {_fmt_compact_pct(revenue_yoy)}"
            if revenue_period else f"營收 {_fmt_compact_pct(revenue_yoy)}"
        )
        parts.append(revenue_label)
    return "｜".join(parts)


def _fundamentals_detail_line(fundamentals):
    label = _fundamentals_label(fundamentals)
    return f"  財報：{label}" if label else ""


def collect_target_fundamentals(
    results_map,
    fundamentals_source=None,
    max_items=MOPS_DEFAULT_MAX_TARGETS,
    now=None,
    mops_revenue_fetcher=None,
):
    if not isinstance(fundamentals_source, dict):
        return {"status": "missing-source", "items": []}
    if fundamentals_source.get("status") in {"source-error", "missing-source", "insufficient-data"}:
        return {"status": fundamentals_source.get("status"), "items": []}

    items = []
    targets = _target_stocks(results_map, max_targets=max_items)
    revenue_month_candidates = _roc_year_month_candidates(now, lookback=2)
    expected_revenue_month = revenue_month_candidates[0]
    items_by_code = fundamentals_source.setdefault("items_by_code", {})
    can_refresh_mops = bool(mops_revenue_fetcher) or fundamentals_source.get("source") == "TWSE/TPEX OpenAPI"
    stale_codes = [
        target["code"]
        for target in targets
        if can_refresh_mops
        and (_fundamentals_for_code(fundamentals_source, target["code"]).get("revenue_month") or "") < expected_revenue_month
    ]
    refreshed = _refresh_monthly_revenue_from_mops(
        items_by_code,
        stale_codes,
        revenue_month_candidates,
        fetcher=mops_revenue_fetcher,
    )

    for target in targets:
        fundamentals = _fundamentals_for_code(fundamentals_source, target["code"])
        items.append({
            "code": target["code"],
            "name": target["name"],
            "reason": target["reason"],
            "fundamentals": fundamentals,
            "fundamentals_label": _fundamentals_label(fundamentals),
        })
    return {
        "status": "available",
        "items": items,
        "expected_revenue_month": expected_revenue_month,
        "revenue_month_candidates": revenue_month_candidates,
        "mops_revenue_refreshed_codes": refreshed,
    }


def _mops_event_title(row):
    summary = str(row.get("summary") or row.get("event_summary") or "").strip()
    if summary:
        quoted = re.search(r"[「\"]([^」\"]+)[」\"]", summary)
        if quoted:
            return quoted.group(1).strip()
        title = re.split(r"[，,；;。]\s*說明", summary, maxsplit=1)[0].strip()
        title = re.sub(r"^本公司受邀參加", "", title).strip()
        title = re.sub(r"^本公司受邀", "", title).strip()
        title = re.sub(r"^受邀參加", "", title).strip()
        title = title.replace("舉辦之法人說明會", "法人說明會")
        return title[:60] if len(title) > 60 else title
    return row.get("event") or row.get("event_name") or row.get("事件") or "法人說明會"


def _event_from_pattern(html, pattern, event, impact, source, default_year):
    match = re.search(pattern, html, flags=re.I | re.S)
    if not match:
        return None
    raw_date = match.group("date") if "date" in match.groupdict() else match.group(0)
    event_date = _normalize_official_event_date(raw_date, default_year)
    if not event_date:
        return None
    return {"date": event_date, "event": event, "impact": impact, "source": source}


def _source_label(source, source_kind=None):
    if not source:
        return ""
    suffix = "備援" if source_kind == "seed-fallback" else "官方"
    if str(source).endswith(("官方", "備援")):
        return str(source)
    return f"{source}{suffix}"


def _taiwan_market_impact_note(impact):
    text = str(impact or "")
    parts = []
    if "通膨" in text:
        parts.append("牽動Fed路徑與科技股估值")
    if "利率" in text:
        parts.append("影響外資風險偏好與台股估值")
    if "匯率" in text:
        parts.append("牽動美元/台幣與外資流向")
    if "政治風險" in text:
        parts.append("提高避險情緒與供應鏈不確定性")
    if "能源" in text:
        parts.append("影響成本、通膨與航運/製造族群")
    if not parts:
        return "可能改變外資風險偏好與台股資金面"
    deduped = []
    for part in parts:
        if part not in deduped:
            deduped.append(part)
    return "；".join(deduped[:2])


def build_live_global_event_source(now=None, get_text=None):
    base_date = _as_date(now or datetime.now()) or datetime.now().date()
    year = base_date.year
    events = []
    sources = [
        (
            "Fed",
            "https://www.federalreserve.gov/monetarypolicy/fomccalendars.htm",
            r"(?P<date>June\s+16\s*-\s*17)",
            "Fed FOMC 利率決策/SEP",
            "利率/匯率",
        ),
        (
            "BLS",
            "https://www.bls.gov/schedule/news_release/cpi.htm",
            r"(?P<date>06/10/2026|June\s+10,\s+2026)",
            "美國 CPI",
            "通膨/利率",
        ),
        (
            "BOJ",
            "https://www.boj.or.jp/en/about/calendar/",
            r"(?P<date>June\s+15\s*[-–]\s*16|06/15\s*[-–]\s*16)",
            "日本央行 BOJ 利率會議",
            "利率/匯率",
        ),
        (
            "BEA",
            "https://www.bea.gov/news/schedule",
            r"(?P<date>June\s+25,\s+2026|06/25/2026)",
            "美國 BEA GDP/PCE",
            "通膨/利率",
        ),
        (
            "ECB",
            "https://www.ecb.europa.eu/press/calendars/mgcgc/html/index.en.html",
            r"(?P<date>June\s+10\s*[-–]\s*11|10\s+June\s+2026)",
            "ECB 利率決策/記者會",
            "利率/匯率",
        ),
    ]
    source_errors = []
    for source, url, pattern, event, impact in sources:
        try:
            html = _request_get_text(url, requester=get_text)
            item = _event_from_pattern(html, pattern, event, impact, source, year)
            if item:
                events.append(item)
        except Exception as exc:
            source_errors.append(f"{source}:{str(exc)[:40]}")
            continue

    if events:
        return {"status": "available", "events": events, "source": "official-live", "errors": source_errors}
    return {
        "status": "available",
        "events": list(_DEFAULT_GLOBAL_EVENT_SEED),
        "source": "seed-fallback",
        "errors": source_errors,
    }


def collect_mops_events(
    results_map,
    now,
    mops_adapter=None,
    fundamentals_source=None,
    max_items=MOPS_DEFAULT_MAX_ITEMS,
    max_targets=MOPS_DEFAULT_MAX_TARGETS,
    max_queries=MOPS_DEFAULT_MAX_QUERIES,
    max_seconds=MOPS_DEFAULT_MAX_SECONDS,
):
    if mops_adapter is None:
        return {
            "status": "missing-source",
            "items": [],
            "queried_months": [],
            "query_count": 0,
            "target_count": 0,
            "budget_exhausted": False,
        }

    start = _as_date(now)
    end = start + timedelta(days=30)
    targets = _target_stocks(results_map, max_targets=max_targets)
    target_by_code = {item["code"]: item for item in targets}
    queried = []
    source_errors = []
    rows = []
    cache = {}
    started_at = monotonic()
    budget_exhausted = False
    try:
        month_keys = _month_keys(start, end)
        resolved_markets = set()
        max_typek_passes = max(len(_mops_typek_order(target)) for target in targets) if targets else 0
        for typek_pass in range(max_typek_passes):
            for target in targets:
                typek_order = _mops_typek_order(target)
                if typek_pass >= len(typek_order):
                    continue
                typek = typek_order[typek_pass]
                for year, month in month_keys:
                    resolved_key = (target["code"], year, month)
                    if resolved_key in resolved_markets:
                        continue
                    if len(queried) >= max_queries or (monotonic() - started_at) >= max_seconds:
                        budget_exhausted = True
                        break
                    params = {
                        "encodeURIComponent": "1",
                        "step": "1",
                        "firstin": "1",
                        "off": "1",
                        "TYPEK": typek,
                        "year": year,
                        "month": month,
                        "co_id": target["code"],
                    }
                    key = _mops_query_key(params)
                    if key in cache:
                        response = cache[key]
                    else:
                        queried.append(params)
                        response = mops_adapter(params)
                        cache[key] = response
                    if isinstance(response, dict) and response.get("status") == "source-error":
                        source_errors.append(params)
                        if target.get("typek") == typek:
                            resolved_markets.add(resolved_key)
                            continue
                        continue
                    data_rows = response.get("rows", []) if isinstance(response, dict) else response
                    if target.get("typek") == typek:
                        resolved_markets.add(resolved_key)
                    if data_rows:
                        resolved_markets.add(resolved_key)
                    for row in data_rows or []:
                        event_date = row.get("date") or row.get("event_date") or row.get("日期")
                        code = str(row.get("co_id") or row.get("stock_code") or row.get("公司代號") or target["code"])
                        if not _in_window(event_date, start, end) or code not in target_by_code:
                            continue
                        target_info = target_by_code[code]
                        fundamentals = _fundamentals_for_code(fundamentals_source, code)
                        rows.append({
                            "date": _as_date(event_date),
                            "code": code,
                            "name": row.get("name") or row.get("stock_name") or row.get("公司簡稱") or target_info["name"],
                            "event": _mops_event_title(row),
                            "summary": row.get("summary") or row.get("event_summary") or "",
                            "reason": target_info["reason"],
                            "fundamentals": fundamentals,
                            "fundamentals_label": _fundamentals_label(fundamentals),
                            "source": "MOPS",
                        })
                if budget_exhausted:
                    break
            if budget_exhausted:
                break
    except Exception:
        return {
            "status": "source-error",
            "items": [],
            "queried_months": queried,
            "query_count": len(queried),
            "target_count": len(targets),
            "budget_exhausted": budget_exhausted,
            "source_error_count": len(source_errors),
        }

    if not rows and source_errors:
        return {
            "status": "source-error",
            "items": [],
            "queried_months": queried,
            "query_count": len(queried),
            "target_count": len(targets),
            "budget_exhausted": budget_exhausted,
            "source_error_count": len(source_errors),
        }

    rows.sort(key=lambda item: (item["date"], item["code"], item["event"]))
    return {
        "status": "available",
        "items": rows[:max_items],
        "queried_months": queried,
        "query_count": len(queried),
        "target_count": len(targets),
        "budget_exhausted": budget_exhausted,
        "source_error_count": len(source_errors),
    }


def collect_global_events(now, global_event_source=None, max_items=5):
    if global_event_source is None:
        return {"status": "source-error", "items": []}
    if isinstance(global_event_source, dict):
        if global_event_source.get("status") == "source-error":
            return {"status": "source-error", "items": []}
        source_rows = global_event_source.get("events") or []
        source_kind = global_event_source.get("source")
    else:
        source_rows = global_event_source or []
        source_kind = "official-live"

    start = _as_date(now)
    end = start + timedelta(days=30)
    rows = []
    for row in source_rows:
        event_date = row.get("date") or row.get("event_date")
        if not _in_window(event_date, start, end):
            continue
        impact = row.get("impact") or row.get("impact_area") or ""
        first_impact = str(impact).split("/")[0].split("／")[0]
        rows.append({
            "date": _as_date(event_date),
            "date_label": _date_label(event_date),
            "event": row.get("event") or row.get("name"),
            "impact": impact,
            "impact_note": row.get("impact_note") or row.get("reason") or _taiwan_market_impact_note(impact),
            "source": row.get("source"),
            "source_label": _source_label(row.get("source"), source_kind),
            "priority": _EVENT_PRIORITY.get(first_impact, 9),
        })
    rows = [row for row in rows if row["event"] and row["impact"] and row["source"]]
    rows.sort(key=lambda item: (item["date"], item["priority"], item["event"]))
    return {"status": "available", "items": rows[:max_items]}


def fail_closed_mops_adapter(_params):
    return {"status": "source-error", "source": "MOPS", "reason": "official-adapter-not-configured"}


def default_future_watch_sources(now=None):
    return {
        "today_features": None,
        "historical_source": build_live_twse_historical_source(now),
        "mops_adapter": live_mops_adapter,
        "fundamentals_source": build_live_stock_fundamentals_source(now),
        "global_event_source": build_live_global_event_source(now),
    }


def build_future_watch_payload(
    results_map,
    now,
    *,
    today_features=None,
    historical_source=None,
    mops_adapter=None,
    fundamentals_source=None,
    global_event_source=None,
    mops_revenue_fetcher=None,
):
    return {
        "historical_analogy": build_historical_analogy(today_features, historical_source),
        "mops_events": collect_mops_events(
            results_map,
            now,
            mops_adapter=mops_adapter,
            fundamentals_source=fundamentals_source,
        ),
        "target_fundamentals": collect_target_fundamentals(
            results_map,
            fundamentals_source=fundamentals_source,
            now=now,
            mops_revenue_fetcher=mops_revenue_fetcher,
        ),
        "global_events": collect_global_events(now, global_event_source=global_event_source),
    }


def format_future_watch_message(payload, now, version):
    if not payload:
        return None

    lines = [
        f"【{now.strftime('%m/%d')} 未來30日關注｜{version}】",
        "【未來30日關注】",
    ]

    analogy = payload.get("historical_analogy") or {}
    lines.extend(["", "歷史類比", analogy.get("line") or CRASH_ANALOGY_FALLBACK])

    mops = payload.get("mops_events") or {}
    mops_items = mops.get("items") or []
    if mops.get("status") == "source-error":
        lines.extend(["", "未來30日法說會", MOPS_SOURCE_ERROR])
    elif mops_items:
        lines.extend(["", "未來30日法說會"])
        for item in mops_items[:MOPS_DEFAULT_MAX_ITEMS]:
            parts = [
                f"{_date_label(item.get('date'))} {item.get('code')} {item.get('name')}",
                item.get("event"),
            ]
            parts.append(f"關注原因：{item.get('reason')}")
            lines.append("｜".join(part for part in parts if part))

    target_fundamentals = payload.get("target_fundamentals") or {}
    fundamental_items = target_fundamentals.get("items") or []
    if target_fundamentals.get("status") == "source-error":
        lines.extend(["", "關注標的財報", "關注標的財報：官方來源暫時不可用，本次不列未確認數據"])
    elif fundamental_items:
        lines.extend(["", "關注標的財報"])
        for item in fundamental_items:
            label = item.get("fundamentals_label")
            if not label:
                label = "財報資料不足"
            lines.append(f"{item.get('code')} {item.get('name')}｜{label}｜關注原因：{item.get('reason')}")

    global_events = payload.get("global_events") or {}
    global_items = global_events.get("items") or []
    lines.extend(["", "未來30日台股影響事件"])
    if global_events.get("status") == "source-error":
        lines.append(TAIWAN_MARKET_EVENT_SOURCE_ERROR)
    elif global_items:
        for item in global_items[:5]:
            lines.append(
                f"{item.get('date_label') or _date_label(item.get('date'))} {item.get('event')}｜"
                f"影響面：{item.get('impact')}｜說明：{item.get('impact_note')}"
            )
    else:
        lines.append(TAIWAN_MARKET_EVENT_EMPTY)

    has_visible = (
        bool(analogy)
        or bool(mops_items)
        or mops.get("status") == "source-error"
        or bool(fundamental_items)
        or target_fundamentals.get("status") == "source-error"
        or bool(global_items)
        or global_events.get("status") in {"source-error", "available"}
    )
    return "\n".join(lines) if has_visible else None
