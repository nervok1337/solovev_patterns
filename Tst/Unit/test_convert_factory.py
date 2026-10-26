import json
from datetime import date, datetime, time, timedelta, timezone
from pathlib import Path

import pytest

from Src.Core.validator import argument_exception
from Src.Logics.basic_convertor import basic_convertor
from Src.Logics.convert_factory import convert_factory
from Src.Logics.datetime_convertor import datetime_convertor
from Src.Logics.reference_convertor import reference_convertor
from Src.Logics.storage_manager import storage_manager
from Src.Models.ingredient_model import ingredient_model
from Src.Models.nomenclature_group_model import nomenclature_group_model
from Src.Models.nomenclature_model import nomenclature_model
from Src.Models.range_model import range_model
from Src.Models.recipe_model import recipe_model
from Src.Models.settings_model import settings_model


class dated_group_model(nomenclature_group_model):
    """Дополняет группу датой и ссылкой для совместной проверки конвертеров."""

    def __init__(
        self,
        name: str,
        created_at: datetime,
        related_group: nomenclature_group_model,
    ) -> None:
        """Создаёт модель с простыми, временными и ссылочными свойствами."""
        super().__init__(name)
        self.__created_at = created_at
        self.__related_group = related_group

    @property
    def created_at(self) -> datetime:
        """Возвращает дату создания группы."""
        return self.__created_at

    @property
    def related_group(self) -> nomenclature_group_model:
        """Возвращает связанную группу."""
        return self.__related_group


@pytest.fixture
def populated_storage(monkeypatch):
    """Создаёт начальные данные, изолируя singleton от остальных тестов."""
    monkeypatch.delattr(storage_manager, "instance", raising=False)
    storage = storage_manager()
    storage.convert(settings_model())
    yield storage
    delattr(storage_manager, "instance")


@pytest.mark.parametrize(
    ["source", "expected_type"],
    [
        [12, basic_convertor],
        [0.5, basic_convertor],
        ["Сахар", basic_convertor],
        [False, basic_convertor],
        [None, basic_convertor],
        [datetime(2026, 10, 26), datetime_convertor],
        [date(2026, 10, 26), datetime_convertor],
        [time(12, 30), datetime_convertor],
        [{}, reference_convertor],
        [[], reference_convertor],
        [object(), reference_convertor],
    ],
)
def test_instance_convert_factory_create_selected_convertor(source, expected_type):
    """<summary>Проверяет, что фабрика возвращает обработчик нужного типа.</summary>"""
    # Подготовка
    factory = convert_factory()

    # Действие
    result = factory.create(source)

    # Проверки
    assert isinstance(result, expected_type)


def test_instance_convert_factory_create_without_reading_properties():
    """<summary>Проверяет, что выбор обработчика не запускает преобразование.</summary>"""
    # Подготовка
    class unreadable_model:
        """Запрещает чтение свойства во время выбора конвертера."""

        @property
        def value(self):
            """Вызывает ошибку при попытке прочитать исходное значение."""
            raise AssertionError("Фабрика не должна читать свойства объекта")

    source = unreadable_model()
    factory = convert_factory()

    # Действие
    result = factory.create(source)

    # Проверки
    assert isinstance(result, reference_convertor)


def test_instance_convert_factory_create_inherited_type():
    """<summary>Проверяет выбор конвертера для наследника зарегистрированного типа.</summary>"""
    # Подготовка
    class custom_string(str):
        """Представляет пользовательский строковый тип."""

    source = custom_string("Сахар")
    factory = convert_factory()

    # Действие
    result = factory.create(source)

    # Проверки
    assert isinstance(result, basic_convertor)
    assert result.convert(source, "name") == {"name": "Сахар"}


