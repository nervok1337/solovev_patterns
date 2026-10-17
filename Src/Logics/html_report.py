from html import escape

from Src.Core.abstarct_report import abstract_report
from Src.Core.validator import validator
from Src.Dtos.report_result_dto import report_result_dto
from Src.Models.recipe_model import recipe_model


class html_report(abstract_report):
    """Формирует состав рецепта в виде HTML-таблицы."""

    def build(self, source: recipe_model) -> report_result_dto:
        """Создаёт HTML-таблицу с ингредиентами рецепта."""
        validator.validate(source, recipe_model)
        rows = []

        for item in source.ingredients:
            values = (
                item.unique_code,
                item.name,
                item.gross_weight,
                item.net_weight,
            )
            cells = "".join(f"<td>{escape(str(value))}</td>" for value in values)
            rows.append(f"<tr>{cells}</tr>")

        result = report_result_dto()
        result.text = (
            "<table>"
            "<thead><tr>"
            "<th>Код</th>"
            "<th>Наименование</th>"
            "<th>Брутто</th>"
            "<th>Нетто</th>"
            "</tr></thead>"
            f"<tbody>{''.join(rows)}</tbody>"
            "</table>"
        )
        return result
