from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass, field
from typing import Dict, List, Optional

from django import template
from menus.models import MenuItem

register = template.Library()


@dataclass
class Node:
    item: MenuItem
    children: List["Node"] = field(default_factory=list)
    url: str = "#"
    is_active: bool = False
    is_ancestor: bool = False
    expanded: bool = False


def _build_tree(items: List[MenuItem]) -> List[Node]:
    node_by_id: Dict[int, Node] = {it.id: Node(item=it) for it in items}
    roots: List[Node] = []

    for node in node_by_id.values():
        pid = node.item.parent_id
        if pid and pid in node_by_id:
            node_by_id[pid].children.append(node)
        else:
            roots.append(node)

    def sort_children(n: Node) -> None:
        n.children.sort(key=lambda c: (c.item.order, c.item.id))
        for ch in n.children:
            sort_children(ch)

    for r in roots:
        sort_children(r)
    return roots


def _mark_active_and_expand(roots: List[Node], full_path: str, path_only: str) -> None:
    """
    Сначала пытаемся активировать по ПОЛНОМУ пути (включая query-string),
    если совпадений нет — фоллбэк на path без query.
    Также раскрываем всех предков и первый уровень детей активного узла.
    """
    id_to_parent: Dict[int, Optional[Node]] = {}
    id_to_node: Dict[int, Node] = {}

    def map_parent(node: Node, parent: Optional[Node]) -> None:
        id_to_node[node.item.id] = node
        id_to_parent[node.item.id] = parent
        for ch in node.children:
            map_parent(ch, node)

    for r in roots:
        map_parent(r, None)

    for node in id_to_node.values():
        node.url = node.item.resolved_url

    active: Optional[Node] = None

    # 1) точное совпадение с полным путём (учитывает ?query)
    for node in id_to_node.values():
        if node.url == full_path:
            node.is_active = True
            active = node
            break

    # 2) фоллбэк — сравнение только по path
    if not active and path_only:
        for node in id_to_node.values():
            if node.url == path_only:
                node.is_active = True
                active = node
                break

    if not active:
        return

    cursor = active
    while cursor:
        cursor.expanded = True
        parent = id_to_parent.get(cursor.item.id)
        if parent:
            parent.expanded = True
            parent.is_ancestor = True
        cursor = parent

    for child in active.children:
        child.expanded = True


_PREFETCH_KEY = "menus_prefetch_cache"


@register.simple_tag(takes_context=True)
def menu_prefetch(context, *slugs: str):
    """
    Префетчит пункты для нескольких меню ОДНИМ запросом и кладёт в кэш контекста.
    Даже если меню пустое — кладём пустой список, чтобы draw_menu не делал fallback-запрос.
    """
    cache: Dict[str, List[MenuItem]] = context.render_context.setdefault(_PREFETCH_KEY, {})

    to_fetch = [s for s in slugs if s and s not in cache]
    if not to_fetch:
        return ""

    items = list(
        MenuItem.objects.filter(menu__slug__in=to_fetch)
        .select_related("parent", "menu")
        .order_by("menu__slug", "parent__id", "order", "id")
    )

    grouped: Dict[str, List[MenuItem]] = defaultdict(list)
    for it in items:
        grouped[it.menu.slug].append(it)

    for slug in to_fetch:
        cache[slug] = grouped.get(slug, [])

    return ""


@register.inclusion_tag("menus/draw_menu.html", takes_context=True)
def draw_menu(context, menu_slug: str):
    """
    Рендер меню по slug. Источник данных:
      1) если есть кэш из menu_prefetch — берём оттуда (0 доп. запросов),
      2) иначе — выполняем 1 запрос для этого меню (fallback).
    """
    request = context.get("request")
    full_path = "/"
    path_only = "/"
    if request is not None:
        try:
            full_path = request.get_full_path()  # включает query-string
        except Exception:
            full_path = getattr(request, "path", "/")
        path_only = getattr(request, "path", full_path.split("?", 1)[0])

    cache: Dict[str, List[MenuItem]] = context.render_context.get(_PREFETCH_KEY, {})
    items = cache.get(menu_slug)

    if items is None:
        items = list(
            MenuItem.objects.filter(menu__slug=menu_slug)
            .select_related("parent", "menu")
            .order_by("parent__id", "order", "id")
        )

    roots = _build_tree(items)
    _mark_active_and_expand(roots, full_path, path_only)

    return {"nodes": roots, "menu_slug": menu_slug}
