REQUIRED_STRUCTURED_FIELDS = {
    "as_of",
    "freshness",
    "confidence",
    "supports_claims",
    "limitations",
}

REPORT_DERIVED_FAMILY = "report_derived"

STRUCTURED_CONFIRMED_FAMILIES = {
    "market_state",
    "price_volume",
    "structured_strategy_evidence",
    "watchlist_theme_breadth",
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
    return normalized


def _sources_from_existing_evidence(evidence):
    if not isinstance(evidence, dict):
        return []

    families = evidence.get("source_family_details") or evidence.get("source_families") or []
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
    family = source.get("source_family") or "unknown"
    if family == REPORT_DERIVED_FAMILY:
        return "來源不足，僅來自報文衍生資料"
    if missing:
        return f"{family} 缺 {'、'.join(missing)}，不可計入 confirmed"
    if not _source_is_fresh(source):
        return f"{family} freshness={source.get('freshness')}，不可計入 confirmed"
    return None


def _source_is_fresh(source):
    freshness = str(source.get("freshness") or "").lower()
    return freshness in {"fresh", "same_day", "current"}


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
):
    raw_sources = []
    report_theme = theme or _theme_from_results_map(results_map)

    if report_theme:
        raw_sources.append({
            "source_family": REPORT_DERIVED_FAMILY,
            "theme": report_theme,
            "limitations": ["來源不足，僅來自報文衍生資料"],
        })

    if watchlist_groups:
        if not report_theme and isinstance(watchlist_groups, dict):
            report_theme = next(iter(watchlist_groups.keys()), None)
        raw_sources.append({
            "source_family": REPORT_DERIVED_FAMILY,
            "theme": report_theme,
            "limitations": ["來源不足，僅來自報文衍生資料"],
        })

    formatter_theme = _theme_from_text(formatter_report_input)
    if formatter_theme:
        raw_sources.append({
            "source_family": REPORT_DERIVED_FAMILY,
            "theme": formatter_theme or report_theme,
            "limitations": ["來源不足，僅來自報文衍生資料"],
        })
        report_theme = report_theme or formatter_theme

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
    source_families = []
    limitations = []
    theme_label = report_theme

    for source in raw_sources:
        family = source.get("source_family") or REPORT_DERIVED_FAMILY
        if family not in source_families:
            source_families.append(family)

        theme_label = theme_label or _source_theme(source)

        missing = _missing_structured_fields(source)
        limitation = _source_limitation_text(source, missing)
        if limitation and limitation not in limitations:
            limitations.append(limitation)

        if (
            family != REPORT_DERIVED_FAMILY
            and family in STRUCTURED_CONFIRMED_FAMILIES
            and not missing
            and _source_is_fresh(source)
            and family not in valid_structured_by_family
        ):
            valid_structured_by_family[family] = source

    valid_families = list(valid_structured_by_family.keys())
    has_direction_source = any(
        family in valid_structured_by_family
        for family in ["market_state", "structured_strategy_evidence"]
    )
    confirmed = len(valid_families) >= 2 and has_direction_source

    if not limitations and raw_sources and not confirmed:
        limitations.append("來源不足，缺少兩類完整 structured sources")

    theme_status = "confirmed" if confirmed else ("weak" if raw_sources or theme_label else "absent")
    theme_direction = "bullish" if confirmed and has_direction_source else None
    actionability = "theme_confirmed" if confirmed else ("track_only" if theme_status == "weak" else "absent")

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
        "actionability": actionability,
        "source_families": source_families,
        "source_family_details": raw_sources,
        "confirmed_source_families": valid_families,
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
        return []

    theme_label = evidence.get("theme_label") or "未命名主題"
    if evidence.get("confirmed"):
        return [
            f"市場題材：{theme_label}證據偏多，但買點仍看個股條件",
        ]

    return [
        "市場題材：來源不足，僅追蹤",
    ]
