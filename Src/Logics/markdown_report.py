from Src.Core.abstarct_report import abstract_report
from Src.Core.validator import validator
from Src.Dtos.report_result_dto import report_result_dto
from Src.Models.recipe_model import recipe_model


class markdown_report(abstract_report):
    """Формирует состав рецепта в виде Markdown-таблицы."""

    @staticmethod
    def __escape(value: object) -> str:
        """Экранирует символы, влияющие на структуру Markdown-таблицы."""
        return str(value).replace("\\", "\\\\").replace("|", "\\|")

    def build(self, source: recipe_model) -> report_result_dto:
        """Создаёт Markdown-таблицу с ингредиентами рецепта."""
        validator.validate(source, recipe_model)
        rows = [
            "| Код | Наименование | Брутто | Нетто |",
            "| --- | --- | ---: | ---: |",
        ]

        for item in source.ingredients:
            values = (
                item.unique_code,
                item.name,
                item.gross_weight,
                item.net_weight,
            )
            escaped_values = (self.__escape(value) for value in values)
            rows.append(f"| {' | '.join(escaped_values)} |")

        result = report_result_dto()
        result.text = "\n".join(rows)
        return result
