"""Future 30-day Telegram watch payload helpers."""

import re
from html import unescape
from datetime import date, datetime, timedelta

try:
    import requests
except ImportError:
    requests = None


CRASH_ANALOGY_FALLBACK = "歷史類比：無高相似崩盤樣本｜依據不足/相似度低"
GLOBAL_SOURCE_ERROR = "全球事件：source-error，本次不列未確認事件"
GLOBAL_EMPTY = "全球事件：未查到未來30日官方事件"
MOPS_SOURCE_ERROR = "法說會提醒：source-error（MOPS），本次不列事件"
MOPS_ENDPOINT = "https://mopsov.twse.com.tw/mops/web/ajax_t100sb02_1"
MOPS_METHOD = "POST"
MOPS_TYPEKS = ("sii", "otc", "rotc", "pub")
TWSE_MI_INDEX_ENDPOINT = "https://openapi.twse.com.tw/v1/exchangeReport/MI_INDEX"
TWSE_TAIEX_HISTORY_ENDPOINT = "https://openapi.twse.com.tw/v1/exchangeReport/MI_5MINS_HIST"
TWSE_TAIEX_HISTORY_RWD_ENDPOINT = "https://www.twse.com.tw/rwd/zh/TAIEX/MI_5MINS_HIST"
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
        "event": "ECB monetary policy meeting/press conference",
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
        "event": "BOJ MPM",
        "impact": "利率/匯率",
        "source": "BOJ",
    },
    {
        "date": "2026/06/15-17",
        "event": "G7 Evian",
        "impact": "政治風險",
        "source": "G7",
    },
    {
        "date": "2026/06/16-17",
        "event": "Fed FOMC SEP",
        "impact": "利率/匯率",
        "source": "Fed",
    },
    {
        "date": "2026/06/18",
        "event": "BoE MPC",
        "impact": "利率/匯率",
        "source": "BoE",
    },
    {
        "date": "2026/06/25",
        "event": "BEA GDP third estimate / Personal Income and Outlays",
        "impact": "通膨/利率",
        "source": "BEA",
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


def _target_stocks(results_map):
    targets = []
    seen = set()
    for name, data in (results_map or {}).items():
        code = str((data or {}).get("stock_code") or "").strip()
        if not code or code in seen:
            continue
        seen.add(code)
        reason = "持倉" if (data or {}).get("holding") else "候選"
        targets.append({"code": code, "name": name, "reason": reason})
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
    return {"status": "available", "line": "｜".join(item for item in parts if item)}


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
            close = _parse_number(row.get("ClosingIndex"))
            if trade_date and close is not None:
                parsed_history.append((trade_date, close))
        parsed_history.sort(key=lambda item: item[0])

        change_pct = _parse_number(taiex.get("漲跌百分比"))
        close = _parse_number(taiex.get("收盤指數"))
        line = f"{CRASH_ANALOGY_FALLBACK}｜source=TWSE"
        return {
            "status": "insufficient-data",
            "line": line,
            "source_url": TWSE_MI_INDEX_ENDPOINT,
            "today_features": {
                "index": "發行量加權股價指數",
                "close": close,
                "change_pct": change_pct,
                "history_rows": len(parsed_history),
            },
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
    parsed = []
    for cells in _extract_html_table_rows(html):
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
        if "法" not in joined and "說明會" not in joined and "法人" not in joined:
            continue
        parsed.append({
            "date": event_date,
            "co_id": code or fallback_code,
            "name": fallback_name or "",
            "event": "法人說明會",
        })
    return parsed


def live_mops_adapter(params, post_text=None):
    try:
        body = _request_post_text(MOPS_ENDPOINT, params, requester=post_text)
        rows = _parse_mops_rows(body, fallback_code=params.get("co_id"))
        if not rows:
            return {"status": "source-error", "source": "MOPS", "reason": "unparseable-or-empty"}
        return {"rows": rows}
    except Exception as exc:
        return {"status": "source-error", "source": "MOPS", "reason": str(exc)[:120]}


def _event_from_pattern(html, pattern, event, impact, source, default_year):
    match = re.search(pattern, html, flags=re.I | re.S)
    if not match:
        return None
    raw_date = match.group("date") if "date" in match.groupdict() else match.group(0)
    event_date = _normalize_official_event_date(raw_date, default_year)
    if not event_date:
        return None
    return {"date": event_date, "event": event, "impact": impact, "source": source}


def build_live_global_event_source(now=None, get_text=None):
    base_date = _as_date(now or datetime.now()) or datetime.now().date()
    year = base_date.year
    events = []
    sources = [
        (
            "Fed",
            "https://www.federalreserve.gov/monetarypolicy/fomccalendars.htm",
            r"(?P<date>June\s+16\s*-\s*17)",
            "Fed FOMC SEP",
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
            "BOJ MPM",
            "利率/匯率",
        ),
        (
            "BEA",
            "https://www.bea.gov/news/schedule",
            r"(?P<date>June\s+25,\s+2026|06/25/2026)",
            "BEA GDP third estimate / Personal Income and Outlays",
            "通膨/利率",
        ),
        (
            "ECB",
            "https://www.ecb.europa.eu/press/calendars/mgcgc/html/index.en.html",
            r"(?P<date>June\s+10\s*[-–]\s*11|10\s+June\s+2026)",
            "ECB monetary policy meeting/press conference",
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


def collect_mops_events(results_map, now, mops_adapter=None, max_items=5):
    if mops_adapter is None:
        return {"status": "missing-source", "items": [], "queried_months": []}

    start = _as_date(now)
    end = start + timedelta(days=30)
    targets = _target_stocks(results_map)
    target_by_code = {item["code"]: item for item in targets}
    queried = []
    rows = []
    try:
        for target in targets:
            for year, month in _month_keys(start, end):
                for typek in MOPS_TYPEKS:
                    params = {
                        "TYPEK": typek,
                        "year": year,
                        "month": month,
                        "co_id": target["code"],
                    }
                    queried.append(params)
                    response = mops_adapter(params)
                    if isinstance(response, dict) and response.get("status") == "source-error":
                        return {"status": "source-error", "items": [], "queried_months": queried}
                    data_rows = response.get("rows", []) if isinstance(response, dict) else response
                    for row in data_rows or []:
                        event_date = row.get("date") or row.get("event_date") or row.get("日期")
                        code = str(row.get("co_id") or row.get("stock_code") or row.get("公司代號") or target["code"])
                        if not _in_window(event_date, start, end) or code not in target_by_code:
                            continue
                        target_info = target_by_code[code]
                        rows.append({
                            "date": _as_date(event_date),
                            "code": code,
                            "name": row.get("name") or row.get("stock_name") or row.get("公司簡稱") or target_info["name"],
                            "event": row.get("event") or row.get("event_name") or row.get("事件") or "法人說明會",
                            "reason": target_info["reason"],
                            "source": "MOPS",
                        })
    except Exception:
        return {"status": "source-error", "items": [], "queried_months": queried}

    rows.sort(key=lambda item: (item["date"], item["code"], item["event"]))
    return {"status": "available", "items": rows[:max_items], "queried_months": queried}


def collect_global_events(now, global_event_source=None, max_items=5):
    if global_event_source is None:
        return {"status": "source-error", "items": []}
    if isinstance(global_event_source, dict):
        if global_event_source.get("status") == "source-error":
            return {"status": "source-error", "items": []}
        source_rows = global_event_source.get("events") or []
    else:
        source_rows = global_event_source or []

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
            "source": row.get("source"),
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
        "global_event_source": build_live_global_event_source(now),
    }


def build_future_watch_payload(
    results_map,
    now,
    *,
    today_features=None,
    historical_source=None,
    mops_adapter=None,
    global_event_source=None,
):
    return {
        "historical_analogy": build_historical_analogy(today_features, historical_source),
        "mops_events": collect_mops_events(results_map, now, mops_adapter=mops_adapter),
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
        lines.extend(["", "法說會提醒", MOPS_SOURCE_ERROR])
    elif mops_items:
        lines.extend(["", "法說會提醒"])
        for item in mops_items[:5]:
            lines.append(
                f"{_date_label(item.get('date'))} {item.get('code')} {item.get('name')}｜"
                f"{item.get('event')}｜關注原因：{item.get('reason')}｜source=MOPS"
            )

    global_events = payload.get("global_events") or {}
    global_items = global_events.get("items") or []
    lines.extend(["", "全球事件"])
    if global_events.get("status") == "source-error":
        lines.append(GLOBAL_SOURCE_ERROR)
    elif global_items:
        for item in global_items[:5]:
            lines.append(
                f"{item.get('date_label') or _date_label(item.get('date'))} {item.get('event')}｜"
                f"影響面：{item.get('impact')}｜source={item.get('source')}"
            )
    else:
        lines.append(GLOBAL_EMPTY)

    has_visible = (
        bool(analogy)
        or bool(mops_items)
        or mops.get("status") == "source-error"
        or bool(global_items)
        or global_events.get("status") in {"source-error", "available"}
    )
    return "\n".join(lines) if has_visible else None
