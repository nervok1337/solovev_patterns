from dataclasses import dataclass

from Src.Core.validator import validator
from Src.Models.nomenclature_model import nomenclature_model
from Src.Models.range_model import range_model
from Src.Models.recipe_model import recipe_model


@dataclass(frozen=True)
class report_data:
    """Унифицированные данные сущности для форматирования отчёта."""

    root_name: str
    row_name: str | None
    name: str
    keys: tuple[str, ...]
    headers: tuple[str, ...]
    rows: tuple[tuple[object, ...], ...]
    numeric_columns: frozenset[int] = frozenset()


def create_report_data(
    source: recipe_model | nomenclature_model | range_model,
) -> report_data:
    """Преобразует поддерживаемую сущность в табличные данные отчёта."""
    validator.validate(
        source,
        (recipe_model, nomenclature_model, range_model),
    )

    if isinstance(source, recipe_model):
        return report_data(
            root_name="recipe",
            row_name="ingredient",
            name=source.name,
            keys=("code", "name", "gross_weight", "net_weight"),
            headers=("Код", "Наименование", "Брутто", "Нетто"),
            rows=tuple(
                (
                    item.unique_code,
                    item.name,
                    item.gross_weight,
                    item.net_weight,
                )
                for item in source.ingredients
            ),
            numeric_columns=frozenset((2, 3)),
        )

    if isinstance(source, nomenclature_model):
        return report_data(
            root_name="nomenclature",
            row_name=None,
            name=source.name,
            keys=("code", "name", "full_name", "group", "unit"),
            headers=(
                "Код",
                "Наименование",
                "Полное наименование",
                "Группа",
                "Единица измерения",
            ),
            rows=(
                (
                    source.unique_code,
                    source.name,
                    source.full_name,
                    source.group.name,
                    source.range.name,
                ),
            ),
        )

    return report_data(
        root_name="range",
        row_name=None,
        name=source.name,
        keys=("code", "name", "conversion_factor", "base_unit"),
        headers=("Код", "Наименование", "Коэффициент", "Базовая единица"),
        rows=(
            (
                source.unique_code,
                source.name,
                source.conversion_factor,
                source.base_range.name,
            ),
        ),
        numeric_columns=frozenset((2,)),
    )
