import logging
import pytest
from django.contrib.auth import get_user_model
from django.contrib.auth.tokens import default_token_generator
from django.core import mail
from django.test import Client
from django.urls import reverse
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode

from accounts.models import BootstrapState, Mailbox
from core.bootstrap import ensure_bootstrap_state
from jobs.models import WorkerHeartbeat


@pytest.mark.django_db
def test_bootstrap_one_time_setup(bootstrap_token):
    ensure_bootstrap_state()
    client = Client()
    url = reverse("setup", kwargs={"token": bootstrap_token})
    resp = client.post(url, {"username": "admin", "password1": "ComplexPass123!", "password2": "ComplexPass123!"})
    assert resp.status_code == 302
    User = get_user_model()
    assert User.objects.filter(username="admin", is_superuser=True).exists()
    state = BootstrapState.objects.get()
    assert state.consumed_at is not None

    resp2 = client.post(
        url,
        {"username": "admin2", "password1": "ComplexPass123!", "password2": "ComplexPass123!"},
    )
    assert resp2.status_code == 403


@pytest.mark.django_db
def test_bootstrap_redeploy_does_not_reset(bootstrap_token):
    ensure_bootstrap_state()
    client = Client()
    url = reverse("setup", kwargs={"token": bootstrap_token})
    client.post(url, {"username": "admin", "password1": "ComplexPass123!", "password2": "ComplexPass123!"})
    ensure_bootstrap_state()
    resp = client.get(url)
    assert resp.status_code == 403


@pytest.mark.django_db
def test_bootstrap_token_not_logged(bootstrap_token, caplog):
    caplog.set_level(logging.DEBUG)
    ensure_bootstrap_state()
    combined = caplog.text + " ".join(str(r.msg) for r in caplog.records)
    assert bootstrap_token not in combined


@pytest.mark.django_db
def test_registration_disabled():
    client = Client()
    resp = client.get("/accounts/register/")
    assert resp.status_code == 404


@pytest.mark.django_db
def test_health_and_readiness():
    client = Client()
    assert client.get("/healthz").status_code == 200
    WorkerHeartbeat.objects.create(pid=1)
    ready = client.get("/readyz")
    assert ready.status_code == 200
    data = ready.json()
    assert data["database"] == "ok"
    assert "mailbox" not in str(data).lower()


@pytest.mark.django_db
def test_password_reset_to_recovery_email(bootstrap_token):
    User = get_user_model()
    user = User.objects.create_user(username="u1", password="oldpass")
    user.recovery_email = "recovery@example.com"
    user.save()
    client = Client()
    resp = client.post(reverse("password_reset"), {"username": "u1"})
    assert resp.status_code == 302
    assert len(mail.outbox) == 1
    assert mail.outbox[0].to == ["recovery@example.com"]


@pytest.mark.django_db
def test_password_reset_rate_limit(bootstrap_token):
    User = get_user_model()
    User.objects.create_user(username="u1", password="x", recovery_email="r@e.com")
    client = Client()
    url = reverse("password_reset")
    for _ in range(6):
        client.post(url, {"username": "u1"})
    resp = client.post(url, {"username": "u1"})
    assert resp.status_code == 200
    assert b"Too many" in resp.content


@pytest.mark.django_db
def test_reset_token_invalid_after_password_change(bootstrap_token):
    User = get_user_model()
    user = User.objects.create_user(username="u1", password="oldpass")
    user.recovery_email = "recovery@example.com"
    user.save()
    token = default_token_generator.make_token(user)
    user.set_password("another-pass-123")
    user.save()
    assert not default_token_generator.check_token(user, token)


@pytest.mark.django_db
def test_sessions_invalidated_on_password_reset(bootstrap_token):
    User = get_user_model()
    user = User.objects.create_user(username="u1", password="oldpass")
    user.recovery_email = "recovery@example.com"
    user.save()
    client = Client()
    login = client.post(reverse("login"), {"username": "u1", "password": "oldpass"})
    assert login.status_code == 302
    assert client.session.session_key
    old_session = client.cookies["sessionid"].value
    token = default_token_generator.make_token(user)
    uid = urlsafe_base64_encode(force_bytes(user.pk))
    confirm = reverse("password_reset_confirm", kwargs={"uidb64": uid, "token": token})
    client.post(confirm, {"new_password1": "NewComplex123!", "new_password2": "NewComplex123!"})
    client2 = Client()
    client2.cookies["sessionid"] = old_session
    resp = client2.get("/admin/")
    assert resp.status_code == 302
    assert "/login" in resp.url


@pytest.mark.django_db
def test_logout_post_signs_out_user(bootstrap_token):
    User = get_user_model()
    User.objects.create_user(username="u1", password="Complex123!")
    client = Client()
    login = client.post(reverse("login"), {"username": "u1", "password": "Complex123!"})
    assert login.status_code == 302
    assert client.get(reverse("logout")).status_code == 405
    logout = client.post(reverse("logout"))
    assert logout.status_code == 302
    assert logout.url.endswith("/accounts/login/")
    inbox = client.get(reverse("mail_inbox"))
    assert inbox.status_code == 302
    assert "/login" in inbox.url


@pytest.mark.django_db
def test_disabled_mailbox_cannot_login(bootstrap_token):
    User = get_user_model()
    user = User.objects.create_user(username="u1", password="Complex123!")
    Mailbox.objects.create(user=user, address="u1@mail.test", state=Mailbox.State.DISABLED)
    client = Client()
    resp = client.post(reverse("login"), {"username": "u1", "password": "Complex123!"})
    assert resp.status_code == 200
    assert b"disabled" in resp.content.lower()


@pytest.mark.django_db
@pytest.mark.postgres
def test_postgres_settings_switch():
    import os

    if not os.environ.get("DATABASE_URL", "").startswith("postgres"):
        pytest.skip("DATABASE_URL postgres not set")
    from django.conf import settings

    assert settings.DATABASES["default"]["ENGINE"].endswith("postgresql")
