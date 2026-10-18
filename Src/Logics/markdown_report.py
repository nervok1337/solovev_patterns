from Src.Core.abstract_binary_report import abstract_binary_report
from Src.Dtos.report_result_dto import report_result_dto
from Src.Logics.report_data import create_report_data


class markdown_report(abstract_binary_report):
    """Формирует данные сущности в виде Markdown-таблицы."""

    content_type = "text/markdown; charset=utf-8"
    file_name = "report.md"

    @staticmethod
    def __escape(value: object) -> str:
        """Экранирует символы, влияющие на структуру Markdown-таблицы."""
        return str(value).replace("\\", "\\\\").replace("|", "\\|")

    def build(self, source) -> report_result_dto:
        """Создаёт Markdown-таблицу с данными сущности."""
        data = create_report_data(source)
        rows = [
            f"| {' | '.join(data.headers)} |",
            "| "
            + " | ".join(
                "---:" if index in data.numeric_columns else "---"
                for index in range(len(data.headers))
            )
            + " |",
        ]

        for row in data.rows:
            escaped_values = (self.__escape(value) for value in row)
            rows.append(f"| {' | '.join(escaped_values)} |")

        result = report_result_dto()
        result.binary = list("\n".join(rows).encode("utf-8"))
        return result
