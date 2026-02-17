from django.contrib.auth.signals import user_logged_in
from django.dispatch import receiver
from django.contrib import messages

from .utils import send_login_alert_email, send_login_alert_sms


@receiver(user_logged_in)
def on_user_logged_in(sender, request, user, **kwargs):
    try:
        messages.success(request, "Login successful")
    except Exception:
        pass

    identifier_kind = None
    identifier_value = None
    try:
        if request is not None:
            identifier_kind = request.session.get('login_identifier_kind')
            identifier_value = request.session.get('login_identifier_value')
            request.session.pop('login_identifier_kind', None)
            request.session.pop('login_identifier_value', None)
    except Exception:
        identifier_kind = None
        identifier_value = None

    if identifier_kind == 'phone' and identifier_value:
        try:
            send_login_alert_sms(identifier_value)
        except Exception:
            pass
        return

    identifier = None
    if identifier_kind in {'email', 'username'} and identifier_value:
        identifier = identifier_value

    try:
        send_login_alert_email(user, identifier=identifier)
    except Exception:
        pass
