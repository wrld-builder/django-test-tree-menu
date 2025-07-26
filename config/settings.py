# file: config/settings.py
from pathlib import Path
import os
from urllib.parse import urlparse

BASE_DIR = Path(__file__).resolve().parent.parent

# ——— Простое считывание .env ———
env_path = BASE_DIR / '.env'
if env_path.exists():
    for line in env_path.read_text(encoding='utf-8').splitlines():
        line = line.strip()
        if not line or line.startswith('#') or '=' not in line:
            continue
        key, val = line.split('=', 1)
        os.environ.setdefault(key, val)

# ——— DEBUG, SECRET_KEY, ALLOWED_HOSTS ———
DEBUG = os.getenv('DEBUG', 'False').lower() in ('1', 'true', 'yes')
SECRET_KEY = os.getenv('SECRET_KEY', '')
ALLOWED_HOSTS = [h.strip() for h in os.getenv('ALLOWED_HOSTS', '').split(',') if h.strip()]

# ——— DATABASE_URL и SQLite ———
default_db = os.getenv('DATABASE_URL', f"sqlite:///{BASE_DIR / 'db.sqlite3'}")
parsed = urlparse(default_db)

if parsed.scheme in ('postgres', 'postgresql'):
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.postgresql',
            'NAME': parsed.path.lstrip('/'),
            'USER': parsed.username,
            'PASSWORD': parsed.password,
            'HOST': parsed.hostname,
            'PORT': parsed.port or '',
        }
    }

elif parsed.scheme == 'sqlite':
    # Если путь абсолютный: sqlite:////home/user/db.sqlite3
    # Если относительный: sqlite:///db.sqlite3
    raw_path = parsed.path
    if raw_path.startswith('/') and len(raw_path) > 1:
        # Убираем ведущий слэш, чтобы объединить с BASE_DIR
        db_file = raw_path.lstrip('/')
    else:
        db_file = raw_path or 'db.sqlite3'
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': str(BASE_DIR / db_file),
        }
    }

else:
    raise RuntimeError(f"Unsupported DATABASE_URL scheme: {parsed.scheme}")

# Dev secret для тестового задания
DEBUG = True
ALLOWED_HOSTS = ["*"]

INSTALLED_APPS = [
    # Базовые Django приложения
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    # Наше приложение меню
    "menus",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "config.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        # Общая папка шаблонов проекта
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                # Включаем request в контекст, чтобы тег видел текущий path
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
            # Регистрируем наш тег как built-in, чтобы не писать {% load %}
            "builtins": ["menus.templatetags.menu_tags"],
        },
    },
]

WSGI_APPLICATION = "config.wsgi.application"

AUTH_PASSWORD_VALIDATORS = []

LANGUAGE_CODE = "ru-ru"
TIME_ZONE = "Europe/Oslo"
USE_I18N = True
USE_TZ = True

from pathlib import Path
BASE_DIR = Path(__file__).resolve().parent.parent

STATIC_URL = "/static/"
STATIC_ROOT = BASE_DIR / "staticfiles"

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# Debug Toolbar — dev only
if DEBUG:
    INSTALLED_APPS += ["debug_toolbar"]
    MIDDLEWARE = [
        "debug_toolbar.middleware.DebugToolbarMiddleware",
        *MIDDLEWARE,
    ]
    # адреса, с которых показывать панель; для Docker чаще всего 172.17.0.1
    INTERNAL_IPS = ["127.0.0.1", "localhost", "0.0.0.0", "172.17.0.1"]

