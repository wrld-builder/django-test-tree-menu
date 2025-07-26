from django.contrib import admin
from django.urls import path, include, re_path
from django.shortcuts import render
from django.conf import settings

from menus.views import catalog_stub


def page(request, slug=None):
    return render(request, "base.html", {"slug": slug})

urlpatterns = [
    path("admin/", admin.site.urls),
    path("", page, name="home"),
    path("about/", page, {"slug": "about"}, name="about"),
    path("catalog/", page, {"slug": "catalog"}, name="catalog"),
    path("catalog/<slug:slug>/", page, name="catalog_item"),
    re_path(r'^catalog/.*$', catalog_stub, name='catalog'),
]

if settings.DEBUG:
    urlpatterns += [path("__debug__/", include("debug_toolbar.urls"))]
