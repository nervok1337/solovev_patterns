import pytest

from Src.Core.entity_model import entity_model
from Src.Core.exception import arguments_exception
from Src.Models.nomenclature_group_model import nomenclature_group_model
from Src.Models.nomenclature_model import nomenclature_model
from Src.Models.organization_model import organization_model
from Src.Models.range_model import range_model
from Src.Models.warehouse_model import warehouse_model


def test_group_created_with_valid_name():
    """Проверяет корректное создание группы номенклатуры."""
    # Подготовка
    name = "Продукты"

    # Действие
    group = nomenclature_group_model(name)

    # Проверки
    assert group.name == name
    assert group.id != ""


def test_warehouse_created_with_valid_name():
    """Проверяет корректное создание склада."""
    # Подготовка
    name = "Основной склад"

    # Действие
    warehouse = warehouse_model(name)

    # Проверки
    assert warehouse.name == name
    assert warehouse.id != ""


def test_base_range_created_without_explicit_base_range():
    """Проверяет создание базовой единицы измерения без третьего аргумента."""
    # Подготовка
    name = "грамм"
    conversion_factor = 1

    # Действие
    gram = range_model(name, conversion_factor)

    # Проверки
    assert gram.name == name
    assert gram.conversion_factor == conversion_factor
    assert gram.base_range is gram


def test_derived_range_created_with_explicit_base_range():
    """Проверяет пример из ТЗ для килограмма и грамма."""
    # Подготовка
    gram = range_model("грамм", 1)
    name = "кг"
    conversion_factor = 1000

    # Действие
    kilogram = range_model(name, conversion_factor, gram)

    # Проверки
    assert kilogram.name == name
    assert kilogram.conversion_factor == conversion_factor
    assert kilogram.base_range is gram


def test_organization_created_with_all_details():
    """Проверяет создание организации со всеми обязательными реквизитами."""
    # Подготовка
    name = "Ромашка"
    inn = "3801000000"
    bik = "042520607"
    account = "40702810000000000001"
    ownership_form = "ООО"

    # Действие
    organization = organization_model(name, inn, bik, account, ownership_form)

    # Проверки
    assert organization.name == name
    assert organization.inn == inn
    assert organization.bik == bik
    assert organization.account == account
    assert organization.ownership_form == ownership_form


def test_nomenclature_created_with_group_and_range():
    """Проверяет создание номенклатуры со вложенными моделями."""
    # Подготовка
    name = "Молоко"
    full_name = "Молоко пастеризованное 3,2%"
    group = nomenclature_group_model("Молочные продукты")
    unit = range_model("литр", 1)

    # Действие
    nomenclature = nomenclature_model(name, full_name, group, unit)

    # Проверки
    assert nomenclature.name == name
    assert nomenclature.full_name == full_name
    assert nomenclature.group is group
    assert nomenclature.range is unit


@pytest.mark.parametrize(
    "model_type",
    [
        nomenclature_group_model,
        nomenclature_model,
        range_model,
        organization_model,
        warehouse_model,
    ],
)
def test_models_inherit_entity_model(model_type):
    """Проверяет наследование доменных моделей от абстрактной модели."""
    # Подготовка
    base_model_type = entity_model

    # Действие
    result = issubclass(model_type, base_model_type)

    # Проверки
    assert result is True


def test_name_accepts_fifty_characters():
    """Проверяет допустимую границу в 50 символов для обычного наименования."""
    # Подготовка
    name = "a" * 50

    # Действие
    group = nomenclature_group_model(name)

    # Проверки
    assert len(group.name) == len(name)


def test_arguments_exception_raised_when_name_longer_than_fifty_characters():
    """Проверяет ошибку при длине обычного наименования более 50 символов."""
    # Подготовка
    name = "a" * 51

    # Действие
    with pytest.raises(arguments_exception) as exception:
        warehouse_model(name)

    # Проверки
    assert exception.type is arguments_exception


def test_full_name_accepts_two_hundred_fifty_five_characters():
    """Проверяет допустимую границу в 255 символов для полного наименования."""
    # Подготовка
    full_name = "a" * 255
    group = nomenclature_group_model("Группа")
    unit = range_model("штука", 1)

    # Действие
    nomenclature = nomenclature_model(
        "Продукт",
        full_name,
        group,
        unit,
    )

    # Проверки
    assert len(nomenclature.full_name) == len(full_name)


def test_arguments_exception_raised_when_full_name_longer_than_limit():
    """Проверяет ошибку при длине полного наименования более 255 символов."""
    # Подготовка
    full_name = "a" * 256
    group = nomenclature_group_model("Группа")
    unit = range_model("штука", 1)

    # Действие
    with pytest.raises(arguments_exception) as exception:
        nomenclature_model(
            "Продукт",
            full_name,
            group,
            unit,
        )

    # Проверки
    assert exception.type is arguments_exception


@pytest.mark.parametrize("conversion_factor", [0, -1, "1000", True])
def test_arguments_exception_raised_when_conversion_factor_invalid(
    conversion_factor,
):
    """Проверяет ошибку для нечислового или неположительного коэффициента."""
    # Подготовка
    name = "кг"

    # Действие
    with pytest.raises(arguments_exception) as exception:
        range_model(name, conversion_factor)

    # Проверки
    assert exception.type is arguments_exception


def test_arguments_exception_raised_when_base_range_factor_not_one():
    """Проверяет ошибку, если коэффициент базовой единицы не равен единице."""
    # Подготовка
    name = "кг"
    conversion_factor = 1000

    # Действие
    with pytest.raises(arguments_exception) as exception:
        range_model(name, conversion_factor)

    # Проверки
    assert exception.type is arguments_exception


def test_arguments_exception_raised_when_base_range_invalid():
    """Проверяет ошибку при передаче объекта неверного типа вместо базовой единицы."""
    # Подготовка
    invalid_base_range = object()

    # Действие
    with pytest.raises(arguments_exception) as exception:
        range_model("кг", 1000, invalid_base_range)

    # Проверки
    assert exception.type is arguments_exception


def test_arguments_exception_raised_when_nomenclature_group_invalid():
    """Проверяет ошибку при передаче объекта неверного типа вместо группы."""
    # Подготовка
    invalid_group = object()
    unit = range_model("штука", 1)

    # Действие
    with pytest.raises(arguments_exception) as exception:
        nomenclature_model(
            "Продукт",
            "Полное имя",
            invalid_group,
            unit,
        )

    # Проверки
    assert exception.type is arguments_exception


def test_arguments_exception_raised_when_nomenclature_range_invalid():
    """Проверяет ошибку при передаче объекта неверного типа вместо единицы измерения."""
    # Подготовка
    group = nomenclature_group_model("Группа")
    invalid_range = object()

    # Действие
    with pytest.raises(arguments_exception) as exception:
        nomenclature_model(
            "Продукт",
            "Полное имя",
            group,
            invalid_range,
        )

    # Проверки
    assert exception.type is arguments_exception


@pytest.mark.parametrize("field", ["inn", "bik", "account", "ownership_form"])
def test_arguments_exception_raised_when_organization_detail_empty(field):
    """Проверяет ошибку при пустом обязательном реквизите организации."""
    # Подготовка
    details = {
        "inn": "3801000000",
        "bik": "042520607",
        "account": "40702810000000000001",
        "ownership_form": "ООО",
    }
    details[field] = ""

    # Действие
    with pytest.raises(arguments_exception) as exception:
        organization_model("Ромашка", **details)

    # Проверки
    assert exception.type is arguments_exception
