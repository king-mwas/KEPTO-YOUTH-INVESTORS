web: gunicorn core.wsgi:application
release: python manage.py migrate && python manage.py create_superuser
