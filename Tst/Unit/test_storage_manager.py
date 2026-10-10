import pytest

from Src.Core.abstract_manager import abstract_manager
from Src.Core.validator import argument_exception
from Src.Logics.storage_manager import storage_manager
from Src.Models.nomenclature_group_model import nomenclature_group_model
from Src.Models.nomenclature_model import nomenclature_model
from Src.Models.range_model import range_model
from Src.Models.recipe_model import recipe_model
from Src.Models.settings_model import settings_model
from Src.Models.warehouse_model import warehouse_model


@pytest.fixture(autouse=True)
def reset_storage_manager_singleton():
    """Изолирует состояние singleton между модульными тестами."""
    if hasattr(storage_manager, "instance"):
        delattr(storage_manager, "instance")
    yield
    if hasattr(storage_manager, "instance"):
        delattr(storage_manager, "instance")


def create_settings(is_first_start: bool = True) -> settings_model:
    """Создаёт настройки с указанным признаком первого запуска."""
    settings = settings_model()
    settings.is_first_start = is_first_start
    return settings

def test_not_raise_storage_manager_convert():
    # Подготовка
    settings = create_settings()
    manager = storage_manager()

    # Действие
    result = manager.convert(settings)

    # Проверка
    assert result

def test_not_empty_storage_manager_convert():
    # Подготовка
    settings = create_settings()
    manager = storage_manager()

    # Действие
    manager.convert(settings)

    # Проверка
    assert manager.ranges
    assert manager.groups
    assert manager.warehouses
    assert manager.nomenclatures
    assert manager.recipes

def test_equals_storage_manager_create():
    # Подготовка
    instance1 = storage_manager()

    # Действие
    instance2 = storage_manager()

    # Проверка
    assert instance1 == instance2

def test_is_loaded_storage_manager_true():
    # Подготовка
    settings = create_settings()
    manager = storage_manager()

    # Действие
    manager.convert(settings)

    # Проверка
    assert manager.is_loaded

def test_equals_storage_manager_data():
    # Подготовка
    settings = create_settings()
    instance1 = storage_manager()
    instance2 = storage_manager()

    # Действие
    instance1.convert(settings)

    # Проверка
    assert instance1.ranges == instance2.ranges
    assert instance1.groups == instance2.groups
    assert instance1.warehouses == instance2.warehouses
    assert instance1.nomenclatures == instance2.nomenclatures
    assert instance1.recipes == instance2.recipes

def test_convert_storage_manager_first_start():
    # Подготовка
    settings = create_settings()
    manager = storage_manager()

    # Действие
    result = manager.convert(settings)

    # Проверка
    assert settings.is_first_start
    assert result

def test_not_convert_storage_manager_not_first_start():
    # Подготовка
    settings = create_settings(False)
    manager = storage_manager()

    # Действие
    result = manager.convert(settings)

    # Проверка
    assert not result
    assert manager.ranges == []
    assert manager.groups == []
    assert manager.warehouses == []
    assert manager.nomenclatures == []
    assert manager.recipes == []


def test_storage_manager_inherits_abstract_manager():
    """Проверяет наследование хранилища от общего менеджера."""
    assert isinstance(storage_manager(), abstract_manager)


def test_is_loaded_storage_manager_false_before_convert():
    """Проверяет начальное состояние хранилища."""
    assert not storage_manager().is_loaded


def test_convert_storage_manager_creates_expected_initial_data():
    """Проверяет состав первичных данных при первом старте."""
    settings = settings_model()
    settings.is_first_start = True
    manager = storage_manager()

    manager.convert(settings)

    assert {item.name for item in manager.ranges} == {
        "Штука",
        "Килограмм",
        "Грамм",
        "Литр",
        "Миллилитр",
    }
    assert {item.name for item in manager.groups} == {
        "Продукты",
        "Напитки",
        "Упаковка",
    }
    assert {item.name for item in manager.warehouses} == {
        "Основной склад",
        "Кухня",
        "Бар",
    }
    assert {item.name for item in manager.nomenclatures} == {
        "Вода",
        "Молоко",
        "Сахар",
        "Пакет",
    }
    assert {item.name for item in manager.recipes} == {"Молочная карамель"}


