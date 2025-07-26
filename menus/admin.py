from django.contrib import admin
from django import forms
from .models import Menu, MenuItem


class MenuItemAdminForm(forms.ModelForm):
    """
    Форма для отдельной страницы MenuItem:
    ограничивает выбор parent пунктами того же меню.
    """
    class Meta:
        model = MenuItem
        fields = "__all__"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        menu = None
        if self.instance and self.instance.pk:
            menu = self.instance.menu
        else:
            initial_menu_id = self.initial.get("menu") or self.data.get("menu")
            if initial_menu_id:
                try:
                    menu = Menu.objects.get(pk=initial_menu_id)
                except Menu.DoesNotExist:
                    menu = None
        if menu:
            self.fields["parent"].queryset = MenuItem.objects.filter(menu=menu)
        else:
            self.fields["parent"].queryset = MenuItem.objects.none()
            self.fields["parent"].help_text = "Сначала выберите «Меню», сохраните, затем назначьте «Родителя»."


class MenuItemInline(admin.TabularInline):
    """
    Inline на странице Menu, чтобы удобно добавлять пункты.
    Важный момент: фильтруем parent по текущему Menu (obj).
    """
    model = MenuItem
    fields = ("title", "parent", "url", "named_url", "named_args", "named_kwargs", "order")
    extra = 0
    show_change_link = True

    def get_formset(self, request, obj=None, **kwargs):
        # прокинем текущий Menu в request, чтобы ниже в formfield_for_foreignkey
        # можно было отфильтровать parent
        request._current_menu_obj = obj
        return super().get_formset(request, obj, **kwargs)

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        # Ограничим parent пунктами текущего меню
        if db_field.name == "parent":
            menu_obj = getattr(request, "_current_menu_obj", None)
            if menu_obj:
                kwargs["queryset"] = MenuItem.objects.filter(menu=menu_obj)
            else:
                kwargs["queryset"] = MenuItem.objects.none()
        return super().formfield_for_foreignkey(db_field, request, **kwargs)


@admin.register(Menu)
class MenuAdmin(admin.ModelAdmin):
    list_display = ("title", "slug")
    search_fields = ("title", "slug")
    prepopulated_fields = {"slug": ("title",)}
    inlines = [MenuItemInline]


@admin.register(MenuItem)
class MenuItemAdmin(admin.ModelAdmin):
    form = MenuItemAdminForm
    list_display = ("title", "menu", "parent", "order")
    list_filter = ("menu",)
    search_fields = ("title", "url", "named_url")
    list_select_related = ("menu", "parent")
    ordering = ("menu", "parent__id", "order", "id")
