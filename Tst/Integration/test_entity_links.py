"""Проверки связей CRUD с настоящими моделями и хранилищем без HTTP."""
import pytest

from Src.Core.validator import operation_exception
from Src.Logics.convert_factory import convert_factory
from Src.Logics.deserialize_factory import deserialize_factory
from Src.Logics.entity_mapper import entity_mapper
from Src.Logics.entity_service import entity_service
from Src.Logics.storage_manager import storage_manager
from Src.Models.nomenclature_group_model import nomenclature_group_model
from Src.Models.nomenclature_model import nomenclature_model
from Src.Models.range_model import range_model
from Src.Models.recipe_model import recipe_model


@pytest.fixture
def storage(monkeypatch):
    """Создаёт изолированный экземпляр настоящего хранилища."""
    monkeypatch.delattr(storage_manager, "instance", raising=False)
    return storage_manager()


def change_identity(service, collection, entity, operation, data):
    """Удаляет сущность либо меняет её код через публичный сценарий CRUD."""
    if operation == "delete":
        service.delete(collection, entity.unique_code)
        return None
    mapper = entity_mapper(deserialize_factory(), convert_factory())
    return service.update(
        collection, entity.unique_code,
        lambda original, source: mapper.updated(
            original, {**data, "unique_code": "changed-code"}, source,
        ),
    )


@pytest.mark.parametrize("operation", ["delete", "recode"])
@pytest.mark.parametrize("relation", ["property", "collection"])
def test_raises_entity_service_incoming_links(storage, operation, relation):
    """<summary>Запрещает удаление и смену кода при ссылках в свойствах и коллекциях.</summary>"""
    # Подготовка
    if relation == "property":
        target = nomenclature_group_model("Группа")
        owner = nomenclature_model("Товар", "Товар", target, range_model("Штука", 1))
        collection, owner_collection = "groups", "nomenclatures"
    else:
        target = recipe_model("Вложенный рецепт")
        owner = recipe_model("Общий рецепт", [target])
        collection = owner_collection = "recipes"
    storage.save_entity(owner_collection, owner)
    service = entity_service(storage)
    before = service.get(collection, target.unique_code)

    # Действие
    with pytest.raises(operation_exception, match="Сущность используется другим объектом"):
        change_identity(service, collection, target, operation, {"name": "Новое имя"})

    # Проверки
    unchanged = service.get(collection, target.unique_code)
    assert unchanged.name == before.name
    assert unchanged.unique_code == before.unique_code


@pytest.mark.parametrize("operation", ["delete", "recode"])
def test_not_raise_entity_service_free_self_reference(storage, operation):
    """<summary>Разрешает удаление и смену кода свободной единицы с самоссылкой.</summary>"""
    # Подготовка
    unit = range_model("Штука", 1)
    storage.save_entity("ranges", unit)
    service = entity_service(storage)

    # Действие
    changed = change_identity(
        service, "ranges", unit, operation, {"name": "Штука", "conversion_factor": 1},
    )

    # Проверки
    with pytest.raises(KeyError):
        service.get("ranges", unit.unique_code)
    if operation == "recode":
        assert changed.unique_code == "changed-code"
        assert changed.base_range is changed
        assert service.get("ranges", "changed-code").unique_code == "changed-code"
    else:
        assert service.list("ranges") == []