def test_convert_storage_manager_preserves_model_relationships():
    """Проверяет связи первичной номенклатуры с группами и единицами."""
    settings = settings_model()
    settings.is_first_start = True
    manager = storage_manager()

    manager.convert(settings)
    sugar = next(item for item in manager.nomenclatures if item.name == "Сахар")
    gram = next(item for item in manager.ranges if item.name == "Грамм")
    kilogram = next(item for item in manager.ranges if item.name == "Килограмм")

    assert sugar.group.name == "Продукты"
    assert sugar.range is kilogram
    assert gram.base_range is kilogram
    assert gram.conversion_factor == 0.001


def test_convert_storage_manager_does_not_duplicate_initial_data():
    """Проверяет идемпотентность повторного формирования данных."""
    settings = settings_model()
    settings.is_first_start = True
    manager = storage_manager()

    manager.convert(settings)
    initial_counts = (
        len(manager.ranges),
        len(manager.groups),
        len(manager.warehouses),
        len(manager.nomenclatures),
        len(manager.recipes),
    )
    manager.convert(settings)

    assert initial_counts == (
        len(manager.ranges),
        len(manager.groups),
        len(manager.warehouses),
        len(manager.nomenclatures),
        len(manager.recipes),
    )


def test_equals_storage_manager_initial_recipe_weights():
    """Проверяет веса рецепта, созданного при первом запуске."""
    settings = create_settings()
    manager = storage_manager()

    manager.convert(settings)
    recipe = manager.recipes[0]

    assert recipe.gross_weight == 510
    assert recipe.net_weight == 500
    assert any(
        item.nomenclature.group.name == "Упаковка"
        for item in recipe.ingredients
    )


def test_add_group_storage_manager_does_not_duplicate_object():
    """Проверяет уникальность одного объекта в коллекции хранилища."""
    manager = storage_manager()
    group = nomenclature_group_model("Тестовая группа")

    manager.add_group(group)
    manager.add_group(group)

    assert manager.groups == [group]


def test_add_range_storage_manager_does_not_duplicate_object():
    """Проверяет добавление уникальной единицы измерения."""
    manager = storage_manager()
    unit = range_model("Упаковка", 1)

    manager.add_range(unit)
    manager.add_range(unit)

    assert manager.ranges == [unit]


def test_add_warehouse_storage_manager_does_not_duplicate_object():
    """Проверяет добавление уникального склада."""
    manager = storage_manager()
    warehouse = warehouse_model("Тестовый склад")

    manager.add_warehouse(warehouse)
    manager.add_warehouse(warehouse)

    assert manager.warehouses == [warehouse]


def test_add_nomenclature_storage_manager_does_not_duplicate_object():
    """Проверяет добавление уникальной номенклатуры."""
    manager = storage_manager()
    group = nomenclature_group_model("Тестовая группа")
    unit = range_model("Штука", 1)
    nomenclature = nomenclature_model(
        "Тестовый товар",
        "Тестовый товар, полное наименование",
        group,
        unit,
    )

    manager.add_nomenclature(nomenclature)
    manager.add_nomenclature(nomenclature)

    assert manager.nomenclatures == [nomenclature]


def test_add_recipe_storage_manager_does_not_duplicate_object():
    """Проверяет добавление уникальной технологической карты."""
    manager = storage_manager()
    recipe = recipe_model.create("Тестовый рецепт")

    manager.add_recipe(recipe)
    manager.add_recipe(recipe)

    assert manager.recipes == [recipe]


def test_argument_exception_storage_manager_invalid_object():
    """Проверяет отклонение объекта неверного доменного типа."""
    with pytest.raises(argument_exception):
        storage_manager().add_group(object())
