from datetime import date, datetime, time, timedelta, timezone

import pytest

from Src.Core.validator import argument_exception
from Src.Logics.basic_convertor import basic_convertor
from Src.Logics.datetime_convertor import datetime_convertor
from Src.Logics.reference_convertor import reference_convertor
from Src.Models.nomenclature_group_model import nomenclature_group_model
from Src.Models.range_model import range_model


class value_model:
    """Предоставляет одно публичное свойство для проверки конвертеров."""

    def __init__(self, value: object) -> None:
        """Сохраняет переданное тестовое значение."""
        self.__value = value

    @property
    def value(self) -> object:
        """Возвращает значение простого или составного типа."""
        return self.__value


@pytest.mark.parametrize("value", ["Сахар", "", 0, -10, 12.5, True, False, None])
def test_equals_basic_convertor_convert_simple_values(value):
    """<summary>Проверяет сохранение простого значения, его типа и имени поля.</summary>"""
    # Подготовка
    source = value_model(value)
    convertor = basic_convertor()

    # Действие
    result = convertor.convert(source)

    # Проверки
    assert result == {"value": value}
    assert type(result["value"]) is type(value)


@pytest.mark.parametrize(
    "value",
    [datetime(2026, 10, 24), [1, 2], {"name": "Сахар"}, value_model("Сахар")],
)
def test_empty_basic_convertor_convert_complex_values(value):
    """<summary>Проверяет исключение дат, коллекций и ссылок из простых полей.</summary>"""
    # Подготовка
    source = value_model(value)
    convertor = basic_convertor()

    # Действие
    result = convertor.convert(source)

    # Проверки
    assert result == {}


def test_equals_basic_convertor_convert_inherited_properties():
    """<summary>Проверяет чтение унаследованных свойств реальной модели.</summary>"""
    # Подготовка
    source = nomenclature_group_model.create("Продукты")
    convertor = basic_convertor()

    # Действие
    result = convertor.convert(source)

    # Проверки
    assert result == {
        "id": source.id,
        "name": "Продукты",
        "unique_code": source.unique_code,
    }


@pytest.mark.parametrize(
    ["value", "expected"],
    [
        [datetime(2026, 10, 24, 12, 30, 45), "2026-10-24T12:30:45"],
        [
            datetime(2026, 10, 24, 12, 30, 45, 123456, timezone(timedelta(hours=8))),
            "2026-10-24T12:30:45.123456+08:00",
        ],
        [date(2026, 10, 24), "2026-10-24"],
        [time(12, 30, 45), "12:30:45"],
    ],
)
def test_equals_datetime_convertor_convert_dates(value, expected):
    """<summary>Проверяет ISO-формат дат, времени, микросекунд и часового пояса.</summary>"""
    # Подготовка
    source = value_model(value)
    convertor = datetime_convertor()

    # Действие
    result = convertor.convert(source)

    # Проверки
    assert result == {"value": expected}


def test_empty_datetime_convertor_convert_without_dates():
    """<summary>Проверяет пустой результат для модели без дат и времени.</summary>"""
    # Подготовка
    source = nomenclature_group_model.create("Продукты")
    convertor = datetime_convertor()

    # Действие
    result = convertor.convert(source)

    # Проверки
    assert result == {}


@pytest.mark.parametrize("value", ["Сахар", 0, False, None, datetime(2026, 10, 24)])
def test_empty_reference_convertor_convert_simple_fields(value):
    """<summary>Проверяет исключение полей, принадлежащих другим конвертерам.</summary>"""
    # Подготовка
    source = value_model(value)
    convertor = reference_convertor()

    # Действие
    result = convertor.convert(source)

    # Проверки
    assert result == {}


def test_equals_reference_convertor_convert_nested_objects():
    """<summary>Проверяет сохранение двух уровней вложенности и полей модели.</summary>"""
    # Подготовка
    group = nomenclature_group_model.create("Продукты")
    source = value_model(value_model(group))
    convertor = reference_convertor()

    # Действие
    result = convertor.convert(source)

    # Проверки
    assert result == {
        "value": {
            "value": {
                "id": group.id,
                "name": "Продукты",
                "unique_code": group.unique_code,
            },
        },
    }


def test_equals_reference_convertor_convert_nested_datetime():
    """<summary>Проверяет преобразование даты в свойстве вложенного объекта.</summary>"""
    # Подготовка
    source = value_model(value_model(datetime(2026, 10, 24, 12, 30)))
    convertor = reference_convertor()

    # Действие
    result = convertor.convert(source)

    # Проверки
    assert result == {"value": {"value": "2026-10-24T12:30:00"}}


