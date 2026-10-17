from Src.Dtos.report_result_dto import report_result_dto
from Src.Logics.text_report import text_report
from Src.Models.ingredient_model import ingredient_model
from Src.Models.nomenclature_group_model import nomenclature_group_model
from Src.Models.nomenclature_model import nomenclature_model
from Src.Models.range_model import range_model
from Src.Models.recipe_model import recipe_model


def test_text_report_builds_recipe_table():
    """Проверяет формирование текстового отчёта по составу рецепта."""
    # Подготовка
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
    report = text_report()

    # Действие
    result = report.build(recipe)

    # Проверки
    assert isinstance(result, report_result_dto)
    assert result.text.splitlines() == [
        "Код | Наименование | Брутто | Нетто",
        f"{sugar.unique_code} | Сахар | 200.0 | 190.0",
        f"{milk.unique_code} | Молоко | 250.0 | 240.0",
    ]
    assert result.binary == []
