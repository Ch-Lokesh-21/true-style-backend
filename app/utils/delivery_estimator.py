from __future__ import annotations
from datetime import date, timedelta
import math

# -----------------------------
# Heuristics & small lookup data
# -----------------------------
# Major metros (first 3 digits / common city prefixes). Tweak as you like.
METRO_PREFIXES = {
    "110",  # Delhi
    "400",  # Mumbai
    "700",  # Kolkata
    "600",  # Chennai
    "560",  # Bengaluru
    "500",  # Hyderabad
    "411",  # Pune
    "380",  # Ahmedabad
}

# Remote / difficult logistics areas (sample prefixes).
# Expand this list for your business.
REMOTE_OR_DIFFICULT_PREFIXES = {
    "737",  # Sikkim
    "744",  # Andaman & Nicobar
    "194",  # Ladakh
    "686",  # Idukki (hilly)
    "793",  # Meghalaya (sample)
    "794",  # Garo Hills (sample)
}

def _validate_pin(pin: str) -> str:
    """Return the normalized PIN (string) if valid, else raise ValueError."""
    s = str(pin).strip()
    if len(s) != 6 or not s.isdigit() or s[0] == "0":
        raise ValueError(f"Invalid Indian PIN code: {pin!r}")
    return s

def _business_add_days(start: date, days: int, skip_sundays: bool = True) -> date:
    """Add 'days' business days to start date. If skip_sundays=False, adds calendar days."""
    if not skip_sundays:
        return start + timedelta(days=days)

    d = start
    added = 0
    while added < days:
        d += timedelta(days=1)
        if d.weekday() != 6:  # 0=Mon ... 6=Sun
            added += 1
    return d

def _zone_bucket(src_pin: str, dst_pin: str) -> str:
    """
    Very lightweight zoning using PIN structure:
    - Same 6 digits        -> 'same_pin'
    - Same first 3 digits  -> 'intra_district'   (same sorting district)
    - Same first 2 digits  -> 'intra_subregion'
    - Same first 1 digit   -> 'intra_region'
    - Else                 -> 'inter_region'
    """
    if src_pin == dst_pin:
        return "same_pin"
    if src_pin[:3] == dst_pin[:3]:
        return "intra_district"
    if src_pin[:2] == dst_pin[:2]:
        return "intra_subregion"
    if src_pin[0] == dst_pin[0]:
        return "intra_region"
    return "inter_region"

def _base_transit_days(bucket: str) -> tuple[int, int]:
    """
    Return a (min_days, max_days) band for the zone bucket.
    Tune these numbers to match your carrier SLAs/historical data.
    """
    return {
        "same_pin":        (0, 1),  # courier pickup + same-day or next-day
        "intra_district":  (1, 2),
        "intra_subregion": (2, 4),
        "intra_region":    (3, 5),
        "inter_region":    (4, 7),
    }[bucket]

def estimate_delivery_days(
    src_pin: str,
    dst_pin: str,
    service_level: str = "standard",   # 'standard' | 'express'
    include_handling_day: bool = True, # add 1 day for warehouse pick/pack
) -> tuple[int, int]:
    """
    Core estimator. Returns (min_days, max_days) in business days (not dates).
    """
    s = _validate_pin(src_pin)
    d = _validate_pin(dst_pin)

    bucket = _zone_bucket(s, d)
    min_days, max_days = _base_transit_days(bucket)

    # Handling time (pick/pack) – typically 0.5–1 day; we add 1 to be safe.
    if include_handling_day:
        min_days += 1
        max_days += 1

    # Metro-to-metro advantage: shave 1 day (but never below 1 total day).
    if s[:3] in METRO_PREFIXES and d[:3] in METRO_PREFIXES:
        min_days = max(1, min_days - 1)
        max_days = max(1, max_days - 1)

    # Remote/difficult areas: add 1–2 days
    if s[:3] in REMOTE_OR_DIFFICULT_PREFIXES or d[:3] in REMOTE_OR_DIFFICULT_PREFIXES:
        min_days += 1
        max_days += 2

    # Express service: generally 30–40% faster. Round conservatively.
    if service_level.lower() == "express":
        # Reduce but keep min<=max and floor at 1
        min_days = max(1, math.floor(min_days * 0.7))
        max_days = max(min_days, math.ceil(max_days * 0.75))

    return (min_days, max_days)

def expected_delivery_window(
    src_pin: str,
    dst_pin: str,
    ship_on: date | None = None,
    service_level: str = "standard",
    skip_sundays: bool = True,
    include_handling_day: bool = True,
) -> dict:
    """
    Returns both the expected business-day band and the concrete delivery date range.
    Example return:
    {
        'days_min': 2,
        'days_max': 4,
        'ship_on': date(2025, 11, 11),
        'deliver_earliest': date(2025, 11, 13),
        'deliver_latest': date(2025, 11, 17)
    }
    """
    ship_on = ship_on or date.today()

    days_min, days_max = estimate_delivery_days(
        src_pin, dst_pin, service_level=service_level, include_handling_day=include_handling_day
    )

    earliest = _business_add_days(ship_on, days_min, skip_sundays=skip_sundays)
    latest   = _business_add_days(ship_on, days_max, skip_sundays=skip_sundays)

    return {
        "days_min": days_min,
        "days_max": days_max,
        "ship_on": ship_on,
        "deliver_earliest": earliest,
        "deliver_latest": latest,
    }