import logging
from django.contrib.auth.signals import user_logged_in, user_logged_out, user_login_failed
from django.dispatch import receiver

log = logging.getLogger("security")

def ip(request):
    return request.META.get("REMOTE_ADDR", "-") if request else "-"

@receiver(user_logged_in)
def ok(sender, request, user, **kw):
    log.info("LOGIN_OK user=%s role=%s ip=%s", user.username, user.role, ip(request))

@receiver(user_login_failed)
def fail(sender, credentials, request=None, **kw):
    log.warning("LOGIN_FAIL user=%s ip=%s", credentials.get("username"), ip(request))

@receiver(user_logged_out)
def out(sender, request, user, **kw):
    log.info("LOGOUT user=%s ip=%s", getattr(user, "username", "-"), ip(request))