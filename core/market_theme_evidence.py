REQUIRED_STRUCTURED_FIELDS = {
    "as_of",
    "freshness",
    "freshness_reason",
    "level",
    "supports_claims",
    "limitations",
}

REPORT_DERIVED_FAMILY = "report_derived"

WATCHLIST_SOURCE = "watchlist_breadth"
MARKET_SOURCE_TYPES = {"market_index", "sector_index"}
BACKGROUND_SOURCE_TYPES = {"flow", "official", "external_context"}
LEGACY_SOURCE_TYPE_MAP = {
    "market_state": "market_index",
    "price_volume": "market_index",
    "structured_strategy_evidence": "watchlist_breadth",
    "watchlist_theme_breadth": "watchlist_breadth",
}
CONFIRMED_REQUIRED_SOURCE_TYPES = {WATCHLIST_SOURCE, *MARKET_SOURCE_TYPES}
PERSISTENT_SOURCE_FAMILIES = {"production_db", "owner_approved_persistent"}
NON_PERSISTENT_SOURCE_FAMILIES = {
    "runtime",
    "runtime_diagnostic",
    "local",
    "cache",
    "worktree",
    "test_fixture",
    "test fixture",
    REPORT_DERIVED_FAMILY,
}
SUPPORTIVE_LEVELS = {"supportive", "confirmed", "supporting"}
WEAK_LEVELS = {"weak"}
MIXED_LEVELS = {"mixed", "neutral"}
EVIDENCE_ALLOWED_EFFECTS = ["wording", "排序提示", "detail trace"]
EVIDENCE_FORBIDDEN_EFFECTS = [
    "不得改核心交易門檻",
    "不得變 BUY",
    "不得覆蓋風控",
    "不得 fake confirmed",
    "不得用 runtime 補 DB",
]
FAIL_CLOSED_SOURCE_STATUSES = {
    "absent",
    "missing-source",
    "source-error",
    "insufficient-data",
}


def _theme_from_text(text):
    text = str(text or "")
    if any(keyword in text for keyword in ["AI", "人工智慧", "電子供應鏈"]):
        return "AI/電子供應鏈"
    return None


def _theme_from_results_map(results_map):
    for data in (results_map or {}).values():
        result = data.get("result") if isinstance(data, dict) else None
        for source in [data, result or {}]:
            theme = source.get("theme") if isinstance(source, dict) else None
            if theme:
                return str(theme)
    return None


def _normalize_source(source, fallback_family=None):
    if not isinstance(source, dict):
        return None

    normalized = dict(source)
    normalized["source_family"] = (
        normalized.get("source_family")
        or fallback_family
        or REPORT_DERIVED_FAMILY
    )
    normalized["source_type"] = (
        normalized.get("source_type")
        or LEGACY_SOURCE_TYPE_MAP.get(normalized["source_family"])
        or normalized["source_family"]
    )
    normalized["source_name"] = (
        normalized.get("source_name")
        or normalized.get("name")
        or normalized["source_family"]
    )
    return normalized


def _sources_from_existing_evidence(evidence):
    if not isinstance(evidence, dict):
        return []

    families = (
        evidence.get("sources")
        or evidence.get("source_family_details")
        or evidence.get("source_families")
        or []
    )
    if isinstance(families, dict):
        families = [families]
    if isinstance(families, str):
        families = [families]

    sources = []
    for family in families:
        if isinstance(family, dict):
            sources.append(family)
            continue
        if family:
            sources.append({"source_family": family})

    if not sources and evidence.get("source_family"):
        sources.append({"source_family": evidence.get("source_family")})

    return sources


def _missing_structured_fields(source):
    return sorted(
        field for field in REQUIRED_STRUCTURED_FIELDS
        if field not in source or source.get(field) in (None, "")
    )


def _source_theme(source):
    if not isinstance(source, dict):
        return None

    for key in ["theme_label", "theme", "topic", "sector"]:
        if source.get(key):
            return str(source.get(key))

    claims = source.get("supports_claims") or []
    if isinstance(claims, str):
        claims = [claims]
    for claim in claims:
        theme = _theme_from_text(claim)
        if theme:
            return theme

    return None


def _source_limitation_text(source, missing):
    source_type = source.get("source_type") or source.get("source_family") or "unknown"
    if source_type == REPORT_DERIVED_FAMILY:
        return "來源不足，僅來自報文衍生資料"
    if missing:
        return f"{source_type} 缺 {'、'.join(missing)}，不可計入 confirmed"
    if not _source_is_fresh(source):
        return f"{source_type} freshness={source.get('freshness')}，不可計入 confirmed"
    return None


