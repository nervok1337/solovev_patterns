import pytest

from Src.Core.validator import argument_exception
from Src.Dtos.report_result_dto import report_result_dto
from Src.Dtos.report_type_dto import report_type_enum
from Src.Logics.report_factory import report_factory
from Src.Logics.text_report import text_report
from Src.Models.ingredient_model import ingredient_model
from Src.Models.nomenclature_group_model import nomenclature_group_model
from Src.Models.nomenclature_model import nomenclature_model
from Src.Models.range_model import range_model
from Src.Models.recipe_model import recipe_model
from Src.Models.settings_model import settings_model


@pytest.fixture
def settings():
    """Возвращает настройки с текстовым форматом отчёта."""
    value = settings_model()
    value.response_format = report_type_enum.TXT
    return value


def test_report_factory_creates_text_report(settings):
    """Проверяет создание реализации текстового отчёта фабрикой."""
    # Подготовка
    factory = report_factory(settings)

    # Действие
    report = factory.create(report_type_enum.TXT)

    # Проверка
    assert isinstance(report, text_report)


def test_report_factory_raises_exception_for_invalid_type(settings):
    """Проверяет исключение для неподдерживаемого типа отчёта."""
    # Подготовка
    factory = report_factory(settings)

    # Действие и проверка
    with pytest.raises(argument_exception):
        factory.create("PDF")


def test_text_report_created_by_factory_builds_report(settings):
    """Проверяет формирование отчёта через фабрику."""
    # Подготовка
    factory = report_factory(settings)
    products = nomenclature_group_model.create("Продукты")
    gram = range_model.create("Грамм", 1)
    sugar = ingredient_model.create(
        nomenclature_model.create("Сахар", "Сахар-песок", products, gram),
        200,
        190,
    )
    milk = ingredient_model.create(
        nomenclature_model.create("Молоко", "Молоко питьевое", products, gram),
        250,
        240,
    )
    recipe = recipe_model.create("Карамель", (sugar, milk))

    # Действие
    report = factory.create(report_type_enum.TXT)
    result = report.build(recipe)

    # Проверка
    assert isinstance(result, report_result_dto)
    assert result.text.splitlines() == [
        "gross_weight | id | name | net_weight | nomenclature | unique_code",
        (
            f"200.0 | {sugar.id} | Сахар | 190.0 | Сахар | "
            f"{sugar.unique_code}"
        ),
        (
            f"250.0 | {milk.id} | Молоко | 240.0 | Молоко | "
            f"{milk.unique_code}"
        ),
    ]
    assert result.binary == []


def test_report_factory_creates_default_report_from_settings(settings):
    """Проверяет создание отчёта в формате из настроек."""
    # Подготовка
    factory = report_factory(settings)

    # Действие
    report = factory.create_default()

    # Проверка
    assert isinstance(report, text_report)
