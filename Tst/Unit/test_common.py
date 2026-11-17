from Src.Core.common import common


def test_get_fields_common_tracks_property_changes():
    """Проверяет обнаружение добавленных и удалённых свойств класса."""
    # Подготовка
    class changeable_model:
        @property
        def first(self):
            return "first"

    source = changeable_model()

    # Действие
    initial_fields = common.get_fields(source)
    changeable_model.second = property(lambda self: "second")
    added_fields = common.get_fields(source)
    del changeable_model.first
    removed_fields = common.get_fields(source)

    # Проверки
    assert initial_fields == ["first"]
    assert added_fields == ["first", "second"]
    assert removed_fields == ["second"]


def test_equals_walk_links_preserves_edges_to_visited_nodes():
    """<summary>Сохраняет самоссылки и ссылки на посещённые узлы через общие коллекции.</summary>"""
    # Подготовка
    class linked_model:
        """Узел с публичной ссылкой для проверки обхода графа."""

        @property
        def link(self):
            """Возвращает ссылку на узел или коллекцию."""
            return self._link

    target = linked_model()
    target._link = target
    owner = linked_model()
    items = [target]
    links = {"items": items, "shared": items}
    links["cycle"] = links
    owner._link = links
    roots = [owner, target]

    # Действие
    edges = list(common.walk_links(roots))

    # Проверки
    assert len(edges) == 6
    assert any(parent is target and child is target for parent, child in edges)
    assert any(parent is items and child is target for parent, child in edges)
    assert all(parent is not roots for parent, _ in edges)


def test_equals_walk_links_expands_shared_nodes_once():
    """<summary>Раскрывает каждый узел длинной общей цепочки один раз для всех корней.</summary>"""
    # Подготовка
    class counted_model:
        """Узел, считающий чтения свойства при обходе."""

        def __init__(self, linked):
            """Сохраняет ссылку и обнуляет счётчик чтений."""
            self._linked = linked
            self.reads = 0

        @property
        def linked(self):
            """Считает раскрытия узла и возвращает следующий узел."""
            self.reads += 1
            return self._linked

    roots = []
    for _ in range(100):
        roots.append(counted_model(roots[-1] if roots else None))

    # Действие
    edges = list(common.walk_links(roots))

    # Проверки
    assert len(edges) == len(roots)
    assert all(node.reads == 1 for node in roots)