def test_equals_reference_convertor_convert_mixed_collection():
    """<summary>Проверяет порядок объектов, дат и простых значений в списке.</summary>"""
    # Подготовка
    group = nomenclature_group_model.create("Продукты")
    values = [group, datetime(2026, 10, 24, 12, 30), 0, False, None, ["Сахар"]]
    source = value_model(values)
    convertor = reference_convertor()

    # Действие
    result = convertor.convert(source)

    # Проверки
    assert result == {
        "value": [
            {"id": group.id, "name": "Продукты", "unique_code": group.unique_code},
            "2026-10-24T12:30:00",
            0,
            False,
            None,
            ["Сахар"],
        ],
    }
    assert values[0] is group
    assert isinstance(values[1], datetime)


def test_equals_reference_convertor_convert_mapping():
    """<summary>Проверяет сохранение ключей словаря и преобразование его значений.</summary>"""
    # Подготовка
    group = nomenclature_group_model.create("Продукты")
    source = value_model({"group": group, "dates": [date(2026, 10, 24)]})
    convertor = reference_convertor()

    # Действие
    result = convertor.convert(source)

    # Проверки
    assert result == {
        "value": {
            "group": {
                "id": group.id,
                "name": "Продукты",
                "unique_code": group.unique_code,
            },
            "dates": ["2026-10-24"],
        },
    }


@pytest.mark.parametrize(["value", "expected"], [[[], []], [{}, {}], [set(), []]])
def test_equals_reference_convertor_convert_empty_collections(value, expected):
    """<summary>Проверяет сохранение пустых коллекций в результате конвертации.</summary>"""
    # Подготовка
    source = value_model(value)
    convertor = reference_convertor()

    # Действие
    result = convertor.convert(source)

    # Проверки
    assert result == {"value": expected}


def test_equals_reference_convertor_convert_shared_reference():
    """<summary>Проверяет, что общая ссылка в соседних элементах не считается циклом.</summary>"""
    # Подготовка
    group = nomenclature_group_model.create("Продукты")
    source = value_model([group, group])
    expected = {"id": group.id, "name": "Продукты", "unique_code": group.unique_code}
    convertor = reference_convertor()

    # Действие
    result = convertor.convert(source)

    # Проверки
    assert result == {"value": [expected, expected]}


def test_equals_reference_convertor_convert_self_reference():
    """<summary>Проверяет замену ссылки единицы на саму себя её уникальным кодом.</summary>"""
    # Подготовка
    source = range_model.create("Килограмм", 1)
    convertor = reference_convertor()

    # Действие
    result = convertor.convert(source)

    # Проверки
    assert result == {"base_range": {"unique_code": source.unique_code}}
    assert source.base_range is source


def test_equals_reference_convertor_convert_indirect_cycle():
    """<summary>Проверяет завершение обхода при циклической связи двух объектов.</summary>"""
    # Подготовка
    kilogram = range_model.create("Килограмм", 1)
    gram = range_model.create("Грамм", 0.001, kilogram)
    kilogram.base_range = gram
    convertor = reference_convertor()

    # Действие
    result = convertor.convert(kilogram)

    # Проверки
    assert result == {
        "base_range": {
            "base_range": {"unique_code": kilogram.unique_code},
            "conversion_factor": 0.001,
            "id": gram.id,
            "name": "Грамм",
            "unique_code": gram.unique_code,
        },
    }


def test_argument_exception_reference_convertor_convert_cycle_without_code():
    """<summary>Проверяет понятную ошибку для цикла без уникального кода.</summary>"""
    # Подготовка
    values = []
    values.append(values)
    source = value_model(values)
    convertor = reference_convertor()

    # Действие
    with pytest.raises(argument_exception) as error:
        convertor.convert(source)

    # Проверки
    assert "циклическую ссылку без unique_code" in str(error.value)


def test_argument_exception_reference_convertor_convert_unsupported_value():
    """<summary>Проверяет явную ошибку вместо потери неподдерживаемого значения.</summary>"""
    # Подготовка
    source = value_model(b"data")
    convertor = reference_convertor()

    # Действие
    with pytest.raises(argument_exception) as error:
        convertor.convert(source)

    # Проверки
    assert "Неподдерживаемый тип ссылочного значения: bytes" in str(error.value)


@pytest.mark.parametrize(
    "convertor_type", [basic_convertor, datetime_convertor, reference_convertor]
)
def test_argument_exception_convertor_convert_missing_source(convertor_type):
    """<summary>Проверяет отклонение отсутствующего исходного объекта.</summary>"""
    # Подготовка
    convertor = convertor_type()

    # Действие
    with pytest.raises(argument_exception) as error:
        convertor.convert(None)

    # Проверки
    assert "Некорректно переданы аргументы" in str(error.value)
