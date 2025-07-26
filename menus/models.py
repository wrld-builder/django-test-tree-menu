# file: menus/models.py
from __future__ import annotations
import json
from typing import Any
from django.core.exceptions import ValidationError
from django.db import models
from django.urls import NoReverseMatch, reverse

class Menu(models.Model):
    """
    Контейнер меню. Идентифицируется по slug.
    """
    title = models.CharField(max_length=100, verbose_name="Название")
    slug = models.SlugField(unique=True, verbose_name="Код (slug)")

    class Meta:
        verbose_name = "Меню"
        verbose_name_plural = "Меню"

    def __str__(self) -> str:
        return f"{self.title} ({self.slug})"

class MenuItem(models.Model):
    """
    Пункт меню. Поддерживает явный URL и именованный URL через reverse().
    Иерархия строится через self.parent.
    """
    menu = models.ForeignKey("Menu", on_delete=models.CASCADE, related_name="items", verbose_name="Меню")
    parent = models.ForeignKey("self", on_delete=models.CASCADE, null=True, blank=True, related_name="children", verbose_name="Родитель")

    title = models.CharField(max_length=255, verbose_name="Заголовок")

    # Явный URL (приоритет ниже, чем у named_url)
    url = models.CharField(max_length=255, blank=True, verbose_name="URL")

    # Именованный URL (приоритет выше)
    named_url = models.CharField(max_length=255, blank=True, verbose_name="Named url")
    # Позиционные и именованные аргументы для reverse() хранятся JSON-строкой
    named_args = models.CharField(max_length=255, blank=True, verbose_name="Named args (JSON)")
    named_kwargs = models.CharField(max_length=255, blank=True, verbose_name="Named kwargs (JSON)")

    # Поле сортировки в пределах одного уровня
    order = models.PositiveIntegerField(default=0, verbose_name="Порядок")

    class Meta:
        verbose_name = "Пункт меню"
        verbose_name_plural = "Пункты меню"
        ordering = ["order", "id"]
        indexes = [models.Index(fields=["menu", "parent"])]

    def __str__(self) -> str:
        return self.title

    def clean(self) -> None:
        # Родитель должен принадлежать тому же меню
        if self.parent and self.parent.menu_id != self.menu_id:
            raise ValidationError("Родительский пункт должен принадлежать тому же меню.")

    def _json_or_default(self, raw: str, default: Any) -> Any:
        # Безопасный парсинг JSON, возврат default при ошибке
        if not raw:
            return default
        try:
            return json.loads(raw)
        except Exception:
            return default

    @property
    def resolved_url(self) -> str:
        """
        Рассчитывает итоговый URL:
        1) если задан named_url — делаем reverse с args/kwargs;
        2) иначе берём явный url;
        3) при любой ошибке — фолбэк '#'.
        """
        if self.named_url:
            args = self._json_or_default(self.named_args, [])
            kwargs = self._json_or_default(self.named_kwargs, {})
            try:
                return reverse(self.named_url, args=args, kwargs=kwargs)
            except NoReverseMatch:
                return self.url or "#"
        return self.url or "#"