def _source_is_fresh(source):
    freshness = str(source.get("freshness") or "").lower()
    reason = str(source.get("freshness_reason") or "").lower()
    if freshness not in {"fresh", "same_day", "current"}:
        return False
    return not reason or reason in {
        "same_trade_date",
        "previous_trade_date_allowed",
    }


def _source_is_stale(source):
    freshness = str(source.get("freshness") or "").lower()
    reason = str(source.get("freshness_reason") or "").lower()
    return freshness in {"stale", "unavailable", "missing"} or reason in {"older_than_threshold"}


def _source_level(source):
    support_level = str(source.get("support_level") or "").lower()
    if support_level in {"confirmed", "supporting"}:
        return support_level
    return str(source.get("level") or source.get("market_direction") or "").lower()


def _source_supports_confirmed(source):
    return _source_level(source) in SUPPORTIVE_LEVELS


def _source_family_is_persistent(source):
    return str(source.get("source_family") or "").lower() in PERSISTENT_SOURCE_FAMILIES


def _source_family_is_non_persistent(source):
    family = str(source.get("source_family") or "").lower()
    return (
        family in NON_PERSISTENT_SOURCE_FAMILIES
        or family.startswith("runtime")
        or family.startswith("local")
        or family.startswith("cache")
        or family.startswith("worktree")
        or family.startswith("test")
        or bool(source.get("runtime_diagnostic"))
        or bool(source.get("runtime_fallback"))
    )


def _source_can_confirm(source):
    return (
        _source_family_is_persistent(source)
        and not _source_family_is_non_persistent(source)
        and source.get("source_type") in CONFIRMED_REQUIRED_SOURCE_TYPES.union(BACKGROUND_SOURCE_TYPES)
        and not _missing_structured_fields(source)
        and _source_is_fresh(source)
    )


def _source_boundary_family(raw_sources, has_watchlist_diagnostic=False, confirmed=False):
    if confirmed:
        confirmed_families = [
            str(source.get("source_family") or "").lower()
            for source in raw_sources
            if isinstance(source, dict) and _source_can_confirm(source)
        ]
        if "production_db" in confirmed_families:
            return "production_db"
        if "owner_approved_persistent" in confirmed_families:
            return "owner_approved_persistent"

    if has_watchlist_diagnostic or any(
        isinstance(source, dict)
        and (
            source.get("runtime_diagnostic")
            or source.get("runtime_fallback")
            or _source_family_is_non_persistent(source)
        )
        for source in raw_sources
    ):
        return "runtime_diagnostic"
    if any(
        isinstance(source, dict)
        and str(source.get("source_family") or "").lower() == "owner_approved_persistent"
        for source in raw_sources
    ):
        return "owner_approved_persistent"
    if any(
        isinstance(source, dict)
        and source.get("source_type") != REPORT_DERIVED_FAMILY
        for source in raw_sources
    ):
        return "production_db"
    return "production_db"


def _source_status_for_evidence(theme_status, confirmed, raw_sources, missing_source_reasons):
    if confirmed:
        return "ready"
    if any(
        isinstance(source, dict)
        and (
            _source_is_stale(source)
            or str(source.get("freshness") or "").lower() == "unknown"
        )
        for source in raw_sources
    ):
        return "stale"
    if missing_source_reasons:
        return "missing-source"
    if raw_sources:
        return "insufficient-data"
    if theme_status == "absent":
        return "missing-source"
    return "insufficient-data"


def _confidence_for_evidence(theme_status):
    return {
        "confirmed": "confirmed",
        "weak": "weak",
        "mixed": "mixed",
        "stale": "absent",
        "absent": "absent",
    }.get(theme_status, "absent")


def _freshness_for_evidence(raw_sources, confirmed):
    freshness_values = [
        str(source.get("freshness") or "").lower()
        for source in raw_sources
        if isinstance(source, dict) and source.get("freshness")
    ]
    if not freshness_values:
        return None
    if confirmed and all(value in {"fresh", "same_day", "current"} for value in freshness_values):
        return "fresh"
    if any(value in {"stale", "unavailable", "missing", "unknown"} for value in freshness_values):
        return "stale"
    return None


