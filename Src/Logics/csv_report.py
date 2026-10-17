import csv
from io import StringIO

from Src.Core.abstarct_report import abstract_report
from Src.Core.validator import validator
from Src.Dtos.report_result_dto import report_result_dto
from Src.Models.recipe_model import recipe_model


class csv_report(abstract_report):
    """Формирует состав рецепта в формате CSV."""

    def build(self, source: recipe_model) -> report_result_dto:
        """Создаёт CSV-таблицу с ингредиентами рецепта."""
        validator.validate(source, recipe_model)
        stream = StringIO(newline="")
        writer = csv.writer(stream, lineterminator="\n")
        writer.writerow(("Код", "Наименование", "Брутто", "Нетто"))

        for item in source.ingredients:
            writer.writerow(
                (
                    item.unique_code,
                    item.name,
                    item.gross_weight,
                    item.net_weight,
                )
            )

        result = report_result_dto()
        result.text = stream.getvalue().rstrip("\n")
        return result
