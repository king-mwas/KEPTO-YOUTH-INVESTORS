from django.contrib.auth.models import User
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = 'List all users in the database (for debugging)'

    def handle(self, *args, **options):
        users = User.objects.all().order_by('-date_joined')
        self.stdout.write(self.style.SUCCESS(f'Total users: {users.count()}'))
        self.stdout.write('-' * 80)
        for u in users:
            flags = []
            if u.is_superuser: flags.append('SUPERUSER')
            if u.is_staff: flags.append('STAFF')
            if not u.is_active: flags.append('INACTIVE')
            flag_str = f'  [{", ".join(flags)}]' if flags else ''
            self.stdout.write(f'{u.username:30} | {u.email or "-":30} | joined {u.date_joined:%Y-%m-%d}{flag_str}')
