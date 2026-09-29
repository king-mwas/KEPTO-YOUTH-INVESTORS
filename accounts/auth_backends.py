from django.contrib.auth import get_user_model
from django.contrib.auth.backends import ModelBackend


class CaseInsensitiveModelBackend(ModelBackend):
    """
    Allow users to log in with their username in any case (@KING_investor,
    @king_investor, @King_Investor all work). Password remains case-sensitive.
    """

    def authenticate(self, request, username=None, password=None, **kwargs):
        User = get_user_model()
        if username is None:
            username = kwargs.get(User.USERNAME_FIELD)
        if not username:
            return None

        try:
            user = User.objects.get(**{f'{User.USERNAME_FIELD}__iexact': username})
        except User.DoesNotExist:
            User().set_password(password)
            return None
        except User.MultipleObjectsReturned:
            user = User.objects.filter(**{f'{User.USERNAME_FIELD}__iexact': username}).order_by('id').first()

        if user.check_password(password) and self.user_can_authenticate(user):
            return user
        return None
