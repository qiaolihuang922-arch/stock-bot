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
SUPPORTIVE_LEVELS = {"supportive"}
WEAK_LEVELS = {"weak"}
MIXED_LEVELS = {"mixed", "neutral"}


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
    return str(source.get("level") or source.get("market_direction") or "").lower()


def _source_supports_confirmed(source):
    return _source_level(source) in SUPPORTIVE_LEVELS


def _build_watchlist_breadth_source(results_map, as_of=None):
    if not results_map or not as_of:
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
        "as_of": as_of,
        "freshness": "fresh",
        "freshness_reason": "same_trade_date",
        "level": level,
        "supports_claims": [f"watchlist supportive {supportive}/{tracked}"],
        "limitations": ["只佐證題材背景，不改變個股買點"],
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

    generated_watchlist_source = _build_watchlist_breadth_source(results_map, as_of=as_of)
    if generated_watchlist_source:
        raw_sources.append(generated_watchlist_source)

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

    valid_structured_by_family = {}
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
            source_type != REPORT_DERIVED_FAMILY
            and source_type in CONFIRMED_REQUIRED_SOURCE_TYPES.union(BACKGROUND_SOURCE_TYPES)
            and not missing
            and _source_is_fresh(source)
            and family not in valid_structured_by_family
        ):
            valid_structured_by_family[family] = source
            valid_structured_by_type.setdefault(source_type, source)

    valid_families = list(valid_structured_by_family.keys())
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

    return {
        "level": theme_status,
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
        "source_family_count_for_confirmed": len(valid_families),
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
    existing_sources = _sources_from_existing_evidence(market_theme_evidence)
    theme = None
    if isinstance(market_theme_evidence, dict):
        theme = (
            market_theme_evidence.get("theme_label")
            or market_theme_evidence.get("theme")
            or market_theme_evidence.get("topic")
        )
        structured_sources.setdefault("as_of", market_theme_evidence.get("as_of"))

    return build_market_theme_evidence(
        results_map=results_map,
        watchlist_groups=watchlist_groups,
        formatter_report_input=formatter_report_input,
        sources=existing_sources,
        theme=theme,
        **structured_sources,
    )


def format_market_theme_summary_lines(evidence):
    if not evidence or evidence.get("theme_status") == "absent":
        return [
            "市場 / 題材證據：absent",
            "限制：市場證據不足，僅依策略分類追蹤",
        ]

    theme_label = evidence.get("theme_label") or "未命名主題"
    level = evidence.get("level") or evidence.get("theme_status")
    lines = [f"市場 / 題材證據：{level}"]
    if evidence.get("confirmed"):
        lines.append("限制：題材可追蹤，不代表可買")
    elif level == "stale":
        lines.append("限制：市場資料過期，本輪不判斷主線")
    elif level == "mixed":
        lines.append("限制：來源不同向，只能背景追蹤")
    else:
        lines.append("限制：市場證據不足，僅依策略分類追蹤")

    source_labels = []
    for source in evidence.get("sources") or evidence.get("source_family_details") or []:
        if not isinstance(source, dict) or source.get("source_type") == REPORT_DERIVED_FAMILY:
            continue
        source_name = source.get("source_type") or source.get("source_family") or "unknown"
        freshness = source.get("freshness_reason") or source.get("freshness") or "unavailable"
        source_labels.append(f"{source_name} {freshness}")

    if source_labels:
        lines.append(f"來源：{'; '.join(source_labels[:3])}")

    return lines
