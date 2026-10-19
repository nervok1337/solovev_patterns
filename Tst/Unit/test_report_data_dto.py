import pytest

from Src.Dtos.report_data_dto import report_data_dto


def test_report_data_dto_exposes_read_only_properties():
    """Проверяет доступ к данным DTO только через свойства."""
    # Подготовка
    data = report_data_dto(
        root_name="recipe",
        row_name="ingredient",
        name="Карамель",
        keys=("name", "weight"),
        headers=("name", "weight"),
        rows=(("Сахар", 100),),
        numeric_columns=frozenset((1,)),
    )

    # Действие
    values = (
        data.root_name,
        data.row_name,
        data.name,
        data.keys,
        data.headers,
        data.rows,
        data.numeric_columns,
    )

    # Проверки
    assert values == (
        "recipe",
        "ingredient",
        "Карамель",
        ("name", "weight"),
        ("name", "weight"),
        (("Сахар", 100),),
        frozenset((1,)),
    )
    with pytest.raises(AttributeError):
        data.name = "Другое имя"
