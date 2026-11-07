import json
from pathlib import Path

import pytest

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


def test_storage_file_restores_values_types_and_shared_references(storage, loader, tmp_path):
    expected = serialize(storage)
    path = tmp_path / "storage.json"
    path.write_text(json.dumps(expected, ensure_ascii=False), encoding="utf-8")
    restored = loader.load_storage(path)

    # Equality моделей сравнивает только код: здесь проверяются все поля.
    assert serialize(restored) == expected
    for section in ("ranges", "groups", "warehouses", "nomenclatures", "recipes"):
        for original, loaded in zip(getattr(storage, section), getattr(restored, section)):
            assert type(loaded) is type(original)
            assert loaded is not original
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
