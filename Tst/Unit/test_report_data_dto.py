import pytest

from Src.Dtos.report_data_dto import report_data_dto
from Src.Dtos.report_row_dto import report_row_dto


def test_report_data_dto_exposes_read_only_properties():
    """Проверяет доступ к данным DTO только через свойства."""
    # Подготовка
    row = report_row_dto(["Сахар", 100])
    data = report_data_dto(
        root_name="recipe",
        row_name="ingredient",
        name="Карамель",
        keys=["name", "weight"],
        headers=["name", "weight"],
        rows=[row],
        numeric_columns=frozenset([1]),
    )

    # Действие
    values = data.rows[0].values

    # Проверки
    assert data.root_name == "recipe"
    assert data.row_name == "ingredient"
    assert data.name == "Карамель"
    assert data.keys == ["name", "weight"]
    assert data.headers == ["name", "weight"]
    assert data.rows == [row]
    assert values == ["Сахар", 100]
    assert data.numeric_columns == frozenset([1])
    with pytest.raises(AttributeError):
        data.name = "Другое имя"
