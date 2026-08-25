"""Authentication backend: one credential field, three ways to fill it in."""
from django.contrib.auth import get_user_model
from django.contrib.auth.backends import ModelBackend
from django.db.models import Q

from apps.accounts.utils import normalise_phone


class EmailPhoneOrUsernameBackend(ModelBackend):
    """
    Authenticates against the email address, the phone number or the username.

    Staff at the school are far more likely to remember the mobile number they
    gave the office than an email address they may not use, so the login form
    takes one "email or phone" field and this backend works out which it is.

    Phone matching is done on digits alone: a number stored as
    ``+880 1700-000000`` still authenticates when typed as ``01700000000``.
    The comparison is narrowed in SQL and then confirmed in Python, and an
    ambiguous number — two accounts normalising to the same digits — is refused
    rather than guessed at.
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

        digits = normalise_phone(identifier)
        if len(digits) < 6:
            return None

        # `endswith` narrows the scan; the Python comparison below is what
        # actually decides, since formatting differs between records.
        candidates = [
            user
            for user in User.objects.filter(phone__endswith=digits[-6:]).select_related("role")
            if normalise_phone(user.phone) == digits
        ]
        return candidates[0] if len(candidates) == 1 else None

    def user_can_authenticate(self, user) -> bool:
        return bool(user.is_active and not user.is_deleted)


#: Kept so an existing ``AUTHENTICATION_BACKENDS`` entry keeps importing.
EmailOrUsernameBackend = EmailPhoneOrUsernameBackend
