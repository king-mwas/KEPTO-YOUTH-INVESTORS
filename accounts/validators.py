import re

from django.core.exceptions import ValidationError


class StrongPasswordValidator:
    """Require at least one uppercase, one lowercase, one digit, and one special character."""

    SPECIAL_CHARS = r'!@#$%^&*(),.?":{}|<>_\-+=[\]\\;\'/`~'

    def validate(self, password, user=None):
        errors = []
        if not re.search(r'[A-Z]', password):
            errors.append('at least one uppercase letter (A-Z)')
        if not re.search(r'[a-z]', password):
            errors.append('at least one lowercase letter (a-z)')
        if not re.search(r'\d', password):
            errors.append('at least one number (0-9)')
        if not re.search(f'[{re.escape(self.SPECIAL_CHARS)}]', password):
            errors.append('at least one special character (like @, ., !, #)')

        if errors:
            raise ValidationError(
                'Password must contain ' + ', '.join(errors) + '.',
                code='password_not_strong',
            )

    def get_help_text(self):
        return (
            'Your password must contain at least one uppercase letter, '
            'one lowercase letter, one number, and one special character.'
        )
