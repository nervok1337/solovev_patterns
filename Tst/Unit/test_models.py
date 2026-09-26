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
    group = nomenclature_group_model("Продукты")

    assert group.name == "Продукты"
    assert group.id != ""


def test_warehouse_created_with_valid_name():
    """Проверяет корректное создание склада."""
    warehouse = warehouse_model("Основной склад")

    assert warehouse.name == "Основной склад"
    assert warehouse.id != ""


def test_base_range_created_without_explicit_base_range():
    """Проверяет создание базовой единицы измерения без третьего аргумента."""
    gram = range_model("грамм", 1)

    assert gram.name == "грамм"
    assert gram.conversion_factor == 1
    assert gram.base_range is gram


def test_derived_range_created_with_explicit_base_range():
    """Проверяет пример из ТЗ для килограмма и грамма."""
    gram = range_model("грамм", 1)
    kilogram = range_model("кг", 1000, gram)

    assert kilogram.name == "кг"
    assert kilogram.conversion_factor == 1000
    assert kilogram.base_range is gram


def test_organization_created_with_all_details():
    """Проверяет создание организации со всеми обязательными реквизитами."""
    organization = organization_model(
        "Ромашка",
        "3801000000",
        "042520607",
        "40702810000000000001",
        "ООО",
    )

    assert organization.name == "Ромашка"
    assert organization.inn == "3801000000"
    assert organization.bik == "042520607"
    assert organization.account == "40702810000000000001"
    assert organization.ownership_form == "ООО"


def test_nomenclature_created_with_group_and_range():
    """Проверяет создание номенклатуры со вложенными моделями."""
    group = nomenclature_group_model("Молочные продукты")
    unit = range_model("литр", 1)
    nomenclature = nomenclature_model(
        "Молоко",
        "Молоко пастеризованное 3,2%",
        group,
        unit,
    )

    assert nomenclature.name == "Молоко"
    assert nomenclature.full_name == "Молоко пастеризованное 3,2%"
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
    assert issubclass(model_type, entity_model)


def test_name_accepts_fifty_characters():
    """Проверяет допустимую границу в 50 символов для обычного наименования."""
    group = nomenclature_group_model("a" * 50)

    assert len(group.name) == 50


def test_arguments_exception_raised_when_name_longer_than_fifty_characters():
    """Проверяет ошибку при длине обычного наименования более 50 символов."""
    with pytest.raises(arguments_exception):
        warehouse_model("a" * 51)


def test_full_name_accepts_two_hundred_fifty_five_characters():
    """Проверяет допустимую границу в 255 символов для полного наименования."""
    nomenclature = nomenclature_model(
        "Продукт",
        "a" * 255,
        nomenclature_group_model("Группа"),
        range_model("штука", 1),
    )

    assert len(nomenclature.full_name) == 255


def test_arguments_exception_raised_when_full_name_longer_than_limit():
    """Проверяет ошибку при длине полного наименования более 255 символов."""
    with pytest.raises(arguments_exception):
        nomenclature_model(
            "Продукт",
            "a" * 256,
            nomenclature_group_model("Группа"),
            range_model("штука", 1),
        )


@pytest.mark.parametrize("conversion_factor", [0, -1, "1000", True])
def test_arguments_exception_raised_when_conversion_factor_invalid(
    conversion_factor,
):
    """Проверяет ошибку для нечислового или неположительного коэффициента."""
    with pytest.raises(arguments_exception):
        range_model("кг", conversion_factor)


def test_arguments_exception_raised_when_base_range_factor_not_one():
    """Проверяет ошибку, если коэффициент базовой единицы не равен единице."""
    with pytest.raises(arguments_exception):
        range_model("кг", 1000)


def test_arguments_exception_raised_when_base_range_invalid():
    """Проверяет ошибку при передаче объекта неверного типа вместо базовой единицы."""
    with pytest.raises(arguments_exception):
        range_model("кг", 1000, object())


def test_arguments_exception_raised_when_nomenclature_group_invalid():
    """Проверяет ошибку при передаче объекта неверного типа вместо группы."""
    with pytest.raises(arguments_exception):
        nomenclature_model(
            "Продукт",
            "Полное имя",
            object(),
            range_model("штука", 1),
        )


def test_arguments_exception_raised_when_nomenclature_range_invalid():
    """Проверяет ошибку при передаче объекта неверного типа вместо единицы измерения."""
    with pytest.raises(arguments_exception):
        nomenclature_model(
            "Продукт",
            "Полное имя",
            nomenclature_group_model("Группа"),
            object(),
        )


@pytest.mark.parametrize("field", ["inn", "bik", "account", "ownership_form"])
def test_arguments_exception_raised_when_organization_detail_empty(field):
    """Проверяет ошибку при пустом обязательном реквизите организации."""
    details = {
        "inn": "3801000000",
        "bik": "042520607",
        "account": "40702810000000000001",
        "ownership_form": "ООО",
    }
    details[field] = ""

    with pytest.raises(arguments_exception):
        organization_model("Ромашка", **details)
