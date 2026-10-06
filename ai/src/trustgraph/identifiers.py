"""Canonical forms for identifiers, so the same account, number or domain
written differently compares equal across signals."""
import re

# Two-label public suffixes, so "mail.acme.co.uk" reduces to "acme.co.uk".
_TWO_LABEL_SUFFIXES = {"co.uk", "org.uk", "ac.uk", "gov.uk", "com.au", "net.au", "co.nz",
                       "co.in", "co.za", "com.br", "co.jp", "com.sg", "com.mx"}


def split_domain(domain: str) -> tuple[str, str]:
    """(brand, suffix): "mail.acme-corp.co.uk" -> ("acme-corp", "co.uk")."""
    labels = domain.split(".")
    n = 2 if ".".join(labels[-2:]) in _TWO_LABEL_SUFFIXES else 1
    if len(labels) <= n:
        return domain, ""
    return labels[-n - 1], ".".join(labels[-n:])


def normalize_account(value: str) -> str:
    return re.sub(r"[^0-9A-Za-z]", "", value).upper()


def normalize_phone(value: str) -> str:
    """The national number: "+44 (0)20 7946 0958", "020 7946 0958" and
    "+442079460958" are the same line."""
    return re.sub(r"\D", "", value)[-10:]


def normalize_domain(value: str) -> str:
    """Registrable domain of a domain, URL or email address."""
    host = value.strip().lower()
    host = re.sub(r"^[a-z]+://", "", host).split("/")[0].split("?")[0]
    host = host.split("@")[-1].split(":")[0].strip(".")
    brand, suffix = split_domain(host)
    return f"{brand}.{suffix}" if suffix else brand
