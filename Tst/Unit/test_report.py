import csv
from io import StringIO
from xml.etree import ElementTree

from Src.Dtos.report_result_dto import report_result_dto
from Src.Logics.csv_report import csv_report
from Src.Logics.html_report import html_report
from Src.Logics.markdown_report import markdown_report
from Src.Logics.text_report import text_report
from Src.Logics.xml_report import xml_report
from Src.Models.ingredient_model import ingredient_model
from Src.Models.nomenclature_group_model import nomenclature_group_model
from Src.Models.nomenclature_model import nomenclature_model
from Src.Models.range_model import range_model
from Src.Models.recipe_model import recipe_model


def create_recipe():
    """Создаёт рецепт с двумя ингредиентами для проверки отчётов."""
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
    return recipe, sugar, milk


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


def test_csv_report_builds_recipe_table():
    """Проверяет состав и порядок строк CSV-отчёта."""
    # Подготовка
    recipe, sugar, milk = create_recipe()
    report = csv_report()

    # Действие
    result = report.build(recipe)
    content = bytes(result.binary).decode("utf-8")
    rows = list(csv.reader(StringIO(content)))

    # Проверки
    assert isinstance(result, report_result_dto)
    assert rows == [
        ["Код", "Наименование", "Брутто", "Нетто"],
        [sugar.unique_code, "Сахар", "200.0", "190.0"],
        [milk.unique_code, "Молоко", "250.0", "240.0"],
    ]
    assert result.text == ""
    assert result.binary != []


def test_markdown_report_builds_recipe_table():
    """Проверяет состав и разметку Markdown-отчёта."""
    # Подготовка
    recipe, sugar, milk = create_recipe()
    report = markdown_report()

    # Действие
    result = report.build(recipe)
    content = bytes(result.binary).decode("utf-8")

    # Проверки
    assert isinstance(result, report_result_dto)
    assert content.splitlines() == [
        "| Код | Наименование | Брутто | Нетто |",
        "| --- | --- | ---: | ---: |",
        f"| {sugar.unique_code} | Сахар | 200.0 | 190.0 |",
        f"| {milk.unique_code} | Молоко | 250.0 | 240.0 |",
    ]
    assert result.text == ""
    assert result.binary != []


def test_xml_report_builds_recipe_document():
    """Проверяет состав и структуру XML-отчёта."""
    # Подготовка
    recipe, sugar, milk = create_recipe()
    report = xml_report()

    # Действие
    result = report.build(recipe)
    root = ElementTree.fromstring(result.text)

    # Проверки
    assert isinstance(result, report_result_dto)
    assert root.tag == "recipe"
    assert root.attrib == {"name": "Карамель"}
    assert [
        {element.tag: element.text for element in ingredient}
        for ingredient in root.findall("ingredient")
    ] == [
        {
            "code": sugar.unique_code,
            "name": "Сахар",
            "gross_weight": "200.0",
            "net_weight": "190.0",
        },
        {
            "code": milk.unique_code,
            "name": "Молоко",
            "gross_weight": "250.0",
            "net_weight": "240.0",
        },
    ]
    assert result.binary == []


def test_html_report_builds_recipe_table():
    """Проверяет состав и структуру HTML-отчёта."""
    # Подготовка
    recipe, sugar, milk = create_recipe()
    report = html_report()

    # Действие
    result = report.build(recipe)

    # Проверки
    assert isinstance(result, report_result_dto)
    assert result.text == (
        "<table><thead><tr>"
        "<th>Код</th><th>Наименование</th><th>Брутто</th><th>Нетто</th>"
        "</tr></thead><tbody>"
        f"<tr><td>{sugar.unique_code}</td><td>Сахар</td>"
        "<td>200.0</td><td>190.0</td></tr>"
        f"<tr><td>{milk.unique_code}</td><td>Молоко</td>"
        "<td>250.0</td><td>240.0</td></tr>"
        "</tbody></table>"
    )
    assert result.binary == []
