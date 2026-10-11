from django.contrib.auth import get_user_model
from django.contrib.auth.signals import user_logged_in
from django.db.models.signals import post_save
from django.dispatch import receiver

from accounts.models import Mailbox


@receiver(post_save, sender=get_user_model())
def ensure_mailbox_placeholder(sender, instance, created, **kwargs):
    """Mailboxes are normally assigned by admin; no auto-create on user save."""
    return


@receiver(user_logged_in)
def reject_disabled_user(sender, request, user, **kwargs):
    if hasattr(user, "mailbox") and user.mailbox.state == Mailbox.State.DISABLED:
        from django.contrib.auth import logout

        logout(request)
