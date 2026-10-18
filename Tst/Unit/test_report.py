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
        [
            "gross_weight",
            "id",
            "name",
            "net_weight",
            "nomenclature",
            "unique_code",
        ],
        ["200.0", sugar.id, "Сахар", "190.0", "Сахар", sugar.unique_code],
        ["250.0", milk.id, "Молоко", "240.0", "Молоко", milk.unique_code],
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
        (
            "| gross_weight | id | name | net_weight | nomenclature | "
            "unique_code |"
        ),
        "| ---: | --- | --- | ---: | --- | --- |",
        (
            f"| 200.0 | {sugar.id} | Сахар | 190.0 | Сахар | "
            f"{sugar.unique_code} |"
        ),
        (
            f"| 250.0 | {milk.id} | Молоко | 240.0 | Молоко | "
            f"{milk.unique_code} |"
        ),
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
            "gross_weight": "200.0",
            "id": sugar.id,
            "name": "Сахар",
            "net_weight": "190.0",
            "nomenclature": "Сахар",
            "unique_code": sugar.unique_code,
        },
        {
            "gross_weight": "250.0",
            "id": milk.id,
            "name": "Молоко",
            "net_weight": "240.0",
            "nomenclature": "Молоко",
            "unique_code": milk.unique_code,
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
        "<th>gross_weight</th><th>id</th><th>name</th>"
        "<th>net_weight</th><th>nomenclature</th><th>unique_code</th>"
        "</tr></thead><tbody>"
        f"<tr><td>200.0</td><td>{sugar.id}</td><td>Сахар</td>"
        f"<td>190.0</td><td>Сахар</td><td>{sugar.unique_code}</td></tr>"
        f"<tr><td>250.0</td><td>{milk.id}</td><td>Молоко</td>"
        f"<td>240.0</td><td>Молоко</td><td>{milk.unique_code}</td></tr>"
        "</tbody></table>"
    )
    assert result.binary == []
