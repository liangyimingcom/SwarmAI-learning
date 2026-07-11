"""Tests for textkit.truncate."""
from textkit import truncate


def test_no_truncation_when_short():
    assert truncate("short", 80) == "short"
    assert truncate("", 10) == ""


def test_truncates_with_suffix_within_limit():
    r = truncate("hello world", 8)
    assert r == "hello w…"
    assert len(r) <= 8


def test_custom_suffix_and_rstrip():
    assert truncate("edge case here", 10, "...") == "edge ca..."


def test_zero_and_none():
    assert truncate("anything", 0) == ""
    raised = False
    try:
        truncate(None)  # type: ignore[arg-type]
    except TypeError:
        raised = True
    assert raised
