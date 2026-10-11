from django.conf import settings


def branding(request):
    return {
        "mail_domain": getattr(settings, "MAIL_DOMAIN", "") or "",
    }