def test_equals_convert_factory_create_delegated_nested_values():
    """<summary>Проверяет применение выбранного обработчика к полям и спискам.</summary>"""
    # Подготовка
    class marked_datetime_convertor(datetime_convertor):
        """Помечает значение, прошедшее через подставленный обработчик."""

        def convert(self, source, field_name=None):
            """Возвращает маркер вместо обычного представления даты."""
            key = "value" if field_name is None else field_name
            return {key: "selected-datetime-convertor"}

    class custom_factory(convert_factory):
        """Подменяет обработчик даты через общий интерфейс фабрики."""

        def create(self, source, ancestors=None):
            """Выбирает тестовый конвертер дат и обычные остальные конвертеры."""
            if isinstance(source, datetime):
                return marked_datetime_convertor()
            return super().create(source, ancestors)

    moment = datetime(2026, 10, 26, 12, 30)
    source = {"created_at": moment, "items": [moment]}
    factory = custom_factory()

    # Действие
    result = factory.create(source).convert(source)

    # Проверки
    assert result == {
        "created_at": "selected-datetime-convertor",
        "items": ["selected-datetime-convertor"],
    }


def test_equals_convert_factory_create_root_collection():
    """<summary>Проверяет преобразование коллекции, переданной прямо в фабрику.</summary>"""
    # Подготовка
    source = [0, False, None, datetime(2026, 10, 26, 12, 30), []]
    factory = convert_factory()

    # Действие
    result = factory.create(source).convert(source)

    # Проверки
    assert result == {"value": [0, False, None, "2026-10-26T12:30:00", []]}


def test_equals_convert_factory_create_fields_named_value():
    """<summary>Проверяет сохранение поля value на нескольких уровнях вложенности.</summary>"""
    # Подготовка
    source = {"value": {"value": [0, {"value": False}]}}
    factory = convert_factory()

    # Действие
    result = factory.create(source).convert(source)

    # Проверки
    assert result == source


@pytest.mark.parametrize("key", [None, 1])
def test_argument_exception_convert_factory_create_non_string_field_name(key):
    """<summary>Проверяет отклонение ключа, который нельзя считать именем поля.</summary>"""
    # Подготовка
    source = {key: "Сахар"}
    factory = convert_factory()

    # Действие
    with pytest.raises(argument_exception) as error:
        factory.create(source).convert(source)

    # Проверки
    assert "Имя поля словаря должно быть строкой" in str(error.value)


def test_equals_convert_factory_create_mixed_fields():
    """<summary>Проверяет объединение простых полей, даты и вложенного объекта.</summary>"""
    # Подготовка
    group = nomenclature_group_model.create("Продукты")
    source = dated_group_model(
        "Основная группа",
        datetime(2026, 10, 24, 12, 30, tzinfo=timezone(timedelta(hours=8))),
        group,
    )
    factory = convert_factory()

    # Действие
    result = factory.create(source).convert(source)

    # Проверки
    assert result == {
        "id": source.id,
        "name": "Основная группа",
        "unique_code": source.unique_code,
        "created_at": "2026-10-24T12:30:00+08:00",
        "related_group": {
            "id": group.id,
            "name": "Продукты",
            "unique_code": group.unique_code,
        },
    }
    assert json.loads(json.dumps(result, ensure_ascii=False)) == result


def test_equals_convert_factory_create_nested_recipe():
    """<summary>Проверяет сохранение состава рецепта и связей его ингредиента.</summary>"""
    # Подготовка
    group = nomenclature_group_model.create("Продукты")
    unit = range_model.create("Килограмм", 1)
    sugar = nomenclature_model.create("Сахар", "Сахар-песок", group, unit)
    ingredient = ingredient_model.create(sugar, 200, 190)
    base_recipe = recipe_model.create("Основа", [ingredient])
    source = recipe_model.create("Карамель", [base_recipe])
    factory = convert_factory()

    # Действие
    result = factory.create(source).convert(source)

    # Проверки
    assert result["id"] == source.id
    assert result["name"] == "Карамель"
    assert result["gross_weight"] == 200.0
    assert result["net_weight"] == 190.0
    assert len(result["ingredients"]) == 1
    base_data = result["ingredients"][0]
    assert base_data["id"] == base_recipe.id
    assert base_data["name"] == "Основа"
    assert len(base_data["ingredients"]) == 1
    ingredient_data = base_data["ingredients"][0]
    assert ingredient_data["id"] == ingredient.id
    assert ingredient_data["gross_weight"] == 200.0
    assert ingredient_data["net_weight"] == 190.0
    assert ingredient_data["nomenclature"] == {
        "id": sugar.id,
        "name": "Сахар",
        "full_name": "Сахар-песок",
        "unique_code": sugar.unique_code,
        "group": {
            "id": group.id,
            "name": "Продукты",
            "unique_code": group.unique_code,
        },
        "range": {
            "id": unit.id,
            "name": "Килограмм",
            "unique_code": unit.unique_code,
            "conversion_factor": 1.0,
            "base_range": {"unique_code": unit.unique_code},
        },
    }


