"""
Heuristics to drop obvious ad / tracking DNS noise from storage and analytics.
Patterns are substring/regex matches on the full queried name (lowercased).
"""

import re
from typing import Pattern

# ad/tracker hostname fragments - add more if needed
_AD_REGEX_PARTS = [
    r"doubleclick\.net",
    r"googlesyndication\.com",
    r"googleadservices\.com",
    r"pagead2\.googlesyndication",
    r"googleads\.g\.doubleclick",
    r"googletagmanager\.com",
    r"googletagservices\.com",
    r"adservice\.google",
    r"ads-twitter\.com",
    r"ads\.reddit\.com",
    r"amazon-adsystem\.com",
    r"advertising\.com",
    r"adnxs\.com",
    r"adsrvr\.org",
    r"pubmatic\.com",
    r"rubiconproject\.com",
    r"taboola\.com",
    r"outbrain\.com",
    r"scorecardresearch\.com",
    r"moatads\.com",
    r"criteo\.com",
    r"criteo\.net",
    r"adsafeprotected\.com",
    r"adform\.net",
    r"2mdn\.net",
    r"fls\.doubleclick",
    r"fundingchoicesmessages\.google\.com",
    r"ads\.yahoo\.com",
]

_COMPILED: Pattern[str] = re.compile(
    "|".join(f"(?:{p})" for p in _AD_REGEX_PARTS),
    re.IGNORECASE,
)


def is_ad_tracking_domain(domain: str) -> bool:
    if not domain or not isinstance(domain, str):
        return False
    return bool(_COMPILED.search(domain.strip().lower()))