def _source_name_for_evidence(raw_sources, missing_source_reasons):
    names = []
    for source in raw_sources:
        if not isinstance(source, dict) or source.get("source_type") == REPORT_DERIVED_FAMILY:
            continue
        name = source.get("source_name") or source.get("source_type") or source.get("source_family")
        if name and name not in names:
            names.append(str(name))
    if names:
        return names
    return missing_source_reasons or ["market/theme production source missing"]


def _build_watchlist_breadth_diagnostic(results_map, as_of=None):
    if not results_map:
        return None

    tracked = 0
    supportive = 0
    weak = 0
    for data in results_map.values():
        if not isinstance(data, dict) or data.get("holding"):
            continue
        result = data.get("result") if isinstance(data.get("result"), dict) else {}
        tracked += 1
        if result.get("market_grade") in {"A+", "A", "B"} and result.get("decision") != "FAIL":
            supportive += 1
        if result.get("market_grade") == "D" or result.get("decision") in {"FAIL", "NO_TRADE"}:
            weak += 1

    if not tracked:
        return None

    if supportive >= max(1, tracked // 2 + tracked % 2):
        level = "supportive"
    elif weak:
        level = "weak"
    else:
        level = "neutral"

    return {
        "source_family": "watchlist_theme_breadth",
        "source_type": WATCHLIST_SOURCE,
        "source_name": "watchlist_strategy_snapshot",
        "as_of": as_of or "runtime_report",
        "freshness": "fresh",
        "freshness_reason": "same_trade_date",
        "level": level,
        "runtime_diagnostic": True,
        "supports_claims": [f"watchlist supportive {supportive}/{tracked}"],
        "limitations": ["非交易診斷，不可計入市場證據或 confirmed"],
    }


def build_market_theme_evidence(
    results_map=None,
    watchlist_groups=None,
    formatter_report_input=None,
    market_state=None,
    price_volume=None,
    structured_strategy_evidence=None,
    watchlist_theme_breadth=None,
    sources=None,
    theme=None,
    as_of=None,
    missing_db_evidence=False,
):
    raw_sources = []
    report_theme = theme or _theme_from_results_map(results_map)

    if report_theme:
        raw_sources.append({
            "source_family": REPORT_DERIVED_FAMILY,
            "source_type": REPORT_DERIVED_FAMILY,
            "theme": report_theme,
            "limitations": ["來源不足，僅來自報文衍生資料"],
        })

    if watchlist_groups:
        if not report_theme and isinstance(watchlist_groups, dict):
            report_theme = next(iter(watchlist_groups.keys()), None)
        raw_sources.append({
            "source_family": REPORT_DERIVED_FAMILY,
            "source_type": REPORT_DERIVED_FAMILY,
            "theme": report_theme,
            "limitations": ["來源不足，僅來自報文衍生資料"],
        })

    formatter_theme = _theme_from_text(formatter_report_input)
    if formatter_theme:
        raw_sources.append({
            "source_family": REPORT_DERIVED_FAMILY,
            "source_type": REPORT_DERIVED_FAMILY,
            "theme": formatter_theme or report_theme,
            "limitations": ["來源不足，僅來自報文衍生資料"],
        })
        report_theme = report_theme or formatter_theme

    watchlist_breadth_diagnostic = (
        _build_watchlist_breadth_diagnostic(results_map, as_of=as_of)
        if missing_db_evidence
        else None
    )

    structured_candidates = [
        (market_state, "market_state"),
        (price_volume, "price_volume"),
        (structured_strategy_evidence, "structured_strategy_evidence"),
        (watchlist_theme_breadth, "watchlist_theme_breadth"),
    ]
    for source, family in structured_candidates:
        normalized = _normalize_source(source, family)
        if normalized:
            raw_sources.append(normalized)

    for source in sources or []:
        normalized = _normalize_source(source)
        if normalized:
            raw_sources.append(normalized)

    valid_structured_by_key = {}
    valid_structured_by_type = {}
    source_families = []
    source_types = []
    limitations = []
    theme_label = report_theme

    for source in raw_sources:
        family = source.get("source_family") or REPORT_DERIVED_FAMILY
        source_type = source.get("source_type") or family
        if family not in source_families:
            source_families.append(family)
        if source_type not in source_types:
            source_types.append(source_type)

        theme_label = theme_label or _source_theme(source)

        missing = _missing_structured_fields(source)
        limitation = _source_limitation_text(source, missing)
        if limitation and limitation not in limitations:
            limitations.append(limitation)

        if (
            _source_can_confirm(source)
            and (family, source_type, source.get("source_name")) not in valid_structured_by_key
        ):
            valid_structured_by_key[(family, source_type, source.get("source_name"))] = source
            valid_structured_by_type.setdefault(source_type, source)

    valid_families = []
    for source in valid_structured_by_key.values():
        family = source.get("source_family")
        if family not in valid_families:
            valid_families.append(family)
    has_watchlist = (
        WATCHLIST_SOURCE in valid_structured_by_type
        and _source_supports_confirmed(valid_structured_by_type[WATCHLIST_SOURCE])
    )
    market_source_type = next(
        (
            source_type for source_type in MARKET_SOURCE_TYPES
            if source_type in valid_structured_by_type
            and _source_supports_confirmed(valid_structured_by_type[source_type])
        ),
        None,
    )
    has_market_source = market_source_type is not None
    stale_required = any(
        (source.get("source_type") in {WATCHLIST_SOURCE, *MARKET_SOURCE_TYPES}) and _source_is_stale(source)
        for source in raw_sources
        if isinstance(source, dict)
    )
    confirmed = has_watchlist and has_market_source and not stale_required
    confirmed_source_types = (
        [WATCHLIST_SOURCE, market_source_type]
        if confirmed
        else []
    )

    if not limitations and raw_sources and not confirmed:
        limitations.append("來源不足，缺少 watchlist breadth + market/sector index 同向 fresh sources")

    has_runtime_watchlist = any(
        isinstance(source, dict)
        and source.get("source_type") == WATCHLIST_SOURCE
        and source.get("runtime_fallback")
        for source in raw_sources
    )
    has_runtime_supportive_watchlist = any(
        isinstance(source, dict)
        and source.get("source_type") == WATCHLIST_SOURCE
        and source.get("runtime_fallback")
        and _source_level(source) == "supportive"
        for source in raw_sources
    )
    has_any_market_index = any(
        isinstance(source, dict) and source.get("source_type") == "market_index"
        for source in raw_sources
    )
    has_any_sector_index = any(
        isinstance(source, dict) and source.get("source_type") == "sector_index"
        for source in raw_sources
    )
    missing_source_reasons = []
    if missing_db_evidence:
        missing_source_reasons.append("缺 DB evidence table/cache")
    if not has_runtime_watchlist and not watchlist_breadth_diagnostic:
        missing_source_reasons.append("缺 runtime watchlist breadth")
    if not has_any_market_index:
        missing_source_reasons.append("缺 market_index")
    if not has_any_sector_index:
        missing_source_reasons.append("缺 sector_index")

    supportive_count = sum(
        1 for source in valid_structured_by_type.values()
        if _source_level(source) in SUPPORTIVE_LEVELS
    )
    conflicting_count = sum(
        1 for source in raw_sources
        if isinstance(source, dict)
        and source.get("source_type") != REPORT_DERIVED_FAMILY
        and _source_level(source) in WEAK_LEVELS.union(MIXED_LEVELS)
    )
    if confirmed:
        theme_status = "confirmed"
    elif missing_db_evidence and not valid_structured_by_type:
        theme_status = "absent"
    elif stale_required:
        theme_status = "stale"
    elif supportive_count and conflicting_count:
        theme_status = "mixed"
    elif raw_sources or theme_label:
        theme_status = "weak"
    else:
        theme_status = "absent"

    theme_direction = "supportive" if confirmed else ("mixed" if theme_status == "mixed" else None)
    actionability = "track_only" if theme_status in {"confirmed", "weak", "mixed", "stale"} else "absent"

    source_status = _source_status_for_evidence(
        theme_status,
        confirmed,
        raw_sources,
        missing_source_reasons,
    )

    return {
        "level": theme_status,
        "source_status": source_status,
        "source_family": _source_boundary_family(
            raw_sources,
            has_watchlist_diagnostic=bool(watchlist_breadth_diagnostic),
            confirmed=confirmed,
        ),
        "source_name": _source_name_for_evidence(raw_sources, missing_source_reasons),
        "freshness": _freshness_for_evidence(raw_sources, confirmed),
        "confidence": _confidence_for_evidence(theme_status),
        "allowed_effects": EVIDENCE_ALLOWED_EFFECTS,
        "forbidden_effects": EVIDENCE_FORBIDDEN_EFFECTS,
        "as_of": next(
            (
                source.get("as_of")
                for source in raw_sources
                if isinstance(source, dict) and source.get("as_of")
            ),
            None,
        ),
        "theme_status": theme_status,
        "theme_direction": theme_direction,
        "theme_label": theme_label,
        "theme": theme_label or "unknown",
        "market_direction": theme_direction or ("unknown" if theme_status == "absent" else theme_status),
        "execution_implication": "track_only" if actionability == "track_only" else "unavailable",
        "actionability": actionability,
        "source_families": source_families,
        "source_types": source_types,
        "source_family_details": raw_sources,
        "sources": raw_sources,
        "confirmed_source_families": valid_families,
        "confirmed_source_types": confirmed_source_types,
        "source_family_count_for_confirmed": len(valid_structured_by_type),
        "runtime_fallback": has_runtime_watchlist,
        "runtime_supportive": has_runtime_supportive_watchlist,
        "watchlist_breadth_diagnostic": watchlist_breadth_diagnostic,
        "missing_source_reasons": missing_source_reasons,
        "supports_claims": [
            claim
            for source in raw_sources
            if isinstance(source, dict)
            for claim in (
                source.get("supports_claims")
                if isinstance(source.get("supports_claims"), list)
                else ([source.get("supports_claims")] if source.get("supports_claims") else [])
            )
        ],
        "limitations": limitations,
        "confirmed": confirmed,
    }


def build_market_theme_evidence_provider(
    results_map=None,
    watchlist_groups=None,
    formatter_report_input=None,
    market_theme_evidence=None,
    **structured_sources,
):
    if (
        isinstance(market_theme_evidence, dict)
        and not market_theme_evidence.get("confirmed")
        and market_theme_evidence.get("status") in FAIL_CLOSED_SOURCE_STATUSES
    ):
        status = market_theme_evidence.get("status")
        reason = market_theme_evidence.get("reason")
        evidence = build_market_theme_evidence(
            results_map=results_map,
            watchlist_groups=watchlist_groups,
            formatter_report_input=formatter_report_input,
            theme=(
                market_theme_evidence.get("theme_label")
                or market_theme_evidence.get("theme")
                or market_theme_evidence.get("sector_theme_key")
            ),
            missing_db_evidence=True,
            **structured_sources,
        )
        evidence["source_status"] = status
        evidence["source_family"] = "production_db"
        evidence["source_of_truth"] = market_theme_evidence.get("source_of_truth") or "production_db"
        if reason:
            evidence["source_name"] = [reason]
            if reason not in evidence["missing_source_reasons"]:
                evidence["missing_source_reasons"].append(reason)
        return evidence

    existing_sources = _sources_from_existing_evidence(market_theme_evidence)
    theme = None
    missing_db_evidence = not existing_sources
    if isinstance(market_theme_evidence, dict):
        theme = (
            market_theme_evidence.get("theme_label")
            or market_theme_evidence.get("theme")
            or market_theme_evidence.get("topic")
        )
        structured_sources.setdefault("as_of", market_theme_evidence.get("as_of"))
        missing_db_evidence = not existing_sources

    evidence = build_market_theme_evidence(
        results_map=results_map,
        watchlist_groups=watchlist_groups,
        formatter_report_input=formatter_report_input,
        sources=existing_sources,
        theme=theme,
        missing_db_evidence=missing_db_evidence,
        **structured_sources,
    )
    if isinstance(market_theme_evidence, dict) and market_theme_evidence.get("evidence_trend"):
        evidence["evidence_trend"] = market_theme_evidence.get("evidence_trend")
    return evidence


def _display_range(lookback_range):
    if not lookback_range:
        return None
    return str(lookback_range).replace("~", " 至 ")


def _auxiliary_trend_text(trend):
    status = str(trend.get("status") or "")
    if status in {"confirmed_trend", "supporting_trend"}:
        return "延續順風"
    if status == "single_day":
        return "偏順風"
    return "資料不足"


def _primary_theme_name(evidence):
    theme = evidence.get("theme_label") or evidence.get("theme")
    if theme and str(theme) != "unknown":
        return str(theme)
    for source in evidence.get("sources") or evidence.get("source_family_details") or []:
        if not isinstance(source, dict):
            continue
        theme = source.get("theme_label") or source.get("theme")
        if theme:
            return str(theme)
    return "未命名題材"


def _format_market_theme_auxiliary_lines(evidence):
    if not evidence or not evidence.get("confirmed"):
        return ["市場/題材輔助：資料不足"]

    trend = evidence.get("evidence_trend") or {}
    lookback_range = _display_range(trend.get("lookback_range"))
    support_streak_days = trend.get("support_streak_days")
    if not lookback_range or not support_streak_days:
        return ["市場/題材輔助：資料不足"]

    lines = [
        "市場/題材輔助",
        f"- 題材：{_primary_theme_name(evidence)}",
        (
            f"背景：{_auxiliary_trend_text(trend)}；"
            f"觀察區間 {lookback_range}；"
            f"連續支持 {support_streak_days} 天。"
        ),
        "解讀：背景有支持，但不等於個股買點，不追高；仍看個股進場與風控條件。",
    ]
    return lines


def format_market_theme_summary_lines(evidence):
    if not evidence or evidence.get("theme_status") == "absent":
        missing = evidence.get("missing_source_reasons") if isinstance(evidence, dict) else []
        has_watchlist_diagnostic = bool(
            evidence.get("watchlist_breadth_diagnostic")
        ) if isinstance(evidence, dict) else False
        lines = ["證據：production 來源不足，不作確認。"]
        if has_watchlist_diagnostic:
            lines.append("詳情：runtime 觀察僅供診斷，非確認來源。")
        elif missing:
            lines.append("詳情：缺結構化 market/theme production source。")
        lines.extend(_format_market_theme_auxiliary_lines(evidence))
        return lines

    theme_label = evidence.get("theme_label") or "未命名主題"
    level = evidence.get("level") or evidence.get("theme_status")
    if evidence.get("confirmed"):
        lines = ["證據：production confirmed，市場/題材支持成立。"]
    else:
        lines = [f"市場 / 題材證據：{level}"]
    if evidence.get("confirmed"):
        lines.append("限制：題材只能追蹤，不代表可買")
    elif level == "stale":
        lines.append("限制：市場資料過期，本輪不判斷主線")
    elif level == "mixed":
        lines.append("限制：來源不同向，只能背景追蹤")
    else:
        lines.append("限制：內部題材證據未達確認，仍依量價 / 風控判斷")

    source_labels = []
    source_trade_dates = []
    requested_trade_dates = []
    for source in evidence.get("sources") or evidence.get("source_family_details") or []:
        if not isinstance(source, dict) or source.get("source_type") == REPORT_DERIVED_FAMILY:
            continue
        source_name = source.get("source_type") or source.get("source_family") or "unknown"
        freshness = source.get("freshness_reason") or source.get("freshness") or "unavailable"
        trade_date = source.get("trade_date")
        requested_trade_date = source.get("requested_trade_date")
        if trade_date and trade_date not in source_trade_dates:
            source_trade_dates.append(trade_date)
        if requested_trade_date and requested_trade_date not in requested_trade_dates:
            requested_trade_dates.append(requested_trade_date)
        if trade_date:
            source_labels.append(f"{source_name} latest_trade_date={trade_date} ({freshness})")
        else:
            source_labels.append(f"{source_name} {freshness}")

    if source_trade_dates:
        latest_trade_date = max(str(value) for value in source_trade_dates)
        previous_dates = sorted(
            {str(value) for value in source_trade_dates if str(value) != latest_trade_date},
            reverse=True,
        )
        date_parts = [f"latest_trade_date={latest_trade_date}"]
        if previous_dates:
            date_parts.append(f"previous_trade_date={previous_dates[0]}")
        if requested_trade_dates and str(requested_trade_dates[0]) != latest_trade_date:
            date_parts.append(f"report_date={requested_trade_dates[0]} uses latest trading day evidence")
        lines.append("證據日期：" + "；".join(date_parts))

    if source_labels:
        lines.append(f"來源：{'; '.join(source_labels[:3])}")

    trend = evidence.get("evidence_trend") or {}
    if evidence.get("confirmed") and trend.get("observed_days"):
        status_text = {
            "confirmed_trend": "連續支持",
            "supporting_trend": "偏多延續",
            "single_day": "單日確認",
        }.get(trend.get("status"), "歷史不足")
        lines.append(
            "趨勢："
            f"{status_text}｜近{trend.get('observed_days')}個證據日｜"
            f"連續{trend.get('support_streak_days', 0)}日支持"
            + (
                f"｜lookback_range={trend.get('lookback_range')}"
                if trend.get("lookback_range")
                else ""
            )
        )

    lines.extend(_format_market_theme_auxiliary_lines(evidence))
    return lines
