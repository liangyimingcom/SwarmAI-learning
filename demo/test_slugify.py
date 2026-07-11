"""TDD tests for slugify — each test maps to an acceptance criterion (AC).

Regression tests below the ACs cover the Gate 2 adversarial findings.
"""
from slugify import slugify


# AC1: lowercase, whitespace / repeated separators collapse to a single hyphen
def test_ac1_lowercase_and_collapse():
    assert slugify("Hello, World!") == "hello-world"
    assert slugify("a   b\t\nc") == "a-b-c"
    assert slugify("foo___bar---baz") == "foo-bar-baz"


# AC2: strip edge hyphens, keep only [a-z0-9-]
def test_ac2_edges_and_charset():
    assert slugify("  --Trim Me--  ") == "trim-me"
    assert slugify("Price: $42 (USD)") == "price-42-usd"
    assert all(c.isalnum() or c == "-" for c in slugify("A!B@C#1"))


# AC3: empty / all-symbol input returns "" and never raises
def test_ac3_empty_and_symbols():
    assert slugify("") == ""
    assert slugify("!!!") == ""
    assert slugify("   ") == ""


# pre_mortem coverage: CJK / accented latin folding
def test_premortem_unicode():
    assert slugify("Café del Mar") == "cafe-del-mar"
    assert slugify("石老人 surf report") == "surf-report"
    assert slugify("naïve") == "naive"


# --- Gate 2 adversarial regression tests ---

# MED: length cap so a slug can't blow past filename/URL limits
def test_adv_med_length_cap():
    s = slugify("x!" * 100000)
    assert len(s) <= 200
    assert not s.endswith("-") and not s.startswith("-")
    assert slugify("a" * 50, max_len=10) == "a" * 10


# LOW: None fails loud instead of silently collapsing to ""
def test_adv_low_none_raises():
    raised = False
    try:
        slugify(None)  # type: ignore[arg-type]
    except TypeError:
        raised = True
    assert raised, "slugify(None) must raise TypeError, not return ''"


# LOW: pre-fold so ß/ø/æ transliterate instead of being silently dropped
def test_adv_low_prefold():
    assert slugify("Straße") == "strasse"
    assert slugify("Kjøbenhavn") == "kjobenhavn"
    assert slugify("Æther") == "aether"
