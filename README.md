# Django Tree Menu

Production‑quality древовидное меню для Django 5.x с 1 SQL-запросом на меню (или на страницу при префетче), редактируемое через админку, с поддержкой named URL, строгим контролем SQL и точным определением активного пункта по URL.

---

## 🚀 Ключевые особенности

- **Template tag**: `{% draw_menu 'slug' %}` — рендер меню по имени в любом шаблоне.
- **Активный пункт** по `request.get_full_path()` (включая query).
- **Раскрытие** всех предков активного и первого уровня его детей.
- **Named URL** (`reverse()` с args/kwargs в JSON).
- **Не[menus](menus)сколько меню** на одной странице.
- **1 SQL-запрос** на меню или один на страницу через `{% menu_prefetch %}`.
- **Хранение в БД**, удобное редактирование дерева в админке.
- **Нулевые зависимости** — только Django и стандартная библиотека.
- **Docker** и `docker-compose` в комплекте.

## 📦 Установка

### A. Docker

```bash
docker compose up --build
docker compose exec web python manage.py createsuperuser
docker compose exec web python manage.py create_demo_menu
```
Сайт: http://localhost:8000/

Админка: http://localhost:8000/admin/

### B. Локально
```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt

python manage.py migrate
python manage.py createsuperuser
python manage.py create_demo_menu
python manage.py runserver
```

## 🗂 Модели

- **Menu** — (`title`, `slug`) — контейнер для дерева пунктов.
- **MenuItem** — (`menu`, `parent`, `title`, `url`, `named_url`, `named_args`, `named_kwargs`, `order`) — узел дерева.

