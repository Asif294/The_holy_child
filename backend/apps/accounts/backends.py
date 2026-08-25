"""Authentication backend: one credential field, three ways to fill it in."""
from django.contrib.auth import get_user_model
from django.db.models import Q
from django.contrib.auth.backends import ModelBackend

from apps.accounts.utils import users_matching_phone


class EmailPhoneOrUsernameBackend(ModelBackend):
    """
    Authenticates against the email address, the phone number or the username.

    Staff at the school are far more likely to remember the mobile number they
    gave the office than an email address they may not use, so the login form
    takes one "email or phone" field and this backend works out which it is.

    Phone matching ignores formatting and the country code — ``01700000000``
    signs in an account stored as ``+880 1700-000000``. An ambiguous number,
    one that somehow reaches two accounts, is refused rather than guessed at;
    :func:`~apps.accounts.utils.validate_phone_value` stops that pair being
    created in the first place.
    """

    def authenticate(self, request, username=None, password=None, **kwargs):
        User = get_user_model()
        identifier = (username or kwargs.get("email") or kwargs.get("identifier") or "").strip()
        if not identifier or not password:
            return None

        user = self._find_user(User, identifier)
        if user is None:
            # Equalise timing between "no such user" and "wrong password".
            User().set_password(password)
            return None

        if user.check_password(password) and self.user_can_authenticate(user):
            return user
        return None

    def _find_user(self, User, identifier: str):
        exact = (
            User.objects.filter(Q(email__iexact=identifier) | Q(username__iexact=identifier))
            .select_related("role")
            .first()
        )
        if exact is not None:
            return exact

        candidates = users_matching_phone(identifier)
        return candidates[0] if len(candidates) == 1 else None

    def user_can_authenticate(self, user) -> bool:
        return bool(user.is_active and not user.is_deleted)


#: Kept so an existing ``AUTHENTICATION_BACKENDS`` entry keeps importing.
EmailOrUsernameBackend = EmailPhoneOrUsernameBackend
