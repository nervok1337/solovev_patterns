import json
from pathlib import Path

import pytest

from Src.Core.common import common
from Src.Core.exception import arguments_exception
from Src.Logics.convert_factory import convert_factory
from Src.Logics.deserialize_factory import deserialize_factory
from Src.Logics.deserializer import deserializer
from Src.Logics.json_deserializer import json_deserializer
from Src.Logics.storage_manager import storage_manager
from Src.Models.ingredient_model import ingredient_model
from Src.Models.organization_model import organization_model
from Src.Models.range_model import range_model
from Src.Models.recipe_model import recipe_model
from Src.Models.settings_model import settings_model


def serialize(model):
    """Выгружает все публичные свойства объекта существующей фабрикой конвертеров."""
    factory = convert_factory()
    return factory.create(model).convert(model)


@pytest.fixture
def storage():
    previous = getattr(storage_manager, "instance", None)
    if previous is not None:
        del storage_manager.instance
    model = storage_manager()
    model.convert(settings_model())
    yield model
    del storage_manager.instance
    if previous is not None:
        storage_manager.instance = previous


@pytest.fixture
def loader():
    return json_deserializer(deserializer(deserialize_factory()))


def test_full_storage_export_import_compares_all_models(storage, loader, tmp_path):
    """Выгружает всё хранилище в файл, загружает и сравнивает все модели и связи."""
    # Подготовка: storage содержит все первичные модели из storage_manager.convert.
    expected = serialize(storage)
    path = tmp_path / "storage.json"
    # Действие: весь снимок проходит через настоящий JSON-файл.
    path.write_text(json.dumps(expected, ensure_ascii=False, allow_nan=False), encoding="utf-8")
    restored = loader.load_storage(path)

    # Проверка: сравниваем объекты напрямую, независимо от повторной сериализации.
    restored_by_original = {}
    original_by_restored = {}

    def compare(original, loaded):
        """Сравнивает каждое свойство и сохраняемую структуру ссылок, учитывая циклы."""
        assert type(loaded) is type(original)
        if common.is_simple_value(original):
            assert loaded == original
            return
        if isinstance(original, list):
            assert len(loaded) == len(original)
            for original_item, loaded_item in zip(original, loaded):
                compare(original_item, loaded_item)
            return

        assert loaded is not original
        if id(original) in restored_by_original:
            assert restored_by_original[id(original)] is loaded
            return
        # Разные исходные объекты не должны случайно объединиться при загрузке.
        assert id(loaded) not in original_by_restored
        restored_by_original[id(original)] = loaded
        original_by_restored[id(loaded)] = original
        fields = common.get_fields(original)
        assert fields
        assert common.get_fields(loaded) == fields
        for field in fields:
            compare(getattr(original, field), getattr(loaded, field))

    # Корневой DTO заменяет менеджер; все его коллекции содержат исходные типы моделей.
    fields = common.get_fields(storage)
    assert common.get_fields(restored) == fields
    assert storage.is_loaded is True
    for field in fields:
        compare(getattr(storage, field), getattr(restored, field))

    # Дополнительно проверяем полное совпадение повторной выгрузки с исходной.
    assert serialize(restored) == expected
    ranges = {item.unique_code: item for item in restored.ranges}
    groups = {item.unique_code: item for item in restored.groups}
    nomenclatures = {item.unique_code: item for item in restored.nomenclatures}
    for unit in restored.ranges:
        assert unit.base_range is ranges[unit.base_range.unique_code]
    for item in restored.nomenclatures:
        assert item.range is ranges[item.range.unique_code]
        assert item.group is groups[item.group.unique_code]

    recipe = restored.recipes[0]
    assert isinstance(recipe.ingredients[0], recipe_model)
    ingredients = recipe.ingredients[0].ingredients + [recipe.ingredients[1]]
    for item in ingredients:
        assert isinstance(item, ingredient_model)
        assert item.nomenclature is nomenclatures[item.nomenclature.unique_code]
    assert recipe.gross_weight == 510
    assert recipe.net_weight == 500
    assert storage_manager() is storage
    assert serialize(storage) == expected
    assert loader.load_storage(path).recipes[0] is not recipe


def test_existing_export_is_supported(loader):
    path = Path(__file__).resolve().parents[2] / "Docs/Serialization/storage.json"
    assert serialize(loader.load_storage(path)) == json.loads(path.read_text(encoding="utf-8"))


def test_separate_organization(loader):
    original = organization_model("Кафе", "123", "456", "789", "ООО")
    expected = serialize(original)
    restored = loader.loads(json.dumps(expected), organization_model)
    assert type(restored) is organization_model
    assert serialize(restored) == expected


