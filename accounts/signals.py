import os


def create_or_update_superuser(sender, **kwargs):
    from django.contrib.auth import get_user_model

    username = os.environ.get('ADMIN_USERNAME', 'admin')
    email = os.environ.get('ADMIN_EMAIL', 'keptoinvestor@gmail.com')
    password = os.environ.get('ADMIN_PASSWORD', '')

    if not password:
        print('[superuser] Skipped: ADMIN_PASSWORD env var not set.')
        return

    User = get_user_model()
    user, created = User.objects.get_or_create(
        username=username,
        defaults={'email': email, 'is_staff': True, 'is_superuser': True},
    )
    user.email = email
    user.is_staff = True
    user.is_superuser = True
    user.set_password(password)
    user.save()

    action = 'created' if created else 'password reset'
    print(f'[superuser] "{username}" {action} successfully.')
