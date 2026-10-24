import json
from datetime import datetime, timedelta, timezone

import pytest

from Src.Core.validator import argument_exception
from Src.Logics.convert_factory import convert_factory
from Src.Models.ingredient_model import ingredient_model
from Src.Models.nomenclature_group_model import nomenclature_group_model
from Src.Models.nomenclature_model import nomenclature_model
from Src.Models.range_model import range_model
from Src.Models.recipe_model import recipe_model


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
    result = factory.create(source)

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
    result = factory.create(source)

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
    result = factory.create(source)

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
    first_result = factory.create(unit)
    second_result = factory.create(group)

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
        factory.create(None)

    # Проверки
    assert "Некорректно переданы аргументы" in str(error.value)
