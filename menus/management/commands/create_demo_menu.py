# file: menus/management/commands/create_demo_menu.py
from django.core.management.base import BaseCommand
from menus.models import Menu, MenuItem

class Command(BaseCommand):
    help = "Создаёт демо-меню 'main_menu' с тремя интересными каталогами: Велосипеды, Мотоциклы, Автомобили"

    def handle(self, *args, **options):
        # Создаём или получаем контейнер меню
        menu, _ = Menu.objects.get_or_create(
            slug="main_menu",
            defaults={"title": "Main menu"}
        )
        # Очищаем старые пункты для воспроизводимости
        MenuItem.objects.filter(menu=menu).delete()

        # Корневые пункты: три каталога
        bicycles = MenuItem.objects.create(
            menu=menu,
            title="Велосипеды",
            url="/catalog/bicycles/",
            order=0
        )
        motorcycles = MenuItem.objects.create(
            menu=menu,
            title="Мотоциклы",
            url="/catalog/motorcycles/",
            order=1
        )
        cars = MenuItem.objects.create(
            menu=menu,
            title="Автомобили",
            url="/catalog/cars/",
            order=2
        )

        # Подэлементы для Велосипеды
        MenuItem.objects.create(menu=menu, parent=bicycles, title="Горные", url="/catalog/bicycles/mountain/", order=0)
        MenuItem.objects.create(menu=menu, parent=bicycles, title="Шоссейные", url="/catalog/bicycles/road/", order=1)
        MenuItem.objects.create(menu=menu, parent=bicycles, title="Гибриды", url="/catalog/bicycles/hybrid/", order=2)
        MenuItem.objects.create(menu=menu, parent=bicycles, title="Электрические", url="/catalog/bicycles/electric/", order=3)
        MenuItem.objects.create(menu=menu, parent=bicycles, title="Детские", url="/catalog/bicycles/kids/", order=4)

        # Подэлементы для Мотоциклы
        MenuItem.objects.create(menu=menu, parent=motorcycles, title="Круизеры", url="/catalog/motorcycles/cruiser/", order=0)
        MenuItem.objects.create(menu=menu, parent=motorcycles, title="Спортбайки", url="/catalog/motorcycles/sport/", order=1)
        MenuItem.objects.create(menu=menu, parent=motorcycles, title="Офф-роад", url="/catalog/motorcycles/offroad/", order=2)
        MenuItem.objects.create(menu=menu, parent=motorcycles, title="Туреры", url="/catalog/motorcycles/touring/", order=3)
        MenuItem.objects.create(menu=menu, parent=motorcycles, title="Эндуро", url="/catalog/motorcycles/enduro/", order=4)

        # Подэлементы для Автомобили
        MenuItem.objects.create(menu=menu, parent=cars, title="Седаны", url="/catalog/cars/sedan/", order=0)
        MenuItem.objects.create(menu=menu, parent=cars, title="Внедорожники", url="/catalog/cars/suv/", order=1)
        MenuItem.objects.create(menu=menu, parent=cars, title="Купе", url="/catalog/cars/coupe/", order=2)
        MenuItem.objects.create(menu=menu, parent=cars, title="Хэтчбеки", url="/catalog/cars/hatchback/", order=3)
        MenuItem.objects.create(menu=menu, parent=cars, title="Минивэны", url="/catalog/cars/minivan/", order=4)

        self.stdout.write(self.style.SUCCESS(
            "✅ Demo menu 'main_menu' обновлено: Велосипеды, Мотоциклы, Автомобили с подкатегориями."
        ))
