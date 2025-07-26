# menus/views.py
from django.shortcuts import render

def catalog_stub(request, *args, **kwargs):
    """
    Заглушка для всех страниц /catalog/...
    Рендерит только меню и ничего больше.
    """
    return render(request, 'menus/catalog_stub.html')
