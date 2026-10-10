from django.contrib.auth import get_user_model
from django.contrib.sessions.models import Session


def invalidate_user_sessions(user_id: int, except_session_key: str | None = None) -> int:
    removed = 0
    uid = str(user_id)
    for session in Session.objects.all().iterator():
        try:
            data = session.get_decoded()
        except Exception:
            continue
        if data.get("_auth_user_id") != uid:
            continue
        if except_session_key and session.session_key == except_session_key:
            continue
        session.delete()
        removed += 1
    return removed
