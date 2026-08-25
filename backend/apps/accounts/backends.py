from django.contrib.auth import get_user_model
from django.contrib.auth.backends import ModelBackend
from django.db.models import Q


class EmailOrUsernameBackend(ModelBackend):
    """
    Authenticates against either the email address or the username.

    Login stays email-first everywhere in the UI; accepting the username as well
    costs nothing and avoids surprising staff who were issued one.
    """

    def authenticate(self, request, username=None, password=None, **kwargs):
        User = get_user_model()
        identifier = username or kwargs.get("email")
        if not identifier or not password:
            return None

        user = (
            User.objects.filter(Q(email__iexact=identifier.strip()) | Q(username__iexact=identifier.strip()))
            .select_related("role")
            .first()
        )
        if user is None:
            # Equalise timing between "no such user" and "wrong password".
            User().set_password(password)
            return None

        if user.check_password(password) and self.user_can_authenticate(user):
            return user
        return None

    def user_can_authenticate(self, user) -> bool:
        return bool(user.is_active and not user.is_deleted)