def test_equals_convert_factory_create_self_reference():
    """<summary>Проверяет объединение простых полей с представлением цикла.</summary>"""
    # Подготовка
    source = range_model.create("Килограмм", 1)
    factory = convert_factory()

    # Действие
    result = factory.create(source).convert(source)

    # Проверки
    assert result == {
        "id": source.id,
        "name": "Килограмм",
        "unique_code": source.unique_code,
        "conversion_factor": 1.0,
        "base_range": {"unique_code": source.unique_code},
    }


def test_equals_convert_factory_create_independent_results():
    """<summary>Проверяет отсутствие переноса полей между вызовами фабрики.</summary>"""
    # Подготовка
    unit = range_model.create("Килограмм", 1)
    group = nomenclature_group_model.create("Продукты")
    factory = convert_factory()

    # Действие
    first_result = factory.create(unit).convert(unit)
    second_result = factory.create(group).convert(group)

    # Проверки
    assert second_result == {
        "id": group.id,
        "name": "Продукты",
        "unique_code": group.unique_code,
    }
    assert first_result["name"] == "Килограмм"
    assert first_result["base_range"] == {"unique_code": unit.unique_code}


def test_argument_exception_convert_factory_create_missing_source():
    """<summary>Проверяет передачу ошибки конвертера при отсутствии объекта.</summary>"""
    # Подготовка
    factory = convert_factory()

    # Действие
    with pytest.raises(argument_exception) as error:
        factory.create(None).convert(None)

    # Проверки
    assert "Некорректно переданы аргументы" in str(error.value)


def test_equals_convert_factory_create_full_storage(populated_storage):
    """<summary>Проверяет выгрузку всех коллекций и состояния хранилища.</summary>"""
    # Подготовка
    source = populated_storage
    factory = convert_factory()

    # Действие
    result = factory.create(source).convert(source)

    # Проверки
    assert set(result) == {
        "ranges", "groups", "warehouses", "nomenclatures", "recipes", "is_loaded",
    }
    assert result["is_loaded"] is True
    for name in ["ranges", "groups", "warehouses", "nomenclatures", "recipes"]:
        original_items = getattr(source, name)
        assert len(result[name]) == len(original_items)
        assert {item["unique_code"] for item in result[name]} == {
            item.unique_code for item in original_items
        }
    assert result["recipes"][0]["name"] == "Молочная карамель"
    assert len(result["recipes"][0]["ingredients"]) == 2


def test_equals_convert_factory_storage_json_complete_collections():
    """<summary>Проверяет состав единого JSON, приложенного к результату работы.</summary>"""
    # Подготовка
    file_path = Path(__file__).resolve().parents[2] / "Docs/Serialization/storage.json"

    # Действие
    result = json.loads(file_path.read_text(encoding="utf-8"))

    # Проверки
    assert set(result) == {
        "ranges", "groups", "warehouses", "nomenclatures", "recipes", "is_loaded",
    }
    assert result["is_loaded"] is True
    assert len(result["ranges"]) == 5
    assert len(result["groups"]) == 3
    assert len(result["warehouses"]) == 3
    assert len(result["nomenclatures"]) == 4
    assert len(result["recipes"]) == 1
