from core.settings import build_csrf_trusted_origins


def test_csrf_origins_include_public_url_and_railway_wildcard():
    origins = build_csrf_trusted_origins(
        "https://mail.example.com",
        ["mail.example.com", ".up.railway.app"],
        on_railway=True,
    )
    assert "https://mail.example.com" in origins
    assert "http://mail.example.com" in origins
    assert "https://*.up.railway.app" in origins


def test_csrf_origins_trust_railway_service_domain_when_public_url_is_custom():
    origins = build_csrf_trusted_origins(
        "https://mail.example.com",
        ["mail.example.com", "myapp-production.up.railway.app", ".up.railway.app"],
        on_railway=True,
    )
    assert "https://myapp-production.up.railway.app" in origins
    assert "https://*.up.railway.app" in origins


def test_csrf_origins_extra_env_style_hosts():
    origins = build_csrf_trusted_origins(
        "https://primary.example",
        [],
        extra="https://alt.example,legacy.example",
    )
    assert "https://alt.example" in origins
    assert "https://legacy.example" in origins
