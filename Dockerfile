# file: Dockerfile
FROM python:3.12-slim

# Не писать .pyc, сразу флэшить вывод
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    DJANGO_SETTINGS_MODULE=config.settings \
    PYTHONPATH=/app

WORKDIR /app

# Билд-инструменты на случай компиляции (минимум)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
 && rm -rf /var/lib/apt/lists/*

# Устанавливаем зависимости
COPY requirements.txt /app/
RUN pip install --no-cache-dir -r requirements.txt

# Код
COPY . /app/

EXPOSE 8000

# Простая команда для SQLite окружения
CMD ["sh","-c","python manage.py migrate --noinput && python manage.py runserver 0.0.0.0:8000"]