@pytest.mark.parametrize("field,value", [
    ("conversion_factor", 0),
    ("conversion_factor", True),
    ("unique_code", ""),
    ("base_range", "unknown"),
    ("extra", 1),
])
def test_invalid_model_is_rejected(loader, field, value):
    source = serialize(range_model.create("Грамм", 1))
    source[field] = value
    with pytest.raises(arguments_exception):
        loader.loads(json.dumps(source), range_model)


def test_conflicting_repeated_object_is_rejected(storage, loader):
    source = serialize(storage)
    source["nomenclatures"][0]["range"]["name"] = "Другое имя"
    with pytest.raises(arguments_exception, match="Противоречивые"):
        loader.loads_storage(json.dumps(source))


def test_recipe_cannot_override_computed_weight(storage, loader):
    source = serialize(storage.recipes[0])
    source["net_weight"] = 100
    with pytest.raises(arguments_exception, match="Вычисляемое свойство"):
        loader.loads(json.dumps(source), recipe_model)


@pytest.mark.parametrize("text", ['{"name": "a", "name": "b"}', '{"value": NaN}'])
def test_ambiguous_or_nonstandard_json_is_rejected(loader, text):
    with pytest.raises(arguments_exception):
        loader.loads_storage(text)


def test_existing_report_dto_without_entity_fields(loader):
    from Src.Dtos.report_data_dto import report_data_dto
    from Src.Dtos.report_row_dto import report_row_dto

    original = report_data_dto(
        "report", None, "Отчёт", ["quantity"], ["Количество"],
        [report_row_dto([12, None, {"comment": "пример"}])], frozenset({0}),
    )
    source = serialize(original)
    restored = loader.loads(json.dumps(source), report_data_dto)
    assert type(restored) is report_data_dto
    assert type(restored.rows[0]) is report_row_dto
    assert restored.numeric_columns == frozenset({0})
    assert serialize(restored) == source
    assert not hasattr(restored, "unique_code")


def test_new_nested_dto_requires_no_factory_registration(loader):
    from dataclasses import dataclass

    @dataclass
    class measurement:
        amplitude: float
        valid: bool

    @dataclass
    class observation:
        samples: list[measurement]
        station: str = "unknown"

    restored = loader.loads(
        '{"samples": [{"amplitude": 2.5, "valid": true}]}', observation
    )
    assert isinstance(restored.samples[0], measurement)
    assert restored.samples[0].amplitude == 2.5
    assert restored.station == "unknown"


def test_inherited_properties_are_discovered_without_executing_getters(loader):
    class parent:
        def __init__(self, count: int):
            self._count = count

        @property
        def count(self) -> int:
            return self._count

    class child(parent):
        @property
        def doubled(self) -> int:
            return self.count * 2

    restored = loader.loads('{"count": 3, "doubled": 6}', child)
    assert restored.count == 3
    assert restored.doubled == 6
    with pytest.raises(arguments_exception, match="Вычисляемое свойство"):
        loader.loads('{"count": 3, "doubled": 7}', child)


def test_ambiguous_union_is_rejected(loader):
    from dataclasses import dataclass

    @dataclass
    class first:
        value: int

    @dataclass
    class second:
        value: int

    with pytest.raises(arguments_exception, match="однозначно"):
        loader.loads('{"value": 1}', first | second)


def test_model_constructor_validation_is_preserved(storage, loader):
    source = serialize(storage.recipes[0].ingredients[1])
    source["net_weight"] = source["gross_weight"] + 1
    with pytest.raises(arguments_exception, match="нетто"):
        loader.loads(json.dumps(source), ingredient_model)


def test_typed_dictionary_and_optional_dto(loader):
    from Src.Dtos.report_row_dto import report_row_dto

    result = loader.loads('{"a": {"values": [1]}, "b": null}',
                          dict[str, report_row_dto | None])
    assert isinstance(result["a"], report_row_dto)
    assert result["a"].values == [1]
    assert result["b"] is None


@pytest.mark.parametrize("error_type", [TypeError, ValueError, RuntimeError])
def test_constructor_error_preserves_original_cause(loader, error_type):
    """Проверяет контекст ошибки создания модели и сохранение исходной причины."""
    original_error = error_type("Ошибка конструктора")

    class failing_model:
        """Модель с конструктором, завершающимся ошибкой."""

        def __init__(self, value: int):
            """Имитирует ошибку при создании модели из корректно разобранных данных."""
            raise original_error

    with pytest.raises(arguments_exception, match="Не удалось создать failing_model") as caught:
        loader.loads('{"value": 1}', failing_model)

    assert caught.value.__cause__ is original_error
