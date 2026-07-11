"""slugify — convert an arbitrary string into a URL slug.

Convention (GitHub/Jekyll style): lowercase, non-alphanumeric runs collapse to a
single hyphen, leading/trailing hyphens stripped, output limited to [a-z0-9-].
Non-ASCII letters fold to ASCII where a well-known transliteration exists
(ß->ss, ø->o, æ->ae, …); anything still non-ASCII is dropped. Empty / all-symbol
input returns "" and never raises. ``None`` raises TypeError (fail-loud).

Hardened per adversarial review (run_6469c1bb, Gate 2):
  * MED  — length cap (default 200) so a slug can't blow past filename/URL limits.
  * LOW  — None raises TypeError instead of silently collapsing to "".
  * LOW  — pre-fold map so "Straße" -> "strasse", not the misleading "strae".
"""
from __future__ import annotations

import re
import unicodedata

_NON_ALNUM = re.compile(r"[^a-z0-9]+")
_EDGE_HYPHENS = re.compile(r"^-+|-+$")

__all__ = ["slugify", "DEFAULT_MAX_LEN"]

# Well-known folds that NFKD does NOT decompose (would otherwise be dropped).
_PREFOLD = str.maketrans({
    "ß": "ss", "ø": "o", "Ø": "o", "æ": "ae", "Æ": "ae",
    "œ": "oe", "Œ": "oe", "ı": "i", "İ": "i", "đ": "d", "Đ": "d",
    "ł": "l", "Ł": "l", "þ": "th", "Þ": "th",
})

DEFAULT_MAX_LEN = 200


def slugify(text: str, max_len: int = DEFAULT_MAX_LEN) -> str:
    """Return a URL slug for ``text`` (fail-loud on ``None``).

    >>> slugify("Hello, World!")
    'hello-world'
    >>> slugify("  Café del Mar  ")
    'cafe-del-mar'
    >>> slugify("Straße")
    'strasse'
    >>> slugify("石老人 surf report")
    'surf-report'
    >>> slugify("!!!")
    ''
    """
    if text is None:
        raise TypeError("slugify() argument must be str, not None")
    if not text:
        return ""
    folded = text.translate(_PREFOLD)
    normalized = unicodedata.normalize("NFKD", folded)
    ascii_only = normalized.encode("ascii", "ignore").decode("ascii")
    hyphenated = _NON_ALNUM.sub("-", ascii_only.lower())
    slug = _EDGE_HYPHENS.sub("", hyphenated)
    if max_len and len(slug) > max_len:
        slug = _EDGE_HYPHENS.sub("", slug[:max_len])  # re-strip after truncation
    return slug
