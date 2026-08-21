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

    _create_or_update_test_member()


def _create_or_update_test_member():
    """Create a pre-seeded member account from env vars for easy testing.

    Env vars used:
      MEMBER_USERNAME  - login username
      MEMBER_PASSWORD  - login password
      MEMBER_EMAIL     - email (optional)
      MEMBER_PHONE     - 10-digit phone starting with 0 (required)
    """
    from django.contrib.auth import get_user_model
    from .models import Member, Institution

    username = os.environ.get('MEMBER_USERNAME', '')
    password = os.environ.get('MEMBER_PASSWORD', '')
    phone = os.environ.get('MEMBER_PHONE', '')
    email = os.environ.get('MEMBER_EMAIL', '')

    if not username or not password or not phone:
        return

    User = get_user_model()
    user, user_created = User.objects.get_or_create(
        username=username,
        defaults={'email': email},
    )
    if email:
        user.email = email
    user.set_password(password)
    user.save()

    inst, _ = Institution.objects.get_or_create(name='KEPTO Test')
    member, member_created = Member.objects.get_or_create(
        user=user,
        defaults={
            'phone_number': phone,
            'member_type': Member.STUDENT,
            'status': Member.APPROVED,
            'institution': inst,
            'year_of_study': 1,
        },
    )
    if not member_created:
        member.phone_number = phone
        member.status = Member.APPROVED
        member.save()

    action = 'created' if user_created else 'password reset'
    print(f'[member] "{username}" {action} successfully (phone {phone}).')
