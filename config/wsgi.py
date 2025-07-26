# project/wsgi.py

import os
from django.core.wsgi import get_wsgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'project.settings')
application = get_wsgi_application()

# ——— Инициализация базы и демо‑данных при старте ———
def _init_db_and_demo():
    from django.db import connections, OperationalError
    from django.core.management import call_command
    try:
        # Попробуем получить список таблиц
        tables = connections['default'].introspection.table_names()
        # Если таблиц нет или нет ни одного меню — создаём схему и демо‑меню
        from menus.models import Menu
        if not tables or not Menu.objects.exists():
            call_command('migrate', interactive=False, run_syncdb=True)
            call_command('create_demo_menu')
    except OperationalError:
        # Если не удалось подключиться — тоже прогоняем миграции и демо‑данные
        call_command('migrate', interactive=False, run_syncdb=True)
        call_command('create_demo_menu')

_init_db_and_demo()
