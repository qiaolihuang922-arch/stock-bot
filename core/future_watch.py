"""Future 30-day Telegram watch payload helpers."""

import re
from datetime import date, datetime, timedelta


CRASH_ANALOGY_FALLBACK = "歷史類比：無高相似崩盤樣本｜依據不足/相似度低"
GLOBAL_SOURCE_ERROR = "全球事件：source-error，本次不列未確認事件"
GLOBAL_EMPTY = "全球事件：未查到未來30日官方事件"
MOPS_SOURCE_ERROR = "法說會提醒：source-error（MOPS），本次不列事件"
MOPS_ENDPOINT = "https://mopsov.twse.com.tw/mops/web/ajax_t100sb02_1"
MOPS_METHOD = "POST"
MOPS_TYPEKS = ("sii", "otc", "rotc", "pub")

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


def default_future_watch_sources():
    return {
        "historical_source": {"status": "insufficient-data", "source": "official-history-not-configured"},
        "mops_adapter": fail_closed_mops_adapter,
        "global_event_source": {"status": "available", "events": list(_DEFAULT_GLOBAL_EVENT_SEED)},
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
