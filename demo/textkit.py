"""textkit — small text helpers for the demo toolkit."""
from __future__ import annotations

__all__ = ["truncate"]


def truncate(text: str, limit: int = 80, suffix: str = "…") -> str:
    """Truncate ``text`` to at most ``limit`` chars, appending ``suffix`` if cut.

    The result (including suffix) never exceeds ``limit``. Trailing whitespace
    before the suffix is stripped.

    >>> truncate("hello world", 8)
    'hello w…'
    >>> truncate("short", 80)
    'short'
    >>> truncate("edge case here", 10, "...")
    'edge ca...'
    """
    if text is None:
        raise TypeError("truncate() argument must be str, not None")
    if limit <= 0:
        return ""
    if len(text) <= limit:
        return text
    keep = limit - len(suffix)
    if keep <= 0:
        return suffix[:limit]
    return text[:keep].rstrip() + suffix
