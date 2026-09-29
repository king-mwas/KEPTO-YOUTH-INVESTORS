from django.apps import AppConfig


class AccountsConfig(AppConfig):
    name = 'accounts'

    def ready(self):
        from django.db.models.signals import post_migrate
        from . import signals
        post_migrate.connect(signals.create_or_update_superuser, sender=self)
