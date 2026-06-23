import pytest

from masterblaster_control.p0_policy import TargetParseError, parse_target


_VALID = (
    "example.com",
    "sub.example.com",
    "192.0.2.1",
    "192.0.2.0/24",
    "https://example.com/path",
    "host-name",
)


@pytest.mark.parametrize("target", _VALID)
def test_parse_target_accepts_valid_corpus(target: str):
    target_type, normalized, _host = parse_target(target)
    assert target_type in {"domain", "host", "ip", "cidr", "url"}
    assert normalized


@pytest.mark.parametrize(
    "target",
    (
        "",
        "   ",
        "not a valid target!!!",
        "https://user@example.com/",
        "https://example.com?q=1",
        "a" * 300,
        "exa mple.com",
        "https://example.com#frag",
    ),
)
def test_parse_target_rejects_malformed_inputs(target: str):
    with pytest.raises((TargetParseError, Exception)):
        parse_target(target)


def test_parse_target_idn_homoglyph_ascii_form():
    # Punycode domains must be presented in ASCII for deterministic parsing.
    target_type, normalized, host = parse_target("xn--e1awd7f.com")
    assert target_type == "domain"
    assert normalized == "xn--e1awd7f.com"
    assert host == "xn--e1awd7f.com"


def test_parse_target_rejects_mixed_case_credential_patterns():
    with pytest.raises(Exception, match="URL targets must not include"):
        parse_target("HTTPS://USER:PASS@EXAMPLE.COM/")