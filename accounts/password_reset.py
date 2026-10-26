from __future__ import annotations

from django.conf import settings
from django.contrib.auth.tokens import default_token_generator
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.urls import reverse
from django.utils.encoding import force_bytes, force_str
from django.utils.http import urlsafe_base64_decode, urlsafe_base64_encode

from accounts.forms import SessionAwareSetPasswordForm
from accounts.session_utils import invalidate_user_sessions


def send_password_reset(user) -> None:
    token = default_token_generator.make_token(user)
    uid = urlsafe_base64_encode(force_bytes(user.pk))
    reset_path = reverse("password_reset_confirm", kwargs={"uidb64": uid, "token": token})
    reset_url = settings.PUBLIC_URL.rstrip("/") + reset_path
    app_url = f"mailstead://reset/{uid}/{token}"
    context = {"user": user, "reset_url": reset_url, "app_url": app_url}
    subject = render_to_string("accounts/password_reset_subject.txt", context).strip()
    body = render_to_string("accounts/password_reset_email.txt", context)
    send_mail(subject, body, settings.DEFAULT_FROM_EMAIL, [user.recovery_email])


def confirm_password_reset(*, uidb64: str, token: str, password: str, password_confirm: str):
    from django.contrib.auth import get_user_model

    try:
        uid = force_str(urlsafe_base64_decode(uidb64))
        user = get_user_model().objects.get(pk=uid)
    except Exception as exc:
        raise ValueError("invalid_token") from exc
    if not default_token_generator.check_token(user, token):
        raise ValueError("invalid_token")
    form = SessionAwareSetPasswordForm(
        user,
        {"new_password1": password, "new_password2": password_confirm},
    )
    if not form.is_valid():
        return form
    form.save()
    invalidate_user_sessions(user.pk)
    from api.auth import revoke_api_tokens

    revoke_api_tokens(user)
    return user
