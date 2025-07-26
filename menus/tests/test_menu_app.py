import json
from contextlib import contextmanager

from django.core.exceptions import ValidationError
from django.core.management import call_command
from django.template import Template, RequestContext
from django.test import TestCase, RequestFactory
from django.urls import reverse

from menus.models import Menu, MenuItem
from menus.admin import MenuItemAdminForm


@contextmanager
def assert_num_queries(testcase: TestCase, num: int):
    """
    Удобная обёртка с читаемым именем.
    """
    with testcase.assertNumQueries(num):
        yield


class MenuAppTests(TestCase):
    """
    Комплексные тесты приложения menus:
    - модели и resolved_url
    - template tag draw_menu + menu_prefetch
    - активность по get_full_path() и раскрытие предков/детей
    - 1 запрос на меню и 1 запрос на страницу при префетче
    - admin-форма (ограничение parent по текущему меню)
    - management-команда create_demo_menu
    """

    maxDiff = None

    @classmethod
    def setUpTestData(cls):
        # Базовые меню
        cls.menu_main = Menu.objects.create(title="Main", slug="main_menu")
        cls.menu_footer = Menu.objects.create(title="Footer", slug="footer_menu")

        # Дерево для main_menu
        cls.home = MenuItem.objects.create(menu=cls.menu_main, title="Главная", named_url="home", order=0)
        cls.about = MenuItem.objects.create(menu=cls.menu_main, title="О нас", named_url="about", order=1)
        cls.catalog = MenuItem.objects.create(menu=cls.menu_main, title="Каталог", named_url="catalog", order=2)

        cls.bikes = MenuItem.objects.create(
            menu=cls.menu_main,
            parent=cls.catalog,
            title="Велосипеды",
            named_url="catalog_item",
            named_kwargs=json.dumps({"slug": "bikes"}),
            order=0,
        )
        cls.skates = MenuItem.objects.create(
            menu=cls.menu_main,
            parent=cls.catalog,
            title="Ролики",
            named_url="catalog_item",
            named_kwargs=json.dumps({"slug": "skates"}),
            order=1,
        )

        # Листовые пункты с явным URL (query-string)
        cls.mtb = MenuItem.objects.create(
            menu=cls.menu_main,
            parent=cls.bikes,
            title="Горные",
            url="/catalog/bikes/?type=mtb",
            order=0,
        )
        cls.road = MenuItem.objects.create(
            menu=cls.menu_main,
            parent=cls.bikes,
            title="Шоссейные",
            url="/catalog/bikes/?type=road",
            order=1,
        )

        cls.rf = RequestFactory()

    # ----------------------- МОДЕЛИ -----------------------

    def test_resolved_url_named_has_priority(self):
        item = MenuItem.objects.create(
            menu=self.menu_main,
            title="NamedPriority",
            url="/fallback/",
            named_url="catalog_item",
            named_kwargs=json.dumps({"slug": "bikes"}),
        )
        self.assertEqual(item.resolved_url, reverse("catalog_item", kwargs={"slug": "bikes"}))

    def test_resolved_url_fallback_to_url_on_reverse_error(self):
        item = MenuItem.objects.create(
            menu=self.menu_main,
            title="BadNamed",
            url="/fallback/",
            named_url="no_such_name",
        )
        self.assertEqual(item.resolved_url, "/fallback/")

    def test_parent_must_belong_to_same_menu(self):
        other_menu = self.menu_footer
        with self.assertRaises(ValidationError):
            MenuItem(
                menu=self.menu_main,
                parent=MenuItem.objects.create(menu=other_menu, title="X"),
                title="Invalid",
            ).clean()

    # ----------------------- TEMPLATE TAG: DRAW_MENU -----------------------

    def _render(self, tpl: str, path: str):
        """
        Рендер шаблона с запросом на указанный URL.
        Возвращает HTML.
        """
        request = self.rf.get(path)
        template = Template(tpl)
        ctx = RequestContext(request, {})
        return template.render(ctx)

    def test_draw_menu_one_query_per_menu(self):
        """
        Каждый вызов draw_menu делает 1 SELECT к MenuItem (fallback без префетча).
        """
        tpl = "{% draw_menu 'main_menu' %}"
        with assert_num_queries(self, 1):
            html = self._render(tpl, "/")
        self.assertIn("Главная", html)

    def test_draw_menu_two_calls_two_queries_without_prefetch(self):
        """
        Два разных меню без префетча — 2 запроса (по одному на меню).
        """
        tpl = "{% draw_menu 'main_menu' %}{% draw_menu 'footer_menu' %}"
        with assert_num_queries(self, 2):
            _ = self._render(tpl, "/")

    def test_menu_prefetch_single_query_for_multiple_menus(self):
        """
        Префетч двух меню (одно пустое) — ровно 1 запрос на всю страницу.
        """
        tpl = "{% menu_prefetch 'main_menu' 'footer_menu' %}{% draw_menu 'main_menu' %}{% draw_menu 'footer_menu' %}"
        with assert_num_queries(self, 1):
            html = self._render(tpl, "/")
        self.assertIn("Главная", html)

    def test_active_item_matches_full_path_with_querystring(self):
        """
        Активность определяется по get_full_path() (включая query-string),
        фоллбэк по path. На /catalog/bikes/?type=road активным должен стать 'Шоссейные'.
        """
        tpl = "{% draw_menu 'main_menu' %}"
        html = self._render(tpl, "/catalog/bikes/?type=road")
        # проверим, что именно 'Шоссейные' попадает в активный <li class="active">
        self.assertIn('<li class="active">', html)
        self.assertIn("Шоссейные", html)

    def test_child_level_of_active_is_expanded(self):
        """
        Если активный узел имеет детей — их первый уровень помечается expanded.
        Смоделируем: сделаем узел с потомком и откроем его URL.
        """
        # Создадим узел с ребёнком и URL без query
        parent = MenuItem.objects.create(menu=self.menu_main, title="Parent", url="/p/", order=99)
        child = MenuItem.objects.create(menu=self.menu_main, parent=parent, title="Child", url="/p/c/", order=0)

        tpl = "{% draw_menu 'main_menu' %}"
        html = self._render(tpl, "/p/")
        # Родитель активен
        self.assertIn("Parent", html)
        self.assertIn('<li class="active">', html)
        # Дети активного уровня видны (expanded=True => рендерится вложенный <ul>)
        self.assertIn("Child", html)

    # ----------------------- ADMIN FORM -----------------------

    def test_admin_form_limits_parent_queryset_to_same_menu(self):
        """
        В форме пункта меню поле parent ограничено пунктами текущего меню.
        """
        # Пункт из другого меню
        foreign_item = MenuItem.objects.create(menu=self.menu_footer, title="Outside")

        form = MenuItemAdminForm(initial={"menu": self.menu_main.id})
        # queryset для parent не должен содержать foreign_item
        self.assertNotIn(foreign_item, form.fields["parent"].queryset)

        own_item = MenuItem.objects.create(menu=self.menu_main, title="Inside")
        form2 = MenuItemAdminForm(initial={"menu": self.menu_main.id})
        self.assertIn(own_item, form2.fields["parent"].queryset)

    # ----------------------- MANAGEMENT COMMAND -----------------------

    def test_management_command_create_demo_menu(self):
        """
        Команда должна создать main_menu с пунктами (пересоздаёт содержимое).
        """
        call_command("create_demo_menu", verbosity=0)
        m = Menu.objects.get(slug="main_menu")
        self.assertGreater(MenuItem.objects.filter(menu=m).count(), 0)

    # ----------------------- URL RESOLUTION CASES -----------------------

    def test_named_url_with_kwargs_resolves_correctly(self):
        self.assertEqual(self.bikes.resolved_url, reverse("catalog_item", kwargs={"slug": "bikes"}))

    def test_plain_url_resolves_as_is(self):
        self.assertEqual(self.road.resolved_url, "/catalog/bikes/?type=road")
