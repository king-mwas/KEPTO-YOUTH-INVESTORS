"""Gunicorn config — picked up automatically when gunicorn starts from the repo root.

Runs pending database migrations once, in the master process, before any
worker starts serving requests. This guarantees the database schema always
matches the code, even if the host's build/release step skipped `migrate`
(which previously left new columns missing and crashed signup + the admin panel).
"""
import os


def on_starting(server):
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')

    import django
    from django.core.management import call_command
    from django.db import connections

    django.setup()
    try:
        call_command('migrate', interactive=False)
    except Exception as exc:  # never block the site from booting
        server.log.error(f'[startup] migrate failed: {exc}')
    finally:
        # Don't let forked workers inherit the master's DB connection.
        connections.close_all()
