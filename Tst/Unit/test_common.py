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
