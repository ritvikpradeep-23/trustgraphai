"""Deterministic, offline URL parsing and signal extraction."""

from dataclasses import dataclass
import ipaddress
import re
from urllib.parse import urlsplit, urlunsplit


MAX_URL_LENGTH = 4096
_SUSPICIOUS_PATTERNS = re.compile(r"(?:%25|%2e|%2f|%5c|%40|\\\\|(?:^|[./_-])(?:login|verify|secure|account|update)(?:[./_-]|$))", re.I)
_MULTI_LABEL_SUFFIXES = {"co.uk", "org.uk", "ac.uk", "com.au", "net.au", "org.au", "co.nz", "com.br", "com.cn", "com.sg", "co.jp", "co.in"}


@dataclass(frozen=True)
class URLAnalysis:
    normalized_url: str
    scheme: str
    hostname: str
    registrable_domain: str
    port: int | None
    path: str
    query: str
    signals: dict[str, bool]
    reasons: list[str]


def _registrable_domain(hostname: str, is_ip: bool) -> str:
    if is_ip:
        return hostname
    labels = hostname.rstrip(".").split(".")
    if len(labels) < 2:
        return hostname
    suffix2 = ".".join(labels[-2:])
    suffix_size = 2 if suffix2 in _MULTI_LABEL_SUFFIXES else 1
    if len(labels) <= suffix_size:
        return hostname
    return ".".join(labels[-(suffix_size + 1):])


def analyze_url(value: str) -> URLAnalysis:
    raw = value.strip()
    if not raw:
        raise ValueError("URL must not be empty")
    if len(raw) > MAX_URL_LENGTH:
        raise ValueError(f"URL exceeds maximum length of {MAX_URL_LENGTH} characters")
    if any(ord(ch) < 32 or ch.isspace() for ch in raw):
        raise ValueError("URL contains whitespace or control characters")
    candidate = raw if re.match(r"^[A-Za-z][A-Za-z0-9+.-]*://", raw) else "https://" + raw
    try:
        parsed = urlsplit(candidate)
        scheme = parsed.scheme.lower()
        if scheme not in {"http", "https"}:
            raise ValueError("Only HTTP and HTTPS URLs are supported")
        if not parsed.netloc or not parsed.hostname:
            raise ValueError("URL must include a hostname")
        hostname = parsed.hostname.rstrip(".").encode("idna").decode("ascii").lower()
        if not hostname or len(hostname) > 253:
            raise ValueError("Invalid hostname")
        is_ip = False
        try:
            ipaddress.ip_address(hostname.strip("[]"))
            is_ip = True
        except ValueError:
            if any(not label or len(label) > 63 or label.startswith("-") or label.endswith("-") or not re.fullmatch(r"[a-z0-9-]+", label) for label in hostname.split(".")):
                raise ValueError("Invalid hostname")
        port = parsed.port
        userinfo = parsed.username is not None or parsed.password is not None
    except (UnicodeError, ValueError) as exc:
        raise ValueError(str(exc) or "Malformed URL") from exc

    path = parsed.path or "/"
    normalized_netloc = hostname + (f":{port}" if port is not None else "")
    normalized = urlunsplit((scheme, normalized_netloc, path, parsed.query, ""))
    subdomain_count = 0 if is_ip or "." not in hostname else max(0, len(hostname.split(".")) - len(_registrable_domain(hostname, is_ip).split(".")))
    signals = {
        "http": scheme == "http",
        "ip_hostname": is_ip,
        "unusual_port": port is not None and port not in ({80} if scheme == "http" else {443}),
        "excessive_subdomains": subdomain_count > 3,
        "suspicious_encoding_or_pattern": bool(_SUSPICIOUS_PATTERNS.search(raw)),
        "excessive_length": len(raw) > 2048,
        "embedded_userinfo": userinfo,
    }
    reasons = [name.replace("_", " ") for name, present in signals.items() if present]
    return URLAnalysis(
        normalized_url=normalized,
        scheme=scheme,
        hostname=hostname,
        registrable_domain=_registrable_domain(hostname, is_ip),
        port=port,
        path=path,
        query=parsed.query,
        signals=signals,
        reasons=reasons,
    )
